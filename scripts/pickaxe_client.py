#!/usr/bin/env python3
"""Dependency-free client for Pickaxe's HTTP JSON-RPC endpoint.

Credentials:
  * Explicit token= Authorization header for Python callers.
  * PICKAXE_API_KEY for the default server, "pickaxe", only.
  * Named mcpServers entries in ~/.claude.json or ~/.cursor/mcp.json.

A named server never falls back to the generic environment key.

Shell:
    python3 pickaxe_client.py pickaxe_list '{}'
    python3 pickaxe_client.py --server pickaxe-other pickaxe_list '{}'

Python:
    from pickaxe_client import call, run_completion
    reply = run_completion("BOT_ID", message="Hello")
    reply = run_completion("BOT_ID", inputs={"userinput:FIELD_ID": "..."})

Completion calls make one attempt by default. Read back remote mutations.
"""
import ast
import http.client
import json
import os
import sys
import time
import urllib.error
import urllib.request

URL = "https://mcp.pickaxe.co"
DEFAULT_SERVER = "pickaxe"


class PickaxeError(RuntimeError):
    """A transport, response, credential, or tool failure."""


def load_token(server=DEFAULT_SERVER):
    """Resolve one workspace without falling back across named servers."""
    key = os.environ.get("PICKAXE_API_KEY", "").strip()
    if server == DEFAULT_SERVER and key:
        return key if key.startswith("Bearer ") else f"Bearer {key}"

    for path in ("~/.claude.json", "~/.cursor/mcp.json"):
        full = os.path.expanduser(path)
        if not os.path.exists(full):
            continue
        try:
            with open(full) as f:
                servers = json.load(f).get("mcpServers", {})
            auth = servers.get(server, {}).get("headers", {}).get("Authorization")
        except (json.JSONDecodeError, AttributeError):
            continue
        if auth:
            return auth

    raise PickaxeError(
        f"no credentials for server {server!r}. Configure that mcpServers "
        "entry in ~/.claude.json or ~/.cursor/mcp.json, or pass token= "
        "to the Python client. PICKAXE_API_KEY applies only to 'pickaxe'."
    )


def _decode_text(value):
    """Recognize encoded envelopes without rewriting ordinary answer text."""
    if isinstance(value, str):
        for parse in (json.loads, ast.literal_eval):
            try:
                parsed = parse(value)
            except (ValueError, SyntaxError):
                continue
            if isinstance(parsed, dict) and isinstance(parsed.get("success"), bool):
                return parsed
    return value


def _check_success(tool, value):
    if isinstance(value, dict) and value.get("success") is False:
        raise PickaxeError(f"{tool}: {str(value)[:300]}")
    return value


def _read_response(response):
    """Read JSON or the matching JSON-RPC result from an MCP SSE response."""
    if "text/event-stream" not in getattr(response, "headers", {}).get("Content-Type", ""):
        return json.loads(response.read().decode())
    data = []
    for raw_line in response:
        line = raw_line.decode().rstrip("\r\n")
        if line.startswith("data:"):
            value = line[5:]
            data.append(value[1:] if value.startswith(" ") else value)
        elif not line and data:
            event = json.loads("\n".join(data))
            data = []
            if isinstance(event, dict) and event.get("id") == 1 and ("result" in event or "error" in event):
                return event
    raise PickaxeError("MCP event stream ended without the matching response")


def call(tool, args=None, server=DEFAULT_SERVER, timeout=120, token=None):
    """Call a tool once. Return data when present, otherwise its payload.

    token is a complete Authorization header, for example "Bearer ...".
    A mutation returning {"success": true} needs no data key to succeed.
    """
    if args is not None and not isinstance(args, dict):
        raise ValueError("tool arguments must be a JSON object")
    payload = {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": tool, "arguments": args if args is not None else {}},
    }
    req = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": token or load_token(server),
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            envelope = _read_response(response)
    except urllib.error.HTTPError as error:
        raise PickaxeError(f"{tool}: HTTP {error.code} {error.read().decode()[:300]}") from error
    except (urllib.error.URLError, ConnectionError, TimeoutError,
            http.client.HTTPException, UnicodeError, json.JSONDecodeError) as error:
        raise PickaxeError(f"{tool}: response unavailable or invalid: {error}") from error

    if not isinstance(envelope, dict):
        raise PickaxeError(f"{tool}: expected a JSON-RPC object")
    if "error" in envelope:
        raise PickaxeError(f"{tool}: {envelope['error']}")
    result = envelope.get("result")
    if not isinstance(result, dict):
        raise PickaxeError(f"{tool}: missing tool result")
    if result.get("isError"):
        raise PickaxeError(f"{tool}: {str(result.get('content', result))[:300]}")

    value = result.get("structuredContent")
    if value is None:
        blocks = result.get("content", [])
        if not isinstance(blocks, list):
            raise PickaxeError(f"{tool}: invalid content blocks")
        texts = [block["text"] for block in blocks
                 if isinstance(block, dict) and block.get("type") == "text"
                 and isinstance(block.get("text"), str)]
        if not texts:
            raise PickaxeError(f"{tool}: no structured or text payload")
        for text in texts:
            _check_success(tool, _decode_text(text))
        value = _decode_text("\n".join(texts))
    value = _check_success(tool, value)
    if isinstance(value, dict) and "data" in value:
        value = value["data"]
    return _check_success(tool, _decode_text(value))


def run_completion(pickaxe_id, message=None, server=DEFAULT_SERVER,
                   conversation_id=None, timeout=330, retries=0,
                   inputs=None, token=None):
    """Return a live completion, using exactly one of message or inputs.

    message bypasses the prompt frame. inputs exercises the form prompt
    with already-extracted text, not the real file-upload pipeline.

    No paid retries by default: an unavailable response may have completed
    and incurred cost. Recover history/Insights before buying another run.
    retries is an explicit opt-in retained for existing callers. It retries
    only "Could not reach the Completion API" errors, with backoff. It does
    not determine whether a failed request reached the server.
    """
    if (message is None) == (inputs is None):
        raise ValueError("pass exactly one of message or inputs")
    if message is not None and not isinstance(message, str):
        raise ValueError("message must be a string")
    if inputs is not None and not isinstance(inputs, dict):
        raise ValueError("inputs must be a dict")
    if not isinstance(retries, int) or retries < 0:
        raise ValueError("retries must be a nonnegative integer")
    args = {"pickaxeId": pickaxe_id}
    args["inputs" if inputs is not None else "message"] = inputs if inputs is not None else message
    if conversation_id:
        args["conversationId"] = conversation_id

    for attempt in range(retries + 1):
        try:
            data = call("run_pickaxe_completion", args, server=server,
                        timeout=timeout, token=token)
        except PickaxeError as error:
            if "Could not reach the Completion API" in str(error) and attempt < retries:
                time.sleep(10 * (attempt + 1))
                continue
            raise
        data = _check_success("run_pickaxe_completion", _decode_text(data))
        return data["result"] if isinstance(data, dict) and "result" in data else data


def main():
    argv = list(sys.argv[1:])
    server = DEFAULT_SERVER
    if argv[:1] == ["--server"]:
        if len(argv) < 2:
            sys.exit("error: --server needs a name")
        server, argv = argv[1], argv[2:]
    if not argv:
        sys.exit(__doc__)
    try:
        args = json.loads(argv[1]) if len(argv) > 1 else {}
        result = call(argv[0], args, server=server)
    except (ValueError, PickaxeError) as error:
        sys.exit(f"error: {error}")
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
