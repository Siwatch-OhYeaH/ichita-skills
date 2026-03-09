---
name: ichita-template
description: "Use when applying ICHITA template to an existing PPTX (restyle fonts and colors while preserving layout), or generating a new presentation from the ICHITA Company Demo base template using slide-type definitions. Trigger keywords: 'ichita template', 'apply ichita template', 'convert to ichita', 'rebrand pptx', 'ichita company demo'. For building fully branded PPTX from scratch with PptxGenJS or process diagrams, use ichita-pptx instead."
---

# ICHITA Template — Apply & Generate

Two modes for applying ICHITA visual identity to PowerPoint presentations.

---

## Mode 1: Restyle Existing PPTX (Preserve Layout)

**When to use**: User has an existing PPTX and wants ICHITA fonts/colors applied — keep all shapes, positions, and layout unchanged.

**Script**: `scripts/restyle_pptx.py`

```bash
python scripts/restyle_pptx.py INPUT.pptx OUTPUT.pptx
```

### What it changes

| Element | Old (typical) | ICHITA |
|---------|--------------|--------|
| Latin font | Calibri, Arial, etc. | `Aeonik` |
| Thai font | Angsana New, Cordia New | `TH Sarabun New` |
| Theme major font | Calibri Light | `Aeonik` |
| Theme minor font | Calibri | `Aeonik` |
| Accent blue | `4472C4` | `2978FF` |
| Dark navy | `1A2B5E`, `253880` | `263338` / `1B4F8A` |
| Gold/amber | `D4A017`, `F0C040` | `788F9C` / `CFD9DB` |
| Dark gray text | `334155` | `263338` |
| Teal accent | `0F7D8C` | `2978FF` |

### Files modified
- `ppt/theme/theme*.xml` — font scheme + color scheme
- `ppt/slides/slide*.xml` — all slide XMLs
- `ppt/slideMasters/slideMaster*.xml` — master slide
- `ppt/slideLayouts/slideLayout*.xml` — layout templates

---

## Mode 2: Generate New PPTX from Company Demo Template

**When to use**: User wants a new presentation built with ICHITA's Company Demo template as the base (background image, fonts, colors already embedded in the template file).

**Template**: `C:\Users\Dell\Desktop\Company Demo.pptx` (WSL: `/mnt/c/Users/Dell/Desktop/Company Demo.pptx`)

**Script**: `scripts/generate_pptx.py`

```bash
python scripts/generate_pptx.py
# Edit CONTENT_SLIDES array and output path in the script before running
```

### Slide Types

| Type | Layout | Use for |
|------|--------|---------|
| `"cover"` | Full-bleed background image, centered title | Opening + closing slides |
| `"bullets"` | Right-aligned title + numbered/bulleted body | Agenda, lists, roadmaps, action plans |
| `"twocol"` | Right-aligned title + two columns + gray divider | Comparisons, features, opportunities |
| `"stacked"` | Right-aligned title + two stacked text sections | Detail slides with two grouped sections |
| `"benefits"` | Right-aligned title + section label + left/right panels | Strategic benefits, KPI slides |

### CONTENT_SLIDES definition

```python
CONTENT_SLIDES = [
    # bullets — agenda, lists, roadmaps
    {
        "type": "bullets",
        "title": "Slide Title",
        "title_sz": 2400,           # optional, default 2400 (hundredths of pt)
        "items": [
            ("Bold label", "regular explanation"),
            ("", "sub-bullet text (no bold)"),
        ]
    },

    # twocol — comparisons, two-column content
    {
        "type": "twocol",
        "title": "Slide Title",
        "left":  {"header": "Left Section",  "items": [("Key", "value"), ("", "plain item")]},
        "right": {"header": "Right Section", "items": [("Key", "value"), ("", "plain item")]},
    },

    # stacked — two grouped sections vertically
    {
        "type": "stacked",
        "title": "Slide Title",
        "top":    {"header": "Section A", "lines": ["Line 1", "Line 2"]},
        "bottom": {"header": "Section B", "lines": ["Line 1", "Line 2"]},
    },

    # benefits — left panel + right panel with section label
    {
        "type": "benefits",
        "title": "STRATEGIC BENEFITS",
        "section_label": "ESG & Sustainability Impact",
        "left":  {"header": "Environmental", "lines": ["Detail one", "Detail two"]},
        "right": {"header": "Governance",    "lines": ["UN SDG 6 compliance", "ISO 14001"]},
    },
]
```

### EMU position constants (Company Demo template)

| Element | x | y | cx | cy |
|---------|---|---|----|----|
| Title (most slides) | 2360746 | -135170 | 9831254 | 1143000 |
| Title (bullets variant) | 2070101 | 80367 | 9831254 | 1143000 |
| Full-width body | 1575527 | 1323352 | 9040945 | 4600000 |
| Left column | 1050000 | 1300000 | 5050000 | 5200000 |
| Right column | 7106741 | 1300000 | 4800000 | 5200000 |
| Column divider | 6150000 | 1100000 | 45719 | 5400000 |
| Section label | 495310 | 1147161 | 9000000 | 400000 |
| Left panel | 495310 | 1700000 | 5500000 | 4800000 |
| Right panel | 6253654 | 1700000 | 5500000 | 4800000 |
| Cover title | 0 | 2246934 | 12192000 | 2007014 |
| Stacked top | 1473950 | 2253594 | 6600215 | 1231106 |
| Stacked bottom | 1473950 | 3724108 | 6725344 | 1015663 |

### Color & font constants

```python
DARK  = "44546A"   # body dark text
BLUE  = "1B4F8A"   # section headers
COVER_TITLE_COLOR = "CFD6DC"   # cover slide title
FONT_LATIN = "Aeonik"
FONT_THAI  = "TH Sarabun New"
```

### Slide size
- `cx = 12192000 EMU`, `cy = 6858000 EMU` (widescreen 16:9)

---

## Workflow

### Restyle existing PPTX
1. Run `python scripts/restyle_pptx.py INPUT.pptx OUTPUT.pptx`
2. Open OUTPUT.pptx — verify fonts and colors
3. If colors look off, update `COLOR_MAP` in `restyle_pptx.py` with any new hex codes found in the source

### Generate from template
1. Extract content from source PPTX (use `python -c "import zipfile, re; ..."` to read slide XMLs)
2. Map each slide to a type: `cover`, `bullets`, `twocol`, `stacked`, `benefits`
3. Edit `generate_pptx.py` — fill `CONTENT_SLIDES`, set `OUTPUT` path
4. Run `python scripts/generate_pptx.py`

---

## Dependencies

- Python 3 stdlib only (`zipfile`, `re`) — no external packages required
- Source template file: `/mnt/c/Users/Dell/Desktop/Company Demo.pptx`

---

## Related skills

| Skill | Use when |
|-------|----------|
| `ichita-pptx` | Building fully branded presentations from scratch using PptxGenJS or process diagrams |
| `ichita-docx` | Branded Word documents (rebrand or generate from Markdown) |
| `ichita-template` | (this skill) Restyle existing PPTX or generate from Company Demo base template |
