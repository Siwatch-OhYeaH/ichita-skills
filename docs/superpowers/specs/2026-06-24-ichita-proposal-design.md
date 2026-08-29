# ichita-proposal — Design Spec

**Date:** 2026-06-24
**Author:** Lelouch (Strategist Oracle)
**Status:** Design approved in principle — 2 open decisions pending (see end)
**Repo:** ichita-skills

---

## Problem

The `ichita-skills` toolkit is **format-oriented**: `ichita-docx` (words→branded DOCX),
`ichita-exe-brief` (HTML→print PDF), `ichita-pptx` (decks), `ichita-template` (restyle).
None of them know what a *proposal* is — its sections, its rigor level, or what changes
between a quick budget number and a credibility-winning technical document.

A proposal is not a format. It is a **document type with a defined structure and a rigor
level**. That structure + rigor is the missing layer.

## Scope

Front-of-pipeline proposals only — the "win the work / get shortlisted" zone:

| Level | Purpose | Price rigor | Default render |
|-------|---------|-------------|----------------|
| **Feasibility** | Frame the problem, compare options, go/no-go | none / lab basis | PPTX or DOCX *(open Q1)* |
| **Budgetary** | Get a number into the customer's budget | indicative ±25–40%, sourced | DOCX |
| **Technical** | Win on scope & process credibility | indicative or none | DOCX (or PPTX pitch) |

**Out of scope:** detailed/firm contract-grade proposals (BOQ + T&C + commercial terms).
That is a legal/execution artifact, handled separately.

## Architecture

A new skill `skills/ichita-proposal/` that is **structure-agnostic**: it owns the proposal
blueprint and routes to existing renderers. Build model is **intake → assembled draft**
with **narrative assembly** (the skill drafts real prose, not just a skeleton).

```
intake.yaml ──► assemble.py --level technical --format docx ──► draft.md ──► proposal.docx
                     ▲              ▲                                            (via ichita-docx)
                levels/*.md     library/                          or ──► proposal.pptx
                                                                            (via ichita-pptx)
```

### Five components, each one job

1. **`intake.yaml`** — single source of truth for one proposal. Captures:
   - Customer profile: sector, decision-makers, **3-layer need** (stated / operational / political)
   - Problem statement
   - Proposed solution / scope
   - References to include (which past projects)
   - **Numbers as `{value, unit, basis, source}`** — never bare figures
   - `level` (feasibility | budgetary | technical) + `format` (docx | pptx)

2. **`levels/*.md`** — declarative spec per level: which sections appear, in what order,
   the rigor bar, and the "so-what?" prompt for each section. **Data, not code** — tune a
   level without touching the engine.

3. **`library/`** — Ichita boilerplate reused across every proposal: company intro,
   capability statements, reference projects, process-partner positioning lines, standard
   assumptions/exclusions. **Versioned** (Nothing is Deleted).

4. **`scripts/assemble.py`** — reads intake + level spec + library → emits intermediate
   **`draft.md`**. Applies the proposal logic:
   - Page 1 is about **THEM**, never about us
   - Every spec answers "so what?" (impact, not feature)
   - Process-partner framing ("we solve your process, not just sell equipment")

5. **Render routing** — `draft.md` → `ichita-docx` (`md_to_docx.py`) for DOCX, or →
   `ichita-pptx` slide lib for PPTX. (The python-pptx lib already advertises a
   "proposal generator" hook to build on.)

## The non-negotiable: numbers are never drafted

Narrative assembly applies to **qualitative framing only**. Numbers are copied verbatim
from `intake.yaml` with their `source`. Any number that would appear without a `source` is
emitted as `⚠ source needed` — never invented. This is what lets "the skill writes the
prose" coexist with Ichita's engineering credibility: the strategist drafts the *argument*,
never the *figures*.

## Why this shape

- **Structure-agnostic** — DOCX or PPTX is a choice in the intake, not baked into the skill.
- **Levels are config** — `levels/*.md` is editable without code; rigor ladder is visible.
- **Strategy lives in the engine** — the intake→draft step is where proposal logic is
  encoded, instead of being re-typed every proposal.
- **Reuse without duplication** — `library/` is the shared, versioned boilerplate; all three
  levels draw from it.

## Open decisions (pending OhYeaH!)

1. **Feasibility default render** — PPTX (presented) or DOCX (read document)? Defaulted to
   "PPTX-or-DOCX" pending confirmation of how feasibility studies are actually delivered.
2. **Intake completeness** — confirm fields. Candidates not yet included: project timeline,
   competitor context, customer's hinted budget ceiling. Decide which belong in `intake.yaml`.

## Next steps

1. Resolve the 2 open decisions.
2. Spec self-review (placeholder / consistency / scope / ambiguity).
3. Invoke `superpowers:writing-plans` → implementation plan.
