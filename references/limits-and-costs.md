# Platform limits and cost architecture

## The 300-second completion ceiling

Completions die server-side at 300 seconds (observed August 2026, reproduced across models and search backends with a client timeout far higher). The error is an empty-detail "Could not reach the Completion API:", which looks like an outage rather than a timeout and has cost hours of misdiagnosis.

- **Check the wall clock first.** A failure at almost exactly 300 seconds is the ceiling. Retrying changes nothing unless the run gets faster.
- **Design to the ceiling.** Treat 300 seconds as the budget even if the platform someday raises it, because users will not wait longer anyway. Cap search calls and output length so healthy runs finish with margin. Measure per-call action latency before committing to a multi-call architecture.
- Whether the ceiling applies to end-user embed chat, where streaming may keep the connection alive, was unconfirmed at the time of observation.

## Input paths and their caps

Three different paths carry user input, each with its own cap:

- **API completion messages** are capped by the bot's `chatinputlength` (default 250 tokens on new bots).
- **Form text fields and upload fields** are capped by their descriptor's `answerlength` (see the prompt fields reference for the silent-truncation trap).
- **Embed file uploads** take a different path than API messages, so an API test does not prove the upload path works, and vice versa.

## Upload format whitelist is client-side

The embed's file picker enforces a format whitelist in the client, and the error ("You can only upload PDF, TXT, DOC...") comes from the platform, not from anything configurable per tool. The whitelist can lag the backend: `.m4a` audio was blocked by the picker while the transcription backend handled the format fine when it got through (observed August 2026, reported to Pickaxe). If a format matters to your users, test it through the real embed, and file a ticket when the picker is the only thing blocking it.

## Credit caps are per-deployment

Usage limits on public access groups enforce hard, but **per deployment (per tool), not aggregated per user across a workspace**. A user who exhausts the cap on one tool keeps full allowance on every other tool. The group settings UI states this, in fine print that is easy to read past.

Mechanics worth knowing (observed August 2026):

- Each user record has a top-level `currentUses` counter and a per-deployment `uses[]` array. For public groups, live runs debit and enforcement reads the per-deployment counters. The top-level counter sits unused.
- The embed's low-credit warning banner reads the top-level counter, so users on public groups get no warning before hitting the wall on one tool.
- Members-group wallets behave differently: a credits-per-month wallet on a members group aggregates across the workspace into the top-level counter.
- `run_pickaxe_completion` does not debit member wallets. API runs bill the workspace owner, so API testing does not distort user credit counters, and also does not exercise the enforcement path.
- Auditing usage: `user_get` exposes the per-deployment `uses[]` array. A user's real total is the sum across deployments, and a per-deployment counter pinned at exactly the cap value means enforcement fired.

## Temperature is on its way out

Pickaxe plans to deprecate the temperature setting as models move to dynamic temperature. Do not build fixes or A/B tests around temperature values. Reach for prompt-side fixes and model choice instead, so the work survives the platform change.

## Cost architecture patterns

Two decisions dominate per-run cost:

- **Single-shot retrieval beats tool loops.** In a search-action loop, the full input context re-bills on every round trip, so an 8-search run pays for the prompt 8 times. Architectures that gather everything in one retrieval pass are dramatically cheaper and also fit the timeout ceiling.
- **Ask for the smallest sufficient input.** A tool that only needs a book blurb should not accept a full manuscript. Moving a tool from manuscript input to blurb input cuts per-run token cost by orders of magnitude and usually improves focus.

For retrieval-heavy tools, remember the token allocation waterfall (knowledge base reference): raising one budget starves another, and the failure is silent.

## Embedding on WordPress behind Cloudflare

Cloudflare's Rocket Loader rewrites script tags and breaks inline JavaScript, including Pickaxe embed and SSO handshake snippets. Fix: add `data-cfasync="false"` to the script tag so Rocket Loader leaves it alone.

## Big-workspace responses overflow clients

`document_list` and `pickaxe_documents` on a 1,000+ document workspace return over a megabyte, which exceeds most MCP clients' tool-result limits. Save the response to a file and query it with `jq` or a script.
