# Config as code: a git source of truth for Pickaxe

Pickaxe keeps no config history. There is no audit trail, no versioning, and no undo for a bad prompt write. `pickaxe_history` is chat transcripts, not config. If you manage more than a handful of tools, export every config to a git repository and make that the source of truth.

## The export pattern

A script (run on a schedule, or at the start of every working session) that:

1. Lists every Pickaxe in the workspace.
2. Fetches each full config.
3. Writes each to its own directory: `pickaxes/<tool-slug>/config.json` plus `pickaxes/<tool-slug>/role.md` with the system prompt split out as readable Markdown.
4. Commits nothing by itself. The git diff after an export IS the report of what changed on the platform since the last export.

This gives you change detection, rollback material, code review on prompts, and a way to notice when someone or something edited a live tool.

## Strip volatile fields, or the diffs are worthless

The raw API response includes fields that change on every run or every day with no real config change. Left in, they bury real changes under noise and train you to skim diffs. Strip them at export time.

Two classes to strip:

- **Top-level churn**: use counters (`usestoday`, `usestotal`), timestamps (`updatedAt`, `timestamp`), request metadata (`ip_address`), and anything secret-shaped (`apikey`).
- **Per-document bookkeeping** inside the documents array: `lastUsedAt`, `lastRefreshAt`, `updatedAt`, `isRunning`, `chunkCount`, and the whole `embeddingFill*` family (status timestamps, job ids, attempt counters). These move when a user runs the tool or when the platform reindexes, with no content change. Keep `contentHash`: it is the honest signal that a document's content actually changed.

The general principle travels beyond Pickaxe: when exporting any platform's state into git, classify every field as config (keep), content signal (keep), or operational bookkeeping (strip). Do it on day one, because retrofitting it means one giant reformat commit.

## Sort unstable arrays

The API returns document arrays in unstable order. Unsorted, a mere reorder diffs every line of a 1,000-document array. Sort documents and id arrays by a stable key before writing, and use `sort_keys` on the JSON dump.

## Exclude staging bots

If you keep staging Pickaxes (testing reference), give them a recognizable name prefix and have the export skip them. Staging bots churn by design, and their diffs would pollute the history of the real tools.

## What git does not protect

The repo is a mirror, not a lock. Two people or two agent sessions can still write the same live Pickaxe at the same time, and git knows nothing about it. The protection for that lives in write scripts: re-fetch the live state, verify it matches what you based your edit on, and refuse to write on drift. Combined with the export diff, this turns silent concurrent clobbers into loud refusals.

The clobber also arrives on a delay, and the delayed form is easier to miss. A prompt field is replaced whole on write, with no merge step, so a full copy of a field kept as a draft file is a loaded clobber. Re-applying it weeks later silently reverts every live edit made since the draft was last synced, and the reverting commit's diff shows nothing, because the draft file itself did not change. After any live prompt edit, re-sync every draft file that mirrors the edited field so it stays byte-identical, or mark the drifted section superseded and name the live field as authoritative. A whole-field draft is a mirror that must be maintained, not an archive that is safe to leave stale.

## Bonus: the repo becomes context

An exported `role.md` per tool doubles as onboarding context for AI coding sessions. A session assigned to improve one tool reads that tool's export instead of pulling the live config, and the diff against the export shows exactly what the session changed.
