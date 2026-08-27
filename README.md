# pickaxe-skill

An agent skill for building, updating, and debugging AI tools on the [Pickaxe](https://pickaxe.co) platform through its MCP server and HTTP JSON-RPC API.

Pickaxe keeps no config history, has no dry-run mode, and has several places where a write reports success while doing nothing. This skill teaches an AI coding agent the platform's mechanics and its traps: the field names behind the builder UI, the two-layer knowledge base, silent input truncation, the completion timeout ceiling, and the verification habits that catch all of the above. It was distilled from months of production work on a workspace of 80+ live tools.

It uses the open [Agent Skills](https://code.claude.com/docs/en/skills) format (a `SKILL.md` with reference files), which Claude Code, Codex, and Cursor all read.

## Install

**Claude Code** (personal, all projects):

```bash
git clone https://github.com/ThomasUmstattd/pickaxe-skill ~/.claude/skills/pickaxe
```

**Codex** (personal, all projects):

```bash
git clone https://github.com/ThomasUmstattd/pickaxe-skill ~/.agents/skills/pickaxe
```

**Cursor** (personal, all projects):

```bash
git clone https://github.com/ThomasUmstattd/pickaxe-skill ~/.cursor/skills/pickaxe
```

For a single project instead, clone into the project's skill directory: `.claude/skills/pickaxe`, `.agents/skills/pickaxe`, or `.cursor/skills/pickaxe`.

## Connect to Pickaxe

The skill includes a walkthrough for the initial MCP connection, including where the API key hides in Pickaxe Studio's settings. See [references/getting-connected.md](references/getting-connected.md), or just ask your agent to connect you to Pickaxe once the skill is installed.

## What's inside

| File | Covers |
|---|---|
| [SKILL.md](SKILL.md) | The five rules that prevent the worst failures, and the map below |
| [references/getting-connected.md](references/getting-connected.md) | First-time MCP setup for Claude Code, Codex, and Cursor |
| [references/api-mechanics.md](references/api-mechanics.md) | Envelopes, create/update mechanics, completion testing, the HTTP fallback |
| [references/prompt-and-form-fields.md](references/prompt-and-form-fields.md) | Role, Prompt Frame, Model Reminder, form descriptors, input caps |
| [references/knowledge-base.md](references/knowledge-base.md) | The two-layer KB, refresh masking, RAG vs Role, retrieval starvation |
| [references/actions.md](references/actions.md) | The four-action limit, credit-backed vs own-key, manifest traps, Wingman |
| [references/limits-and-costs.md](references/limits-and-costs.md) | The 300s ceiling, upload whitelist, credit caps, cost architecture |
| [references/testing-and-verification.md](references/testing-and-verification.md) | Staging discipline, realistic-length testing, A/B variance, anti-hallucination |
| [references/source-of-truth.md](references/source-of-truth.md) | Exporting configs to git with clean diffs |
| [scripts/pickaxe_client.py](scripts/pickaxe_client.py) | A dependency-free Python client for the HTTP JSON-RPC path |

## Status and provenance

This is an independent community project, not affiliated with or endorsed by Pickaxe. Everything in it was observed on the live platform, and observations are dated (mostly August 2026) because the platform evolves. When something here contradicts current platform behavior, trust the platform and open an issue.

Built by [Thomas Umstattd Jr.](https://www.authormedia.com) while building the Patron Toolbox, a suite of AI tools for authors.

## License

[MIT](LICENSE)
