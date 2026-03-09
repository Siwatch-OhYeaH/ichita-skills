"""
generate_pptx.py — Generate a new PPTX from the ICHITA Company Demo base template.

Uses stdlib zipfile only — no python-pptx or external packages.
The Company Demo template supplies: background image, slide master, fonts, theme.
This script replaces all slides with new content defined in CONTENT_SLIDES.

Usage:
    Edit CONTENT_SLIDES, COVER_TITLE, CLOSING_TITLE, OUTPUT below, then run:
    python generate_pptx.py

Slide types: "cover", "bullets", "twocol", "stacked", "benefits"
See SKILL.md for full type definitions.
"""
import zipfile
import re
import os

# ── Configuration ─────────────────────────────────────────────────────────────

TEMPLATE = "/mnt/c/Users/Dell/Desktop/Company Demo.pptx"
OUTPUT   = "/mnt/c/Users/Dell/Desktop/ICHITA_Generated.pptx"

COVER_TITLE   = "Presentation Title\n& Subtitle"
CLOSING_TITLE = "Thank You"

# ── Color / font constants ────────────────────────────────────────────────────

DARK             = "44546A"    # body dark text
BLUE             = "1B4F8A"    # section header blue
COVER_TEXT_COLOR = "CFD6DC"    # cover/closing title
FONT_LATIN       = "Aeonik"
FONT_THAI        = "TH Sarabun New"

# ── XML helpers ───────────────────────────────────────────────────────────────

def esc(s: str) -> str:
    """Escape XML special characters."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def run_xml(text: str, sz: int, bold: bool = False,
            color: str = DARK, font: str = FONT_LATIN) -> str:
    b    = ' b="1"' if bold else ' b="0"'
    fill = f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
    lat  = f'<a:latin typeface="{font}"/>' if font else ""
    thai = f'<a:ea typeface="{FONT_THAI}"/>'
    return (f'<a:r><a:rPr lang="th-TH" sz="{sz}"{b} dirty="0">'
            f'{fill}{lat}{thai}</a:rPr>'
            f'<a:t>{esc(text)}</a:t></a:r>')


def bullet_para(bold_text: str, regular_text: str,
                sz: int = 1400, indent: bool = False) -> str:
    """200% line spacing, spcBef/Aft=0 — matches bullets/twocol body."""
    r = ""
    if bold_text:    r += run_xml(bold_text,             sz, bold=True,  color=DARK)
    if regular_text: r += run_xml("  " + regular_text,  sz, bold=False, color=DARK)
    hang = ' marL="285750" indent="-285750"' if indent else ""
    return (f'<a:p><a:pPr{hang}>'
            f'<a:spcBef><a:spcPts val="0"/></a:spcBef>'
            f'<a:spcAft><a:spcPts val="0"/></a:spcAft>'
            f'<a:lnSpc><a:spcPct val="200000"/></a:lnSpc>'
            f'</a:pPr>{r}</a:p>')


def panel_para(text: str, sz: int = 1400, bold: bool = False,
               color: str = DARK, indent: bool = False) -> str:
    """Fixed 20.5pt line spacing — matches benefits/stacked panels."""
    hang = ' marL="285750" indent="-285750"' if indent else ""
    return (f'<a:p><a:pPr{hang}>'
            f'<a:spcBef><a:spcPts val="0"/></a:spcBef>'
            f'<a:spcAft><a:spcPts val="0"/></a:spcAft>'
            f'<a:lnSpc><a:spcPts val="2050"/></a:lnSpc>'
            f'</a:pPr>{run_xml(text, sz, bold=bold, color=color)}</a:p>')


def txbox(id_: int, name: str, x: int, y: int, cx: int, cy: int,
          content: str, anchor: str = "t") -> str:
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{id_}" name="{name}"/>'
            f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
            f'<p:txBody><a:bodyPr wrap="square" rtlCol="0" anchor="{anchor}">'
            f'<a:spAutoFit/></a:bodyPr><a:lstStyle/>{content}</p:txBody></p:sp>')


def filled_rect(id_: int, name: str, x: int, y: int,
                cx: int, cy: int, color: str) -> str:
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{id_}" name="{name}"/>'
            f'<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
            f'<a:ln><a:noFill/></a:ln></p:spPr>'
            f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>')


def slide_wrap(shapes: list) -> str:
    return (f"<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
            f'<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            f'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
            f'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
            f'<p:cSld><p:spTree>'
            f'<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
            f'<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
            f'<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
            f'{"".join(shapes)}'
            f'</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')


def title_shape(text: str, sz: int = 2400,
                x: int = 2360746, y: int = -135170,
                cx: int = 9831254, cy: int = 1143000) -> str:
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title"/>'
            f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
            f'<p:txBody>'
            f'<a:bodyPr anchor="ctr" lIns="91440" rIns="91440" tIns="45720" bIns="45720">'
            f'<a:spAutoFit/></a:bodyPr><a:lstStyle/>'
            f'<a:p><a:pPr algn="r"/>'
            f'{run_xml(text, sz, bold=True)}</a:p>'
            f'</p:txBody></p:sp>')


# ── Slide builders ────────────────────────────────────────────────────────────

def cover_xml(title: str) -> str:
    """Full-bleed background image + centered title. Uses image2.jpeg from template."""
    runs = ""
    for line in title.split("\n"):
        runs += run_xml(line, 4800, bold=True, color=COVER_TEXT_COLOR)
        runs += (f'<a:br><a:rPr lang="th-TH" b="1" dirty="0">'
                 f'<a:solidFill><a:srgbClr val="{COVER_TEXT_COLOR}"/></a:solidFill>'
                 f'<a:latin typeface="{FONT_LATIN}"/>'
                 f'<a:ea typeface="{FONT_THAI}"/></a:rPr></a:br>')

    bg = ('<p:pic><p:nvPicPr><p:cNvPr id="2" name="Background"/>'
          '<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
          '<p:blipFill><a:blip r:embed="rId2"/><a:srcRect/>'
          '<a:stretch><a:fillRect/></a:stretch></p:blipFill>'
          '<p:spPr bwMode="auto"><a:xfrm><a:off x="0" y="0"/>'
          '<a:ext cx="12192000" cy="6858000"/></a:xfrm>'
          '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
          '<a:noFill/><a:ln><a:noFill/></a:ln></p:spPr></p:pic>')

    sp = (f'<p:sp><p:nvSpPr><p:cNvPr id="4" name="CoverTitle"/>'
          f'<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
          f'<p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr>'
          f'<p:spPr><a:xfrm><a:off x="0" y="2246934"/>'
          f'<a:ext cx="12192000" cy="2007014"/></a:xfrm></p:spPr>'
          f'<p:txBody><a:bodyPr><a:normAutofit/></a:bodyPr><a:lstStyle/>'
          f'<a:p><a:pPr algn="ctr">'
          f'<a:lnSpc><a:spcPct val="150000"/></a:lnSpc></a:pPr>{runs}</a:p>'
          f'</p:txBody></p:sp>')

    return slide_wrap([bg, sp])


def bullets_xml(cs: dict) -> str:
    """Right-aligned title + bulleted/numbered body (slide 6 style)."""
    body = "".join(
        bullet_para(b, r, indent=(b == ""))
        for b, r in cs["items"]
    )
    sz = cs.get("title_sz", 2400)
    return slide_wrap([
        title_shape(cs["title"], sz=sz, y=80367),
        txbox(3, "Body", 1575527, 1323352, 9040945, 4600000, body),
    ])


def twocol_xml(cs: dict) -> str:
    """Right-aligned title + two columns separated by a gray divider."""
    lbody = panel_para(cs["left"]["header"],  sz=1600, bold=True, color=BLUE)
    for b, r in cs["left"]["items"]:
        text = f"{b}  {r}" if b and r else (b or r)
        lbody += panel_para(text, sz=1300, indent=bool(b and r))

    rbody = panel_para(cs["right"]["header"], sz=1600, bold=True, color=BLUE)
    for b, r in cs["right"]["items"]:
        text = f"{b}  {r}" if b and r else (b or r)
        rbody += panel_para(text, sz=1300, indent=bool(b and r))

    return slide_wrap([
        title_shape(cs["title"], sz=cs.get("title_sz", 2400)),
        txbox(3, "LeftCol",  1050000, 1300000, 5050000, 5200000, lbody),
        filled_rect(10, "Divider", 6150000, 1100000, 45719, 5400000, "DDDDDD"),
        txbox(5, "RightCol", 7106741, 1300000, 4800000, 5200000, rbody),
    ])


def stacked_xml(cs: dict) -> str:
    """Right-aligned title + two vertically stacked sections."""
    def section_body(sec: dict, sz_header: int = 1600) -> str:
        body = panel_para(sec["header"], sz=sz_header, bold=True, color=BLUE)
        for line in sec["lines"]:
            body += panel_para(line, sz=1400, indent=True)
        return body

    return slide_wrap([
        title_shape(cs["title"], sz=cs.get("title_sz", 3200),
                    x=2360746, y=-135170, cx=8621679, cy=1143000),
        txbox(3, "TopSection",    1473950, 2253594, 6600215, 1231106, section_body(cs["top"])),
        txbox(4, "BottomSection", 1473950, 3724108, 6725344, 1015663, section_body(cs["bottom"])),
    ])


def benefits_xml(cs: dict) -> str:
    """Right-aligned title + section label + left/right panels."""
    label = panel_para(cs["section_label"], sz=2000, bold=True)
    lbody = panel_para(cs["left"]["header"],  sz=2000, bold=True, color=BLUE)
    for line in cs["left"]["lines"]:
        lbody += panel_para(line, sz=1400, indent=True)
    rbody = panel_para(cs["right"]["header"], sz=2000, bold=True, color=BLUE)
    for line in cs["right"]["lines"]:
        rbody += panel_para(line, sz=1400, indent=True)

    return slide_wrap([
        title_shape(cs["title"], sz=cs.get("title_sz", 2800)),
        txbox(3, "SectionLabel", 495310,  1147161, 9000000, 400000,  label),
        txbox(4, "LeftPanel",    495310,  1700000, 5500000, 4800000, lbody),
        txbox(5, "RightPanel",   6253654, 1700000, 5500000, 4800000, rbody),
    ])


def slide_xml(cs: dict) -> str:
    t = cs.get("type", "bullets")
    if t == "twocol":   return twocol_xml(cs)
    if t == "stacked":  return stacked_xml(cs)
    if t == "benefits": return benefits_xml(cs)
    return bullets_xml(cs)


# ── Relationship / presentation XML ──────────────────────────────────────────

COVER_RELS = """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image2.jpeg"/>
</Relationships>"""

CONTENT_RELS = """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>"""


def prs_xml(n: int) -> str:
    refs = "\n".join(
        f'    <p:sldId id="{256+i}" r:id="rId{i+2}"/>' for i in range(n)
    )
    return (f"<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
            f'<p:presentation '
            f'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            f'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
            f'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            f'saveSubsetFonts="1">'
            f'<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
            f'<p:sldIdLst>\n{refs}\n</p:sldIdLst>'
            f'<p:sldSz cx="12192000" cy="6858000" type="custom"/>'
            f'<p:notesSz cx="6858000" cy="9144000"/>'
            f'<p:defaultTextStyle>'
            f'<a:defPPr><a:defRPr lang="th-TH"/></a:defPPr>'
            f'</p:defaultTextStyle>'
            f'</p:presentation>')


def prs_rels(n: int) -> str:
    rels = "\n".join(
        f'  <Relationship Id="rId{i+2}" '
        f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" '
        f'Target="slides/slide{i+1}.xml"/>'
        for i in range(n)
    )
    return (f"<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
            f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'<Relationship Id="rId1" '
            f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" '
            f'Target="slideMasters/slideMaster1.xml"/>\n{rels}\n</Relationships>')


# ── CONTENT — edit this section ───────────────────────────────────────────────
# Replace with your actual presentation content.
# Supported types: "cover", "bullets", "twocol", "stacked", "benefits"

CONTENT_SLIDES = [
    {
        "type": "bullets",
        "title": "Slide Title Here",
        "items": [
            ("Bold Label",   "regular explanation text"),
            ("Another Point", "more detail here"),
            ("",             "sub-bullet plain text"),
        ]
    },
    {
        "type": "twocol",
        "title": "Two Column Slide",
        "left":  {"header": "Left Section",  "items": [("Bold key", "regular text"), ("", "plain item")]},
        "right": {"header": "Right Section", "items": [("Bold key", "regular text"), ("", "plain item")]},
    },
    {
        "type": "stacked",
        "title": "Stacked Sections",
        "top":    {"header": "Section A", "lines": ["Detail one", "Detail two"]},
        "bottom": {"header": "Section B", "lines": ["Detail one", "Detail two"]},
    },
    {
        "type": "benefits",
        "title": "STRATEGIC BENEFITS",
        "section_label": "ESG & Sustainability Impact",
        "left":  {"header": "Environmental", "lines": ["Detail one", "Detail two"]},
        "right": {"header": "Governance",    "lines": ["UN SDG 6 compliance", "ISO 14001"]},
    },
]

# ── Assemble & write ──────────────────────────────────────────────────────────

def main() -> None:
    if not os.path.isfile(TEMPLATE):
        print(f"Error: template not found: {TEMPLATE}")
        return

    slides = (
        [(cover_xml(COVER_TITLE), COVER_RELS)]
        + [(slide_xml(cs), CONTENT_RELS) for cs in CONTENT_SLIDES]
        + [(cover_xml(CLOSING_TITLE), COVER_RELS)]
    )
    n = len(slides)

    with zipfile.ZipFile(TEMPLATE, "r") as zin:
        files = {name: zin.read(name) for name in zin.namelist()}

    # Remove old slides
    for k in list(files):
        if (re.match(r"ppt/slides/slide\d+\.xml$", k) or
                re.match(r"ppt/slides/_rels/slide\d+\.xml\.rels$", k)):
            del files[k]

    # Replace presentation index + rels
    files["ppt/presentation.xml"]            = prs_xml(n).encode()
    files["ppt/_rels/presentation.xml.rels"] = prs_rels(n).encode()

    # Write new slides
    for i, (xml, rels) in enumerate(slides, start=1):
        files[f"ppt/slides/slide{i}.xml"]            = xml.encode()
        files[f"ppt/slides/_rels/slide{i}.xml.rels"] = rels.encode()

    # Update Content_Types
    ct = files["[Content_Types].xml"].decode()
    ct = re.sub(r'\s*<Override PartName="/ppt/slides/slide\d+\.xml"[^/]*/>', "", ct)
    ct = ct.replace("</Types>", "\n".join(
        f'  <Override PartName="/ppt/slides/slide{i}.xml" '
        f'ContentType="application/vnd.openxmlformats-officedocument.'
        f'presentationml.slide+xml"/>'
        for i in range(1, n + 1)) + "\n</Types>")
    files["[Content_Types].xml"] = ct.encode()

    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in files.items():
            zout.writestr(name, data)

    print(f"Saved: {OUTPUT} ({n} slides)")


if __name__ == "__main__":
    main()
