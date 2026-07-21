#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import time
import urllib.parse


BASE_URL = "https://open.feishu.cn"
JSONRPC_VERSION = "2.0"
USER_TOKEN_ENV = "FEISHU_USER_ACCESS_TOKEN"
USER_REFRESH_TOKEN_ENV = "FEISHU_USER_REFRESH_TOKEN"


def _non_empty_env(name):
    value = os.environ.get(name, "").strip()
    return value or None


class FeishuError(Exception):
    def __init__(self, message, *, payload=None, status=None):
        super().__init__(message)
        self.payload = payload
        self.status = status


class FeishuClient:
    def __init__(self):
        self.app_id = _non_empty_env("FEISHU_APP_ID")
        self.app_secret = _non_empty_env("FEISHU_APP_SECRET")
        self.user_access_token = _non_empty_env(USER_TOKEN_ENV)
        self.user_refresh_token = _non_empty_env(USER_REFRESH_TOKEN_ENV)
        self._tenant_token = None
        self._tenant_token_expires_at = 0

    def require_user_token(self):
        if not self.user_access_token:
            raise FeishuError(
                f"{USER_TOKEN_ENV} is required for this tool. Exchange a fresh browser code first."
            )
        return self.user_access_token

    def get_tenant_token(self):
        now = int(time.time())
        if self._tenant_token and now < self._tenant_token_expires_at - 60:
            return self._tenant_token

        if not self.app_id or not self.app_secret:
            raise FeishuError("FEISHU_APP_ID and FEISHU_APP_SECRET are required for tenant token mode.")

        payload = self._raw_request(
            "POST",
            "/open-apis/auth/v3/tenant_access_token/internal",
            body={"app_id": self.app_id, "app_secret": self.app_secret},
            auth_token=None,
        )
        token = payload.get("tenant_access_token")
        expires_in = int(payload.get("expire", 0))
        if not token:
            raise FeishuError("Failed to obtain tenant_access_token.", payload=payload)
        self._tenant_token = token
        self._tenant_token_expires_at = now + expires_in
        return token

    def _persist_user_tokens(self, access_token, refresh_token=None):
        env_path = os.environ.get("FEISHU_ENV_FILE", ".env")
        try:
            with open(env_path, "r", encoding="utf-8") as fh:
                lines = fh.read().splitlines()
        except FileNotFoundError:
            lines = []

        def upsert(name, value):
            if not value:
                return
            line = f"{name}={value}"
            for index, existing in enumerate(lines):
                if existing.startswith(name + "="):
                    lines[index] = line
                    return
            lines.append(line)

        upsert(USER_TOKEN_ENV, access_token)
        upsert(USER_REFRESH_TOKEN_ENV, refresh_token)
        with open(env_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")

    def refresh_user_token(self):
        if not self.user_refresh_token:
            raise FeishuError(
                f"{USER_REFRESH_TOKEN_ENV} is required to refresh an expired user token."
            )
        if not self.app_id or not self.app_secret:
            raise FeishuError("FEISHU_APP_ID and FEISHU_APP_SECRET are required to refresh user token.")

        payload = self._raw_request(
            "POST",
            "/open-apis/authen/v2/oauth/token",
            body={
                "grant_type": "refresh_token",
                "refresh_token": self.user_refresh_token,
                "client_id": self.app_id,
                "client_secret": self.app_secret,
            },
            auth_token=None,
        )
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        token = data.get("user_access_token") or data.get("access_token")
        refresh_token = data.get("refresh_token") or data.get("user_refresh_token")
        if not token:
            raise FeishuError("Failed to refresh user access token.", payload=payload)
        self.user_access_token = token
        if refresh_token:
            self.user_refresh_token = refresh_token
        self._persist_user_tokens(self.user_access_token, self.user_refresh_token)
        return self.user_access_token

    def _is_expired_user_token_error(self, exc):
        payload = getattr(exc, "payload", None)
        if not isinstance(payload, dict):
            return False
        message = " ".join(
            str(payload.get(key, ""))
            for key in ("msg", "error", "error_description", "message")
        ).lower()
        return "expired" in message or "invalid access token" in message

    def request(self, method, path, *, query=None, body=None, token_mode="user"):
        if token_mode == "tenant":
            token = self.get_tenant_token()
        elif token_mode == "user":
            token = self.require_user_token()
        elif token_mode == "none":
            token = None
        else:
            raise FeishuError(f"Unsupported token mode: {token_mode}")

        try:
            return self._raw_request(method, path, query=query, body=body, auth_token=token)
        except FeishuError as exc:
            if token_mode != "user" or not self._is_expired_user_token_error(exc):
                raise
            token = self.refresh_user_token()
            return self._raw_request(method, path, query=query, body=body, auth_token=token)

    def _raw_request(self, method, path, *, query=None, body=None, auth_token=None):
        url = BASE_URL + path
        if query:
            query = {k: v for k, v in query.items() if v is not None and v != ""}
            if query:
                url = f"{url}?{urllib.parse.urlencode(query, doseq=True)}"

        command = ["curl", "-sS", "-X", method.upper(), url]
        if auth_token:
            command.extend(["-H", f"Authorization: Bearer {auth_token}"])
        if body is not None:
            command.extend(["-H", "Content-Type: application/json; charset=utf-8"])
            command.extend(["-d", json.dumps(body, ensure_ascii=False)])

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
        except subprocess.TimeoutExpired as exc:
            raise FeishuError(f"Timed out calling Feishu OpenAPI: {exc}") from exc

        raw = completed.stdout
        if completed.returncode != 0:
            raise FeishuError(
                f"curl failed calling Feishu OpenAPI: {completed.stderr.strip() or completed.returncode}"
            )

        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            raise FeishuError("Non-JSON response from Feishu OpenAPI.", payload={"raw": raw[:1000]})

        if isinstance(payload, dict) and payload.get("code") not in (None, 0):
            raise FeishuError(payload.get("msg") or "Feishu OpenAPI returned an error.", payload=payload)

        return payload


client = FeishuClient()


def compact_dict(*dicts):
    merged = {}
    for item in dicts:
        if not isinstance(item, dict):
            continue
        for key, value in item.items():
            if value is not None:
                merged[key] = value
    return merged


def tool_result(payload):
    return {
        "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}]
    }


def error_result(message, *, payload=None):
    body = {"errorMessage": message, "instruction": ""}
    if payload is not None:
        body["details"] = payload
    return {
        "content": [{"type": "text", "text": json.dumps(body, ensure_ascii=False)}],
        "isError": True,
    }


TOOLS = [
    {
        "name": "im_v1_chat_list",
        "description": "[Stable HTTP]-Get chats visible to the authorized user or bot.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "params": {"type": "object"},
                "useUAT": {"type": "boolean"},
            },
        },
    },
    {
        "name": "im_v1_chatMembers_get",
        "description": "[Stable HTTP]-Get group members for a chat.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "object", "required": ["chat_id"]},
                "params": {"type": "object"},
                "useUAT": {"type": "boolean"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "im_v1_message_list",
        "description": "[Stable HTTP]-Get message history for a chat or p2p container.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "object"},
                "params": {"type": "object"},
                "useUAT": {"type": "boolean"},
            },
        },
    },
    {
        "name": "im_v1_message_create",
        "description": "[Stable HTTP]-Send a Feishu message.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "data": {"type": "object"},
                "params": {"type": "object"},
                "useUAT": {"type": "boolean"},
            },
            "required": ["data"],
        },
    },
    {
        "name": "docx_v1_document_rawContent",
        "description": "[Stable HTTP]-Get plain text content from a Feishu document.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "object", "required": ["document_id"]},
                "params": {"type": "object"},
                "useUAT": {"type": "boolean"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "docx_builtin_search",
        "description": "[Stable HTTP]-Search user-visible Feishu docs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "data": {"type": "object"},
                "useUAT": {"type": "boolean"},
            },
            "required": ["data"],
        },
    },
    {
        "name": "docx_v1_document_create",
        "description": "[Stable HTTP]-Create a user-owned Feishu Docx document.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "data": {"type": "object"},
                "useUAT": {"type": "boolean"},
            },
        },
    },
    {
        "name": "docx_v1_documentBlockChildren_create",
        "description": "[Stable HTTP]-Append child blocks to a Feishu Docx block.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "object"},
                "data": {"type": "object"},
                "params": {"type": "object"},
                "useUAT": {"type": "boolean"},
            },
            "required": ["path", "data"],
        },
    },
    {
        "name": "drive_v1_meta_batchQuery",
        "description": "[Stable HTTP]-Resolve Feishu document metadata and URLs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "data": {"type": "object"},
                "params": {"type": "object"},
                "useUAT": {"type": "boolean"},
            },
            "required": ["data"],
        },
    },
    {
        "name": "wiki_v1_node_search",
        "description": "[Stable HTTP]-Search Feishu Wiki nodes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "data": {"type": "object"},
                "params": {"type": "object"},
                "useUAT": {"type": "boolean"},
            },
            "required": ["data"],
        },
    },
    {
        "name": "wiki_v2_space_getNode",
        "description": "[Stable HTTP]-Get Feishu Wiki node metadata.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "params": {"type": "object", "required": ["token"]},
                "useUAT": {"type": "boolean"},
            },
            "required": ["params"],
        },
    },
    {
        "name": "contact_v3_user_batchGetId",
        "description": "[Stable HTTP]-Get user IDs by email or mobile.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "data": {"type": "object"},
                "params": {"type": "object"},
            },
            "required": ["data"],
        },
    },
    {
        "name": "bitable_v1_appTableRecord_create",
        "description": "[Stable HTTP]-Create one Feishu Bitable record.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "object"},
                "data": {"type": "object"},
                "params": {"type": "object"},
                "useUAT": {"type": "boolean"},
            },
            "required": ["path", "data"],
        },
    },
    {
        "name": "feishu_openapi_request",
        "description": "[Stable HTTP]-Call a Feishu OpenAPI path directly.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "method": {"type": "string"},
                "path": {"type": "string"},
                "query": {"type": "object"},
                "body": {"type": "object"},
                "token_mode": {"type": "string"},
            },
            "required": ["method", "path"],
        },
    },
]


def token_mode_from_use_uat(use_uat, *, default="user"):
    if use_uat is True:
        return "user"
    if use_uat is False:
        return "tenant"
    return default


def handle_tool_call(name, arguments):
    arguments = arguments or {}

    if name == "im_v1_chat_list":
        payload = client.request(
            "GET",
            "/open-apis/im/v1/chats",
            query=arguments.get("params"),
            token_mode=token_mode_from_use_uat(arguments.get("useUAT"), default="user"),
        )
        return tool_result(payload)

    if name == "im_v1_chatMembers_get":
        path = arguments.get("path") or {}
        payload = client.request(
            "GET",
            f"/open-apis/im/v1/chats/{path['chat_id']}/members",
            query=arguments.get("params"),
            token_mode=token_mode_from_use_uat(arguments.get("useUAT"), default="user"),
        )
        return tool_result(payload)

    if name == "im_v1_message_list":
        query = compact_dict(arguments.get("params"), arguments.get("path"))
        payload = client.request(
            "GET",
            "/open-apis/im/v1/messages",
            query=query,
            token_mode=token_mode_from_use_uat(arguments.get("useUAT"), default="user"),
        )
        return tool_result(payload)

    if name == "im_v1_message_create":
        payload = client.request(
            "POST",
            "/open-apis/im/v1/messages",
            query=arguments.get("params"),
            body=arguments.get("data"),
            token_mode=token_mode_from_use_uat(arguments.get("useUAT"), default="tenant"),
        )
        return tool_result(payload)

    if name == "docx_v1_document_rawContent":
        path = arguments.get("path") or {}
        payload = client.request(
            "GET",
            f"/open-apis/docx/v1/documents/{path['document_id']}/raw_content",
            query=arguments.get("params"),
            token_mode=token_mode_from_use_uat(arguments.get("useUAT"), default="user"),
        )
        return tool_result(payload)

    if name == "docx_builtin_search":
        body = arguments.get("data") or {}
        payload = client.request(
            "POST",
            "/open-apis/suite/docs-api/search/object",
            body=body,
            token_mode=token_mode_from_use_uat(arguments.get("useUAT"), default="user"),
        )
        return tool_result(payload)

    if name == "docx_v1_document_create":
        payload = client.request(
            "POST",
            "/open-apis/docx/v1/documents",
            body=arguments.get("data"),
            token_mode=token_mode_from_use_uat(arguments.get("useUAT"), default="user"),
        )
        return tool_result(payload)

    if name == "docx_v1_documentBlockChildren_create":
        path = arguments.get("path") or {}
        payload = client.request(
            "POST",
            f"/open-apis/docx/v1/documents/{path['document_id']}/blocks/{path['block_id']}/children",
            query=arguments.get("params"),
            body=arguments.get("data"),
            token_mode=token_mode_from_use_uat(arguments.get("useUAT"), default="user"),
        )
        return tool_result(payload)

    if name == "drive_v1_meta_batchQuery":
        payload = client.request(
            "POST",
            "/open-apis/drive/v1/metas/batch_query",
            query=arguments.get("params"),
            body=arguments.get("data"),
            token_mode=token_mode_from_use_uat(arguments.get("useUAT"), default="user"),
        )
        return tool_result(payload)

    if name == "wiki_v1_node_search":
        payload = client.request(
            "POST",
            "/open-apis/wiki/v2/nodes/search",
            query=arguments.get("params"),
            body=arguments.get("data"),
            token_mode=token_mode_from_use_uat(arguments.get("useUAT"), default="user"),
        )
        return tool_result(payload)

    if name == "wiki_v2_space_getNode":
        payload = client.request(
            "GET",
            "/open-apis/wiki/v2/spaces/get_node",
            query=arguments.get("params"),
            token_mode=token_mode_from_use_uat(arguments.get("useUAT"), default="user"),
        )
        return tool_result(payload)

    if name == "contact_v3_user_batchGetId":
        payload = client.request(
            "POST",
            "/open-apis/contact/v3/users/batch_get_id",
            query=arguments.get("params"),
            body=arguments.get("data"),
            token_mode="tenant",
        )
        return tool_result(payload)

    if name == "bitable_v1_appTableRecord_create":
        path = arguments.get("path") or {}
        payload = client.request(
            "POST",
            f"/open-apis/bitable/v1/apps/{path['app_token']}/tables/{path['table_id']}/records",
            query=arguments.get("params"),
            body=arguments.get("data"),
            token_mode=token_mode_from_use_uat(arguments.get("useUAT"), default="user"),
        )
        return tool_result(payload)

    if name == "feishu_openapi_request":
        payload = client.request(
            arguments["method"].upper(),
            arguments["path"],
            query=arguments.get("query"),
            body=arguments.get("body"),
            token_mode=arguments.get("token_mode", "user"),
        )
        return tool_result(payload)

    raise FeishuError(f"Unknown tool: {name}")


def send_message(payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
    sys.stdout.buffer.write(header)
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def send_response(msg_id, result=None, error=None):
    payload = {"jsonrpc": JSONRPC_VERSION, "id": msg_id}
    if error is not None:
        payload["error"] = error
    else:
        payload["result"] = result
    send_message(payload)


def read_message():
    headers = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        decoded = line.decode("utf-8").strip()
        if ":" in decoded:
            key, value = decoded.split(":", 1)
            headers[key.lower()] = value.strip()

    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    body = sys.stdin.buffer.read(length)
    return json.loads(body.decode("utf-8"))


def main():
    while True:
        message = read_message()
        if message is None:
            break

        method = message.get("method")
        msg_id = message.get("id")

        try:
            if method == "initialize":
                send_response(
                    msg_id,
                    {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {"listChanged": False}},
                        "serverInfo": {
                            "name": "Feishu Stable HTTP MCP",
                            "version": "1.1.1",
                        },
                    },
                )
            elif method == "notifications/initialized":
                continue
            elif method == "tools/list":
                send_response(msg_id, {"tools": TOOLS})
            elif method == "tools/call":
                params = message.get("params") or {}
                send_response(msg_id, handle_tool_call(params.get("name"), params.get("arguments")))
            else:
                send_response(
                    msg_id,
                    error={"code": -32601, "message": f"Method not found: {method}"},
                )
        except FeishuError as exc:
            send_response(msg_id, handle_tool_call_error(exc))
        except Exception as exc:
            send_response(
                msg_id,
                error={"code": -32000, "message": str(exc)},
            )


def handle_tool_call_error(exc):
    return error_result(str(exc), payload=exc.payload)


if __name__ == "__main__":
    main()
