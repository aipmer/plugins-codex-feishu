#!/usr/bin/env python3
import argparse
import base64
import hashlib
import json
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 3000
DEFAULT_PATH = "/webhook/feishu"


def _env(name, default=None):
    value = os.environ.get(name, "").strip()
    return value or default


def _json_response(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _read_json(handler):
    length = int(handler.headers.get("Content-Length", "0"))
    if length <= 0:
        return {}, ""
    raw = handler.rfile.read(length)
    raw_text = raw.decode("utf-8")
    return json.loads(raw_text), raw_text


def _unpad_pkcs7(data):
    if not data:
        return data
    pad = data[-1]
    if pad < 1 or pad > 16:
        return data
    if data[-pad:] != bytes([pad]) * pad:
        return data
    return data[:-pad]


def decrypt_feishu_event(encrypted, encrypt_key):
    encrypted_bytes = base64.b64decode(encrypted)
    if len(encrypted_bytes) <= 16:
        raise ValueError("encrypted payload is too short")

    iv = encrypted_bytes[:16]
    ciphertext = encrypted_bytes[16:]
    key = hashlib.sha256(encrypt_key.encode("utf-8")).digest()

    try:
        from Crypto.Cipher import AES  # type: ignore

        cipher = AES.new(key, AES.MODE_CBC, iv)
        plaintext = _unpad_pkcs7(cipher.decrypt(ciphertext))
    except ImportError:
        plaintext = _decrypt_with_openssl(ciphertext, key, iv)

    return json.loads(plaintext.decode("utf-8"))


def _decrypt_with_openssl(ciphertext, key, iv):
    proc = subprocess.run(
        [
            "openssl",
            "enc",
            "-aes-256-cbc",
            "-d",
            "-K",
            key.hex(),
            "-iv",
            iv.hex(),
        ],
        input=ciphertext,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        proc = subprocess.run(
            [
                "openssl",
                "enc",
                "-aes-256-cbc",
                "-d",
                "-nopad",
                "-K",
                key.hex(),
                "-iv",
                iv.hex(),
            ],
            input=ciphertext,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="replace").strip())
    return _unpad_pkcs7(proc.stdout)


def normalize_payload(payload, encrypt_key):
    if "encrypt" not in payload:
        return payload
    if not encrypt_key:
        raise ValueError("FEISHU_ENCRYPT_KEY is required for encrypted Feishu events")
    return decrypt_feishu_event(payload["encrypt"], encrypt_key)


def verify_token(payload, expected_token):
    if not expected_token:
        return True
    return payload.get("token") == expected_token


def calculate_signature(timestamp, nonce, encrypt_key, raw_body):
    content = (timestamp + nonce + encrypt_key + raw_body).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def verify_signature(headers, encrypt_key, raw_body):
    if not encrypt_key:
        return True

    expected = headers.get("X-Lark-Signature") or headers.get("x-lark-signature")
    timestamp = headers.get("X-Lark-Request-Timestamp") or headers.get("x-lark-request-timestamp")
    nonce = headers.get("X-Lark-Request-Nonce") or headers.get("x-lark-request-nonce")

    require_signature = _env("FEISHU_REQUIRE_SIGNATURE", "1") != "0"
    if not expected or not timestamp or not nonce:
        return not require_signature

    actual = calculate_signature(timestamp, nonce, encrypt_key, raw_body)
    return actual == expected


def event_type(payload):
    header = payload.get("header") or {}
    event = payload.get("event") or {}
    return payload.get("type") or header.get("event_type") or event.get("type") or "unknown"


def log_event(payload):
    log_path = _env("FEISHU_WEBHOOK_EVENT_LOG")
    line = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if log_path:
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    print(line, flush=True)


class FeishuWebhookHandler(BaseHTTPRequestHandler):
    server_version = "FeishuWebhook/1.0"

    def do_GET(self):
        if self.path == "/health":
            _json_response(self, 200, {"ok": True})
            return
        _json_response(self, 404, {"error": "not found"})

    def do_POST(self):
        configured_path = self.server.webhook_path  # type: ignore[attr-defined]
        if self.path != configured_path:
            _json_response(self, 404, {"error": "not found"})
            return

        try:
            raw_payload, raw_body = _read_json(self)
        except Exception as exc:
            _json_response(self, 400, {"error": str(exc)})
            return

        if not verify_signature(self.headers, self.server.encrypt_key, raw_body):  # type: ignore[attr-defined]
            _json_response(self, 403, {"error": "signature mismatch"})
            return

        try:
            payload = normalize_payload(raw_payload, self.server.encrypt_key)  # type: ignore[attr-defined]
        except Exception as exc:
            _json_response(self, 400, {"error": str(exc)})
            return

        if not verify_token(payload, self.server.verification_token):  # type: ignore[attr-defined]
            _json_response(self, 403, {"error": "verification token mismatch"})
            return

        if payload.get("type") == "url_verification" or "challenge" in payload:
            _json_response(self, 200, {"challenge": payload.get("challenge", "")})
            return

        log_event({"event_type": event_type(payload), "payload": payload})
        _json_response(self, 200, {"ok": True})

    def log_message(self, fmt, *args):
        if _env("FEISHU_WEBHOOK_QUIET") == "1":
            return
        super().log_message(fmt, *args)


def run_server(host, port, path):
    server = ThreadingHTTPServer((host, port), FeishuWebhookHandler)
    server.webhook_path = path
    server.verification_token = _env("FEISHU_VERIFICATION_TOKEN")
    server.encrypt_key = _env("FEISHU_ENCRYPT_KEY")
    print(f"Feishu webhook listening on http://{host}:{port}{path}", flush=True)
    print("Health check: http://{}:{}/health".format(host, port), flush=True)
    server.serve_forever()


def self_test():
    assert verify_token({"token": "abc"}, "abc")
    assert not verify_token({"token": "abc"}, "def")
    assert calculate_signature("1", "2", "3", "{}") == hashlib.sha256(b"123{}").hexdigest()
    assert event_type({"header": {"event_type": "im.message.receive_v1"}}) == "im.message.receive_v1"
    assert normalize_payload({"type": "url_verification", "challenge": "ok"}, None)["challenge"] == "ok"
    print("ok: webhook self-test passed")


def main():
    parser = argparse.ArgumentParser(description="Run a minimal Feishu event webhook receiver.")
    parser.add_argument("--host", default=_env("FEISHU_WEBHOOK_HOST", DEFAULT_HOST))
    parser.add_argument("--port", type=int, default=int(_env("FEISHU_WEBHOOK_PORT", str(DEFAULT_PORT))))
    parser.add_argument("--path", default=_env("FEISHU_WEBHOOK_PATH", DEFAULT_PATH))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return

    run_server(args.host, args.port, args.path)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
