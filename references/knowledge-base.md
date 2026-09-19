# Knowledge base and retrieval

Observed August–September 2026.

## Inventory, attachments, and citations

Workspace documents and bot attachments are separate. `document_list` inventories workspace documents, while `pickaxe_documents` identifies a bot's attached set. A fully embedded document with a real chunk count can remain unavailable to a bot until attached.

Page `document_list` with `skip` and `take`. The default returned 10 documents and ignored `page`, `limit`, and `pageSize`. A page size of 500 worked in September. Follow the current response/schema through all pages, save large results to disk, and compare IDs rather than displayed counts alone.

Website documents carried their source URL in `name`, `displayName`, and `title`, without a URL-named field. Inspect a sample record before building an inventory matcher. End-user form uploads did not appear in the owner's workspace document inventory.

For attachments:

- `document_connect` takes `documentId` and `pickaxeId`. Reconnecting an existing attachment returned 400 “Document is already connected to this Pickaxe.” Confirm membership before treating that response as a harmless no-op.
- For a complete same-workspace synchronization, September tests replaced more than a thousand attachments with one `pickaxe_update` carrying top-level `documentIds`: `{"pickaxe_id":"BOT_ID","data":{},"documentIds":["DOC_ID"]}`. This replaces the set. Fetch and preserve intended existing IDs before writing, check for concurrent changes, and verify the final set.
- Do not assume IDs travel between workspaces. Copy authorized source content into the target workspace, then attach its new document IDs.

Citation eligibility is a separate check. API/batch-created documents arrived with `isCitable` unset, and `document_get` omitted the flag. Read it through `document_list` or `pickaxe_documents`. The tested `document_update` rejected it alone and silently discarded it alongside a valid title change. The Studio's Enable citing control supported a bulk operation. Check current supported API operations first, then use the permitted Studio path and read every changed flag back.

## RSS Auto Sync

Enable **Auto Sync** on an RSS Feed source for daily syncing. Pickaxe reported this feature available on September 16, 2026, and a builder confirmed it working on September 17. Sync appends new feed items to the knowledge base and retains URLs that disappear from the feed. This supersedes the earlier one-time-import behavior.

Use the RSS Feed source for this append-only behavior. The older workaround of adding a feed URL as a website with auto-sync had different retention: items could leave the knowledge base when they left the feed window.

To check a particular setup, confirm Auto Sync is enabled and look for a newly published item after a sync cycle using the paginated document inventory. Verify the target bot's attachment and citation state too. The feature confirmation does not establish how those settings propagate or how edits to existing feed items are handled.

## Import and copy boundaries

`document_create` accepted 4.0 MB and rejected 5.2 MB in a size probe. Split below the observed ceiling on meaningful content boundaries. Base64 increases payload size and is not a solution to a server request-size limit.

Cross-workspace staging copied extracted text from a document's `storageUrl` and recreated documents. Those tested URLs returned text without authentication. Treat them as sensitive source locations, not permission to publish or copy private material. Verify authorization and target retention before moving documents.

Cache copies by source identity and content/version evidence to avoid duplication. Paginate the cache lookup. Copies are snapshots: a later source re-crawl does not refresh them. Missing content hashes mean a metadata match cannot prove equal text.

Existing URL documents underwent nightly re-crawls. A recent `lastRefreshAt` proves neither a new document nor a current corpus. Compare source inventory to creation dates and content changes. Keep `contentHash` in exports and strip volatile reindex bookkeeping, as described in [Source of truth](source-of-truth.md).

## Placement and token budgets

Put small catalogs, canonical URLs, and other information needed on every turn in the Role. Use RAG for archives where selective retrieval fits the task. A tool that must read an entire upload needs an input path that supplies it, not just a few relevant chunks.

The observed allocation order was memory, end-user documents, then KB remainder. Large allocations or prompt content can starve retrieval. An excessive `reservedtokens` value has also produced null `ragbudget` and fragmentary upload reads. Compare the model's window, stored budgets, and a known-good configuration, then verify actual input coverage. A budget anomaly is a diagnostic lead, not a universal causal explanation.

Inspect Message Insights for input tokens, retrieved sources, served model, and fallback. Zero KB evidence can mean retrieval failure, but only if the query required it and the metric is present and understood. See [API mechanics](api-mechanics.md) for session recovery and privacy limits.

## Retrieval-backed answers

- Make source-dependent output conditional on usable evidence. A mandatory citation format cannot create sources that retrieval did not return.
- For comparable-item searches, descriptive content may work better than a title query that mainly retrieves the original work.
- Ask for checkable quoted evidence and verify it. A quote's existence does not establish its attached claim, date, or attribution.
- A model's confidence is not proof that a URL, category, or title exists. Use source evidence for claims that matter.
- Differences across identical runs are a reason to inspect retrieved evidence. Retrieval variability, changing sources, and model invention can all cause them.
- Date-sensitive tools need a current-date source and an explicit date filter. Distinguish confirmed dates from typical timing.
- A prompt can tell a model to disclose failed retrieval, but a familiar topic may still elicit memory-based answers. Test that failure branch.

Chat links were fetched and injected on a tested interactive path, including a real error page from a dead link. Teach the bot to distinguish usable content from a login/error page and avoid guessing what lies behind it. Do not generalize that fetch behavior to bare URLs sent through every completion API path.
