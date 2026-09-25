#!/usr/bin/env python3
"""
fix_thai_docx.py — repair Thai text in a .docx so Word spell-checks it as Thai
and breaks/justifies lines between Thai words instead of stretching letters.

    python fix_thai_docx.py input.docx            # writes input.fixed.docx
    python fix_thai_docx.py input.docx out.docx
    python fix_thai_docx.py input.docx --inplace
    from fix_thai_docx import fix_file; fix_file("out.docx")   # after doc.save()

Standard library only. What it does, in every text part (body, headers, footers,
footnotes, endnotes, comments, numbering) and in styles.xml:
  1. <w:lang w:bidi="th-TH"/> on every run, style and docDefaults (generators ship
     bidi="ar-SA" or none, so Word has no Thai dictionary and no Thai word breaks).
  1a. Runs split at the Thai/Latin boundary, and <w:cs/> on every Thai piece — the
     complex-script flag, which is what Word itself writes on Thai runs. Without it
     Word 16 proofs Thai with the run's Latin language (en-US): measured 2026-09-24 on
     Windows Word, 119 Thai words flagged with bidi="th-TH" alone, 0 with <w:cs/>.
  2. Complex-script font slot w:cs set, w:cstheme removed (theme wins over explicit).
  3. <w:bCs/> <w:iCs/> <w:szCs/> mirrored from <w:b/> <w:i/> <w:sz/> — Thai uses the
     complex-script versions; without them Thai loses bold and size.
  4. Justified paragraphs containing Thai -> <w:jc w:val="thaiDistribute"/>, unless the
     paragraph is mostly Latin: that one keeps Justify (reported).
  5. Text clean-up: ZWSP/soft hyphen removed (TH Aeonik has no glyphs), decomposed
     SARA AM (U+0E4D U+0E32) -> U+0E33. NBSP is KEPT: measured 2026-09-24, Word and
     LibreOffice both hold an NBSP join and the PDF embeds no fallback font for it.
  5a. Glue (glue=True, the default): a no-break space where a line break reads wrong —
     number + unit ("12–15 m³/h", "48–60 นาที"), comparison + number ("< 10"),
     label + number ("Brix 0–1", "ขั้น 4"), title + name ("Mr Siwatch", "คุณ สมชาย");
     and <w:noBreakHyphen/> in a hyphenated Latin word ("High-Value") and for U+2011.
  6. settings.xml themeFontLang bidi -> th-TH, inserted when the file has none (docx-js).
  6b. compatibilityMode 15 when the file declares none — without it Word does not break Thai
     lines between words (measured 2026-09-25). A declared mode below 14 is reported.
  6a. Thai pieces get <w:spacing w:val="0"/> — fonts.md §3, tracking on any Thai run is 0,
     overriding a tracked style (an eyebrow) as well as the run.
  7. Children of every <w:rPr> put back in schema order — Word may ignore an element
     that is out of place, and python-docx callers append bCs/szCs at the end.
Soft line breaks (<w:br/>) inside Thai justified paragraphs are reported — they make
Word stretch the line before them; replace them with real paragraph breaks.
"""
import re, sys, zipfile

FALLBACK_CS_FONT = "TH Aeonik Book"   # CLAUDE.md: Thai documents default to Book 350
THAI = re.compile("[\u0E00-\u0E7F]")
TEXT_PARTS = re.compile(r"word/(document|header\d*|footer\d*|footnotes|endnotes|comments|numbering|styles)\.xml$")

def attr(tag, name):
    m = re.search(r'\s%s="([^"]*)"' % re.escape(name), tag)
    return m.group(1) if m else None

def fix_rpr(inner):
    # rFonts: explicit cs font, no cstheme
    m = re.search(r"<w:rFonts\b[^>]*/>", inner)
    if m:
        tag = re.sub(r'\sw:cstheme="[^"]*"', "", m.group(0))
        if attr(tag, "w:cs") is None:
            cs = attr(tag, "w:ascii") or attr(tag, "w:hAnsi") or FALLBACK_CS_FONT
            tag = tag.replace("<w:rFonts", '<w:rFonts w:cs="%s"' % cs, 1)
        inner = inner.replace(m.group(0), tag, 1)
    else:
        rs = re.match(r"\s*<w:rStyle\b[^>]*/>", inner)
        at = rs.end() if rs else 0
        inner = inner[:at] + '<w:rFonts w:cs="%s"/>' % FALLBACK_CS_FONT + inner[at:]
    # bold / italic / size -> complex-script twins
    for base, twin in (("b", "bCs"), ("i", "iCs")):
        m = re.search(r"<w:%s(\s[^>]*)?/>" % base, inner)
        if m and "<w:%s" % twin not in inner:
            inner = inner.replace(m.group(0), m.group(0) + "<w:%s%s/>" % (twin, m.group(1) or ""), 1)
    m = re.search(r'<w:sz w:val="(\d+)"\s*/>', inner)
    if m and "<w:szCs" not in inner:
        inner = inner.replace(m.group(0), m.group(0) + '<w:szCs w:val="%s"/>' % m.group(1), 1)
    # language
    old = re.search(r"<w:lang\b[^>]*/>", inner)
    val = (attr(old.group(0), "w:val") if old else None)
    ea = (attr(old.group(0), "w:eastAsia") if old else None)
    new = "<w:lang" + (' w:val="%s"' % val if val else "") + (' w:eastAsia="%s"' % ea if ea else "") + ' w:bidi="th-TH"/>'
    if old:
        inner = inner.replace(old.group(0), "", 1)
    tail = re.search(r"<w:(eastAsianLayout|specVanish|oMath)\b", inner)
    at = tail.start() if tail else len(inner)
    return inner[:at] + new + inner[at:]

RPR_ORDER = ("ins del moveFrom moveTo rStyle rFonts b bCs i iCs caps smallCaps strike dstrike outline "
             "shadow emboss imprint noProof snapToGrid vanish webHidden color spacing w kern position sz "
             "szCs highlight u effect bdr shd fitText vertAlign rtl cs em lang eastAsianLayout specVanish "
             "oMath").split()

def children(inner):
    """Top-level elements of an XML fragment, as strings (text between them is dropped)."""
    out, depth, start = [], 0, 0
    for m in re.finditer(r"<(/?)[\w:]+[^>]*?(/?)>", inner):
        if m.group(1):                    # </x>
            depth -= 1
            if depth == 0:
                out.append(inner[start:m.end()])
        elif m.group(2):                  # <x/>
            if depth == 0:
                out.append(m.group(0))
        else:                             # <x>
            if depth == 0:
                start = m.start()
            depth += 1
    return out

def order_rpr(inner):
    kids = children(inner)
    if "".join(kids) != inner:
        return inner                      # not plain elements — leave untouched
    def key(e):
        name = re.match(r"<([\w:]+)", e).group(1)
        local = name.split(":", 1)[1] if name.startswith("w:") else None
        if local == "rPrChange":
            return len(RPR_ORDER) + 1     # always last
        return RPR_ORDER.index(local) if local in RPR_ORDER else len(RPR_ORDER)
    return "".join(sorted(kids, key=key))

# a Thai piece keeps the brackets and closing punctuation that touch it, so a line never
# breaks between "(เฉลี่ย" and ")"
THAI_SEG = re.compile("([(\\[\u201C\u2018\"']*[\u0E00-\u0E7F]+(?:\\s+[\u0E00-\u0E7F]+)*"
                      "[)\\]\u201D\u2019\"'.,:;!?%]*\\s*)")

def split_thai_runs(xml):
    """<w:cs/> on Thai text, which means one run per script."""
    def run(m):
        open_tag, rpr, body = m.group(1), m.group(2) or "", m.group(4)
        if not THAI.search(body):
            return m.group(0)
        if "<w:cs/>" in rpr:                  # already split (an earlier pass): tracking only
            live = re.sub(r"<w:spacing\b[^>]*/>", "", rpr[len("<w:rPr>"):-len("</w:rPr>")])
            return open_tag + "<w:rPr>" + order_rpr(live + '<w:spacing w:val="0"/>') + "</w:rPr>" + body + "</w:r>"
        parts = children(body)
        if "".join(parts) != body:
            return m.group(0)
        live = rpr[len("<w:rPr>"):-len("</w:rPr>")] if rpr else ""
        live = re.sub(r"<w:spacing\b[^>]*/>", "", live)      # fonts.md §3: Thai tracking is 0,
        thai_rpr = "<w:rPr>" + order_rpr(live + '<w:spacing w:val="0"/><w:cs/>') + "</w:rPr>"   # style too
        pieces = []                           # (is_thai, xml) in order
        for part in parts:
            t = re.fullmatch(r"<w:t(?:\s[^>]*)?>(.*)</w:t>", part, re.S)
            if not t or not THAI.search(t.group(1)):
                pieces.append((False, part))
                continue
            for i, seg in enumerate(THAI_SEG.split(t.group(1))):
                if seg:
                    pieces.append((bool(i % 2), '<w:t xml:space="preserve">' + seg + "</w:t>"))
        out, i = [], 0
        while i < len(pieces):                # neighbours of one script share a run
            j = i
            while j < len(pieces) and pieces[j][0] == pieces[i][0]:
                j += 1
            out.append(open_tag + (thai_rpr if pieces[i][0] else rpr) + "".join(x for _, x in pieces[i:j]) + "</w:r>")
            i = j
        return "".join(out)
    # innermost runs only: a run that holds a text box holds runs of its own, and those are
    # reached on their own match
    return re.sub(r"(<w:r(?:\s[^>]*)?>)(" + RPR + r")?((?:(?!<w:r[\s>]).)*?)</w:r>",
                  run, xml, flags=re.S)

# a run's <w:rPr>, stepping over the old-state <w:rPr> inside a tracked <w:rPrChange>
RPR = r"<w:rPr>((?:<w:rPrChange\b.*?</w:rPrChange>|(?!</w:rPr>).)*)</w:rPr>"

def split_change(inner):
    m = re.search(r"<w:rPrChange\b.*?</w:rPrChange>", inner, re.S)
    return (inner[:m.start()] + inner[m.end():], m.group(0)) if m else (inner, "")

def fix_runs(xml):
    def one(m):
        live, change = split_change(m.group(1))
        return "<w:rPr>" + fix_rpr(live) + change + "</w:rPr>"
    xml = re.sub(RPR, one, xml, flags=re.S)
    xml = re.sub(r"<w:rPr/>", "<w:rPr>" + fix_rpr("") + "</w:rPr>", xml)
    # runs with no rPr at all
    xml = re.sub(r"(<w:r(?:\s[^>]*)?>)(?!<w:rPr)", lambda m: m.group(1) + "<w:rPr>" + fix_rpr("") + "</w:rPr>", xml)
    return re.sub(RPR, lambda m: "<w:rPr>" + order_rpr(m.group(1)) + "</w:rPr>", xml, flags=re.S)

NB = "\u00A0"
UNIT = ("m³/h|m³/d|m³|m²|m/s|µm|mm|cm|km|m|kg/t|kg/d|kg/h|kg|mg/L|g/L|g|t/d|t|L/h|mL|L|µS/cm|mS/cm|°C|%|"
        "ppm|ppb|bar|kPa|MPa|Pa|kW|W|rpm|BV/h|BV|min|h|s|นาที|ชม\\.|ชั่วโมง|วัน|เดือน|ปี|ลิตร|ถุง|รอบ|ครั้ง|กก\\.|บาท|เท่า")
GLUE = [
    (re.compile(r"(\d) (?=(?:%s)(?![A-Za-z0-9]))" % UNIT), "\\1" + NB),                    # 12–15 m³/h
    (re.compile(r"([≤≥≈~±×]|&lt;|&gt;) (?=\d)"), "\\1" + NB),                               # < 10
    (re.compile(r"(?<![A-Za-z])(Brix|pH|EC|No\.|Rev\.|Fig\.|ข้อ|ขั้นที่|ขั้น|หน้า|รูปที่) (?=\d)"), "\\1" + NB),
    (re.compile(r"(?<![A-Za-z])(Mr|Mrs|Ms|Dr|Prof)(\.?) (?=[A-Z\u0E00-\u0E7F])"), "\\1\\2" + NB),
    (re.compile("(?<![\u0E00-\u0E7F])(นางสาว|นาย|นาง|ดร\\.|คุณ) (?=[\u0E00-\u0E7F])"), "\\1" + NB),
    (re.compile(r"(?<=[A-Za-z])-(?=[A-Za-z])"), "\u2011"),          # High-Value, starch-sweetener
]

def glue_text(s):
    for rx, rep in GLUE:
        s = rx.sub(rep, s)
    return s

def clean_text(xml, glue=True):
    def t(m):
        s = m.group(2).replace("\u200B", "").replace("\u00AD", "").replace("\u0E4D\u0E32", "\u0E33")
        if glue:
            s = glue_text(s)
        if "\u2011" in s:    # TH Aeonik has no U+2011 glyph; Word's own element draws the hyphen
            return '<w:t xml:space="preserve">' + s.replace("\u2011", '</w:t><w:noBreakHyphen/><w:t xml:space="preserve">') + m.group(3)
        return m.group(1) + s + m.group(3)
    return re.sub(r"(<w:t(?:\s[^>]*)?>)(.*?)(</w:t>)", t, xml, flags=re.S)

def justified_styles(styles_xml):
    base, jc = {}, {}
    for m in re.finditer(r'<w:style\b[^>]*w:type="paragraph"[^>]*>(.*?)</w:style>', styles_xml, re.S):
        sid = attr(m.group(0)[:m.group(0).index(">") + 1], "w:styleId")
        b = re.search(r'<w:basedOn w:val="([^"]*)"', m.group(1))
        j = re.search(r'<w:pPr>.*?<w:jc w:val="([^"]*)"', m.group(1), re.S)
        base[sid] = b.group(1) if b else None
        jc[sid] = j.group(1) if j else None
    dd = re.search(r'<w:pPrDefault>.*?<w:jc w:val="([^"]*)"', styles_xml, re.S)
    def resolve(sid, depth=0):
        if sid is None or depth > 20:
            return dd.group(1) if dd else None
        return jc.get(sid) or resolve(base.get(sid), depth + 1)
    default_para = re.search(r'<w:style\b[^>]*w:type="paragraph"[^>]*w:default="1"[^>]*w:styleId="([^"]*)"', styles_xml) \
        or re.search(r'<w:style\b[^>]*w:default="1"[^>]*w:type="paragraph"[^>]*w:styleId="([^"]*)"', styles_xml)
    return resolve, (default_para.group(1) if default_para else None)

JC_AFTER = re.compile(r"<w:(textDirection|textAlignment|textboxTightWrap|outlineLvl|divId|cnfStyle|rPr|sectPr|pPrChange)\b")

def fix_paragraphs(xml, resolve, default_style, warnings, part):
    def p(m):
        para = m.group(0)
        if "<w:txbxContent" in para:
            return para
        text = "".join(re.findall(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", para, re.S))
        if not THAI.search(text):
            return para
        ppr = re.search(r"<w:pPr>(.*?)</w:pPr>", para, re.S)
        inner = ppr.group(1) if ppr else ""
        direct = re.search(r'<w:jc w:val="([^"]*)"\s*/>', inner)
        sid = re.search(r'<w:pStyle w:val="([^"]*)"', inner)
        eff = direct.group(1) if direct else resolve(sid.group(1) if sid else default_style)
        if eff not in ("both", "distribute", "lowKashida", "mediumKashida", "highKashida", "thaiDistribute"):
            return para
        thai, latin = len(THAI.findall(text)), len(re.findall(r"[A-Za-z]", text))
        if thai < latin and eff != "thaiDistribute":
            # Thai Distributed on a mostly-English line stretches its one Thai word letter by
            # letter (seminar invitation, Word 16, 2026-09-25); with the runs tagged Thai, Justify
            # widens the spaces instead
            warnings.append("%s: mostly-Latin justified paragraph kept as Justify: %s…" % (part, text[:40]))
            return para
        if re.search(r"<w:br\s*/>", para):
            warnings.append("%s: soft line break inside a justified Thai paragraph: %s…" % (part, text[:40]))
        if direct:
            inner = inner.replace(direct.group(0), '<w:jc w:val="thaiDistribute"/>', 1)
        else:
            at = JC_AFTER.search(inner)
            at = at.start() if at else len(inner)
            inner = inner[:at] + '<w:jc w:val="thaiDistribute"/>' + inner[at:]
        if ppr:
            return para.replace(ppr.group(0), "<w:pPr>" + inner + "</w:pPr>", 1)
        return re.sub(r"^(<w:p(?:\s[^>]*)?>)", lambda o: o.group(1) + "<w:pPr>" + inner + "</w:pPr>", para, count=1)
    return re.sub(r"<w:p(?:\s[^>]*)?>.*?</w:p>", p, xml, flags=re.S)

# CT_Settings children that follow themeFontLang, in schema order
AFTER_THEMEFONTLANG = ("clrSchemeMapping doNotIncludeSubdocsInStats doNotAutoCompressPictures forceUpgrade "
                       "captions readModeInkLockDown smartTagType schemaLibrary shapeDefaults "
                       "doNotEmbedSmartTags decimalSymbol listSeparator").split()

AFTER_COMPAT = "docVars rsids mathPr attachedSchema themeFontLang".split() + AFTER_THEMEFONTLANG
MODE = '<w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/>'

def insert_before(xml, names, tag):
    at = re.search(r"<(?:w|m):(?:%s)\b" % "|".join(names), xml)
    if at:
        return xml[:at.start()] + tag + xml[at.start():]
    return xml.replace("</w:settings>", tag + "</w:settings>", 1)

def compat_mode(xml):
    """Declared compatibilityMode, or None. Attribute order varies (docx-js writes w:val first)."""
    for tag in re.findall(r"<w:compatSetting\b[^>]*>", xml):
        if attr(tag, "w:name") == "compatibilityMode" and (attr(tag, "w:val") or "").isdigit():
            return int(attr(tag, "w:val"))
    return None

def fix_settings(xml, warnings=None):
    if re.search(r"<w:themeFontLang\b", xml):
        xml = re.sub(r"<w:themeFontLang\b[^>]*/>",
                     lambda m: re.sub(r'\s*w:bidi="[^"]*"', "", m.group(0)).replace("/>", ' w:bidi="th-TH"/>'), xml)
    else:
        xml = insert_before(xml, AFTER_THEMEFONTLANG, '<w:themeFontLang w:val="en-US" w:bidi="th-TH"/>')
    # No compatibilityMode = Word's oldest layout mode, which does not break Thai lines at
    # dictionary word boundaries: the rest of a Thai run moves down whole and Thai Distributed
    # stretches the line before it letter by letter. Measured 2026-09-25 on the Report
    # template (Word 16): missing -> stretched; 15 -> breaks between words. Mode 14 (the
    # liquid-sugar sheets) also breaks correctly. An older declared mode is only reported.
    mode = compat_mode(xml)
    if mode is None:
        if re.search(r"<w:compat\s*/>", xml):
            xml = re.sub(r"<w:compat\s*/>", "<w:compat>" + MODE + "</w:compat>", xml, count=1)
        elif "<w:compat>" in xml:
            xml = xml.replace("</w:compat>", MODE + "</w:compat>", 1)
        else:
            xml = insert_before(xml, AFTER_COMPAT, "<w:compat>" + MODE + "</w:compat>")
    elif mode < 14 and warnings is not None:
        warnings.append("settings.xml: compatibilityMode %d — Word may not break Thai lines between "
                        "words below 14 (unmeasured); consider 15" % mode)
    return xml

def fix_file(src, dst=None, glue=True):
    """Fix src in place (dst=None) or write to dst. Import and call this right after doc.save()."""
    import os, tempfile
    if dst is None or os.path.abspath(dst) == os.path.abspath(src):
        fd, tmp = tempfile.mkstemp(suffix=".docx", dir=os.path.dirname(os.path.abspath(src)))
        os.close(fd)
        try:
            main(src, tmp, quiet=True, glue=glue)
            os.replace(tmp, src)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
        print("Fixed Thai:", src)
        return src
    main(src, dst, glue=glue)
    return dst

def main(src, dst, quiet=False, glue=True):
    zin = zipfile.ZipFile(src)
    styles = zin.read("word/styles.xml").decode("utf-8") if "word/styles.xml" in zin.namelist() else ""
    resolve, default_style = justified_styles(styles)
    warnings = []
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if TEXT_PARTS.match(item.filename):
                xml = fix_runs(data.decode("utf-8"))
                if not item.filename.endswith(("styles.xml", "numbering.xml")):
                    xml = clean_text(xml, glue)
                    xml = split_thai_runs(xml)
                    xml = fix_paragraphs(xml, resolve, default_style, warnings, item.filename)
                data = xml.encode("utf-8")
            elif item.filename == "word/settings.xml":
                data = fix_settings(data.decode("utf-8"), warnings).encode("utf-8")
            zout.writestr(item, data)
    for w in warnings:
        print("WARN", w)
    if not quiet:
        print("Wrote", dst)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    args = [a for a in sys.argv[1:] if a not in ("--inplace", "--no-glue")]
    glue = "--no-glue" not in sys.argv
    if "--inplace" in sys.argv:
        fix_file(args[0], glue=glue)
    else:
        main(args[0], args[1] if len(args) > 1 else re.sub(r"\.docx$", "", args[0]) + ".fixed.docx", glue=glue)
