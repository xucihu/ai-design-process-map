# How designers use AI across the design process

An interactive map of 75 AI use cases across the design process, from research to prototyping, built by Xuci Hu.

**View the map:** https://xucihu.github.io/ai-design-process-map/

## What's here

| File | What it is |
|---|---|
| `index.html` | The interactive map |
| `data/versions.json` | Every published release, newest first. The map shows the newest one. |
| `data/releases/2026-oct/` | The 2026 Oct release: the full spreadsheet (`.xlsx`), use cases and resources as CSV, and `use-cases.json`, which the map reads |
| `data/tool-categories.json` | How tools are grouped in the Tool filter |
| `scripts/build_release.py` | Turns the project spreadsheet into a release |

## How updates work

The data is edited in a private Google Sheet. When a new version is ready, it is reviewed, saved as a release in `data/releases/`, and added to `data/versions.json`. Earlier releases stay in the repository unchanged, so every version of the map can be traced.

## How the map works

- **Framework:** Vijay Kumar's 2×2 design process (2009, 2012), building on Charles Owen's work at the IIT Institute of Design. Four phases (research, analysis, synthesis, prototype) are broken into 20 steps adapted from my own practice.
- **Acceptability:** how credible sources judge each use of AI: endorsed, conditional, contested or rejected.
- **Popularity:** how widely practitioners use it. Thresholds follow Rogers' Diffusion of Innovations: over 50% of surveyed practitioners is high, 16 to 50% is medium. Without survey data, the level depends on how many mainstream tools offer the feature and how many independent practitioner reports exist.
- **Sources:** gathered with Claude Research from published papers, expert reports, practitioner writing and tool documentation.

See the Notes tab in the spreadsheet (`data/releases/2026-oct/`) for the full method.

## Status

Version 2026 Oct. Some entries are marked as still being checked and will be re-verified in the next update. I plan to update the map regularly.

This started as a personal list of AI use cases to try, not a comprehensive market study. If you spot something off or see a better way to do this, please open an issue or reach out.

## Coming soon

The toolkit behind this project: research plan, research prompts, spreadsheet template and evaluation forms, so you can build a live map of your own AI use.
