# Limits and costs

Observed August–September 2026. Separate the request path, access-group type, and user identity before interpreting a limit or charge.

In this file:

- Timeouts and paid attempts
- Input and upload limits
- Public allowances and member wallets
- Identity and membership changes
- Cost and model budgets
- WordPress embeds

## Timeouts and paid attempts

The workspace MCP completion tool repeatedly failed near 300 seconds with “Could not reach the Completion API.” A longer client timeout did not remove that measured server ceiling. The same error text can also describe another failure, so record elapsed time.

A client deadline does not prove that the provider stopped or charged nothing. Completed answers and costs have been recovered after client timeouts. Read history and Insights before retrying, preserve the operational failure status, and keep missing charges unknown.

Budget attempts, elapsed time, and spend separately. A small number of premium requests over a large KB can be expensive even inside a short time window. Reuse saved reference answers when the input and configuration still match the question being evaluated.

Streaming public API runs finished between 187 and 252 seconds in one comparison. Those runs did not establish survival past 300 seconds or a ceiling for embed chat. Design for useful response time and margin on the tested path. Do not infer that all interfaces share one timeout.

## Input and upload limits

| Path | Relevant limit |
|---|---|
| Completion `message` | `chatinputlength`, a token cap, defaulting to 250 on observed new bots |
| Form text | Descriptor `answerlength`, a character cap |
| Upload field / extracted text over `inputs` | Descriptor and end-user token budgets, with path-dependent behavior |
| Real upload | Picker acceptance, enabled upload mode, extraction, size, and model context |

A public API message exceeding `chatinputlength` failed loudly with “Message is too long.” Upload caps have truncated silently, but a low configured cap is not sufficient evidence that a particular real-form run was truncated. See [Prompts and fields](prompt-and-form-fields.md).

The picker and backend can support different formats. A blocked audio format transcribed through `document_upload` in an August test. The rejection message also differed from the widget's `accept` list. Inspect that list and use known-content files to distinguish client rejection from extraction failure.

A multi-file upload of several megabytes failed with a model-timeout message while the individual files succeeded. That isolated a multi-file-path problem, but did not establish which internal stage consumed the time. Test the actual files through the actual widget before prescribing a model swap or an architectural workaround.

For workspace documents, `document_create` accepted 4.0 MB and rejected 5.2 MB in a probe. Split on content boundaries below the observed ceiling. Base64 inflates a request. See [Knowledge base](knowledge-base.md).

## Public allowances and member wallets

The observed distinction:

- Public access-group allowances enforced per deployment, rather than one shared user allowance. Check the per-deployment `uses[]` counters.
- Member wallets used top-level counters across tools. Tests spent the recurring allowance before extras and denied new requests after both were exhausted.
- A one-time grant populated `extraUses`. Extras therefore do not establish purchase provenance. Do not add the group's initial allowance to that remaining pool or call it purchased credit without a ledger.
- `-1337` represented unlimited in observed deployment/group limits. Display unlimited explicitly instead of doing subtraction with the sentinel.

The workspace MCP tests and user-attributed deployment requests are different billing paths. Older workspace tests did not debit a user wallet, while September user-attributed REST tests did. Verify the exact endpoint, identity, group, and counter changes before claiming a request does or does not bill the user.

Anonymous embed guests did not appear in `user_get`/`user_list` in the tested workspace. A guest's screenshot and browser session may be the only available evidence. Do not promise a guest reset or merge into a signed-in account without checking that path.

A credit wall during an image-action run appeared as an empty-prompt provider error and a budget-limit interruption. A workspace API test then generated an image because it did not reproduce that guest wallet. Treat this as a diagnostic clue, not proof that every empty-prompt error is billing.

A deployment's `usageLimit`, its access group, and an upgrade/limit message describe different parts of enforcement. Read the active configuration and exercise the relevant identity before attributing an access-denied report to the prompt.

## Identity and membership changes

Assigning a group with `user_update.data.accessGroupId` reset both `currentUses` and `extraUses` in September tests, including reassignment to the user's existing group. Read current membership and skip already-enrolled users. Supplying saved counters in the same update preserved synthetic values, but that read-and-write sequence can race with spending or purchases.

The Studio's group toggles were also destructive: enabling one disabled the other, and removing a credit-pack grant reset extras. Neither API reassignment nor an admin toggle is a wallet-safe migration primitive. Use a verified provider operation for the requested migration, or report the missing guarantee.

For SSO, record how the external identity maps to the Pickaxe account and test changes with a stable upstream user in a fresh session. An earlier report attributed two records to an email change. A later audit found the historical identity evidence inconclusive, so treat email migration as a risk to test rather than a proven universal rule.

Public groups lacked a direct buy-more-credits control in observed settings. Their upgrade path led to a members group, and an SSO purchase journey could encounter a platform sign-in. Test checkout and return-to-site as the intended user before calling that journey complete.

## Cost and model budgets

Message Insights now supplies measured per-answer cost, tokens, served model, fallback, and timing where history is retained. Use the [session recovery procedure](api-mechanics.md). A bot's all-time analytics total mixes configurations and is not a per-run measurement.

Keep fallback charges in campaign cost, while separating those answers from the requested model's quality comparison. Record requested reasoning as well as the served model. A backup model may not support the same reasoning level.

Provider list prices are estimates of cost on this platform, not the bill. Tokenizers, caching, action charges, and promotional rates can affect comparisons. Label estimated and measured costs separately.

Changing the model did not rescale `reservedtokens`, `endusertokens`, `membuffer`, or `ragbudget` in observed updates. Check their fit against the new context window and a working configuration. A window ratio can be a starting estimate for window-derived fields, not a reason to shrink fixed settings or output length without checking the task.

For cost-sensitive tools:

- Ask for the smallest sufficient input.
- Batch searches where the action supports it, reducing sequential latency and repeated context processing.
- Compare observed cost and useful output rather than assuming a particular number of searches or a provider price predicts the bill.
- Confirm model support before varying temperature or reasoning. Treat deprecation plans as dated information, not a ban on a currently supported test.

## WordPress embeds

Cloudflare Rocket Loader can interfere with inline embed/SSO JavaScript. `data-cfasync="false"` on the script is the recorded opt-out. Check the actual failing surface before changing the host page, since an iframe, a login/upgrade page, and an asset request can fail independently.
