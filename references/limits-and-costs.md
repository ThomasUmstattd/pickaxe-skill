# Platform limits and cost architecture

In this file:

- The 300-second completion ceiling
- Input paths and their caps
- Upload format whitelist is client-side
- Credit caps are per-deployment
- SSO identity and monetization paths
- Admin group toggles are mutually exclusive and destroy purchased credits
- Temperature is on its way out
- Cost architecture patterns
- Changing the model does not rescale token budgets
- Per-run cost cannot be measured from the API
- Embedding on WordPress behind Cloudflare
- Big-workspace responses overflow clients

## The 300-second completion ceiling

Completions die server-side at 300 seconds (observed August 2026, reproduced across models and search backends with a client timeout far higher). The error is an empty-detail "Could not reach the Completion API:", which looks like an outage rather than a timeout and has cost hours of misdiagnosis.

- **Check the wall clock first.** A failure at almost exactly 300 seconds is the ceiling. Retrying changes nothing unless the run gets faster. And a run that dies at the ceiling may already have spent an attempt on the workspace fallback, since timeouts are a fallback trigger (testing reference).
- **Design to the ceiling.** Treat 300 seconds as the budget even if the platform someday raises it, because users will not wait longer anyway. Cap search calls and output length so healthy runs finish with margin. Measure per-call action latency before committing to a multi-call architecture.
- The ceiling was measured on the workspace MCP completion tool. The same slow tool completed six times over the public completions endpoint with `stream: true`, at 187 to 252 seconds (api-mechanics reference), so streaming at least removes the client-side idle. Whether a streamed run survives past 300 seconds, and whether the ceiling applies to end-user embed chat, are still unobserved.

## Input paths and their caps

Three different paths carry user input, each with its own cap:

- **API completion messages** are capped by the bot's `chatinputlength` (default 250 tokens on new bots). It is a token cap, it binds only the `message` path, and it fails loudly on the public completions endpoint with "Message is too long".
- **Form text fields and upload fields** are capped by their descriptor's `answerlength` (see the prompt fields reference for the silent-truncation trap). That cap also governs text passed into an upload field over the `inputs` path.
- **Embed file uploads** take a different path than API messages, so an API test does not prove the upload path works, and vice versa. The end-user upload widget also has to be enabled at all: `documentuploadtype` at the owner-only value disables it with "File uploads are disabled for this Pickaxe" (testing reference).

## Upload format whitelist is client-side

The embed's file picker enforces a format whitelist in the client, and the error ("You can only upload PDF, TXT, DOC...") comes from the platform, not from anything configurable per tool. The whitelist can lag the backend: `.m4a` audio was blocked by the picker while the transcription backend handled the format fine when it got through (observed August 2026, reported to Pickaxe). If a format matters to your users, test it through the real embed, and file a ticket when the picker is the only thing blocking it.

The rejection message and the file input's `accept` attribute are two independent lists, and they drift. The input has accepted audio and video MIME types while the error text named neither, so a user can upload an audio file successfully and later be told audio is unsupported. Never diagnose an upload rejection from the error text. Read the `accept` attribute on the rendered embed's file input, which is what the picker enforces, and report a message mismatch and a missing format as separate defects.

## Credit caps are per-deployment

Usage limits on public access groups enforce hard, but **per deployment (per tool), not aggregated per user across a workspace**. A user who exhausts the cap on one tool keeps full allowance on every other tool. The group settings UI states this, in fine print that is easy to read past.

Mechanics worth knowing (observed August 2026):

- Each user record has a top-level `currentUses` counter and a per-deployment `uses[]` array. For public groups, live runs debit and enforcement reads the per-deployment counters. The top-level counter sits unused.
- The embed's low-credit warning banner reads the top-level counter, so users on public groups get no warning before hitting the wall on one tool.
- Members-group wallets behave differently: a credits-per-month wallet on a members group aggregates across the workspace into the top-level counter.
- `run_pickaxe_completion` does not debit member wallets. API runs bill the workspace owner, so API testing does not distort user credit counters, and also does not exercise the enforcement path.
- Auditing usage: `user_get` exposes the per-deployment `uses[]` array. A user's real total is the sum across deployments, and a per-deployment counter pinned at exactly the cap value means enforcement fired.

## SSO identity and monetization paths

Embed SSO hands the embed a signed token carrying the external site's user identity, and the platform mints one user record per distinct email in that token. When the upstream email changes for a user who already paid, the next login creates a second empty record, and the purchased credits stay stranded on the first with no warning on either side. Before wiring SSO to any paid tier, confirm what the token's email derives from and whether it can change for an existing user, and resist fixing a stale email by syncing it upstream, since changing the email is exactly what splits the identity. After any SSO change, list the workspace's users and look for a new record that appeared around the change, because the failure presents as absence of activity on the expected record.

Monetization paths differ by access group type. A public-type group has no buy-more-credits control (`isBuyMoreUses` stays false), so the only path out of a free public tier is `isUpgradeToAnotherGroup` pointed at a members group. That upgrade crosses into platform-native sign-in, which an SSO user has no credentials for, so the purchase journey can dead-end at a login wall for an account the user never knowingly created. Test the whole journey as an SSO user before treating a wired-up upgrade path as working (observed August 2026).

## Admin group toggles are mutually exclusive and destroy purchased credits

Access group assignment is single-group-per-user. Enabling a new group for a user in the Studio's admin drawer silently disables the current one, with no warning and no confirmation step. The vendor confirmed in August 2026 that this is intentional and filed a UI warning as an internal ticket with no date.

Toggling a credit-pack group off destroys the user's purchased `extraUses`, resetting them to zero. This too is by design: the admin toggle is a manual provisioning tool for off-platform payments, so granting mints credits without a payment processor and removing resets to zero. Combined, one accidental click in the admin drawer can wipe a paying customer's purchased credits with no undo, and the vendor acknowledges the UI does not communicate the consequence.

Two habits. Avoid manual group changes in the admin drawer for any user who has purchased credits. And assign groups programmatically through `user_update` with `accessGroupId` (api-mechanics reference) rather than the toggle, for example during an SSO sync, since the API path does not carry the mint-and-destroy behavior.

## Temperature is on its way out

Pickaxe plans to deprecate the temperature setting as models move to dynamic temperature. Do not build fixes or A/B tests around temperature values. Reach for prompt-side fixes and model choice instead, so the work survives the platform change.

## Cost architecture patterns

Three decisions dominate per-run cost and runtime:

- **Single-shot retrieval beats tool loops.** In a search-action loop, the full input context re-bills on every round trip, so an 8-search run pays for the prompt 8 times. Architectures that gather everything in one retrieval pass are dramatically cheaper and also fit the timeout ceiling.
- **When multiple searches are unavoidable, batch them.** Sequential search calls stack per-call latency and per-round re-billing until they hit the 300-second ceiling. In one measured case, no provider's search action completed 8 to 12 sequential calls under the ceiling, on any of three backends. The same work restructured into at most 4 calls, each carrying one objective and several queries, finished with real margin and better result quality. Reserve one batched call for verifying load-bearing facts such as dates. The per-call cost was never the problem, the stacked round trips were.
- **Ask for the smallest sufficient input.** A tool that only needs a book blurb should not accept a full manuscript. Moving a tool from manuscript input to blurb input cuts per-run token cost by orders of magnitude and usually improves focus.

For retrieval-heavy tools, remember the token allocation waterfall (knowledge base reference): raising one budget starves another, and the failure is silent.

## Changing the model does not rescale token budgets

`reservedtokens`, `endusertokens`, `membuffer`, and the `ragbudget` map are sized to whichever model was set when they were written, and a model change leaves all of them untouched with no warning. Moving a tool from a 2,000,000-token-window model to a 500,000-token one left every budget above the new window, and the update reported success. Rescale by the window ratio after a model change, but only the window-derived fields: budgets that appear as identical round numbers across tools on different models are settings, and the output-length cap is worth leaving alone when it already fits, since shrinking it can truncate long reports. One bounding caveat: tools have run with over-window budgets without visible damage, so treat this as post-change hygiene rather than the explanation for a bug you are already chasing.

## Per-run cost cannot be measured from the API

Completions return generated text and a success flag with no usage block, no input token count, and no output token count. The platform's own per-message cost and latency telemetry lives only in the Studio UI. So an API-driven model comparison can measure latency, output length, and instruction compliance, but any cost figure in it is modeled from provider list prices rather than measured, and should be labeled that way in the writeup.

Two things break naive cost models. A model family can change its tokenizer between versions, so identical input text bills a different token count at unchanged per-token pricing, and a newer model at the same sticker price can be materially more expensive per run. And the platform resells inference in credits without publishing per-model rates, so first-party provider pricing is a proxy, not the bill. Establish a token baseline on the actual input before concluding a model is cheaper or dearer, and beware comparisons run during a provider's promotional pricing window, which give the wrong answer for the month after it ends.

## Embedding on WordPress behind Cloudflare

Cloudflare's Rocket Loader rewrites script tags and breaks inline JavaScript, including Pickaxe embed and SSO handshake snippets. Fix: add `data-cfasync="false"` to the script tag so Rocket Loader leaves it alone.

## Big-workspace responses overflow clients

`document_list` and `pickaxe_documents` on a 1,000+ document workspace return over a megabyte, which exceeds most MCP clients' tool-result limits. Save the response to a file and query it with `jq` or a script.
