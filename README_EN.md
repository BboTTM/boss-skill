# Boss.skill

Turn a "hard-pressure boss" into a reusable AI Skill.

This repo supports two creation paths:

- `archetype`
  Build a boss from patterns like high-pressure, PUA-style, result-driven, controlling, or emotionally volatile.
- `real-person`
  Reconstruct a more realistic boss from chats, docs, screenshots, and your own notes.

Once created, you can invoke the generated boss directly with `/{slug}`.
The persona can keep evolving through:

- new material imports
- live corrections
- version rollback

## Core Commands

- `/create-boss`
- `/update-boss {slug}`
- `/{slug}`
- `/boss-rollback {slug} {version}`

## Local Verification

```bash
python3 -m unittest discover -s tests -v
```

---

MIT License © [bobbobttm-droid](https://github.com/bobbobttm-droid)

This skill references the meta-skill structure and README organization style from
[titanwings/colleague-skill](https://github.com/titanwings/colleague-skill).

## Structure

```text
create-boss/
├── SKILL.md
├── prompts/
├── tools/
├── tests/
├── bosses/
└── agents/openai.yaml
```
