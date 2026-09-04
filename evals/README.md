# Trigger evals

`trigger-eval.json` holds twenty realistic prompts, ten that should make an assistant consult this skill and ten near-misses that should not (the npm package called pickaxe, Minecraft, other chatbot platforms, generic MCP setup, WordPress and Cloudflare problems with no Pickaxe in them).

They exist so the `description` in `SKILL.md` can be measured rather than guessed. The skill-creator skill's `run_loop.py` runs each prompt through `claude -p` several times and records whether the skill was the first thing the assistant reached for. Measured September 3, 2026 on the v0.3.1 description: 10 of 12 training prompts and 7 of 8 held-out prompts correct, with zero false triggers on the near-misses. The v0.3.0 description scored 4 of 8 on the same held-out set.

Two caveats before trusting a number from this harness. It counts a trigger only when the skill is the very first tool call, so a prompt that names a local file can fail because the assistant reads the file first. And every call loads the assistant's full context, so a five-iteration run is expensive. Isolate the run from an installed copy of the skill with `--setting-sources project`, or the installed copy will absorb the triggers.
