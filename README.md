# ichita-skills

Private Claude Code plugin for **ICHITA Technology** — brand extension layer for document creation.

## Architecture: Two-Layer Model

```
Layer 1: document-skills@anthropic-agent-skills (AUTO-UPDATE)
  docx    -> General DOCX creation, editing, tracked changes, OOXML
  pptx    -> General PPTX creation, editing, PptxGenJS
  pdf     -> All PDF processing
  xlsx    -> Excel processing

Layer 2: ichita-skills@ichita (THIS PLUGIN)
  ichita-docx  -> Brand DOCX: md_to_docx, rebrand_docx, brand config
  ichita-pptx  -> Brand PPTX: process diagrams, html2pptx, layout patterns
  assets/      -> Brand guidelines, fonts, logos
```

## Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **ichita-docx** | `/ichita-skills:ichita-docx` | Create Ichita-branded DOCX, convert Markdown, rebrand existing docs |
| **ichita-pptx** | `/ichita-skills:ichita-pptx` | Create Ichita-branded PPTX, process diagrams, html2pptx |

### Trigger Behavior

| User request | Skill triggered |
|---|---|
| "Create a Word document" | `docx` (Anthropic) |
| "Create an Ichita-branded proposal" | `ichita-docx` + `docx` |
| "Create a process flow diagram" | `ichita-pptx` + `pptx` |
| "Rebrand this DOCX to Ichita style" | `ichita-docx` |
| "Fill out this PDF form" | `pdf` (Anthropic) |

### DOCX Tools

| Script | Usage | Description |
|--------|-------|-------------|
| `md_to_docx.py` | `python md_to_docx.py INPUT.md OUTPUT.docx` | Convert Markdown to Ichita-branded DOCX |
| `rebrand_docx.py` | `python rebrand_docx.py INPUT.docx OUTPUT.docx` | Rebrand any existing DOCX to Ichita style |

Options: `--no-logo`, `--font NAME`, `--margin CM`, `--no-title-page`, `--logo PATH`

## Setup

### Prerequisites

Install the base document skills first:
```bash
/plugin install document-skills@anthropic-agent-skills
/plugin install example-skills@anthropic-agent-skills   # optional, includes skill-creator
```

### For Admins (OhYeaH!)

1. Push this repo to `Siwatch-OhYeaH/ichita-skills` (private)
2. Go to Claude.ai > Admin Settings > Claude Code > Managed settings
3. Add:

```json
{
  "extraKnownMarketplaces": {
    "ichita": {
      "source": {
        "source": "github",
        "repo": "Siwatch-OhYeaH/ichita-skills"
      }
    }
  },
  "enabledPlugins": {
    "ichita-skills@ichita": true
  }
}
```

### For Team Members

Skills are auto-available after admin setup. No action needed.

If not using managed settings, install manually:

```bash
/plugin marketplace add Siwatch-OhYeaH/ichita-skills
/plugin install ichita-skills@ichita
```

### Font Setup

The scripts auto-detect Aeonik font across platforms:

**Ubuntu/Linux (PC)**:
```bash
cp assets/fonts/aeonik/*.otf ~/.local/share/fonts/
cp assets/fonts/bai-jamjuree/*.ttf ~/.local/share/fonts/
fc-cache -f
```

**macOS (MacBook)**:
```bash
cp assets/fonts/aeonik/*.otf ~/Library/Fonts/
cp assets/fonts/bai-jamjuree/*.ttf ~/Library/Fonts/
```

**Windows**: Font files are at `assets/fonts/` — right-click > Install for all users.

### Dependencies

**Ubuntu/Linux**:
```bash
sudo apt-get install pandoc libreoffice poppler-utils
pip install python-docx defusedxml
```

**macOS**:
```bash
brew install pandoc libreoffice poppler
pip install python-docx defusedxml
```

## Structure

```
ichita-skills/
├── .claude-plugin/        # Plugin metadata
├── skills/
│   ├── ichita-docx/       # Ichita-branded Word documents
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       ├── docx_helpers.py   # Brand config + XML helpers
│   │       ├── md_to_docx.py     # Markdown -> branded DOCX
│   │       ├── rebrand_docx.py   # Rebrand existing DOCX
│   │       ├── document.py       # OOXML editing library
│   │       └── utilities.py      # XML utilities
│   └── ichita-pptx/       # Ichita-branded presentations
│       ├── SKILL.md
│       ├── process-diagrams.md
│       ├── html2pptx.md
│       ├── layout-patterns.json
│       └── scripts/
│           ├── process-diagram-lib.cjs
│           ├── html2pptx.js
│           ├── extract_positions.py
│           ├── inventory.py
│           ├── replace.py
│           ├── rearrange.py
│           └── thumbnail.py
├── assets/
│   ├── brand/             # ichita-defaults.md + brand guidelines PDF
│   ├── fonts/             # Aeonik, Bai Jamjuree, Betatron
│   └── logos/             # ICHITA logos (wordmark, icon, variants)
```

## License

Proprietary — ICHITA Technology Co., Ltd.
