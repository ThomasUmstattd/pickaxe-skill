# Grading and fixtures

Choose the evidence needed for the decision. Reuse an existing rubric and the user's stated preferences before asking for more criteria.

In this file:

- Define success and scope
- Build meaningful fixtures
- Compare runs
- Check evidence and graders

## Define success and scope

For a new judgment task, identify a representative input, useful output, hard requirements, failure severity, and known traps. Ask only for missing choices that would change the test or verdict. Two example outputs can help clarify an unstated preference.

Use a checklist or weighted rubric appropriate to the decision. A fixed 100-point scale is optional. Require the grader to cite output/source evidence for substantive scores, and save the inputs and criteria for reuse.

Write the standard before judging quality. Visual craft, commercial performance, and fidelity to a reference can favor different artifacts. Do not silently choose a different standard or change the product's audience framing while grading it.

Separate these questions:

- Does the output represent the supplied material accurately?
- Is the supplied material's claim supported by external evidence?
- Does the output meet the user's formatting or product requirements?

A book citing a paper does not establish that the paper supports its claim. A summary may describe the author's argument, while a fact checker should flag unsupported claims. Label those expectations in the key so a correct fact checker is not penalized for disagreeing with the manuscript.

Use the actual input scope. A merger cannot repair evidence absent from all supplied summaries, and a three-book test cannot require facts available only in a later volume. Do not grade a tool against an output contract that has not shipped.

## Build meaningful fixtures

Test at realistic length when length affects the defect. Short samples have passed models that dropped content on full chapters. Keep a stable corpus, verified conversion, and permission appropriate to the testing/retention environment.

Include the old prompt or incumbent as a control for a change claim. A reproduction that cannot show the reported defect is weak evidence for a fix. For input-improving tools, include both flawed input and already-good input, so unnecessary rewriting is visible.

Useful cases include:

- A source-mentioned decoy that must not be reported as a real entity.
- Distinctive late-document content to test receipt beyond an old truncation point.
- An input heading resembling a required output header.
- Optional inputs left blank and populated.
- A later revelation that changes an earlier entry even though the entity never reappears.
- Two upload orders where the task accepts multiple files.
- Both first-turn and revision behavior for persistent instructions.

Choose cases relevant to the tool. Do not build every fixture for every edit.

A decoy failure does not prove truncation, and a late quote does not prove every intervening page arrived. Verify the narrower claim supported by each result.

For format comparisons, use equivalent content in different containers and inspect extracted/rendered content where possible. A single differing model verdict is not proof of a format-handling defect.

Keep canonical answers separate from live configuration. Name the field and date the check, but do not copy its prompt wrapper or cap into fixture instructions. Read current labels, caps, and required flags before a graded run. A weak input should remain consistent with the source unless the intended defect is factual and the tool has enough evidence to detect it.

Preserve meaningful source formatting. A conversion that removes strikethrough can turn a joke into two adjacent verbs. Check suspect text against the original and represent formatting in a form the tool can read. Full answer-key preparation can double as a conversion audit.

## Compare runs

Start with the smallest screen that can change the decision. Specify attempt, time, and spend limits before paid comparisons. If results are mixed or incomplete, keep the conclusion inconclusive rather than expanding the test automatically.

For a claim about improvement, use matched inputs and comparable configurations, isolate the changed variable, and record requested/served models. Randomize order where practical. With multiple staging bots, swap arms or otherwise check bot effects. With one bot, sequential randomized arms can avoid a slot confound.

Search-backed output has shown large run-to-run variation. Four or more runs per arm and slot swaps were useful in past campaigns, but that is neither a universal minimum nor statistical proof. Report sample sizes, paired differences where available, failures, and uncertainty. Pool additional observations instead of retaining an early favorable percentage.

Record costs for failed/fallback attempts as well as returned answers. Unknown cost is not zero. A quality verdict on a recovered answer does not change the fact that its request missed an operational deadline.

Save expensive reference answers with input/config provenance for reuse. They are examples to assess, not ground truth just because a premium model produced them.

After a cap change, re-measure content-dependent rules. A model that never saw a late reveal could not leak it. Increasing coverage can expose that compliance problem without showing that the cap fix was wrong.

## Check evidence and graders

Build a source-anchored answer key for recurring analysis tasks, then audit the key before the first scored run. Verify both copied quotations and inferred conclusions. Exact source text can still be used to support an inference that does not follow.

For quote tools, classify exact, trimmed, elided, altered, and invented text. Verify speaker, chapter, and structural claims separately from string matching. Attribute a quotation to the boundary or chapter in the source, not the location a plausible narrative suggests.

A verifier must check every intended quote. A minimum-length regex once skipped short quotes and mispaired later marks, leaving many real quotes untested. Track candidate counts and unmatched/ambiguous spans. Pairing marks within each line worked for one controlled key format, but prose with nested or multi-line quotations needs a suitable parser.

Choose normalization for the metric. Whitespace or quote-glyph normalization may fit source lookup. It must not erase spelling, punctuation, or dialect differences when those are what the tool promises to preserve. Explicitly account for accepted elisions.

Check known-present and known-absent examples before trusting the grader. Hand-check suspicious zeros and perfect scores. A strict phrase match once missed a reveal with an intervening adjective, while a mention-anywhere check missed contradictions in other entries.

For a merge or cumulative report, score supplied-entry survival separately from propagation of later evidence. A document can state the reveal once and contradict it in several dossiers. Check every affected supplied entry without penalizing the merger for the upstream extractor's missing material.

Avoid conclusions broader than the test. A comparison where several models tied on quote fidelity does not establish that model choice never matters. Retrieval changing across two runs does not establish fabrication. Prefer source evidence and a measured control before changing a prompt.
