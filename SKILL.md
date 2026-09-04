---
name: pickaxe
description: >-
  Required first step for any task that touches the Pickaxe.co AI-tool
  platform (Pickaxe Studio), even when the MCP connection is already set up
  and the task looks like a one-line edit, because writes can silently fail
  and every prompt edit hits the live bot immediately. Covers building,
  editing, and configuring Pickaxes (prompts, prompt frames, form fields,
  knowledge bases and documents, actions, deployments, access groups,
  credits), connecting to a workspace for the first time, safely testing or
  comparing prompt versions without affecting live users, grading a Pickaxe's
  output, and diagnosing any misbehaving Pickaxe that end users interact with:
  a bot ignoring its attached documents, rejecting file uploads, reading only
  part of an upload, inventing answers, or showing access denied inside an
  embed on a customer site. If the user's tool, chatbot, or workspace lives on
  pickaxe.co, use this skill, whether building, changing, testing, or
  troubleshooting it. Not for the npm pickaxe package, Minecraft, or other
  chatbot platforms.
---

# Working with Pickaxe

Pickaxe (pickaxe.co) is a platform for building and selling AI tools. Each tool is a "Pickaxe" with a prompt, a model, an optional form, an optional knowledge base, and optional actions. The platform exposes a hosted MCP server at `https://mcp.pickaxe.co` that also answers plain HTTP JSON-RPC, so nearly everything the Studio UI can configure is scriptable. A few fields are UI-only and silently ignore API writes, see `references/api-mechanics.md`.

This skill is a field guide built from months of production work on a large Pickaxe workspace. Every claim was observed on the live platform. Observations are dated because the platform changes fast, so re-verify anything load-bearing before you depend on it.

## Not connected yet?

If no Pickaxe MCP server is configured, or calls fail with authorization errors, read `references/getting-connected.md`. The API key lives on a settings page that is genuinely hard to find, and that file walks through it.

## The five rules that prevent the worst failures

**1. Every prompt write hits the live bot.** `run_pickaxe_completion` has a `pickaxeConfig` parameter, and it does NOT override the prompt. There is no shadow mode. Iterating on a prompt means writing to whatever bot you target, so iterate on a private staging copy and apply the final version to the live tool once.

**2. Never trust a mutation's return value. Read state back.** Mutations can return success while doing nothing, return a different envelope shape than reads, or succeed while a client helper throws. After every write, fetch the state you changed and confirm it, one field at a time, because one call can save two fields and discard a third. `references/api-mechanics.md` has the specific traps.

**3. Client-layer failures need the HTTP fallback, and they are not only large payloads.** MCP client layers can reject large tool arguments (an 18KB role field is enough) before they ever reach Pickaxe, and they can also fail to serialize a 352-byte call. An `InputValidationError` or parse error on a Pickaxe tool is deterministic, so never resend it unchanged. Call `https://mcp.pickaxe.co` directly with HTTP JSON-RPC instead. `scripts/pickaxe_client.py` implements the pattern.

**4. The knowledge base has two layers.** Adding a document to the workspace does not attach it to any bot. A document can be fully embedded and still invisible to the Pickaxe it was meant for. `references/knowledge-base.md` explains the attach step and how to verify it.

**5. Input caps truncate silently, and truncation fabricates.** New Pickaxes default to a 250-token chat input limit. Form fields and upload fields carry their own `answerlength` caps that quietly cut off user input, and the model never knows text is missing. A bot fed one page of a book will invent the rest. Check the caps before blaming the model for shallow or invented output. `references/prompt-and-form-fields.md` covers the fields.

## Reference map

Read the file that matches the task. Each is self-contained and opens with a list of its sections.

| File | Read it when |
|---|---|
| `references/getting-connected.md` | Setting up the MCP connection for the first time, or auth is failing |
| `references/api-mechanics.md` | Calling any tool: envelopes, create/update mechanics, completion testing, the public completions endpoint, HTTP fallback |
| `references/prompt-and-form-fields.md` | Editing prompts, form fields, input limits, or converting form tools to chat |
| `references/knowledge-base.md` | Documents, embeddings, RAG behavior, retrieval problems |
| `references/actions.md` | Attaching, building, copying, or debugging actions |
| `references/limits-and-costs.md` | Timeouts, upload restrictions, credit caps, access groups, cost architecture, embedding on WordPress |
| `references/testing-and-verification.md` | Staging a change safely, verifying writes and form changes, transports, the platform signals that mislead diagnosis |
| `references/grading-and-fixtures.md` | Deciding whether output is good: rubrics, test fixtures, run counts, ground-truth grading, anti-hallucination design |
| `references/source-of-truth.md` | Putting Pickaxe configs under git, clean diffs, recovering from bad edits |

## The helper script

`scripts/pickaxe_client.py` is a dependency-free Python client for the HTTP JSON-RPC path. Use it instead of hand-rolling a request helper, because hand-rolled copies drift. One project had three scripts with three slightly different helpers, and a crash-on-success bug fixed in one copy survived in the other two. Code enforces invariants that documentation only suggests.

Run a tool call from the shell:

```bash
python3 scripts/pickaxe_client.py pickaxe_list '{}'
```

Or import it: `from pickaxe_client import call, run_completion`. `run_completion` takes either a `message` string or an `inputs` dict keyed by the form's field ids, and the two are different code paths on the platform (testing reference).
