# Prompt architecture and form fields

## The three prompt fields

A Pickaxe has three places to put instructions, and they behave differently across a conversation:

- **Role** (`role` in the API). The system prompt. It persists across every turn, so all persona, rules, formatting requirements, and catalog data that must survive follow-up questions belong here. For Form + Chat tools this matters doubly, because the prompt frame fires once and then the conversation continues on the Role alone.
- **Prompt Frame** (`promptframe`). The first user-turn message for form tools. It fires once, injecting form answers via `[bracketed variables]`. Handlebars-style `{{#if}}` conditionals are not supported. Express conditional logic through labeled form options instead ("If the user chose Proposal Comps, then...").
- **Model Reminder** (`responseprefix`). Invisibly prepended to every user message. It is the backstop against instruction drift on long conversations, so reserve it for the few most critical non-negotiable rules rather than duplicating the Role.

## The prompt frame is stored twice

`rawpromptframe` is an HTML rendering of `promptframe`, stored independently and not derived from it. Update both consistently or the builder UI and the runtime drift apart. Converting plain to raw: escape `&`, `<`, `>` and turn newlines into `<br>`.

## Form field descriptors are embedded JSON

Form fields live as JSON objects embedded inline in the prompt frame string, shaped like `{"id":"userinput:...", "type":"...", "answerlength":..., "example":"..."}`. Preserve them byte for byte when editing the surrounding prose. The safe workflow for programmatic edits:

1. Fetch the live config.
2. Apply exact-match string replacements, asserting each match lands exactly once.
3. Write back, re-fetch, and diff against what you intended to write.

Two behaviors of the descriptors that are not obvious:

- **`example` text is model-visible.** Placeholder examples from the form ("Austin, TX", "Urban Fantasy") can leak into outputs when a user leaves the field blank. Write examples you would not mind seeing in a response, or handle the blank case in the prompt.
- **A field id appearing twice in one frame is corruption.** Guard against it before writing.

## `answerlength` silently truncates input

`answerlength` on a field descriptor is a hard cap on how much of the user's input reaches the model, and the model has no idea text was cut. This produces the classic complaint "the tool only looked at the first part of what I gave it" while every run reports success.

Details that matter:

- On a document upload field, `answerlength` caps the upload **regardless of** the bot's overall `endusertokens` budget. A tool with a million-token budget and a 750-token upload cap reads about one page. Audit for this: in one 88-tool workspace, 47 tools had `answerlength` below `endusertokens`.
- The runtime reads only `answerlength` to size a field. But the builder UI keeps `answerlength` correlated with the declared `type` ("Short Answer" vs "Long Answer"), and it has never been observed pairing "Short Answer" with a large cap. Set both together when raising a cap, or a later save from the builder may clamp the cap back down and silently undo your fix.
- A cheap guard against future silent truncation: have the tool's first output step report the first and last section it received. Truncation then becomes visible to the user instead of masquerading as shallow analysis.

## Form to chat conversion

Form + Chat means `type: "form-chat"` plus `enablechatresponses: true`. The `chatflag` field stays false on working form-chat tools, so do not flip it as part of the conversion.

## Prompt-writing findings that held up

- **Character budgets need word-count proxies.** Most models cannot count characters reliably. When output must fit a hard character limit, set a word cap derived from the domain's real average word length, aim below the limit ("aim for 40 to 48, never exceed 50"), state a floor as well as a ceiling, and include a static good and bad example. Never ask the model to display character counts it cannot compute.
- **Prompt length has a real cost.** Two fixes tested at four runs each reached the same target metric, but the longer one (a full new section vs one sentence appended to an existing rule) degraded two unrelated metrics, apparently by crowding the prompt. Prefer extending an existing rule over adding a section, and always measure the metrics a change was not aimed at.
- **Selection criteria and fidelity rules conflict across fields.** A prompt-frame rule to pick "self-contained" quotes plus a Role rule forbidding edits made the model repair quotes into self-containment, silently rewriting them. When a criterion in one field can be satisfied by violating a rule in another, say explicitly which one governs ("self-contained governs which lines you pick, not whether you may change one").
- **Anti-prompt-leak framing.** Prohibitions on revealing the prompt work better placed at the top of the prompt frame with concrete framing such as "the user will copy your entire response", which makes the leak consequence legible to the model.
- **Exact-reproduction mandates need the word-for-word frame.** Soft mandates ("end the section with this note: ...") get skipped or paraphrased. "Close the section with this exact paragraph, reproduced word for word:" followed by the literal text reproduces reliably.
- **Let the user supply ground-truth numbers.** When a prompt needs an arithmetic fact about a long uploaded document (its total length, a count), the model's own estimate can run materially wrong (an observed 18% undercount on a book-length document) while everything else in the output is accurate, and any math built on the estimate inherits the error invisibly. Add an optional form field for the true number, tell the model to scale its per-section estimates to match it when present, and have it disclose that its total is an estimate when the field is blank.
- **Deliberation can leak into the final answer even with reasoning display off.** On tasks that weigh several options in one completion, the user-facing answer can include scratch-work narration ("this option is worse, let me try another"). This is genuine output text, not the hidden reasoning trace, so no display setting controls it. Instruct the prompt to explore options privately and present only the decided result, quote a real leaked sentence in the rule as an example, and check multi-option outputs for this leak specifically since it hides from a skim for factual correctness.
- **State counts as targets, not quotas.** A hard "produce N items" demand forces padding when honest material runs short, and the padding looks plausible (directory pages formatted as real items, near-duplicates split into separate entries). Frame the count as a target, state outright that a shorter honest list is a successful response, and say where the shortfall should be acknowledged.
- **Give banned content a legal outlet.** A flat prohibition ("never include expired items") gets violated when the banned material is most of what the model found. Designating a labeled place for it, separate from the main results, ended the violations that the flat ban did not. Prohibition plus outlet beats prohibition alone.
- **Rules get satisfied mechanically, so write them against intent.** A rule stated as a category quota ("at least half must be type X") was satisfied with items matching the category while missing the actual audience entirely. Restate such rules in terms of the outcome you mean, include one worked example, and explicitly prefer a shorter list over a technically compliant wrong one.
- **Content that arrives unmarked needs a marking rule, not a preservation rule.** A cleanup tool preserved bracketed author notes perfectly and still failed users who dictate, because spoken notes arrive with no brackets to preserve. The output kept every word and dropped the meaning, turning a private note into narrative prose, which is worse than deletion because nothing looks missing. When meaning-bearing markup can be absent from the input, instruct the model to recognize the content and add the markup, and place that rule above any remove-filler rule so the content cannot be classed as filler first.
