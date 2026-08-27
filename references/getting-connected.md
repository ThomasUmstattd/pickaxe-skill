# Getting connected

Pickaxe hosts an official MCP server at `https://mcp.pickaxe.co`. It speaks streamable HTTP MCP and also answers plain HTTP JSON-RPC POSTs, so the same key works for interactive MCP clients and for scripts.

## Find your API key

The key is a workspace API key, and the page it lives on is easy to miss.

1. Log in to Pickaxe Studio and open the workspace you want to control.
2. Open **Settings** for that workspace.
3. Find the **Workspace API Keys** section.
4. Below the key table, expand the panel labeled **Connect an MCP client**.
5. Click **Copy setup**. The UI masks the key on screen, so use what the copy button gives you.

Keys start with `studio-`. Each key is scoped to one workspace, so managing two workspaces means two keys and two MCP server entries.

Official docs: https://pickaxe.co/learn/mcp-server

## Connect Claude Code

One command:

```bash
claude mcp add --transport http --scope user pickaxe "https://mcp.pickaxe.co" --header "Authorization: Bearer YOUR_WORKSPACE_API_KEY"
```

For a second workspace, repeat with a different server name:

```bash
claude mcp add --transport http --scope user pickaxe-other "https://mcp.pickaxe.co" --header "Authorization: Bearer OTHER_WORKSPACE_KEY"
```

## Connect Cursor

Add the server to `.cursor/mcp.json` in the project, or `~/.cursor/mcp.json` for all projects. VS Code and other JSON-configured clients use the same shape:

```json
{
  "mcpServers": {
    "pickaxe": {
      "type": "http",
      "url": "https://mcp.pickaxe.co",
      "headers": { "Authorization": "Bearer YOUR_WORKSPACE_API_KEY" }
    }
  }
}
```

## Connect Codex

Add the server to `~/.codex/config.toml`. Put the key in an environment variable rather than the file, and give Codex the variable's name. Codex reads it at connect time and sends it as `Authorization: Bearer ...` itself, so the variable holds the bare `studio-` key with no Bearer prefix:

```toml
[mcp_servers.pickaxe]
url = "https://mcp.pickaxe.co"
bearer_token_env_var = "PICKAXE_API_KEY"
```

```bash
export PICKAXE_API_KEY="studio-..."
```

## Connect Grok Build

One command:

```bash
grok mcp add --transport http pickaxe "https://mcp.pickaxe.co" --header "Authorization: Bearer YOUR_WORKSPACE_API_KEY"
```

Grok Build also merges MCP configs from `~/.claude.json`, `.cursor/mcp.json`, and a project `.mcp.json`, so a Pickaxe server already configured for Claude Code or Cursor carries over with no extra setup. `grok mcp list` shows what is configured, and `grok mcp doctor pickaxe` diagnoses a failing connection.

## Verify the connection

Call `studio_whoami` with no arguments. A healthy connection returns the workspace identity. Then call `pickaxe_list` to confirm you are in the workspace you think you are in. Do this before any write, because a key for the wrong workspace fails loudly on nothing and quietly edits the wrong bots.

## Key hygiene

The key grants full write access to the workspace, including live public tools. Treat it like a production credential.

- Never commit it. Scripts should read it from the MCP client config or an environment variable, not from source.
- `scripts/pickaxe_client.py` in this skill reads the key from `PICKAXE_API_KEY` or from the `mcpServers` entry in `~/.claude.json`, in that order.
- If a key leaks, rotate it from the same Workspace API Keys page.
