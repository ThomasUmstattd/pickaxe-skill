# Config history and concurrent edits

Keep a versioned snapshot if you need prompt history or rollback. The tested Pickaxe chat-history endpoints did not provide configuration history.

## Exports

Before building an exporter, evaluate the [official Pickaxe CLI](https://pickaxe.co/learn/cli), which now documents pulling a local workspace. Confirm it covers the fields, attachments, redaction, and diff requirements you need. Its documentation alone does not establish those properties.

For a custom export, list and fetch the intended bots, then write a stable per-bot config plus readable prompt files. Keep export separate from committing and publishing. A diff can show what changed since the last snapshot, but it cannot assign authorship or date an unobserved intermediate change.

Strip volatile data that obscures config changes:

- Use counters, update/request timestamps, IP addresses, and credentials.
- Per-document refresh/reindex bookkeeping such as last-used time, embedding job IDs/status timestamps, and runtime flags.

Keep content-change evidence such as `contentHash`. Sort document arrays and ID sets by stable keys where order has no behavioral meaning. Exclude scratch/staging bots by a documented naming or ID rule. Include retained source content only if the repository's privacy and permissions allow it.

Review the first export for nested secrets and private data before committing. A field named `apikey` is one known source, not an exhaustive redaction list.

## Remote concurrency

Separate worktrees protect local files, not a shared live Pickaxe. Read the live object before an edit, compare it with the basis of the change, and refuse on drift. Use provider conditional updates if available. A pre-write check narrows the race but does not make an unconditional remote update atomic.

Take a fresh rollback snapshot before promotion. A stale export or whole-field draft can silently revert someone else's changes. Reconcile drafts after live edits, or mark them superseded and identify the authoritative source.

Examine actual content rather than `updatedAt` when diagnosing prompt history. Nightly platform processes have changed timestamps without changing prompts. Re-read inconsistent local state too, especially in synchronized folders.

## Using the snapshot

A tool's exported prompt is useful onboarding context for a review. Refresh the relevant remote state before using that export as the basis for a live write. Track deployment and attachment changes when they affect the tested behavior, since a prompt-only diff cannot explain every regression.
