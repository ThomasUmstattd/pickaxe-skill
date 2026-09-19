# API mechanics

Observed August–September 2026 unless stated otherwise. Check the current tool schema before relying on an old limitation.

In this file:

- Transports and payloads
- Responses and errors
- Create and update
- Completion paths
- Sessions and Message Insights
- Fields that need a different write path

## Transports and payloads

The hosted MCP endpoint, `https://mcp.pickaxe.co`, also accepts HTTP JSON-RPC with `method: "tools/call"`. Use the configured MCP tools for ordinary calls. Direct HTTP helps when the client rejects large arguments or serializes strings incorrectly. Some Claude Code failures involved untyped `anyOf [{}, null]` parameters. That schema is a diagnostic clue, not proof that another client will fail.

A 422 "body Field required" can also mean malformed arguments. Check the schema and a known-good body before switching transports. These shapes worked over JSON-RPC in September 2026:

| Tool | Arguments |
|---|---|
| `pickaxe_update` | `{"pickaxe_id":"BOT_ID","data":{"role":"..."}}` |
| `deployment_create` | `{"data":{"formId":"BOT_ID","type":"TYPE_FROM_SCHEMA"}}` |
| `deployment_update` | `{"data":{"deploymentId":"DEPLOYMENT_ID","name":"..."}}`, although name writes were discarded |
| `user_update` | Email identifier from the current schema, plus `data: {...}` |

Do not infer that every update argument belongs inside `data`. A September batch attachment replacement used top-level `documentIds` on `pickaxe_update`. See [Knowledge base](knowledge-base.md).

Stop identical retries of deterministic validation failures. After an uncertain mutation, read state before resending it, since the write may have succeeded.

## Responses and errors

The helper `../scripts/pickaxe_client.py` implements the JSON-RPC path with the Python standard library.

- Check the JSON-RPC `error`, MCP result `isError`, and any decoded envelope's `success: false`.
- Reads often carry `{"success":true,"data":...}` in `structuredContent`. Successful mutations can return only `{"success":true}`. Do not require a `data` key.
- Completions have returned structured objects and text containing Python-repr or JSON envelopes. Decode those envelopes, check their error flags, then extract `result`. Treat ordinary answer text as text.
- A successful completion can contain an apology for an action failure. Transport success does not establish action success. Check [action runs and assets](actions.md).
- Fresh state establishes what a mutation stored. Check coupled behavior fields as well as the intended fields, then inspect rendering or runtime behavior where relevant.

Example:

```python
from pickaxe_client import call, run_completion

config = call("pickaxe_get", {"pickaxe_id": "BOT_ID"})
reply = run_completion("BOT_ID", inputs={"userinput:FIELD_ID": "value"})
```

The helper accepts JSON and MCP SSE-wrapped JSON-RPC responses. It does not implement the separate public completion endpoint's token-delta streaming. Use a client suited to that endpoint if streaming is needed. Default completion retries are zero. An explicit `retries=` opts into additional requests and possible charges after an ambiguous error.

## Create and update

`pickaxe_update` is partial. The system prompt is `role`, the per-turn Model Reminder is `responseprefix`, and the form prompt has both `promptframe` and `rawpromptframe`. Reasoning uses `reasoningeffort`. Values observed include `off`, `low`, `medium`, `high`, and null. Copy the tested setting and confirm model support rather than assuming null means the same thing for every model.

Observed create defaults included public privacy, `chatinputlength: 250`, `maxlength: 2000`, `reservedtokens: 10000000`, null `ragbudget`, `endusertokens: 750`, and an owner-only upload mode. Set and verify the intended privacy and behavior before testing. Top-level `prompt`, `model`, and `temperature` were ignored on create, so read back and set required fields with update. `submittext` inside create `data` did persist even though update discarded it.

A create also produced direct-link and email deployments. List what exists before creating more. API and UI create defaults can differ, including the undocumented `featured` flag. Portal membership has its own explicit operation. Do not change an undocumented flag based on its name.

The August–September workflow reused staging bots because no agent-delete operation was available through the tested MCP surface. Recheck current schemas for removal and other previously missing operations. The [official MCP documentation](https://pickaxe.co/learn/mcp-server) now describes a broader operation surface.

For user updates, `limit` and `limitInterval` were accepted but discarded, and `uses[]` was rejected. Later tests successfully changed top-level usage/extra counters. This does not make membership reassignment safe or establish atomic wallet operations. See [Limits and costs](limits-and-costs.md).

`access_group_assign` attached groups to deployments/portals in the observed schema. The user membership path used `user_update` with `accessGroupId`. Verify the current contract rather than choosing from the tool name.

## Completion paths

`run_pickaxe_completion` runs a real bot reachable by its credential, without requiring an API deployment. Prompt variants must already be on the target bot.

| Input | What it tests |
|---|---|
| `message` | Role and Reminder, bypassing the form's static prose and fields |
| `inputs` | Form prompt and supplied values, including already-extracted document text |
| Real embed upload | Picker, upload, extraction, and runtime prompt |
| Public API `imageUrls` | Image input for supported multimodal models, not the local file picker |

The public endpoint is `https://api.pickaxe.co/v1/completions`. It uses an API deployment ID as its Bearer credential. Workspace keys and other deployment types are not interchangeable with that credential. The [completion docs](https://pickaxe.co/v1/documentation/completions) define `inputs`, `imageUrls`, `conversationId`, `userId`, and `stream`. They describe `pickaxeConfig` as business metadata for actions/MCP, not a prompt override.

Use field IDs from the target deployment's API preview. A document field accepted long text through `inputs["userinput:documentupload"]` in September tests. This bypasses extraction and does not validate real uploads.

For multi-turn testing, supply and reuse a conversation ID from the first request. Two `message` turns retained history in a measured test. An `inputs` turn followed by `message` did not in another. Verify the target path before diagnosing follow-up instructions, and do not substitute pasted history without labeling that change.

Streaming returned SSE text deltas in runs below 300 seconds. Survival beyond that ceiling remains unverified. `/v1/triggers` provides a server-originated user turn omitted from user-message history. That omission does not make it a system instruction or a secret channel.

## Sessions and Message Insights

As verified in September 2026, `message_insights_get` accepts `session_id` and `message_index`. Index 0 identifies the first generated answer, not an alternating chat-message position. Read the current schema and returned fields.

Observed telemetry includes served model, fallback flag, measured USD cost, token breakdown, latency, and retrieved document IDs/storage URLs. `originalModel` appeared as null on a non-fallback run. Its fallback value was not verified in that test, so record the requested configuration alongside each run.

A completion can omit its session ID. Recover it without buying another answer:

1. Read history before the run and retain the existing `responseId` values.
2. Make one completion attempt and save any response or failure.
3. Read history again with bounded polling. Use the single new conversation's `responseId`.
4. For `message` runs, exact prompt/answer matching can resolve candidates. Form `inputs` runs can have empty `messages` and `usedTokens: 0` despite complete Insights. Do not require text matching for those.
5. Read Insights with bounded retries for delayed availability. If attribution remains ambiguous, leave telemetry unassigned.

Use one run at a time per bot when matching by history difference. Parallel arms need separate bots or a verified explicit session identifier. Another user can also create ambiguity on a live bot.

Workspaces with maximum privacy retain no retrievable history. Empty history there is expected, and repeated parameter changes do not recover it. On other workspaces, a recent history slice is not necessarily complete lifetime history. Keep missing cost unknown and preserve timeout/error status even if an answer is later recovered.

The historical model field once reflected current config rather than the model used at generation. Pickaxe fixed that reported bug in August. Keep requested and served model evidence per run and investigate conflicting surfaces without reviving the old blanket claim.

## Fields that need a different write path

These are endpoint-specific observations, not permanent limits:

| Field or operation | Observed behavior and next check |
|---|---|
| `pickaxe_update.submittext` | Discarded. Create accepted it. Later label changes used the builder. |
| `description`, `formdescription` | Persisted on the same update that discarded the button label. |
| Deployment name/style | Tested MCP writes failed or discarded changes. Check current schema, then use Studio if still unsupported. |
| Deployment `limits` | Rejected and no editing control found. Access-group `upgrade.limitMessage` may govern the visible message. Verify the exhausted-user surface. |
| Document `isCitable` | Metadata writes rejected or discarded it. Read through document/attachment listings and use the supported citation control. |
| External `coverphoto` | Persisted but did not render in the tested embed. A Studio-uploaded Pickaxe asset rendered. Readback alone is insufficient. |

For unsupported bulk operations, a permitted logged-in browser can inspect and replay the request made by an actual Studio control. September observations included `deployment.create.deployment` and `document.update.documents` tRPC routes. These are private implementation details: recapture the request, retain created IDs, and check state after an automation timeout before retrying. Prefer a supported public operation when one exists.
