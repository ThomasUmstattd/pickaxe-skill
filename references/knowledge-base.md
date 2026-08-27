# Knowledge base and retrieval

## The knowledge base has two layers

Nothing in the UI says this, and it causes silent failures: **workspace documents and bot attachments are separate**.

- `document_list` returns everything in the workspace.
- `pickaxe_documents` returns only what one specific Pickaxe can retrieve.

A document can be fully embedded, with `embeddingFillStatus: complete` and a real `chunkCount`, and still be invisible to the bot it was uploaded for, because it was never connected. Adding to the workspace and attaching to a bot are separate operations. `document_connect` with `{documentId, pickaxeId}` does the attaching.

The failure this produces: a bulk import creates dozens of documents, everything reports success, and the bot's retrievable count does not move. Verify imports with `pickaxe_documents`, not with the import's return values.

Two API behaviors around the connect call:

- `document_connect` returns `{"success": true}` with no `data` key. A strict `sc["data"]` helper crashes on this success. Parse tolerantly.
- Re-connecting an already-attached document returns HTTP 400 "Document is already connected to this Pickaxe". Harmless, and a usable idempotency check.

## Refresh timestamps mask staleness

A nightly platform job re-crawls existing URL-based documents (observed around 2 to 3 AM UTC). Every document then shows a recent `lastRefreshAt` even when nothing new has been added for months. When auditing a knowledge base for gaps, sort by `createdAt`. One workspace had 900+ documents all "refreshed" within 24 hours while the newest was three months old.

For git-diff purposes, `contentHash` is the honest signal that a document's content actually changed. The embedding bookkeeping fields (`embeddingFill*`, `chunkCount`, `lastRefreshAt`, `isRunning`) churn on reindex with no content change. See the source-of-truth reference.

## RAG vs the Role field

RAG retrieves by semantic similarity, which makes it unreliable for structured or comprehensive lookups. Choose placement by access pattern:

- Content the bot must consult on **every** run (catalogs, URL lists, canonical descriptions) belongs in the Role field, where it is always in context.
- Deep archives where selective retrieval adds value (a podcast transcript library, a large document corpus) belong in the knowledge base.

A related diagnostic: if a tool is supposed to analyze one uploaded document in full but inspection shows chunk retrieval instead of the whole document in context, the tool is doing RAG on something it should read whole. Fix the input path, not the prompt.

## Token allocation starves retrieval

The context budget fills in order: memory first, spillover to end-user documents, and the knowledge base gets the remainder. A heavy Role prompt or a large upload allocation can leave the knowledge base with nothing, and the bot answers as if the KB does not exist while every run reports success.

Diagnosis: Pickaxe's Message Insights panel (Studio UI only, not exposed over the API) shows exactly which KB chunks were retrieved and the input token counts. Zero KB chunks with system-prompt-only token counts confirms retrieval starvation. Also know that retrieval behavior can change platform-side with no config change on your end, so a tool that stops citing its knowledge base is not necessarily a prompt regression.

## Design rules for retrieval-backed output

These come from documented hallucination incidents, all reproducible at the time:

- **Never mandate a format the retrieval layer cannot support.** "Include a source link in every paragraph" plus starved retrieval forces the model to invent citations. Format mandates must be conditional on retrieval actually returning something.
- **Search on content, not titles.** Searching a work's title returns Wikipedia, retailer pages, and pirated PDFs of the work itself rather than comparable works. Build queries from descriptive content instead.
- **Require quoted evidence.** A model confirming its own checklist costs nothing to fake. Require direct quotes from retrieved text, with enough attribution that a human can verify one in seconds. Paraphrased evidence drifts: paraphrasing produced wrong publication years where direct quotes stayed correct.
- **Only recommend things the model is confident exist.** In one test, 7 of 10 recommended platform categories did not exist. For anything checkable (categories, URLs, titles), verified-to-exist beats plausible-sounding, and the prompt should say so.
