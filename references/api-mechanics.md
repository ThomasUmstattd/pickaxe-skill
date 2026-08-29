# API mechanics

Everything here was observed on the live platform in August 2026. The server evolves, so treat specific shapes as dated observations and the verification habits as the durable part.

## Two transports, one endpoint

`https://mcp.pickaxe.co` serves MCP clients and also answers plain HTTP JSON-RPC POSTs (`method: "tools/call"`). You need both:

- **MCP through a client** is convenient for reads and small writes.
- **Direct HTTP JSON-RPC** is required for large payloads. MCP client layers can reject big tool arguments with validation errors before the request ever reaches Pickaxe. An 18KB role field is enough to trigger this. Some endpoints have also returned 422 through an MCP client layer while working over direct HTTP. When a write fails at the client layer, switch transports before debugging anything else. And never retry a validation or serialization error unchanged: it is deterministic, and identical retries have burned three round trips at a time. Fix the arguments or switch transports.

`scripts/pickaxe_client.py` implements the HTTP path. Auth is a `Authorization: Bearer studio-...` header on every request.

## Response envelopes are not uniform, and they drift

Read tools generally return `{"success": true, "data": ...}` inside `structuredContent`. Do not generalize from that:

- Some mutations (`document_connect`, `document_disconnect`) return `{"success": true}` with **no** `data` key. A helper that does `sc["data"]` throws `KeyError` on a fully successful call. One session reported 80 failures on 80 successes this way, and the false-failure direction is the dangerous one because it invites "fixes" that break working state.
- The envelope changes over time without notice. In one 24-hour window in August 2026, a read tool gained a third `meta` key and one tool went from a null `outputSchema` to a typed one. Nearly all tools advertise `outputSchema: null`, so the server never promised a shape.

Consequences:

- Parse tolerantly: `sc.get("data", sc)`, never `sc["data"]`.
- **Verify every mutation by reading state back.** The return value tells you the request was accepted. Only a fresh read tells you what the platform actually did.

## Creating and updating Pickaxes

- `pickaxe_create` ignores top-level `prompt`, `model`, and `temperature` parameters. Create, then set everything through `pickaxe_update` with a `data` object: `data: {role, responseprefix, model, temperature, name, chatinputlength, ...}`.
- `pickaxe_update` is a partial update. Only `pickaxe_id` is required, and unmentioned fields are left alone.
- Field name decoder: the system prompt is `role`. The builder UI's "Model Reminder" is `responseprefix`. The form's first-turn prompt is `promptframe` plus its HTML twin `rawpromptframe` (see the prompt fields reference).
- New Pickaxes default to `chatinputlength: 250` tokens and `maxlength: 2000`. The tiny input default silently truncates anything long you send through the completion API, so raise it before testing with real inputs.
- There is no pickaxe delete tool in the API (as of August 2026). Bots created programmatically must be deleted in the Studio UI.
- `user_update` on an email with no existing user returns 404 and does not create the user. Updates go inside `data: {...}`, and top-level fields fail with "data is required". Some fields are accepted and silently ignored, which is one more reason to read the record back. Two discarded fields worth naming: `limit` and `limitInterval` are accepted, reported written, and stay null on read-back, so per-user credit adjustments are a Studio UI operation.
- `access_group_assign` does not put users in groups. It attaches access groups to deployments and portals. The user-side path is `user_update` with an `accessGroupId`, keyed by email, which inherits every `user_update` quirk above.

## Running completions

`run_pickaxe_completion` executes a live Pickaxe and is the workhorse for automated testing. Its sharp edges:

- **`pickaxeConfig` does not override the prompt.** There is no dry-run or shadow config. Testing a prompt variant means writing it to a real bot first, which is why staging copies exist (see the testing reference).
- The response arrives as a **Python-repr dict in the content text**, single quotes and all: `{'success': True, 'result': '<markdown>'}`. Parse with `ast.literal_eval`, not `json.loads`.
- It only reaches Pickaxes inside the workspace its key belongs to.
- Completions take 20 to 40+ seconds. Action-heavy runs take minutes, and there is a hard server-side ceiling (see the limits reference).
- Transient failures show up as "Could not reach the Completion API". Retry with backoff, but if a run dies at almost exactly 300 seconds, that is the ceiling and retrying changes nothing.
- Multi-turn works with a caveat: pass your own `conversationId` string on the first call and reuse it, and the model sees the prior exchange. That held when both turns used `message`. In a measured case on a form bot, an `inputs` first turn followed by a `message` second turn carried no history at all, and the endpoint returns no conversation id of its own to use instead. Confirm conversational behavior in the real embed before concluding that a follow-up instruction works or does not.
- It cannot attach files. Anything involving real file upload or transcription can only be tested through the embed or Studio UI.
- Input is capped by the bot's `chatinputlength`. Embed file uploads take a different path with different caps, so an API test and a real user upload are not the same code path.

## Honest errors worth knowing

Not everything fails silently. Two errors that look scary but are actually the API telling the truth:

- `document_connect` on an already-attached document returns HTTP 400 "Document is already connected to this Pickaxe". Harmless, and usable as an idempotency check.
- Connecting an action that needs a key without providing one fails with `Variable <NAME> is required` (see the actions reference).

## Some advertised fields are UI-only

A schema is not a contract. The server generates its tool list from parameter lists, not from the fields each handler actually writes, so a parameter appearing in the schema proves nothing about whether it saves. Only a read-back does. Observed August 2026: `deployment_update` lists `name` in its published input schema, accepts it in four different request shapes, returns HTTP 200, and bumps `updatedAt`, and the stored name never changes.

When a write is confirmed dead over the API, fetch the endpoint's live schema once, which separates a mangled request from an ignored field, then stop permuting parameters and drive the Studio UI in a browser instead. More parameter shapes after that point are the same experiment repeated. Display labels are the known offenders so far (deployment and portal names, titles, descriptions), while prompt, model, and knowledge writes persist normally. After the UI edit, read the value back over the API, which is the cheap direction and confirms the UI wrote the same record the API reads.

## Big workspaces overflow tool results

`document_list` and `pickaxe_documents` on a workspace with over a thousand documents return more than a megabyte, and `deployment_list` on a workspace with many deployments returns hundreds of kilobytes. That blows past most MCP clients' tool-result limits. Write the response to a file and query it with `jq` or a script instead of reading it into context.

## A second API: the public completions endpoint

Separate from the MCP server, Pickaxe documents a public completions endpoint at `api.pickaxe.co/v1/completions` (docs at `pickaxe.co/v1/documentation/completions`). It authenticates with `Authorization: Bearer <deployment API key>`, taken from a deployment's API preview section in the Studio UI. The workspace MCP key returns 401 and a direct-link deployment id returns 403, and no API path mints the key, so obtaining it is a UI step.

The docs list three capabilities the MCP completion tool lacks: `stream: true` for Server-Sent Events (the natural experiment against the 300-second ceiling, since a streaming connection is never idle), `inputs` for real form-field injection, and `conversationId` for multi-turn. A companion `/v1/triggers` endpoint delivers a server-to-server message the model sees as a user turn without it entering history. The auth failures were measured, and the capabilities are documented rather than verified (August 2026).

## Chat history may be legitimately empty

Workspaces on the strictest privacy setting retain no retrievable transcripts. On such a workspace, `pickaxe_history` and `workspace_history` return empty for every parameter combination, by design. Empty history on a privacy-restricted workspace is an answer, not a bug. Confirm the workspace's privacy setting once, then stop querying instead of burning time on parameter permutations. History is chat transcripts only. There is no config history on the platform at all, which is what the source-of-truth reference solves.

Where history exists, check whether a field is stored or joined before trusting it retrospectively. An API field naming a per-run fact may be joined against current configuration at read time, and a joined field silently rewrites reported history whenever the configuration changes. The test is cheap and generalizes to any API: change the upstream config, re-read a historical record without re-running anything, and see whether the record moves. Run it in both directions to rule out coincidence.

Worked example, from a platform bug that has since been fixed. The history endpoint's per-conversation `model` field tracked the bot's currently configured model rather than the model that generated the response, while the Studio's per-message insights panel held the true value. Two surfaces disagreeing about one message at one instant is what made the join visible. Reported in August 2026, and the vendor shipped a fix within a day that reads the stored generation model, including for records written before the fix. Two habits outlast the bug. Never take a historical attribution on faith when reviewing an A/B test after adopting the winner, because a joined field reports that the winner produced the losing arm's output. And when two surfaces disagree about the same record, the disagreement is the finding: it usually means the data is stored correctly and one read path is wrong, which is a far smaller fix to request than new storage. Per-message cost, token, and latency telemetry may also exist in the UI while absent from the API, so check the UI before concluding a metric is not collected.
