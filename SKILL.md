---
name: pickaxe
description: >-
  Build, update, and debug AI tools on the Pickaxe.co platform through its
  hosted MCP server or HTTP JSON-RPC API. Use this skill whenever the user
  mentions Pickaxe, pickaxe.co, Pickaxe Studio, a Pickaxe workspace, or any
  work on Pickaxes, prompts, knowledge bases, documents, actions, deployments,
  access groups, or credits on the platform, including first-time MCP
  connection setup. Consult it before any Pickaxe write operation, because the
  platform has silent-failure traps that make writes look successful when they
  did nothing.
---

# Working with Pickaxe

Pickaxe (pickaxe.co) is a platform for building and selling AI tools. Each tool is a "Pickaxe" with a prompt, a model, an optional form, an optional knowledge base, and optional actions. The platform exposes a hosted MCP server at `https://mcp.pickaxe.co` that also answers plain HTTP JSON-RPC, so everything the Studio UI can configure is scriptable.

This skill is a field guide built from months of production work on a large Pickaxe workspace. Every claim was observed on the live platform. Observations are dated because the platform changes fast, so re-verify anything load-bearing before you depend on it.

## Not connected yet?

If no Pickaxe MCP server is configured, or calls fail with authorization errors, read `references/getting-connected.md`. The API key lives on a settings page that is genuinely hard to find, and that file walks through it.

## The five rules that prevent the worst failures

**1. Every prompt write hits the live bot.** `run_pickaxe_completion` has a `pickaxeConfig` parameter, and it does NOT override the prompt. There is no shadow mode. Iterating on a prompt means writing to whatever bot you target, so iterate on a private staging copy and apply the final version to the live tool once.

**2. Never trust a mutation's return value. Read state back.** Mutations can return success while doing nothing, return a different envelope shape than reads, or succeed while a client helper throws. After every write, fetch the state you changed and confirm it. `references/api-mechanics.md` has the specific traps.

**3. Large payloads need the HTTP fallback.** MCP client layers can reject large tool arguments (an 18KB role field is enough) before they ever reach Pickaxe. Call `https://mcp.pickaxe.co` directly with HTTP JSON-RPC for big writes. `scripts/pickaxe_client.py` implements the pattern.

**4. The knowledge base has two layers.** Adding a document to the workspace does not attach it to any bot. A document can be fully embedded and still invisible to the Pickaxe it was meant for. `references/knowledge-base.md` explains the attach step and how to verify it.

**5. Input caps truncate silently.** New Pickaxes default to a 250-token chat input limit. Form fields and upload fields carry their own `answerlength` caps that quietly cut off user input, and the model never knows text is missing. Check the caps before blaming the model for shallow output. `references/prompt-and-form-fields.md` covers the fields.

## Reference map

Read the file that matches the task. Each is self-contained.

| File | Read it when |
|---|---|
| `references/getting-connected.md` | Setting up the MCP connection for the first time, or auth is failing |
| `references/api-mechanics.md` | Calling any tool: envelopes, create/update mechanics, completion testing, HTTP fallback |
| `references/prompt-and-form-fields.md` | Editing prompts, form fields, input limits, or converting form tools to chat |
| `references/knowledge-base.md` | Documents, embeddings, RAG behavior, retrieval problems |
| `references/actions.md` | Attaching, building, copying, or debugging actions |
| `references/limits-and-costs.md` | Timeouts, upload restrictions, credit caps, cost architecture, embedding on WordPress |
| `references/testing-and-verification.md` | Testing prompt changes, defining what a good answer looks like, A/B comparisons, grading output, anti-hallucination design |
| `references/source-of-truth.md` | Putting Pickaxe configs under git, clean diffs, recovering from bad edits |

## The helper script

`scripts/pickaxe_client.py` is a dependency-free Python client for the HTTP JSON-RPC path. Use it instead of hand-rolling a request helper, because hand-rolled copies drift. One project had three scripts with three slightly different helpers, and a crash-on-success bug fixed in one copy survived in the other two. Code enforces invariants that documentation only suggests.

Run a tool call from the shell:

```bash
python3 scripts/pickaxe_client.py pickaxe_list '{}'
```

Or import it: `from pickaxe_client import call`.
