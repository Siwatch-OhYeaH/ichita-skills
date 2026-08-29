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
  ichita-docx      -> Brand DOCX: md_to_docx, rebrand_docx, brand config
  ichita-pptx      -> Brand PPTX: process diagrams, html2pptx, layout patterns
  ichita-template  -> Restyle an existing PPTX, or build from the Company Demo base
  ichita-exe-brief -> Executive briefs: content -> branded HTML -> print-ready PDF
  ichita-convert   -> docx/md/html/pdf conversion, and merging a hand-edited DOCX back
  assets/          -> Brand guidelines, fonts, logos, brand CSS
  scripts/         -> The Thai/Latin font toolchain (see docs/)
```

## Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **ichita-docx** | `/ichita-skills:ichita-docx` | Create Ichita-branded DOCX, convert Markdown, rebrand existing docs |
| **ichita-pptx** | `/ichita-skills:ichita-pptx` | Create Ichita-branded PPTX, process diagrams, html2pptx |
| **ichita-template** | `/ichita-skills:ichita-template` | Apply ICHITA template to existing PPTX (restyle fonts/colors), or generate new PPTX from Company Demo base template |
| **ichita-exe-brief** | `/ichita-skills:ichita-exe-brief` | Executive brief pipeline — content, branded HTML layout, print-ready PDF |
| **ichita-convert** | `/ichita-skills:ichita-convert` | Convert between docx/md/html/pdf, and reconcile a hand-edited DOCX back into the Markdown record |

### Trigger Behavior

| User request | Skill triggered |
|---|---|
| "Create a Word document" | `docx` (Anthropic) |
| "Create an Ichita-branded proposal" | `ichita-docx` + `docx` |
| "Create a process flow diagram" | `ichita-pptx` + `pptx` |
| "Rebrand this DOCX to Ichita style" | `ichita-docx` |
| "Fill out this PDF form" | `pdf` (Anthropic) |
| "Apply ichita template to this PPTX" | `ichita-template` |
| "Convert this presentation to ichita template" | `ichita-template` |
| "Generate new PPTX from Company Demo" | `ichita-template` |
| "Write an executive brief / board memo" | `ichita-exe-brief` |
| "Read this client RFP / returned DOCX / supplier PDF" | `ichita-convert` |
| "Merge the edits my colleague made in Word" | `ichita-convert` |

### DOCX Tools

| Script | Usage | Description |
|--------|-------|-------------|
| `md_to_docx.py` | `python md_to_docx.py INPUT.md OUTPUT.docx` | Convert Markdown to Ichita-branded DOCX |
| `rebrand_docx.py` | `python rebrand_docx.py INPUT.docx OUTPUT.docx` | Rebrand any existing DOCX to Ichita style |
| `html_to_docx.py` | `python html_to_docx.py INPUT.html OUTPUT.docx` | Branded DOCX from a designed HTML page |
| `docx_helpers.py` | imported | Brand config (colors, fonts, geometry) + XML helpers |

Options: `--no-logo`, `--font NAME`, `--margin CM`, `--no-title-page`, `--logo PATH`

> **PDF delivery: Print to PDF, never Save as PDF.** Office cannot embed OpenType-CFF and
> substitutes Calibri silently. See `skills/ichita-convert/reference/pdf-delivery.md`.

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

Two families carry every document. **The face is chosen by the document's language:**
English-only → `Aeonik`; Thai or mixed TH/EN → `TH Aeonik`.

**Ubuntu/Linux and macOS** — one command:
```bash
bash scripts/install-fonts.sh
```

**Windows** — install through **Settings → Fonts**, not a script. Close Office first, and
delete every previously installed `TH-Aeonik-*` file: the filenames changed, so a new
install does not overwrite an old one.

Verify: `fc-list | grep -i "TH Aeonik"` should list 22 faces.

> Bilingual work has non-obvious constraints — line pitch, weight, mark clearance, and
> Word-vs-PowerPoint differences. **Read `docs/THAI-LATIN-FONT-ENGINEERING.md` before
> touching any of it.**

### Dependencies

System tools first — none are pip-installable, and each one silently changes what the
skills can do:

**Ubuntu/Linux**:
```bash
sudo apt-get install pandoc libreoffice poppler-utils
```

**macOS**:
```bash
brew install pandoc libreoffice poppler
```

Then per skill, which reports what is still missing rather than assuming:
```bash
bash skills/ichita-convert/install.sh    # also needs: python3 -m playwright install chromium
bash skills/ichita-docx/install.sh
```

The font toolchain in `scripts/` needs `fontTools`, `fontforge` and `uharfbuzz` on the
**system** python3 — `fontforge` is not pip-installable (`sudo apt-get install
python3-fontforge`).

## Structure

```
ichita-skills/
├── .claude-plugin/         # Plugin metadata
├── CLAUDE.md               # Art director + marcom role, brand rules, architecture
├── skills/
│   ├── ichita-docx/        # Ichita-branded Word documents
│   │   └── scripts/        # docx_helpers (brand config), md_to_docx,
│   │                       #   rebrand_docx, html_to_docx
│   ├── ichita-pptx/        # Ichita-branded presentations
│   │   ├── process-diagrams.md, html2pptx.md, layout-patterns.json
│   │   ├── examples/       # test-all-layouts.cjs — visual QA deck
│   │   └── scripts/        # ichita-slide-lib.cjs, process-diagram-lib.cjs,
│   │                       #   html2pptx.js, extract_positions, inventory,
│   │                       #   replace, rearrange, thumbnail
│   ├── ichita-template/    # Restyle an existing PPTX, or build from Company Demo
│   │   └── scripts/        # restyle_pptx, generate_pptx
│   ├── ichita-exe-brief/   # Executive brief pipeline
│   │   └── scripts/        # html2pdf.py — reports the fonts Chromium actually used
│   └── ichita-convert/     # docx/md/html/pdf + reconcile a hand-edited DOCX
│       ├── reference/      # inbound, outbound, pdf-delivery, reconcile
│       └── scripts/        # convert, ingest_*, emit_html, reconcile, pdf_bakeoff
├── assets/
│   ├── brand/              # ichita-defaults.md, docx-standard.md, ichita.css,
│   │                       #   Ichita_Brand_Guidelines_V1.0.pdf
│   ├── fonts/              # Aeonik, TH Aeonik, Slussen, TH Slussen,
│   │                       #   Bai Jamjuree, Betatron (+ web cuts, HELD)
│   ├── logos/              # 12 approved files — use them, never recreate
│   └── templates/          # ichita-document.dotx
├── scripts/                # Thai/Latin font build + QC toolchain
├── docs/                   # THAI-LATIN-FONT-ENGINEERING.md is the font record
├── qc/                     # Document-level font QC reference
└── mcp-server/             # MCP tools: generate_brief, generate_docx, list_templates
```

## License

Proprietary — ICHITA Technology Co., Ltd.
