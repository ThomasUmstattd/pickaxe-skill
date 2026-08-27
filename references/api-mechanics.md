# API mechanics

Everything here was observed on the live platform in August 2026. The server evolves, so treat specific shapes as dated observations and the verification habits as the durable part.

## Two transports, one endpoint

`https://mcp.pickaxe.co` serves MCP clients and also answers plain HTTP JSON-RPC POSTs (`method: "tools/call"`). You need both:

- **MCP through a client** is convenient for reads and small writes.
- **Direct HTTP JSON-RPC** is required for large payloads. MCP client layers can reject big tool arguments with validation errors before the request ever reaches Pickaxe. An 18KB role field is enough to trigger this. Some endpoints have also returned 422 through an MCP client layer while working over direct HTTP. When a write fails at the client layer, switch transports before debugging anything else.

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
- `user_update` on an email with no existing user returns 404 and does not create the user. Updates go inside `data: {...}`, and top-level fields fail with "data is required". Some fields are accepted and silently ignored, which is one more reason to read the record back.

## Running completions

`run_pickaxe_completion` executes a live Pickaxe and is the workhorse for automated testing. Its sharp edges:

- **`pickaxeConfig` does not override the prompt.** There is no dry-run or shadow config. Testing a prompt variant means writing it to a real bot first, which is why staging copies exist (see the testing reference).
- The response arrives as a **Python-repr dict in the content text**, single quotes and all: `{'success': True, 'result': '<markdown>'}`. Parse with `ast.literal_eval`, not `json.loads`.
- It only reaches Pickaxes inside the workspace its key belongs to.
- Completions take 20 to 40+ seconds. Action-heavy runs take minutes, and there is a hard server-side ceiling (see the limits reference).
- Transient failures show up as "Could not reach the Completion API". Retry with backoff, but if a run dies at almost exactly 300 seconds, that is the ceiling and retrying changes nothing.
- Multi-turn works: pass your own `conversationId` string on the first call and reuse it, and the model sees the prior exchange.
- It cannot attach files. Anything involving real file upload or transcription can only be tested through the embed or Studio UI.
- Input is capped by the bot's `chatinputlength`. Embed file uploads take a different path with different caps, so an API test and a real user upload are not the same code path.

## Honest errors worth knowing

Not everything fails silently. Two errors that look scary but are actually the API telling the truth:

- `document_connect` on an already-attached document returns HTTP 400 "Document is already connected to this Pickaxe". Harmless, and usable as an idempotency check.
- Connecting an action that needs a key without providing one fails with `Variable <NAME> is required` (see the actions reference).

## Big workspaces overflow tool results

`document_list` and `pickaxe_documents` on a workspace with over a thousand documents return more than a megabyte. That blows past most MCP clients' tool-result limits. Write the response to a file and query it with `jq` or a script instead of reading it into context.

## Chat history may be legitimately empty

Workspaces on the strictest privacy setting retain no retrievable transcripts. On such a workspace, `pickaxe_history` and `workspace_history` return empty for every parameter combination, by design. Empty history on a privacy-restricted workspace is an answer, not a bug. Confirm the workspace's privacy setting once, then stop querying instead of burning time on parameter permutations. History is chat transcripts only. There is no config history on the platform at all, which is what the source-of-truth reference solves.
