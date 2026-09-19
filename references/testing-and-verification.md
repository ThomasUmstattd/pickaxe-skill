# Testing and verification

Match the test to the intended claim. Reuse the user's existing criteria and stay within the requested targets.

In this file:

- Staging parity
- Cross-workspace copies
- Writes and visible effects
- Input transports and uploads
- Confounds and vendor changes

## Staging parity

Prompt edits change the targeted bot. Keep a private staging copy for experiments and snapshot the current production config before promotion.

1. Copy the behavior settings the test needs: Role, Reminder, both frames, model, reasoning, temperature where supported, output cap, input/memory/knowledge budgets, upload mode, the coupled `type`/`chatflag`/`enablechatresponses` settings, document attachments, retrieval settings, and actions.
2. Read back against an independently chosen parity checklist. Comparing only fields the copy function remembered can certify an empty frame or missing documents as correct.
3. List deliberate differences, such as privacy, name, deployment identity, or a test input limit. A difference may invalidate a particular comparison.
4. Run the scoped experiment. Keep outputs, input/config provenance, requested/served model, and measured cost or its missing-value reason.
5. Promote the tested prompt and configuration only within the authorized change. Keep staging names, privacy, deployment credentials, and test-only settings out of production. Check for live drift, then read back.
6. Verify the affected live behavior with a scoped, authorized check. Restore/release the staging copy according to the project's ownership rules.

Copy the production limits for a parity test. Raise a cap only for a test that needs that difference and record it. A staging copy with a different output cap once scored differently from production despite matching prompts. That makes the staged figure evidence about staging, not a guaranteed live rate.

Check an idle sandbox before use too. A stale prompt, different model, or zero attached documents can invalidate every arm. Batch attachment replacement is available for same-workspace copies, with full-set safeguards in [Knowledge base](knowledge-base.md). Own-key action secrets cannot be recovered from masked readbacks.

## Cross-workspace copies

A standard-privacy testing workspace can retain the history needed for measured telemetry while production remains on maximum privacy. That choice also retains submitted fixtures on the vendor's servers. Use material authorized for that retention and define cleanup as needed. Do not change production privacy just to measure a test.

September cross-workspace tests found:

- The action catalog was account-wide. Credit-backed actions attached using the same action ID and billing flag.
- Document IDs were workspace-scoped. Copying authorized extracted text, creating target documents, and attaching new IDs worked.
- Document copies needed size-aware splitting and a paginated inventory lookup.
- Copied knowledge was a snapshot, not a subscription to future source updates.

Separate workspaces do not prove parity in workspace-wide settings such as fallback. Check the differences relevant to the result. A copied KB can suit a prompt test while being stale for a freshness test.

## Writes and visible effects

Read state before editing and refuse a stale whole-field write. For surgical string changes, assert the anchor occurs exactly once. Afterward, verify the intended fields and coupled settings.

The mutation's return value can expose a discarded field, but only a fresh read establishes stored state. Stored state still does not prove presentation: an external `coverphoto` persisted while the embed rendered no image. Check the rendered UI for visual changes and exercise enforcement for required fields or limits.

Keep a rollback snapshot from the live read, not an old export. A parallel session can change the same remote bot despite separate Git branches.

## Input transports and uploads

Use `message` for chat-path questions. It bypasses the prompt frame, including static prose. Use `inputs` to test the form prompt with supplied text. A pasted resolved frame over `message` is exploratory evidence, not proof of the production form path. One apparent regression disappeared when the same comparison used `inputs`.

Real uploads add picker, transfer, and extraction behavior. Text passed through `inputs` cannot clear those layers. Use a small known-content file to check format support, and realistic-length material for truncation or long-context defects.

For browser testing:

- Open the embed's own URL when the outer page's accessibility tree cannot expose the iframe fields. Public deployments may allow this without an administrator session. Preserve the intended authentication/identity when testing access behavior.
- Verify the form/chat triple and `documentuploadtype`. An owner-only upload mode disabled the user widget on a staging copy.
- Inspect `accept`, labels, required flags, and upload completion state. The submit button can remain disabled for missing required inputs.
- Static HTML proves propagation, not client-side enforcement. An empty shell is inconclusive. Use a bounded retry or live browser check rather than polling until it happens to pass.
- Recorded field inputs can confirm capture where history exposes them. Some API form runs have empty history messages. Use a suitable canary/control if direct input evidence is unavailable.
- Identify profile-image and chat-icon file controls by their labels. Identical MIME attributes do not establish which control is which.

Prefer a browser's supported file-attach operation. If the available tool explicitly permits page JavaScript and file transfer, a tested fallback constructed a `File` from supplied bytes, set a `DataTransfer` on the existing input, and dispatched its change event. Verify bytes and upload state. This is tool-dependent guidance, not permission to bypass browser restrictions. A localhost file server can fail under private-network browser controls.

`document_upload` can separately test backend extraction, and its `rawStorageUrl` exposed extracted text in observed responses. That operation creates a workspace artifact and may incur processing, so use it only within the requested test scope. Verify known content and account for the artifact. It does not prove picker acceptance.

A bare URL in an API test is not a reliable universal “no content” fixture: fetching differs by path. To test a retrieval-failure branch, provide representative failure text or verify that no usable source arrived.

## Confounds and vendor changes

The workspace fallback can serve another model and adjust reasoning to a supported level. Its backup pool changes, so fallback is not a stable comparison arm. Capture served-model and fallback evidence through Insights, retain charges, and report those answers separately.

Time-sensitive retrieval can change between identical inputs. A changed date is a signal to inspect source evidence, not proof of fabrication. A single changed verdict across file formats likewise needs a parsing check or repetitions before assigning causality.

Nightly processes have restamped bot `updatedAt` values. Use exported content diffs to date prompt changes. History's generation-model field once joined current config, but the reported bug was fixed. Verify discrepancies rather than repeating a superseded diagnosis.

For an “Access denied” report, distinguish the actual asset request, guest upgrade page, and blank unauthenticated deployment. A file opening directly may still fail when embedded under a different referrer or authentication context. Reproduce the relevant request.

After a vendor fix, rerun the original reproduction within scope. Then search instructions and references for the old claim and replace it, preserving any useful diagnostic technique. Keep measured facts, unresolved hypotheses, and provider announcements distinct.
