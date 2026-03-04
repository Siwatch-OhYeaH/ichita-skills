# Ichita PowerPoint Template Reference

This document is the authoritative reference for `assets/ichita/templates/powerpoint-template.pptx`. Read this before editing the template.

**When to use this file**: Before editing or building on top of `powerpoint-template.pptx` using OOXML/XML manipulation.

**Two paths for PowerPoint work**:
- **Editing the existing template** (add slides, change text, use branded backgrounds/logo) → Use this reference + ooxml scripts
- **Creating a NEW presentation from scratch** → Use pptxgenjs + `assets/ichita/brand/ichita-defaults.md`

---

## Presentation Setup

| Property | Value |
|----------|-------|
| Slide size (EMU) | cx=12192000, cy=6858000 |
| Slide size (inches) | 13.33 × 7.50 in (standard 16:9 widescreen) |
| Total slides | 3 |
| Slide layouts | 11 |
| Slide masters | 1 |
| Themes | 2 |

---

## Files in the Package

```
[Content_Types].xml
_rels/.rels
docProps/app.xml
docProps/core.xml
docProps/thumbnail.jpeg
ppt/_rels/presentation.xml.rels
ppt/media/image1.png              (Ichita logo)
ppt/media/image2.jpeg             (Background image)
ppt/notesMasters/_rels/notesMaster1.xml.rels
ppt/notesMasters/notesMaster1.xml
ppt/presProps.xml
ppt/presentation.xml
ppt/slideLayouts/_rels/slideLayout1-11.xml.rels
ppt/slideLayouts/slideLayout1-11.xml
ppt/slideMasters/_rels/slideMaster1.xml.rels
ppt/slideMasters/slideMaster1.xml
ppt/slides/_rels/slide1-3.xml.rels
ppt/slides/slide1-3.xml
ppt/tableStyles.xml
ppt/theme/theme1.xml
ppt/theme/theme2.xml
ppt/viewProps.xml
```

---

## Presentation Relationships (`ppt/_rels/presentation.xml.rels`)

| rId | Target | Type |
|-----|--------|------|
| rId1 | slideMasters/slideMaster1.xml | slideMaster |
| rId2 | slides/slide1.xml | slide |
| rId3 | slides/slide2.xml | slide |
| rId4 | slides/slide3.xml | slide |
| rId5 | notesMasters/notesMaster1.xml | notesMaster |
| rId6 | presProps.xml | presProps |
| rId7 | viewProps.xml | viewProps |
| rId8 | theme/theme1.xml | theme |
| rId9 | tableStyles.xml | tableStyles |

---

## Slide Layout Catalog

| Layout # | Name | Purpose |
|----------|------|---------|
| slideLayout1 | Title Slide | Opening/closing slides with title |
| slideLayout2 | Title and Content | Standard content slide with title + body |
| slideLayout3 | Section Header | Divider between sections |
| slideLayout4 | Two Content | Side-by-side comparison |
| slideLayout5 | Comparison | Comparison with subtitles |
| slideLayout6 | Title Only | Title bar only, blank body |
| slideLayout7 | Blank | Completely blank canvas |
| slideLayout8 | Content with Caption | Content area + caption sidebar |
| slideLayout9 | Picture with Caption | Picture area + caption |
| slideLayout10 | Title and Vertical Text | Vertical text orientation |
| slideLayout11 | Vertical Title and Text | Both title and body vertical |

---

## Slide Master Relationships

The slide master (`ppt/slideMasters/slideMaster1.xml`) references:

| rId | Target | Type |
|-----|--------|------|
| rId1–rId11 | slideLayouts/slideLayout1–11.xml | slideLayout |
| rId12 | theme/theme1.xml | theme |
| rId13 | media/image1.png | image (Ichita logo) |

---

## Existing Slides

| Slide | Layout Used | Content | Background Image |
|-------|-------------|---------|-----------------|
| slide1.xml | slideLayout6 (Title Only) | "Topic" | image2.jpeg (background) |
| slide2.xml | slideLayout7 (Blank) | "Slide Title", "Sub topic" | None |
| slide3.xml | slideLayout6 (Title Only) | "Thank you" | image2.jpeg (background) |

---

## Theme Colors

### Theme 1 (Office Theme — custom, used by slide master)

| Role | Token | Hex |
|------|-------|-----|
| dk1 | Dark 1 | #000000 (system windowText) |
| lt1 | Light 1 | #FFFFFF (system window) |
| dk2 | Dark 2 | #44546A |
| lt2 | Light 2 | #E7E6E6 |
| accent1 | Accent 1 | #4472C4 |
| accent2 | Accent 2 | #ED7D31 |
| accent3 | Accent 3 | #A5A5A5 |
| accent4 | Accent 4 | #FFC000 |
| accent5 | Accent 5 | #5B9BD5 |
| accent6 | Accent 6 | #70AD47 |
| hlink | Hyperlink | #0563C1 |
| folHlink | Followed Hyperlink | #954F72 |

### Theme 2 (Office)

Same color scheme as Theme 1.

Note: These are Office default theme colors. For new Ichita-branded content added to slides, override with Ichita brand colors: Blue `#2978ff`, Blue Grey 03 `#263338`, White `#ffffff`. See `assets/ichita/brand/ichita-defaults.md` for the full brand palette.

---

## Theme Fonts

| Property | Value |
|----------|-------|
| Font scheme name | Custom 6 |
| Major font (headings) | Aeonik |
| Minor font (body) | Aeonik |
| EA font | (empty — inherits from system) |

---

## Media Files

| File | Usage | Referenced From |
|------|-------|----------------|
| `ppt/media/image1.png` | Ichita logo | `slideMaster1.xml` (rId13) |
| `ppt/media/image2.jpeg` | Background image (dark) | `slide1.xml` (rId2), `slide3.xml` (rId2) |
| `docProps/thumbnail.jpeg` | Package thumbnail preview | Package root |

---

## XML Patterns for Editing

### Modifying Slide Text

Find `<a:t>` elements within the target slide XML and replace text content:

```xml
<!-- In ppt/slides/slideN.xml -->
<a:r>
  <a:rPr lang="en-US" dirty="0"/>
  <a:t>Your New Text Here</a:t>
</a:r>
```

### Adding a New Slide (by duplicating an existing one)

Follow all five steps — missing any step will break the presentation:

**Step 1** — Copy slide XML:
```
slide2.xml → slide4.xml
```

**Step 2** — Copy slide rels file:
```
slides/_rels/slide2.xml.rels → slides/_rels/slide4.xml.rels
```

**Step 3** — Add relationship in `ppt/_rels/presentation.xml.rels`:
```xml
<Relationship Id="rIdN"
  Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"
  Target="slides/slide4.xml"/>
```

**Step 4** — Add slide reference in `ppt/presentation.xml` inside `<p:sldIdLst>`:
```xml
<p:sldId id="NEXT_ID" r:id="rIdN"/>
```
`NEXT_ID` must be unique and higher than all existing sldId values.

**Step 5** — Add content part in `[Content_Types].xml`:
```xml
<Override PartName="/ppt/slides/slide4.xml"
  ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
```

### Text Box with Ichita Style

```xml
<p:sp>
  <p:nvSpPr>
    <p:cNvPr id="UNIQUE_ID" name="TextBox N"/>
    <p:cNvSpPr txBox="1"/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm>
      <a:off x="LEFT_EMU" y="TOP_EMU"/>
      <a:ext cx="WIDTH_EMU" cy="HEIGHT_EMU"/>
    </a:xfrm>
    <a:prstGeom prst="rect">
      <a:avLst/>
    </a:prstGeom>
    <a:noFill/>
  </p:spPr>
  <p:txBody>
    <a:bodyPr wrap="square" rtlCol="0"/>
    <a:lstStyle/>
    <a:p>
      <a:r>
        <a:rPr lang="en-US" dirty="0"/>
        <a:t>Your text here</a:t>
      </a:r>
    </a:p>
  </p:txBody>
</p:sp>
```

### Image on Slide (referencing an existing media file)

Add the image relationship to the slide's rels file first, then reference it:

```xml
<!-- In ppt/slides/_rels/slideN.xml.rels -->
<Relationship Id="rIdN"
  Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
  Target="../media/imageX.png"/>
```

```xml
<!-- In ppt/slides/slideN.xml -->
<p:pic>
  <p:nvPicPr>
    <p:cNvPr id="UNIQUE_ID" name="Picture N"/>
    <p:cNvPicPr>
      <a:picLocks noChangeAspect="1"/>
    </p:cNvPicPr>
    <p:nvPr/>
  </p:nvPicPr>
  <p:blipFill>
    <a:blip r:embed="rIdN"/>
    <a:stretch>
      <a:fillRect/>
    </a:stretch>
  </p:blipFill>
  <p:spPr>
    <a:xfrm>
      <a:off x="LEFT_EMU" y="TOP_EMU"/>
      <a:ext cx="WIDTH_EMU" cy="HEIGHT_EMU"/>
    </a:xfrm>
    <a:prstGeom prst="rect">
      <a:avLst/>
    </a:prstGeom>
  </p:spPr>
</p:pic>
```

### EMU Quick Reference

| Measurement | EMU value |
|-------------|-----------|
| 1 inch | 914400 |
| 1 cm | 360000 |
| Full slide width (13.33 in) | 12192000 |
| Full slide height (7.50 in) | 6858000 |
| Half slide width | 6096000 |
| Half slide height | 3429000 |

---

## Protected Elements — NEVER MODIFY

These files define the template's structure, branding, and layouts. Editing them will corrupt the template or destroy the Ichita identity.

| File | Reason |
|------|--------|
| `ppt/media/image1.png` | Ichita logo — brand asset |
| `ppt/media/image2.jpeg` | Background image — brand asset |
| `ppt/slideMasters/slideMaster1.xml` | Master slide — defines all layouts |
| `ppt/slideLayouts/*.xml` | All 11 slide layout definitions |
| `ppt/theme/theme1.xml` | Theme colors and fonts |
| `ppt/theme/theme2.xml` | Secondary theme |
| `ppt/notesMasters/*` | Notes master |
| `docProps/*` | Document properties |
| `_rels/.rels` | Package relationships |

---

## What You CAN Modify

| File | Allowed Operations |
|------|--------------------|
| `ppt/slides/slideN.xml` | Edit text in `<a:t>` nodes, add shapes/images |
| `ppt/slides/_rels/slideN.xml.rels` | Add new image or media references |
| `ppt/_rels/presentation.xml.rels` | Add new slide relationship entries |
| `ppt/presentation.xml` | Add slide IDs to `<p:sldIdLst>` |
| `[Content_Types].xml` | Register new slide content parts |

---

## Editing Workflow

```bash
# Step 1 — Copy the original template (never edit the original directly)
cp assets/ichita/templates/powerpoint-template.pptx ./output/working.pptx

# Step 2 — Unpack the PPTX
python .claude/skills/pptx/ooxml/scripts/unpack.py ./output/working.pptx ./output/unpacked/

# Step 3 — Edit slide XML files as needed
# (see XML patterns above)

# Step 4 — Pack back into PPTX
python .claude/skills/pptx/ooxml/scripts/pack.py ./output/unpacked/ ./output/final.pptx
```

---

## Cross-references

| Need | Reference |
|------|-----------|
| Creating new presentations (not from template) | pptxgenjs + `assets/ichita/brand/ichita-defaults.md` |
| Ichita brand colors, fonts, logo specs | `assets/ichita/brand/ichita-defaults.md` |
| OOXML pack/unpack scripts | `.claude/skills/pptx/ooxml/scripts/` |
| DOCX editing reference | `assets/ichita/templates/word-template-reference.md` (if exists) |
