---
kind: handoff
project: ichita-skills / ichita-proposal
date: 2026-06-24
author: Lelouch
phase: brainstorming → (next) writing-plans
---

# Handoff — ichita-proposal skill

## What
Designing a new `ichita-proposal` skill for `ichita-skills`: turns one intake into a
narrative proposal draft at a chosen rigor level, then renders via `ichita-docx`/`ichita-pptx`.
Currently at end of brainstorming — design approved in principle, spec written.

## Shipped / In-Flight
- **Shipped:** Design spec → `docs/superpowers/specs/2026-06-24-ichita-proposal-design.md` (committed)
- **Shipped:** Four brainstorming decisions locked (see State below)
- **In-Flight:** 2 open decisions block the move to writing-plans

## Blockers (2 open decisions, need OhYeaH!)
1. **Feasibility default render** — PPTX (presented) vs DOCX (read)?
2. **Intake fields** — confirm set; candidates to add: timeline, competitor context,
   customer budget ceiling.

## Next (concrete)
1. Get answers to the 2 blockers above.
2. Run spec self-review (placeholders / consistency / scope / ambiguity).
3. Invoke `superpowers:writing-plans` to produce the implementation plan.
4. Then build: `intake.yaml` schema → `levels/*.md` → `library/` → `scripts/assemble.py` → render routing.

## Avoid (dead ends / guardrails)
- Do NOT include detailed/firm contract-grade proposals — explicitly out of scope.
- Do NOT let narrative assembly generate numbers — figures come only from intake `source`,
  else `⚠ source needed`. Non-negotiable (Ichita credibility).
- Do NOT bake format into the skill — DOCX/PPTX is an intake choice.
- PDF-brief render path was rejected by OhYeaH! — don't reintroduce it.

## State (decisions locked in brainstorming)
- **Levels:** feasibility, budgetary, technical (front-of-pipeline only)
- **Output:** DOCX + PPTX, via a structure-agnostic blueprint skill
- **Build model:** intake → assembled draft
- **Assembly depth:** narrative assembly (skill drafts prose, OhYeaH! edits)

## Git
- Branch: `docs/ichita-proposal-design` (off `fix/widescreen-canvas-and-master-bg`)
- This commit contains ONLY the 2 design/handoff docs. Unrelated WIP on the parent branch
  (modified docx/pptx scripts, untracked fonts) was deliberately left unstaged.
