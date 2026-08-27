# Testing and verification

## Never iterate on a live tool

There is no dry-run: `run_pickaxe_completion`'s config parameter does not override the prompt, so testing a variant means writing it somewhere real. Keep at least one private staging Pickaxe and iterate there.

A staging workflow that has held up in production:

1. **Check out**: copy the live tool's full field set onto the private staging bot (role, model reminder, model, temperature, reasoning effort, knowledge document attachments). Overwrite everything, so nothing leaks from the previous checkout.
2. **Verify the checkout**: read the staging bot back and compare every copied field against the source. Fields that did not stick fail loudly here instead of corrupting your test results.
3. Iterate on the staging bot with `pickaxe_update` and `run_pickaxe_completion`.
4. **Apply**: write the final prompt to the live tool in one operation, and read it back.
5. **Release**: reset the staging bot to an empty state so the next checkout starts clean.

Give staging bots large input limits (`chatinputlength`, `endusertokens`, `membuffer`) so full-length real inputs fit in a completion message. Remember that own-key actions cannot be copied programmatically (actions reference), so action-dependent tools need a manual key attach before end-to-end staging runs.

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

## Grade against ground truth, not by reading

For tools that analyze a document, build a quote-anchored answer key for a fixed test corpus once, then grade outputs against the key mechanically. Building the key is expensive (a full careful read). Grading against it is cheap and repeatable, and it catches confident wrong answers that a casual read of the output misses.

For tools that quote source text back to the user, grade fidelity by string-matching every returned quote against the source. Models paraphrase roughly 1 in 3 "verbatim" quotes until explicitly forbidden: flipped pronouns, corrected dialect, invented lead-in clauses, spliced lines. Classify each quote (exact, trimmed, elided, altered, invented) rather than pass/fail, because legal trims like a dropped dialogue tag will otherwise mask the real error rate. The highest-value prompt addition found: require a location and speaker attribution after every quote, which makes fabrication visible and lets the user verify a line in seconds.

String-matching proves the text is real, not that the claims attached to it are. A quote can be reproduced perfectly, down to a typo in the original, and still be presented as "the last line of chapter N" when it actually sits in chapter N-1. When a quote carries a structural claim (which chapter, which section, which side of a boundary), verify the claim itself, for example by checking which heading or marker immediately follows the quoted line in the source.

Verify the answer key itself against the source programmatically before first use. In practice the checks catch errors in both directions: the key catches corruption in how the source was prepared, and the source catches misquotes in the key.

## Anti-hallucination design

Principles distilled from documented failures, all reproducible when found:

- **Self-attested verification fails.** A model confirming its own checklist costs nothing to fake. Require quoted evidence from retrieved or source text instead of yes/no confirmations.
- **Fixed scoring rubrics beat freeform scoring.** A 100-point rubric with explicit per-item weights prevents the model from silently skipping elements. Icon-based or vibe-based scoring invites it.
- **Never mandate a format the data layer cannot support.** Forced citations plus starved retrieval equals invented citations, every time.
- **Verbatim output needs explicit prohibition of every repair class.** Copy character for character, never correct spelling or dialect, never change a pronoun, never splice, never add words, and drop anything you cannot reproduce exactly.
- **Watch for instruction conflicts across prompt fields.** When a selection criterion in one field can be satisfied by violating a fidelity rule in another, the model resolves the conflict silently. State which rule governs.

## What only the UI can test

The completion API cannot attach files. File upload, transcription, and format acceptance can only be tested through the real embed or Studio preview. Keep a tiny known-content test file per format so the check takes seconds.
