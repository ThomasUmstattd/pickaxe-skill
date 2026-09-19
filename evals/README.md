# Skill checks

Run the helper's offline regression tests with the Python standard library:

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
```

These tests use fake credentials and simulated responses. They cover result/error handling, argument validation, credential selection, and paid-attempt behavior. They do not establish current server compatibility.

## Discovery prompts

`trigger-eval.json` contains twenty prompts: ten Pickaxe tasks and ten near-misses involving unrelated packages, Minecraft, other chatbot platforms, or host-site problems.

The v0.3.1 description scored 10/12 training prompts and 7/8 held-out prompts in a September 3 Claude Code harness, with no false triggers. The older description scored 4/8 held-out. Those are historical results, not a measurement of this revision.

That harness counted success only when consulting the skill was the first tool call. Reading a user-named file first is not necessarily a behavioral failure. It also required isolation from an installed copy and loaded enough context to make a large optimization loop expensive.

This revision shortens the loaded instructions and keeps the discovery description's scope, changing its opening from “Required first step” to “Use.” That removes a tool-order mandate and brings the description under the skill validator's 1,024-character limit. One clarified positive now identifies Pickaxe Studio instead of saying only “Studio chatbot.” Neither the revised description nor the edited eval set has a new measured score. Compare a substantially shorter description under the intended client before adopting it or paying for broad trigger optimization.

## Behavioral checks

A useful review should check decisions, not exact wording. Use the revised skill and ordinary task context, without revealing an expected answer to the reviewing agent:

1. Diagnose a partial manuscript upload, with no changes authorized.
2. Plan a form-chat prompt comparison on a private copy with a strict paid-attempt budget.
3. Assess whether a login hook should reassign a user's existing access group.
4. Diagnose an image action that failed while the completion envelope reported success.

Inspect the resulting plan for scope, input-path fidelity, bounded paid work, evidence appropriate to its conclusions, and use of the relevant reference. No live calls are needed for this screen. It complements offline helper checks and does not replace end-to-end tests when a later task needs them.
