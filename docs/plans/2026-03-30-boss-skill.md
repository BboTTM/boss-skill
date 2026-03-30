# Boss Skill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a referenceable boss-simulation skill repo that can create reusable boss personas from archetypes or uploaded materials.

**Architecture:** Use a meta-skill at the repo root to guide creation and management, prompt references for intake and extraction, and a small Python writer to generate boss persona directories with runnable `SKILL.md` files.

**Tech Stack:** Markdown skill files, Python 3 standard library, optional `pypinyin`

---

### Task 1: Scaffold the repo-facing docs

**Files:**
- Create: `README.md`
- Create: `docs/plans/2026-03-30-boss-skill.md`

**Step 1: Write the repo usage doc**

Describe installation, the command model, generated directory layout, and the runtime commands for a generated boss.

**Step 2: Verify the docs read cleanly**

Run: `sed -n '1,220p' README.md`
Expected: clear install and usage sections with `/create-boss`, `/boss-sim`, and `/{slug}` references.

### Task 2: Write the meta-skill

**Files:**
- Create: `SKILL.md`
- Create: `prompts/intake.md`
- Create: `prompts/archetype_catalog.md`
- Create: `prompts/real_person_extractor.md`

**Step 1: Write the root skill**

Define the create flow, the runtime flow, the management commands, and the rules for immersive mode and debrief mode.

**Step 2: Add reference prompts**

Add small prompt/reference files for intake questions, archetype definitions, and real-person extraction dimensions.

**Step 3: Verify the skill body**

Run: `sed -n '1,260p' SKILL.md`
Expected: a usable Chinese-first skill document with both archetype and real-person flows.

### Task 3: Add boss generation tooling

**Files:**
- Create: `tools/skill_writer.py`
- Create: `requirements.txt`

**Step 1: Implement the writer**

Support `create`, `list`, `rollback`, and `delete`. Generate `bosses/{slug}/SKILL.md`, `boss-card.md`, `meta.json`, and version snapshots.

**Step 2: Add optional dependency note**

Add `pypinyin` as an optional dependency for Chinese slug generation.

**Step 3: Smoke-test the CLI**

Run: `python3 tools/skill_writer.py --help`
Expected: argparse help with the management commands.

### Task 4: Verify the repository

**Files:**
- Modify: `README.md`
- Modify: `SKILL.md`
- Modify: `tools/skill_writer.py`

**Step 1: Run the writer help**

Run: `python3 tools/skill_writer.py --help`
Expected: exits successfully.

**Step 2: Create one sample boss**

Run the `create` action with a tiny JSON payload and confirm generated files exist.

**Step 3: Read back the generated skill**

Run: `sed -n '1,220p' bosses/<slug>/SKILL.md`
Expected: a standalone boss runtime skill with immersive and debrief commands.
