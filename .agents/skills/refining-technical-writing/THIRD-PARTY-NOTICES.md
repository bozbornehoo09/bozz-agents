# Third-party notices

Everything in this skill (its instructions, Vale rules and scripts) was written for bozz-agents;
no text from the projects listed here is copied into it. Vale, Deslop and Humanizer are not
bundled. `scripts/install.sh` fetches them onto the user's machine at the versions pinned below
and checks each download against a recorded sha256. WRITING.md is credited because it shaped the
skill's list of what an edit has to leave intact.

| Project | Role in this skill | Pinned at | Copyright | License |
|---|---|---|---|---|
| [Vale](https://github.com/vale-cli/vale) | Prose linter that `scripts/check_prose.py` invokes | release 3.25.1 | Copyright (c) 2016 Joseph Kato | MIT |
| [Deslop](https://github.com/JMill/deslop) | Vale style pack loaded by the checker | release v0.3.0 | Copyright (c) 2026 JMill | MIT |
| [Humanizer](https://github.com/blader/humanizer) | Catalogue of AI-writing patterns read during the edit pass (its `SKILL.md` and `LICENSE` are downloaded) | commit `b48c832` (2026-11-10) | Copyright (c) 2025 Siqi Chen | MIT |
| [WRITING.md](https://github.com/Anbeeld/WRITING.md) | Idea source for what an edit must keep: defined terms, conditions, hedges, structure | not downloaded | Copyright (c) 2026 Anbeeld | MIT |

## MIT License

The text below covers every project in the table, each under its own copyright line.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES
OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
