#!/usr/bin/env python3
import argparse
import http.server
import json
import os
import pathlib
import socketserver
import subprocess
import sys
import time
import urllib.parse


DEFAULT_REDIRECT_URI = "http://localhost:3000/callback"
DEFAULT_SCOPE = "offline_access"


def build_parser():
    parser = argparse.ArgumentParser(
        description="Run a localhost Feishu OAuth callback and write user tokens to .env."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3000)
    parser.add_argument("--redirect-uri", default=DEFAULT_REDIRECT_URI)
    parser.add_argument("--scope", default=DEFAULT_SCOPE)
    parser.add_argument("--state")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--timeout-seconds", type=int, default=240)
    return parser


def non_empty_env(name):
    value = os.environ.get(name, "").strip()
    return value or None


def build_auth_url(app_id, redirect_uri, scope, state):
    query = {
        "client_id": app_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state,
    }
    if scope:
        query["scope"] = scope
    return "https://accounts.feishu.cn/open-apis/authen/v1/authorize?" + urllib.parse.urlencode(query)


def exchange_code(app_id, app_secret, code, redirect_uri):
    body = json.dumps(
        {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": app_id,
            "client_secret": app_secret,
            "redirect_uri": redirect_uri,
        },
        ensure_ascii=False,
    )
    completed = subprocess.run(
        [
            "curl",
            "-sS",
            "https://open.feishu.cn/open-apis/authen/v2/oauth/token",
            "-H",
            "Content-Type: application/json; charset=utf-8",
            "-d",
            body,
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        return {"ok": False, "error": "curl failed", "stderr": completed.stderr[:300]}
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {
            "ok": False,
            "error": "non-json exchange response",
            "raw_prefix": completed.stdout[:120],
        }

    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    token = data.get("user_access_token") or data.get("access_token") if isinstance(data, dict) else ""
    refresh = data.get("refresh_token") or data.get("user_refresh_token") if isinstance(data, dict) else ""
    if not token:
        return {
            "ok": False,
            "response_code": payload.get("code"),
            "error": payload.get("error") or payload.get("msg") or payload.get("message"),
            "error_description": payload.get("error_description"),
            "response_keys": sorted(data.keys()) if isinstance(data, dict) else [],
        }
    return {
        "ok": True,
        "response_code": payload.get("code"),
        "access_token": token,
        "refresh_token": refresh,
        "response_keys": sorted(data.keys()) if isinstance(data, dict) else [],
    }


def upsert_env(env_path, values):
    env_path = pathlib.Path(env_path)
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    else:
        lines = []

    for name, value in values.items():
        if not value:
            continue
        line = f"{name}={value}"
        for index, existing in enumerate(lines):
            if existing.startswith(name + "="):
                lines[index] = line
                break
        else:
            lines.append(line)

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def make_handler(options, app_id, app_secret, state):
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            return

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            if parsed.path != urllib.parse.urlparse(options.redirect_uri).path:
                self.send_response(404)
                self.end_headers()
                return

            code = params.get("code", [""])[0]
            callback_state = params.get("state", [""])[0]
            if callback_state != state:
                result = {"ok": False, "error": "state mismatch"}
            elif not code:
                result = {
                    "ok": False,
                    "error": "missing authorization code",
                    "query_keys": sorted(params.keys()),
                }
            else:
                result = exchange_code(app_id, app_secret, code, options.redirect_uri)
                if result.get("ok"):
                    upsert_env(
                        options.env_file,
                        {
                            "FEISHU_USER_ACCESS_TOKEN": result.get("access_token"),
                            "FEISHU_USER_REFRESH_TOKEN": result.get("refresh_token"),
                        },
                    )
                    result = {
                        "ok": True,
                        "response_code": result.get("response_code"),
                        "response_keys": result.get("response_keys", []),
                        "access_token_len": len(result.get("access_token") or ""),
                        "refresh_token_len": len(result.get("refresh_token") or ""),
                    }

            self.server.result = result
            ok = bool(result.get("ok"))
            self.send_response(200 if ok else 500)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            message = (
                "授权完成，可以回到 Codex。"
                if ok
                else "授权失败，请回到 Codex 查看原因。"
            )
            self.wfile.write(f"<html><body><h3>{message}</h3></body></html>".encode("utf-8"))
            self.server.should_stop = True

    return Handler


def main(argv=None):
    options = build_parser().parse_args(argv)
    app_id = non_empty_env("FEISHU_APP_ID")
    app_secret = non_empty_env("FEISHU_APP_SECRET")
    if not app_id or not app_secret:
        print("error: FEISHU_APP_ID and FEISHU_APP_SECRET are required.", file=sys.stderr)
        return 2

    state = options.state or f"codex-feishu-oauth-{int(time.time())}"
    auth_url = build_auth_url(app_id, options.redirect_uri, options.scope, state)
    handler = make_handler(options, app_id, app_secret, state)

    with ReusableTCPServer((options.host, options.port), handler) as httpd:
        httpd.timeout = 1
        httpd.should_stop = False
        httpd.result = None
        print("AUTH_URL=" + auth_url, flush=True)
        print("WAITING_FOR_CALLBACK=" + options.redirect_uri, flush=True)
        deadline = time.time() + options.timeout_seconds
        while not httpd.should_stop and time.time() < deadline:
            httpd.handle_request()

        if not httpd.result:
            print(
                json.dumps(
                    {"ok": False, "error": "timed out waiting for browser callback"},
                    ensure_ascii=False,
                ),
                flush=True,
            )
            return 5
        print(json.dumps(httpd.result, ensure_ascii=False), flush=True)
        return 0 if httpd.result.get("ok") else 6


if __name__ == "__main__":
    sys.exit(main())
