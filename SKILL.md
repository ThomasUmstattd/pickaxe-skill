---
name: pickaxe
description: >-
  Use for any task that touches the Pickaxe.co AI-tool
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

Use this field guide for Pickaxe-specific behavior that ordinary API or prompt-writing knowledge misses. Observations come from production work in August and September 2026. Check current schemas and the relevant runtime path when a decision depends on an old observation.

## Working rules

- **Test prompt variants on a private copy.** A prompt write changes the targeted bot. Completion `pickaxeConfig` carries business metadata, not a shadow prompt. A review or diagnosis does not authorize a production edit.
- **Verify effects.** Fetch written fields and coupled settings. Refuse stale whole-field writes. For a visible change, check the rendered surface too: stored values can fail to render.
- **Match the test to the input path.** `message` bypasses the form prompt. `inputs` exercises it with supplied text. Real uploads also exercise file parsing. Caps can truncate, but a low cap alone does not prove truncation.
- **Check attachments and retrieval.** Creating a workspace document does not attach it to a bot. Verify the attachment set, citation flags where needed, and retrieval evidence.
- **Bound paid work.** Agree on the decision and useful test size. Track attempts, elapsed time, and measured cost. Recover an uncertain completion before retrying it. Missing telemetry is unknown cost.
- **Treat membership assignment as a wallet mutation.** Assigning even the same group has reset usage and extra credits. Read current membership and skip users already enrolled.

## Read for the task

| Reference | Use for |
|---|---|
| [Getting connected](references/getting-connected.md) | Credentials, workspace identity, first connection |
| [API mechanics](references/api-mechanics.md) | Payloads, errors, completions, session and Insights recovery |
| [Prompts and fields](references/prompt-and-form-fields.md) | Prompt lifetimes, frames, caps, form/chat settings |
| [Knowledge base](references/knowledge-base.md) | Pagination, attachments, citations, retrieval |
| [Actions](references/actions.md) | Keys, triggers, image results, action failures |
| [Limits and costs](references/limits-and-costs.md) | Timeouts, billing, user credits, upload limits |
| [Testing](references/testing-and-verification.md) | Staging parity, uploads, runtime verification |
| [Grading](references/grading-and-fixtures.md) | Rubrics, fixtures, controls, source support |
| [Source of truth](references/source-of-truth.md) | Exports, clean diffs, rollback, concurrent edits |

Read the relevant references rather than the whole library. Reuse existing rubrics and user decisions.

## HTTP fallback

Use the configured MCP connection first. If its client cannot serialize valid arguments, use the dependency-free `scripts/pickaxe_client.py`. Check the payload before changing transports: missing `data` can also cause a 422.

The helper supports JSON-RPC calls and completions, with one completion attempt by default. `PICKAXE_API_KEY` applies only to the default server. Named servers require their own configuration or an explicit Python `token=`. See the connection reference for examples.
