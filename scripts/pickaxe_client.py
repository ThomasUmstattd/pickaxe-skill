#!/usr/bin/env python3
"""Minimal client for the Pickaxe HTTP JSON-RPC API. Stdlib only.

Why this exists: MCP client layers reject large payloads before they reach
Pickaxe, response envelopes are not uniform across tools, and hand-rolled
copies of this helper drift apart (a crash-on-success bug fixed in one copy
of a project's helper survived in two others). Use one shared client.

Key loading order:
  1. PICKAXE_API_KEY environment variable (the bare studio-... key)
  2. ~/.claude.json  ->  mcpServers[<server>].headers.Authorization
  3. ~/.cursor/mcp.json  ->  mcpServers[<server>].headers.Authorization

Usage from the shell:
    python3 pickaxe_client.py pickaxe_list '{}'
    python3 pickaxe_client.py pickaxe_get '{"pickaxe_id": "ABC123XYZ0"}'
    python3 pickaxe_client.py --server pickaxe-other pickaxe_list '{}'

Usage from Python:
    from pickaxe_client import call, run_completion
    tools = call("pickaxe_list", {})
    reply = run_completion("ABC123XYZ0", "Hello")
    reply = run_completion("ABC123XYZ0", inputs={"userinput:<field-id>": "..."})

Remember: never trust a mutation's return value. Read the state back.
"""
import ast
import json
import os
import sys
import time
import urllib.error
import urllib.request

URL = "https://mcp.pickaxe.co"
DEFAULT_SERVER = "pickaxe"  # mcpServers entry name in client config files


class PickaxeError(RuntimeError):
    """A tool call that the server reported as failed."""


def load_token(server=DEFAULT_SERVER):
    """Return the Authorization header value, from env or client configs."""
    key = os.environ.get("PICKAXE_API_KEY", "").strip()
    if key:
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

    sys.exit(
        "error: no Pickaxe API key found. Set PICKAXE_API_KEY, or configure "
        f"an mcpServers entry named {server!r} in ~/.claude.json or "
        "~/.cursor/mcp.json. See references/getting-connected.md."
    )


def call(tool, args=None, server=DEFAULT_SERVER, timeout=120, token=None):
    """Call one Pickaxe tool over HTTP JSON-RPC and return its payload.

    Returns the envelope's `data` value when present, otherwise the whole
    structured result. Mutations like document_connect return {"success":
    true} with no data key, and that is a SUCCESS, so never require the
    data key. Raises PickaxeError on transport or tool failure.
    """
    payload = {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": tool, "arguments": args or {}},
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
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise PickaxeError(f"{tool}: HTTP {e.code} {e.read().decode()[:300]}")
    except urllib.error.URLError as e:
        raise PickaxeError(f"{tool}: {e.reason}")

    if "error" in d:
        raise PickaxeError(f"{tool}: {d['error']}")

    sc = d["result"].get("structuredContent")
    if sc is None:
        # Tool-level errors arrive as plain text content, not structured.
        raise PickaxeError(f"{tool}: {str(d['result'].get('content'))[:300]}")
    if not sc.get("success", True):
        raise PickaxeError(f"{tool}: {str(sc)[:300]}")
    return sc.get("data", sc)


def run_completion(pickaxe_id, message=None, server=DEFAULT_SERVER,
                   conversation_id=None, timeout=330, retries=2,
                   inputs=None):
    """Run a live completion and return the result text.

    Pass either `message` (a chat string) or `inputs` (a dict keyed by the
    form's `userinput:*` field ids from the prompt frame). They are not
    interchangeable: `message` never fires the prompt frame, so a form
    tool driven that way runs on the Role and Model Reminder alone, while
    `inputs` drives the real form path. See
    references/testing-and-verification.md before choosing.

    The response has arrived both as a Python-repr dict inside content
    text (parsed with ast.literal_eval, not json) and as a structured dict,
    so both shapes are unwrapped to the result text. Transient "Could not reach
    the Completion API" errors are retried with backoff, but a run that
    dies at ~300 seconds hit the server-side ceiling and a retry will not
    help unless the run gets faster (see references/limits-and-costs.md).
    Message runs are capped by the bot's chatinputlength, input runs by
    each field's answerlength, and every prompt you want tested must
    already be written to the live bot.
    """
    if (message is None) == (inputs is None):
        raise ValueError("pass exactly one of message or inputs")
    args = {"pickaxeId": pickaxe_id}
    if inputs is not None:
        args["inputs"] = inputs
    else:
        args["message"] = message
    if conversation_id:
        args["conversationId"] = conversation_id

    last = None
    for attempt in range(retries + 1):
        try:
            data = call("run_pickaxe_completion", args,
                        server=server, timeout=timeout)
        except PickaxeError as e:
            last = e
            if "Could not reach the Completion API" in str(e) and attempt < retries:
                time.sleep(10 * (attempt + 1))
                continue
            raise
        # The completion has arrived two ways within one month: as a
        # Python-repr dict inside content text (August 2026) and as a real
        # dict with success and result keys (September 2026). Handle both.
        if isinstance(data, str):
            try:
                parsed = ast.literal_eval(data)
                if isinstance(parsed, dict):
                    return parsed.get("result", parsed)
            except (ValueError, SyntaxError):
                pass
        elif isinstance(data, dict) and "result" in data:
            return data["result"]
        return data
    raise last


def main():
    argv = list(sys.argv[1:])
    server = DEFAULT_SERVER
    if argv[:1] == ["--server"]:
        if len(argv) < 2:
            sys.exit("error: --server needs a name")
        server, argv = argv[1], argv[2:]
    if not argv:
        sys.exit(__doc__)
    tool = argv[0]
    try:
        args = json.loads(argv[1]) if len(argv) > 1 else {}
    except json.JSONDecodeError as e:
        sys.exit(f"error: arguments must be a JSON object: {e}")
    try:
        result = call(tool, args, server=server)
    except PickaxeError as e:
        sys.exit(f"error: {e}")
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False, default=str)
    print()


if __name__ == "__main__":
    main()
