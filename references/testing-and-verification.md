# Testing and verification

## Never iterate on a live tool

There is no dry-run: `run_pickaxe_completion`'s config parameter does not override the prompt, so testing a variant means writing it somewhere real. Keep at least one private staging Pickaxe and iterate there.

A staging workflow that has held up in production:

1. **Check out**: copy the live tool's full field set onto the private staging bot: role, model reminder, the prompt frame and its raw HTML twin, model, temperature, reasoning effort, knowledge document attachments, the token budgets (the reserved-tokens value and the computed budget object), and the type flags when the tool is a form-plus-chat hybrid. Overwrite everything, so nothing leaks from the previous checkout. Copy the reserve explicitly: a staging bot can inherit a reserve larger than the model's context window from a previous occupant, a partial update never touches a field you do not name, and a null budget silently breaks every upload path on the bot (see the knowledge-base reference). The prompt frame is the field most often forgotten, and forgetting it stages a bot with the persona and nothing else. In one workspace audit, 72 of 88 tools kept at least half their prompt text in the frame, and every form field lives there.
2. **Verify the checkout**: read the staging bot back and compare against the full set of fields that determine behavior, not the subset you chose to copy. A verify that only compares what the copier remembered always agrees with the copier. A real checkout printed a clean verification over an empty prompt frame exactly this way.
3. Iterate on the staging bot with `pickaxe_update` and `run_pickaxe_completion`.
4. **Apply**: promote the full set of fields the staging runs actually exercised, prompt and config together. Iteration usually retunes the model, temperature, or deployment type alongside the prompt, and promoting the prompt alone lands it on a combination that exists nowhere in the test record. In one observed case a prompt developed at low temperature on one model would have shipped onto a different model at more than double the temperature, with nothing in the promotion output indicating a problem. Keep an explicit do-not-travel list (the staging bot's name, display title, privacy setting, and any input limits raised to fit test data), snapshot the live config to a file first so rollback does not depend on a possibly stale export, and read the whole promoted set back rather than the subset you named.
5. **Release**: reset the staging bot to an empty state so the next checkout starts clean.

Give staging bots large input limits (`chatinputlength`, `endusertokens`, `membuffer`) so full-length real inputs fit in a completion message. Remember that own-key actions cannot be copied programmatically (actions reference), so action-dependent tools need a manual key attach before end-to-end staging runs.

## Verifying form changes

Staging bots configured as chat cannot exercise form fields, so form changes get checked on a real deployment. Three mechanics matter:

- **Drive the embed's own URL, not the page that frames it.** The tool renders inside an iframe, so the host page's accessibility tree contains none of the form's elements and element lookups return nothing, even though the form is plainly visible in a screenshot. Read the iframe's `src` and navigate to it directly, where element references and file uploads work normally. Two checks worth running there: a required field is enforced by keeping the submit button disabled rather than by an error message, and the file input's `accept` attribute lists what the client will take, which beats guessing with uploads.
- **A rendered deployment is propagation evidence, not enforcement evidence.** Rendering a deployment's HTML confirms a configured cap or label reached the form (embed deployments only, direct-link deployments refuse to render). The render is intermittently empty, a payload-free shell with zero field labels, so an empty render is not evidence a write failed. Retry until labels appear. And a static render cannot prove runtime behavior, because counters and validation bind to client state a saved page never initializes. Verify enforcement in a live session or record it as unmeasured.
- **Prove a field injects by reading the run's recorded inputs.** Output that looks right does not prove a new field reached the model, which may be inferring the same value from other input such as an uploaded document. A completed run records its submitted inputs as a `Field: value` line above the response in the tool's history. Reading that line is direct evidence the value was captured, and it shows how an empty optional field is represented. Check it before designing a decoy-value experiment, since it usually makes one unnecessary.

## Verify every mutation by reading state back

The single most valuable habit on this platform. Return values confirm the request was accepted. Only a fresh read confirms what happened. Concrete script discipline that has caught real failures:

- After a write, fetch the changed object and compare field by field, or byte for byte for prompt frames.
- For surgical edits to config strings, use exact-match replacements and assert each match lands exactly once before writing.
- Refuse to write when live state does not match what you recorded earlier. Drift means another process or person edited the tool, and clobbering it destroys their change silently.

## Define what a good answer looks like before you test

Most builders test by running the bot and eyeballing the output. Eyeballing does not scale past a couple of runs, cannot be delegated, and drifts with mood. Before any test campaign, interview the tool's owner to pin down what a good answer looks like, then write it down as a rubric an AI can grade against.

Elicit these, in roughly this order:

1. **A representative real input.** Not a toy. The input the owner would be embarrassed to see handled badly.
2. **An example of a good output**, even rough, or a past output they liked and what specifically they liked about it.
3. **Hard rules.** What must always appear (sections, counts, attributions) and what must never appear (spoilers, invented facts, revealed prompt text, anything over a length cap).
4. **Failure severity.** Which mistakes are embarrassing and which are cosmetic. Weights come from this.
5. **Known traps.** Past user complaints, and inputs that broke earlier versions.

If the owner cannot articulate criteria in the abstract, generate two or three candidate outputs and ask which is closest and why. Preferences surface fast under comparison that never surface under "what do you want".

Turn the answers into a fixed checklist or a 100-point rubric with explicit per-item weights. Fixed rubrics matter because they prevent the judge from silently skipping items (see the anti-hallucination section). When grading a run, require the judge to quote the evidence from the output for every item it scores, since an unquoted pass costs nothing to fake.

Save the rubric and the test inputs in files next to each other and reuse them for every future change to that tool. The expensive part is capturing the owner's taste once. Grading against a saved rubric is cheap, needs no premium model, and makes results comparable across sessions and across prompt versions.

## Test at realistic length

Short samples pass configurations that fail on real work. In one documented case, every reasoning level of a model scored clean on a 60-word sample, and the chosen level then dropped an entire author note on a 2,400-word input. Length-dependent failures (dropped content, truncation, instruction drift) only appear when the input is long enough to compete for the model's attention.

- Build long test inputs from a consistent real corpus, and reuse the same corpus across sessions so results compare.
- Always include a control arm running the old prompt. A harness that cannot reproduce the original bug is measuring noise.
- Isolate one variable per run. Pause prompt experiments entirely when the platform itself is misbehaving, because platform variance will be attributed to your change.

## Retrieval tools need many runs and swapped arms

On search-grounded tools (Perplexity Sonar and similar), retrieval variance dwarfs prompt effects. The same prompt on the same input measured a 6x swing in output quality across two 20-minute windows with no change of any kind. Two runs per arm produced confident wrong conclusions twice in one session.

Minimum discipline for an A/B on a retrieval tool:

- 4+ runs per arm.
- Swap the arms across staging bots and run again, so bot identity is not a confound.
- Compare pooled means, and treat small differences as noise.
- Before diagnosing a prompt defect from a bad batch, re-run the unmodified prompt in a fresh window to check the failure reproduces at all.

## Two platform signals that mislead diagnosis

**The workspace fallback can serve a model you did not choose.** Pickaxe has a workspace-wide Fallback Model toggle (Settings, Agent tab) that silently retries a failed primary model on a backup, for every bot in the workspace at once, and it can be on without the builder having chosen it. Nothing surfaces when it fires: no indicator, no API flag, no reason code. A run that silently fell back is an invisible confound in any quality investigation, and the likely wrong conclusion is a prompt defect that is not there. Check the toggle before tuning a prompt, check the per-message insights panel where a transcript exists, and treat "which model actually ran" as unverifiable over the API (observed August 2026).

**A bot's `updatedAt` is not evidence its prompt changed.** Nightly platform processes restamp most bots in a workspace within minutes of one another, so a timestamp that lines up suggestively with the date a user started complaining usually means nothing. Reading one as a prompt change has produced a confident, detailed, and entirely wrong account of a regression, caught only by checking version-controlled exports, which are the only reliable record of when content actually moved (source-of-truth reference).

## Grade against ground truth, not by reading

For tools that analyze a document, build a quote-anchored answer key for a fixed test corpus once, then grade outputs against the key mechanically. Building the key is expensive (a full careful read). Grading against it is cheap and repeatable, and it catches confident wrong answers that a casual read of the output misses.

Verify the grader itself before trusting its failures. Check it against lines known to be present in the source, and normalize curly quotes, escaped punctuation, and whitespace before matching. A buggy grader has reported 29% attribution accuracy when the truth was 96%, a false measurement severe enough to drive a wrong prompt change, and a first version once flagged 12 real quotes as fabricated over escaped punctuation alone.

For tools that quote source text back to the user, grade fidelity by string-matching every returned quote against the source. Models paraphrase roughly 1 in 3 "verbatim" quotes until explicitly forbidden: flipped pronouns, corrected dialect, invented lead-in clauses, spliced lines. Classify each quote (exact, trimmed, elided, altered, invented) rather than pass/fail, because legal trims like a dropped dialogue tag will otherwise mask the real error rate. The highest-value prompt addition found: require a location and speaker attribution after every quote, which makes fabrication visible and lets the user verify a line in seconds.

String-matching proves the text is real, not that the claims attached to it are. A quote can be reproduced perfectly, down to a typo in the original, and still be presented as "the last line of chapter N" when it actually sits in chapter N-1. When a quote carries a structural claim (which chapter, which section, which side of a boundary), verify the claim itself, for example by checking which heading or marker immediately follows the quoted line in the source.

Verify the answer key itself against the source programmatically before first use. In practice the checks catch errors in both directions: the key catches corruption in how the source was prepared, and the source catches misquotes in the key.

When a fidelity rate disappoints, a model swap is the obvious move and it does not pay. Three models from two vendors on an identical prompt and book-length document, four runs each, all landed in the same 86 to 91 percent verbatim band, and the newest was several points worse on both fidelity and attribution. Prompt-side prohibition of each repair class moved the metric far more than any model change. Models did differ on quote volume and failure shape (one corrected written dialect, another leaned to ellipsis splices), and those are real reasons to prefer a model. Fidelity rate is not. Decide which metric would change the decision before running a model comparison, and measure the metrics the change was not aimed at, since a model that wins the target metric can lose two others.

## Anti-hallucination design

Principles distilled from documented failures, all reproducible when found:

- **Self-attested verification fails.** A model confirming its own checklist costs nothing to fake. Require quoted evidence from retrieved or source text instead of yes/no confirmations.
- **Fixed scoring rubrics beat freeform scoring.** A 100-point rubric with explicit per-item weights prevents the model from silently skipping elements. Icon-based or vibe-based scoring invites it.
- **Never mandate a format the data layer cannot support.** Forced citations plus starved retrieval equals invented citations, every time.
- **Verbatim output needs explicit prohibition of every repair class.** Copy character for character, never correct spelling or dialect, never change a pronoun, never splice, never add words, and drop anything you cannot reproduce exactly.
- **Watch for instruction conflicts across prompt fields.** When a selection criterion in one field can be satisfied by violating a fidelity rule in another, the model resolves the conflict silently. State which rule governs.

## What only the UI can test

The completion API cannot attach files. File upload, transcription, and format acceptance can only be tested through the real embed or Studio preview. Keep a tiny known-content test file per format so the check takes seconds.

Match the transport to the claim being tested, because form testing over the API has three levels, not two. A bare `message` string bypasses the form entirely, and that includes the frame's static instruction prose, not just the field values. On the `message` path the model runs on the Role and Model Reminder alone, which can be a small fraction of the production prompt, and setting the bot's `type` to form-chat does not change that, since it is a property of the transport. An `inputs` object keyed by the frame's `userinput:*` field ids drives the real form path, including what the model does with a full document. But even `inputs` text arrives already extracted, so it proves nothing about whether the platform parses a real user's uploaded file. An API reproduction that passes clean text does not clear the file-handling path, so when a user reports garbled or partial content from an upload, state which layer a passing test actually covered.

Two techniques sharpen transport testing. To prove a field reaches the model in one run, plant a canary phrased so obeying it is consistent with the output contract, such as a substitution rule ("the input word X is a mistranscription, always replace it with Y"), and pair it with the same instruction pasted inline as a positive control. And treat a pasted frame as exploration only. In one measured case an A/B over the pasted-message path showed a candidate prompt destroying pre-existing content in 7 of 8 runs against 0 of 8 for the old prompt, while the same comparison over `inputs`, same size and same input, showed no difference at all. An A/B can be internally consistent and still not generalize off its transport, so explore on the cheap path, conclude on the path real traffic takes, and record in any writeup how the frame was delivered.

The no-fetch limitation doubles as an error-path test. Sending a URL as a bare string does not run the platform's fetch, so the call lands on whatever branch the prompt defines for "no usable content arrived," which makes that branch testable on demand even though the natural failure it stands in for cannot be scheduled. Paste representative content directly into the field to test the happy path the same way. Both halves are prompt-level tests only.

One backend capability is testable without the picker. `document_upload` bypasses the embed's file-type whitelist entirely, and its response carries a `rawStorageUrl` pointing at the plain text the platform extracted, including transcription for audio. Fetch that URL and compare it against known content: if the text comes back right, the backend handles the format and only the client widget blocks it, which is a much smaller fix to request from the vendor. The upload travels base64 in the request body, so use the HTTP transport, and omit the Pickaxe id so the test document lands unattached in the workspace library. A test recording that states its own purpose out loud makes the check unambiguous.
