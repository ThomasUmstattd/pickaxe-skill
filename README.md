# pickaxe-skill

```
                  .......                                                 
                   .:-=----::.......                                       
                   .:++++++++++==-:....                                    
                   .:++++++++++++++++-:....                                
                   .:+++++++++++++++++++=:... .....                        
                   ..:::--=++++++++++++++++=:..-+=...                      
                           ....:-++++++++++++++++++=.                      
                                 ..:-++++++++++++++++-.                    
                                     .:-++++++++++++-..                    
                                       ..-+++++++++=.                      
                               ............-++++++++=:.                    
                              ......::.......=++++++++:..                  
                           .......:====:......:++++++++-.                  
                          .......-=======:..  .:=+++++++:..                
                          .....-=========:..    .=++++++=:.                
                      .......-=========:....    .:=++++++=:                
                      .....-=========-......    ..:+++++++-..              
                  .......:=========-........      .-++++++=:.              
                  .....:-========-:.....          .:=++++++-.              
              .......:-========-:.......          ..-++++++=.              
              ......-========-:......             ..:++++++=:              
          ........-=========:........               :=++++++:              
          ......:=========-......                   :=++++++:              
          ....:=========-........                   .........              
          ...-========-:........                                           
          ....:=====-:.......                                              
          ......-=-:........                                               
          ...............                                                  
              ..........                                                   
                                                                           
```

Teach your AI assistant to build Pickaxe tools like it has been doing it for months.

## What is a skill?

A skill is a folder of instructions that AI coding assistants read on their own. Claude Code, Codex, Cursor, Grok Build, and Grok Bot all use the same format. You install it once with a single command, and from then on your assistant consults it whenever your conversation touches Pickaxe. There is no code to run and nothing to configure.

If you have never installed a skill before, this is a good first one. The install is one copy-paste, and the payoff shows up in your very next conversation.

## Why you want it

Your assistant already knows what [Pickaxe](https://pickaxe.co) is. Here is what it does not know:

- **Every prompt write hits your live bot.** Pickaxe has no draft mode, so an assistant "iterating" on your prompt is editing what your users see, right now.
- **The platform can report success on a write that did nothing.** Some fields accept your change, return success, and silently discard it. Some tools crash naive scripts on calls that actually succeeded, so an assistant can "fix" 80 things that were never broken.
- **Input caps truncate silently.** A form field cap can feed your bot one page of a 300-page manuscript, and the bot analyzes that page in perfect confidence. Your user is told the analysis covered the book.
- **Adding a document does not attach it.** A file can sit in your workspace, fully processed, and stay invisible to the bot it was uploaded for.
- **Long runs die at exactly 300 seconds** with an error that reads like an outage. Retrying will never help, and an assistant that does not know the ceiling will retry all night.

Without the skill, your assistant discovers each of these the hard way, on your live tools, while your customers are using them. With it, your assistant arrives already knowing the traps, verifies every change by reading it back, and tests on a staging copy before touching anything live.

Everything in the skill comes from months of production work on a workspace of 80+ live Pickaxe tools. Every claim was observed on the real platform and carries the date it was observed.

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
- [Prompts and form fields](references/prompt-and-form-fields.md): the three prompt fields, the silent input caps, and a dozen measured prompt-writing lessons
- [Knowledge bases](references/knowledge-base.md): why your bot ignores documents you added, and how retrieval starves
- [Actions](references/actions.md): the four-action limit, API keys that cannot be copied, and the manifest edit that silently resets your triggers
- [Limits and costs](references/limits-and-costs.md): the 300-second ceiling, credit caps, and the architecture choices that cut per-run cost
- [Testing that catches real failures](references/testing-and-verification.md): staging copies, defining what a good answer looks like so your assistant can judge results, and anti-hallucination design
- [Config as code](references/source-of-truth.md): back up every bot to git, because Pickaxe keeps no history and has no undo

The skill also ships a small [Python client](scripts/pickaxe_client.py) your assistant uses for API calls that the standard connection cannot handle.

## Status

This is an independent community project, not affiliated with or endorsed by Pickaxe. The platform evolves, so when something here contradicts current platform behavior, trust the platform and [open an issue](https://github.com/ThomasUmstattd/pickaxe-skill/issues). Releases are tagged, so you can pin a version or just `git pull` for the latest.

Built by [Thomas Umstattd Jr.](https://www.authormedia.com) while building the Patron Toolbox, a suite of AI tools for authors.

## License

[MIT](LICENSE)
