# Actions

Observed August–September 2026. Check the current action definition and attachment state before changing it.

## Attachments, triggers, and keys

The tested per-Pickaxe limit was four actions. Reduce unnecessary calls first. A larger workflow may need routed Pickaxes, with latency and billing checked across the full route.

Define action purpose and conditions in the Role and the attachment's trigger prompt. Replacing a manifest through `action_update_manifest` reset customized attachment triggers to a generic default. Read and restore the intended triggers for affected attachments after a manifest change.

`isUsingPickaxeCredits` belongs to the attachment. The same action can use different billing credentials on different bots.

| Attachment | Staging implication |
|---|---|
| Credit-backed | Set `isUsingPickaxeCredits: true` when connecting so Pickaxe supplies its managed provider key. |
| Own-key | Readback masks the stored secret. Copying that masked value cannot reproduce the attachment. Use an authorized secret source or the Studio's key control. |
| Keyless built-in | Can avoid key provisioning, but a different backend is a different test configuration. |

Connecting without required credentials returned `Variable <NAME> is required`. Do not interpret a keyless failure as a prompt defect.

Switching an existing own-key attachment to platform credits worked through disconnect/reconnect, with the credit flag both top-level and inside `data` over JSON-RPC. Confirm the current schema. Record action settings and trigger text first, then verify the reconnected state and a permitted run. The trigger survived the observed switch, but do not rely on that for rollback. Disconnecting can lose the original stored key, and this switch changes billing, so it must fall within the user's requested change.

The Studio's deactivate toggle preserved keys for temporary action experiments. Use it when available instead of detaching a keyed action. A prompt asking the model not to call an action is not an enforcement toggle.

The action catalog was account-wide in September cross-workspace tests, and the same credit-backed action ID attached in another workspace on that account. Verify availability and settings on the target. Documents have different scope rules.

## New actions

For a requested custom action, Pickaxe's [Wingman](https://pickaxe.co/learn/wingman) accepts a specification of purpose, endpoint, parameters, credentials, and response handling. Use the supported builder or API that fits the task. Put credentials in its secret control, not in a prompt or committed manifest.

## Image inputs and results

The tested embed appended successful image-action results as native inline asset cards with download/copy controls. A prompt requiring the model to write `![alt](URL)` was unnecessary there and produced a fabricated URL after an action refusal. Check the target surface before imposing an output-link format.

For that native-card surface, keep the reply short and let the platform attach the image. On refusal or failure, report the failure and a relevant next step without claiming an image exists. If another consumer needs a URL, use the actual action result, never a guessed path.

Successful action files were publicly retrievable on Pickaxe's CDN shortly after generation. Long-term retention was not measured. Inspect the exact returned URL and the failing request path before blaming expiry. A guest portal's upgrade page can say “Access denied” even when the file is available.

A tested image upload reached an image-editing action with source layout preserved across six first runs, and a follow-up retained the reference. That supports that action/input path, not a guarantee for every upload or model. To diagnose fidelity, separate the orchestrator's reading, action arguments, and image output.

The orchestrator chose the image action's `aspect_ratio` unless instructed. A tested portrait 2:3 requirement yielded 1024×1536 outputs. Specify the intended format and verify resulting dimensions for print/display tools. Test revisions too: content rules can hold on the first image and fail later.

## Action runs and timing

`action_runs` accepted `actionId` plus optional `limit`. Observed rows included status, parsed arguments, session ID, and a content string containing a Python-repr result. Parse that format with `ast.literal_eval`, not `eval`, when needed.

The observed rows had no action-duration field, and equal `createdAt`/`updatedAt` timestamps were not latency measurements. Message Insights now provides per-answer timing and cost, but do not assume it isolates each action's duration. See [API mechanics](api-mechanics.md).

A completion's `success: true` can wrap an apology after a failed action. Check the run status, returned asset, or embed before counting it as a successful image generation. Action diagnostics can work even when transcript history is unavailable.

Measure latency before designing loops. Sequential searches can exhaust the completion budget. Batch related queries where supported, and check both quality and measured cost. Platform-managed keys still bill credits.
