# Prompts and form fields

Observed August–September 2026. Read the stored config and assembled prompt, then test the input path the user takes.

In this file:

- Prompt lifetimes
- Editing the two frames
- Field descriptors and caps
- Form/chat settings
- Prompt changes worth testing

## Prompt lifetimes

| Field | Lifetime and use |
|---|---|
| Role (`role`) | Persistent system instructions, including behavior needed on follow-up turns |
| Prompt Frame (`promptframe`) | First form turn, with injected answers and static instruction prose |
| Model Reminder (`responseprefix`) | Prepended to user turns, for a few critical rules if testing shows a benefit |

Frame instructions do not persist as system instructions. Move rules needed on revisions into the Role. A Reminder is optional: one twelve-run test moved a target metric from 71% to 73% while increasing runtime 16%. Treat that as a null result, not a general finding that reminders cannot help.

Pickaxe's frame does not support Handlebars-style `{{#if}}` conditionals. Use labeled inputs and explain how to handle empty optional fields. Do not assert that a screenshot or document arrived when the upload is optional.

## Editing the two frames

`promptframe` and `rawpromptframe` are stored independently. Update both. Escape HTML-sensitive prose and represent newlines as `<br>` in the raw frame, while preserving field markup.

A new ordinary field needs its JSON descriptor in the plain frame and a matching non-editable placeholder element in the raw frame, with matching ID/data attributes and example text. Copy the element shape from a current working field. Document-upload descriptors were an exception: their absence from the raw frame was normal in the inspected configurations. Do not synthesize missing markup without checking the field type.

Fetch current state, make exact-match replacements with a unique-match assertion, then read back. The platform has normalized non-breaking spaces to spaces. Allow only known normalization, since broad whitespace normalization can hide a meaningful prompt change.

Assemble the frame with realistic answers before shipping it. A wrapper such as `But [answer] is in the way` mangles a multi-sentence answer and can disagree with the form label. Labeled input blocks usually need fewer assumptions about how users write. Keep the label, placeholder, prompt, and required flag consistent.

## Field descriptors and caps

Descriptors appear as embedded JSON, for example:

```json
{"id":"userinput:FIELD_ID","type":"Long Answer","answerlength":9001,"example":"Describe your audience"}
```

Preserve descriptors while editing surrounding prose. IDs must be unique within one frame, but clones may share IDs across bots. Cross-tool edits should identify both the bot and field.

The `example` text can reach the model for a blank field. Use appropriate placeholders and handle the blank branch. Validate required/optional behavior in the form rather than inferring it from prompt wording.

Text-field `answerlength` controls character capacity and rendered size. Keep Short Answer/Long Answer type consistent with the intended cap. Upload-field `answerlength` is a token budget: leave its upload type unchanged.

Upload caps have caused silent first-page or partial-document reads. Compare `answerlength` with `endusertokens` and the model's usable context before blaming the prompt. However, a September real-form run with `answerlength: 750` still reached late content in a long document. The condition explaining this counterexample remains unresolved.

Use distinctive source anchors to check what arrived. A late anchor demonstrates access to that region, not necessarily complete contiguous coverage. A first/last-section report can help expose truncation, but the model's report also needs checking. Re-measure content-dependent quality after fixing a cap, since newly visible text can expose errors such as spoiler leakage.

Builder saves have reset API-raised upload caps to 750, including a save made for a profile-image change. Read back caps and related budgets after a builder save. Reapply an intended value only after checking the live changes, rather than overwriting the whole config from a stale draft. Builder reasoning labels have also disagreed with stored `reasoningeffort`.

A Knowledge Upload widget accepts links and files, and can accept multiple files. Pasted document text over API `inputs` is a separate path. Wait for an upload to settle before submitting, then confirm a new run started. The tested picker omitted HEIC and TIFF while accepting PNG, JPEG, WebP, and GIF. Inspect the target widget's current `accept` list and offer a supported conversion when relevant.

## Form/chat settings

The tested Form + Chat combination is:

```json
{"type":"form-chat","chatflag":false,"enablechatresponses":true}
```

Setting `chatflag: true` changed `type` to `chat` and removed the form. Read and verify the coupled triple, including when staging or changing the conversation mode. A false `chatflag` alone does not mean follow-up chat is disabled.

Compare sibling configurations when a defect plausibly comes from a missing shared rule. Keep the comparison read-only unless the task includes changing the siblings. Audience assumptions and editorial framing belong to the user.

## Prompt changes worth testing

These are candidate techniques supported by particular tests, not guarantees across models:

- **Repair the instruction that generates an error.** A prohibition can lose to a conflicting format or task instruction. Read Role, Frame, and Reminder together. State which rule governs instead of stacking more prohibitions.
- **Make fixed headers explicit.** An input heading resembling the required output can be copied instead of rebuilt. Name the source of each slot and include an example where the input heading differs from the required one.
- **Anchor exact text to a real section.** A word-for-word mandate cannot fire at a section the output never creates. For a required passage, specify its location and test every sentence/link. Stating their count helped in one small test.
- **Define selection versus alteration.** “Choose self-contained quotes” must not authorize repairing a quote. For verbatim extraction, prohibit the observed repair classes and verify text, attribution, and location.
- **Propagate later evidence.** If later input changes an earlier entity's meaning, update the affected entry even when that entity does not reappear. Give this rule precedence over an “unchanged/no appearance” label.
- **Identify multi-file inputs by content.** Use an explicit header or other recognizer, not assumed upload order. Test both orders when order could matter.
- **Use evidence-appropriate quantities.** Retrieved lists may need fewer items than the target. Generative brainstorming can use fixed counts. Permit an honest shortfall where the supply is limited.
- **Use word budgets as approximations.** They can help meet character limits, but count the output with code when exact length matters. An author-supplied total can fix total-length arithmetic without validating the model's per-section distribution.
- **Measure the cost of extra instructions.** Prefer a local clarification to a new section where both solve the defect. Check nearby quality metrics for regressions.
- **Keep drafts and retractions out of the final output.** A rule to present only the chosen version helped with visible revisions. Validate both item counts and abandoned/replacement text.
- **Design a separate category only if it serves the task.** A labeled place for outdated search results reduced leakage into current results in one workflow. Do not create an outlet for material the user does not want.
- **Check native image rendering.** Use the action's asset card where the target surface provides one. A forced image-URL mandate led to fabrication after refusal. See [Actions](actions.md).

Prompt secrecy instructions are soft guards, not an access-control boundary. Test disclosure behavior if relevant, and keep actual secrets out of prompts.
