# Actions

Actions are the tool calls a Pickaxe can make: web search, image generation, custom API calls. They have their own quirks, and one of the platform's nastier silent failures lives here.

## Structural facts

- **Four actions per Pickaxe, maximum.** A workflow that needs more gets split into a waterfall of routed Pickaxes, each within the limit.
- **Trigger conditions live in two places, and both matter.** Describe when and why to fire the action in the Role field, and also fill the action's own trigger prompt field in the Actions tab. Either one alone under-triggers.

## Replacing a manifest silently resets the trigger prompt

`action_update_manifest` replaces the action definition, and doing so resets the attachment-level trigger prompt on connected Pickaxes back to a generic default. The attachment trigger lives outside the manifest, so the replace does not know it is destroying customization. After any manifest replace, re-check and restore the trigger prompt on every Pickaxe that uses the action. Observed August 2026.

## Credit-backed vs own-key actions

Every action attachment is one of two kinds, and the `isUsingPickaxeCredits` flag tells them apart:

- **Credit-backed** (`isUsingPickaxeCredits: true`): Pickaxe injects its own managed provider key and bills through platform credits. These can be copied between Pickaxes programmatically, but the flag must be set on `action_connect`. Connecting without it fails with `Variable OpenAI API Key is required` or similar.
- **Own-key**: the attachment holds your provider API key. The API returns stored keys **masked**, so an own-key attachment cannot be copied to another Pickaxe programmatically. `action_connect` without the key value fails with `Variable <NAME> is required`, and the value is unrecoverable over the API. Reattaching is a manual step in the Studio UI.

This matters most for staging copies: a cloned bot starts with no working own-key actions, so action-dependent tools cannot be benchmarked end to end without a manual key attach first. A keyless run is still useful for isolating what the knowledge base contributes and for exercising the no-search failure path.

A third kind exists and is easy to overlook: some built-in platform actions attach with no key at all (a built-in web search, a current-time action). When staging a search-dependent tool, check for a keyless equivalent before waiting on a key handoff. One caveat: benchmarks run on one search backend do not validate another, so either test on the backend the live tool uses or switch the live tool to the backend you tested.

## Deactivate, do not detach

The Studio UI can toggle an attached action off without removing it, which preserves the stored key. Use the toggle for single-backend experiments on a tool with multiple keyed actions. Detach and reattach loses the key, and muting via the trigger prompt only steers the model rather than gating the action. The toggle appears to be UI-only.

## Building new actions

Pickaxe ships an action builder called Wingman (https://pickaxe.co/learn/wingman) that creates an action from a single prompt. For a new custom action, write a complete Wingman prompt describing the action's name, endpoint, parameters, auth variable, and response handling, then paste it into Wingman and add the API key in the Studio UI. This beats hand-building manifests over the API, and it keeps provider keys out of chat logs and terminals.

## Budget the latency

Actions bill and stall in ways that break tools (see the limits reference for the hard timeout):

- Measure your per-call latency before designing multi-call workflows. A search action averaging 30 seconds per call cannot fit 8 to 12 calls under a 300-second ceiling.
- Built-in platform actions that use Pickaxe's own keys are not free. Token costs bill through at cost.
