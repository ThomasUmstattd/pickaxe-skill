# Grading and fixtures

How to decide whether an output is good, in a way that survives more than one run and more than one session. The mechanics of running a test safely, and of proving that what you tested is what shipped, are in `testing-and-verification.md`.

In this file:

- Define what a good answer looks like before you test
- Build fixtures that can fail
- Many runs, swapped arms, pooled means
- Grade against ground truth, not by reading
- Validate the measurement before acting on it
- Re-measure after a cap fix
- Anti-hallucination design

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

**A quality-judgment tool needs its standard written above its first verdict.** An answer key for a tool that grades verbatim quotes needs no stated standard, because the standard is string equality. An answer key for a tool that judges quality does, because two defensible standards produce opposite keys for the same artifacts. Building a fixture set for a tool that scores designs, the first key graded craft: composition, typography, execution. The domain expert's standard was commercial performance instead, on the argument that an artifact can be beautiful, skillfully made, admired by everyone the creator knows, and still fail completely at the job it exists to do. Rescoring the identical files against that standard moved roughly two thirds of them into "not doing its job" and inverted individual verdicts in both directions. The most accomplished piece became the flagship failure, because craft was never the question. Three consequences: write the standard at the top of the key with a link to its source, because a future reader of the verdicts alone will re-derive the intuitive standard, which is usually the aesthetic one. Expect a model asked to assess an artifact to drift toward craft, since it is the axis most visible in the artifact itself, and if the tool's own rubric mixes craft and performance criteria without saying which governs, raise that as a prompt defect rather than resolving it silently while grading. And treat "generic" and "conventional" as possible virtues, because penalizing an artifact for resembling others in its category applies an originality standard to a recognition problem.

## Build fixtures that can fail

**Test at realistic length.** Short samples pass configurations that fail on real work. In one documented case, every reasoning level of a model scored clean on a 60-word sample, and the chosen level then dropped an entire author note on a 2,400-word input. Length-dependent failures (dropped content, truncation, instruction drift) only appear when the input is long enough to compete for the model's attention. Build long test inputs from a consistent real corpus, and reuse the same corpus across sessions so results compare.

**Always include a control arm running the old prompt.** A harness that cannot reproduce the original bug is measuring noise. Isolate one variable per run, and pause prompt experiments entirely when the platform itself is misbehaving, because platform variance will be attributed to your change.

**A tool that improves user input needs a bad input and a good control.** When a tool's job is to fix something the user supplies (optimize this listing, tighten this draft), a good input tests nothing, because there is nothing to find. The fixture has to be a deliberately bad input, written the way a real user writes one, paired with an enumerated key of the defects a competent tool should catch, and graded against the key rather than against an impression. Build more than one bad input, each broken in a different way, because one bad example only tests one kind of badness: three drafts for one tool were one that over-shared and buried the point, one that was generic and named nothing concrete, and one that was defensive and argued with the reader, and a tool can be good at cutting and bad at adding specificity. Then pair the bad inputs with a strong-input control using copy that is already good. A useful tool improves a weak input substantially and leaves a strong one largely alone. A tool that rewrites both by the same amount is regenerating, not improving, and that is invisible without the control.

**Plant a decoy the text mentions but does not contain.** A document that jokes about an entity as if it were real, or names a thing that never appears, gives a direct read on whether the full document reached the model: under a truncating input cap the model fills the gap and reports the decoy as real, and with the full text in context it does not (prompt fields reference). A decoy that appears only under truncation is the cheapest available test of the input path.

**Include the same input twice in two file formats.** For tools that judge images or parse documents, identical content, identical dimensions, different container. Any difference in the verdict between them is a format-handling artifact, because there is no substantive difference to find. It isolates the platform's file handling from the model's judgment at the cost of one extra file.

**Include an inverse trap, not just a positive one.** A set that only contains "looks good but fails" cases teaches a grader to be harsh. Pair it with a case that succeeds for a reason that does not generalize, so the tool is also caught recommending an unrepeatable success as a model to copy.

## Many runs, swapped arms, pooled means

On search-grounded tools (Perplexity Sonar and similar), retrieval variance dwarfs prompt effects. The same prompt on the same input measured a 6x swing in output quality across two 20-minute windows with no change of any kind. Two runs per arm produced confident wrong conclusions twice in one session.

Minimum discipline for an A/B on a retrieval tool:

- 4+ runs per arm.
- Swap the arms across staging bots and run again, so bot identity is not a confound.
- Compare pooled means, and treat small differences as noise.
- Before diagnosing a prompt defect from a bad batch, re-run the unmodified prompt in a fresh window to check the failure reproduces at all.

The discipline is not only for search-grounded tools. A prompt arm on a plain document tool at temperature 0.8, with no retrieval anywhere in it, measured 100 percent compliance over seven runs. Adding further control arms later in the same session brought the pooled figure to 79 percent over twenty-four observations, with nothing changed except the number of observations. Report the arm size next to any percentage, treat a 100 percent from a single pair of arms as provisional, and recount pooled when new arms arrive rather than leaving the first flattering number in the record.

Two related cautions on staging. A result replicated across two staging bots can still fail to reproduce on the live tool with identical prompt fields, and a workspace fallback can silently serve a different model or reasoning effort in one arm. Both are in the testing reference.

## Grade against ground truth, not by reading

For tools that analyze a document, build a quote-anchored answer key for a fixed test corpus once, then grade outputs against the key mechanically. Building the key is expensive (a full careful read). Grading against it is cheap and repeatable, and it catches confident wrong answers that a casual read of the output misses.

Verify the grader itself before trusting its failures. Check it against lines known to be present in the source, and normalize curly quotes, escaped punctuation, and whitespace before matching. A buggy grader has reported 29% attribution accuracy when the truth was 96%, a false measurement severe enough to drive a wrong prompt change, and a first version once flagged 12 real quotes as fabricated over escaped punctuation alone.

For tools that quote source text back to the user, grade fidelity by string-matching every returned quote against the source. Models paraphrase roughly 1 in 3 "verbatim" quotes until explicitly forbidden: flipped pronouns, corrected dialect, invented lead-in clauses, spliced lines. Classify each quote (exact, trimmed, elided, altered, invented) rather than pass/fail, because legal trims like a dropped dialogue tag will otherwise mask the real error rate. The highest-value prompt addition found: require a location and speaker attribution after every quote, which makes fabrication visible and lets the user verify a line in seconds.

String-matching proves the text is real, not that the claims attached to it are. A quote can be reproduced perfectly, down to a typo in the original, and still be presented as "the last line of chapter N" when it actually sits in chapter N-1. When a quote carries a structural claim (which chapter, which section, which side of a boundary), verify the claim itself, for example by checking which heading or marker immediately follows the quoted line in the source.

Verify the answer key itself against the source programmatically before first use. In practice the checks catch errors in both directions: the key catches corruption in how the source was prepared, and the source catches misquotes in the key.

When a fidelity rate disappoints, a model swap is the obvious move and it does not pay. Three models from two vendors on an identical prompt and book-length document, four runs each, all landed in the same 86 to 91 percent verbatim band, and the newest was several points worse on both fidelity and attribution. Prompt-side prohibition of each repair class moved the metric far more than any model change. Models did differ on quote volume and failure shape (one corrected written dialect, another leaned to ellipsis splices), and those are real reasons to prefer a model. Fidelity rate is not. Decide which metric would change the decision before running a model comparison, and measure the metrics the change was not aimed at, since a model that wins the target metric can lose two others.

## Validate the measurement before acting on it

A grader's zero is a claim about the grader until you read the source. An automated check reported that a tool never mentioned a document's central reveal, and that finding drove the whole diagnosis. It was false. The pattern searched for a literal two-word phrase against a text that used the same words with an adjective between them. One spot check of the zero found the hit immediately, and the real defect turned out to be narrower and different: the tool stated the reveal in one section and contradicted it in another, so the correct metric was whether the reveal propagated to every section it affected, not whether the output mentioned it anywhere. A mention-anywhere metric passes a document that is internally inconsistent. Hand-verify a zero, and hand-verify a 100, before either one changes a prompt.

## Re-measure after a cap fix

An upload cap that silently truncates a long document is not only losing content. It is also suppressing every instruction-following failure that depends on content the model never received. Raise the cap and those failures appear immediately, which reads as a regression and is not one. Measured on a tool that summarizes an uploaded book under an explicit "never reveal endings or twists" rule in both the system prompt and the per-message reminder: under the old cap it received roughly the first third of the document, so it could not reveal a late twist at any rate, and after the cap was raised to match the token budget the first two runs both put the late-book reveal into user-facing copy, three and four times each.

Two habits follow. Re-run every content-dependent compliance measurement after a cap change, because any rate measured under truncation is a floor rather than an estimate. And when a compliance rule looks like it is holding, check whether the model was ever shown the material the rule governs before crediting the prompt. To prove a raised cap is reaching the model rather than trusting the numbers, grade the output for a specific entity that appears only past the old cut point, which converts an inference about token math into an observation.

## Anti-hallucination design

Principles distilled from documented failures, all reproducible when found:

- **Self-attested verification fails.** A model confirming its own checklist costs nothing to fake. Require quoted evidence from retrieved or source text instead of yes/no confirmations.
- **Fixed scoring rubrics beat freeform scoring.** A 100-point rubric with explicit per-item weights prevents the model from silently skipping elements. Icon-based or vibe-based scoring invites it.
- **Never mandate a format the data layer cannot support.** Forced citations plus starved retrieval equals invented citations, every time.
- **Verbatim output needs explicit prohibition of every repair class.** Copy character for character, never correct spelling or dialect, never change a pronoun, never splice, never add words, and drop anything you cannot reproduce exactly.
- **Watch for instruction conflicts across prompt fields.** When a selection criterion in one field can be satisfied by violating a fidelity rule in another, the model resolves the conflict silently. State which rule governs.
