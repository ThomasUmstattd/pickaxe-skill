# pickaxe-skill

```
 _____ _     _                  _____ _   _ _ _ 
|  _  |_|___| |_ ___ _ _ ___   |   __| |_|_| | |
|   __| |  _| '_| .'|_'_| -_|  |__   | '_| | | |
|__|  |_|___|_,_|__,|_,_|___|  |_____|_,_|_|_|_|
                                                                          
```

Teach your AI assistant to build Pickaxe tools like it has been doing it for months.

## What is a skill?

A skill is a folder of instructions that an AI coding assistant can consult when working on Pickaxe. This one includes reference notes and an optional Python helper. Install the skill, then connect your assistant to the intended workspace.

The instructions cover platform behavior that a general-purpose assistant may not know. The helper needs only Python's standard library.

## Why you want it

Your assistant already knows what [Pickaxe](https://pickaxe.co) is. Here is what it does not know:

- **A prompt write changes the targeted bot.** An assistant testing a variant on a public bot changes what its users receive. Use a private staging copy for those experiments.
- **The platform can report success on a write that did nothing.** Some fields accept your change, return success, and silently discard it. Some tools crash naive scripts on calls that actually succeeded, so an assistant can "fix" 80 things that were never broken.
- **Input caps can truncate silently.** Check configuration and actual source coverage before blaming the model for a partial read.
- **Adding a document does not attach it.** A file can sit in your workspace, fully processed, and stay invisible to the bot it was uploaded for.
- **A timeout can leave a completed, charged answer.** Recover history and measured telemetry before retrying. The tested workspace completion path also had a 300-second server ceiling.

The guide explains staging, readback, real-upload tests, and the difference between a successful request and a useful result. It also covers membership changes that can reset credits, measured costs, and grading against source evidence.

The platform observations come from production work in August and September 2026. The guide distinguishes those observations from test techniques, unresolved behavior, and newer official documentation. Check the relevant path when the platform changes.

## Install

Open your assistant's terminal and run the command for the assistant you use:

**Claude Code**

```bash
git clone https://github.com/ThomasUmstattd/pickaxe-skill ~/.claude/skills/pickaxe
```

**Codex**

```bash
git clone https://github.com/ThomasUmstattd/pickaxe-skill ~/.agents/skills/pickaxe
```

**Cursor**

```bash
git clone https://github.com/ThomasUmstattd/pickaxe-skill ~/.cursor/skills/pickaxe
```

**Grok Build**

```bash
git clone https://github.com/ThomasUmstattd/pickaxe-skill ~/.grok/skills/pickaxe
```

**Grok Bot** installs through the app instead. Open **Settings → Plugins**, and under **Yours** point it at this repo's URL. Reference it by typing `/` in the composer.

Then start a new conversation and say: **"Connect me to my Pickaxe workspace."** The skill walks your assistant through the whole setup, including where your API key hides in Pickaxe's settings, a page most people never find on their own.

## What your assistant learns

- [Getting connected](references/getting-connected.md), including first-time setup for every supported assistant
- [How the API really behaves](references/api-mechanics.md): the fields behind the builder UI, the writes that lie, and the habit of verifying every change by reading it back
- [Prompts and form fields](references/prompt-and-form-fields.md): the three prompt fields, the silent input caps that make bots invent content, and more than a dozen measured prompt-writing lessons
- [Knowledge bases](references/knowledge-base.md): why your bot ignores documents you added, and how retrieval starves
- [Actions](references/actions.md): the four-action limit, API keys that cannot be copied, and the manifest edit that silently resets your triggers
- [Limits and costs](references/limits-and-costs.md): the 300-second ceiling, credit caps, and the architecture choices that cut per-run cost
- [Testing that catches real failures](references/testing-and-verification.md): staging copies, verifying every write, and the platform signals that send a diagnosis the wrong way
- [Grading and fixtures](references/grading-and-fixtures.md): defining what a good answer looks like so your assistant can judge results, building test inputs that can fail, and anti-hallucination design
- [Config as code](references/source-of-truth.md): back up every bot to git, because Pickaxe keeps no history and has no undo

The skill also ships a small [Python client](scripts/pickaxe_client.py) your assistant uses for API calls that the standard connection cannot handle.

## Status

This is an independent community project, not affiliated with or endorsed by Pickaxe. The platform evolves, so when something here contradicts current platform behavior, trust the platform and [open an issue](https://github.com/ThomasUmstattd/pickaxe-skill/issues). Releases are tagged, so you can pin a version or just `git pull` for the latest.

Built by [Thomas Umstattd Jr.](https://www.authormedia.com) while building the Patron Toolbox, a suite of AI tools for authors.

## License

[MIT](LICENSE)
