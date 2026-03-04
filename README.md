# ichita-skills

Private Claude Code plugin for **ICHITA Technology** — document creation skills (PPTX, DOCX, PDF) with brand templates, fonts, and assets.

## Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **PPTX** | `/ichita-skills:pptx` | Create and edit PowerPoint presentations with ICHITA brand templates |
| **DOCX** | `/ichita-skills:docx` | Create, edit, and rebrand Word documents with Ichita styling |
| **PDF** | `/ichita-skills:pdf` | PDF processing, form filling, and manipulation |

### DOCX Tools

| Script | Usage | Description |
|--------|-------|-------------|
| `md_to_docx.py` | `python md_to_docx.py INPUT.md OUTPUT.docx` | Convert Markdown to Ichita-branded DOCX |
| `rebrand_docx.py` | `python rebrand_docx.py INPUT.docx OUTPUT.docx` | Rebrand any existing DOCX to Ichita style |

Options: `--no-logo`, `--font NAME`, `--margin CM`, `--no-title-page`, `--logo PATH`

## Setup

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
# Copy font files to user fonts directory
cp assets/fonts/aeonik/*.otf ~/.local/share/fonts/
cp assets/fonts/bai-jamjuree/*.ttf ~/.local/share/fonts/
fc-cache -f
```

**macOS (MacBook)**:
```bash
# Copy to user fonts — or double-click each .otf to install via Font Book
cp assets/fonts/aeonik/*.otf ~/Library/Fonts/
cp assets/fonts/bai-jamjuree/*.ttf ~/Library/Fonts/
```

**Windows**: Font files are at `assets/fonts/` — right-click > Install for all users.

If fonts are not installed, scripts will fall back to Calibri and warn you.

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
│   ├── docx/              # Word document skill
│   │   ├── SKILL.md       # Skill guide (workflows, decision tree)
│   │   ├── scripts/
│   │   │   ├── docx_helpers.py   # Brand config + generic XML helpers
│   │   │   ├── md_to_docx.py     # Markdown → branded DOCX
│   │   │   ├── rebrand_docx.py   # Rebrand existing DOCX → Ichita
│   │   │   ├── document.py       # OOXML editing library (tracked changes)
│   │   │   └── utilities.py      # XML editor utilities
│   │   ├── ooxml/         # OOXML pack/unpack scripts + schemas
│   │   ├── docx-js.md     # docx-js reference (new docs from scratch)
│   │   └── ooxml.md       # OOXML editing reference
│   ├── pptx/              # PowerPoint skill + scripts
│   └── pdf/               # PDF skill + scripts
├── assets/
│   ├── brand/             # Brand guidelines PDF, ichita-defaults.md
│   ├── fonts/             # Aeonik, Bai Jamjuree, Betatron
│   └── logos/             # ICHITA logos (wordmark, icon, variants)
```

## Brand Architecture

```
ichita-defaults.md          ← source of truth (human-readable brand spec)
        |
    ICHITA_BRAND dict       ← data only (docx_helpers.py)
        | passed to
    docx_helpers.py         ← generic functions, brand-agnostic
        | used by
    md_to_docx.py           ← markdown → branded DOCX
    rebrand_docx.py         ← transform existing DOCX → branded
```

All brand values (colors, fonts, typography, margins) come from a single config dict in `docx_helpers.py`, sourced from `ichita-defaults.md`.

## License

Proprietary — ICHITA Technology Co., Ltd.
