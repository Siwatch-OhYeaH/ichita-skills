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
  1. <w:lang w:bidi="th-TH"/> on every run, style and docDefaults (the root cause:
     generators ship bidi="ar-SA" or none, so Word has no Thai dictionary and no
     Thai word-break points).
  2. Complex-script font slot w:cs set, w:cstheme removed (theme wins over explicit).
  3. <w:bCs/> <w:iCs/> <w:szCs/> mirrored from <w:b/> <w:i/> <w:sz/> — Thai uses the
     complex-script versions; without them Thai loses bold and size.
  4. Justified paragraphs containing Thai -> <w:jc w:val="thaiDistribute"/>.
  5. Text clean-up: NBSP -> space, ZWSP/soft hyphen removed (TH Aeonik has no glyphs),
     decomposed SARA AM (U+0E4D U+0E32) -> U+0E33.
  6. settings.xml themeFontLang bidi -> th-TH.
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

def fix_runs(xml):
    xml = re.sub(r"<w:rPr>(.*?)</w:rPr>", lambda m: "<w:rPr>" + fix_rpr(m.group(1)) + "</w:rPr>", xml, flags=re.S)
    xml = re.sub(r"<w:rPr/>", "<w:rPr>" + fix_rpr("") + "</w:rPr>", xml)
    # runs with no rPr at all
    xml = re.sub(r"(<w:r(?:\s[^>]*)?>)(?!<w:rPr)", lambda m: m.group(1) + "<w:rPr>" + fix_rpr("") + "</w:rPr>", xml)
    return xml

def clean_text(xml):
    def t(m):
        s = m.group(2).replace("\u00A0", " ").replace("\u200B", "").replace("\u00AD", "").replace("\u0E4D\u0E32", "\u0E33")
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

def fix_file(src, dst=None):
    """Fix src in place (dst=None) or write to dst. Import and call this right after doc.save()."""
    import os, tempfile
    if dst is None or os.path.abspath(dst) == os.path.abspath(src):
        fd, tmp = tempfile.mkstemp(suffix=".docx", dir=os.path.dirname(os.path.abspath(src)))
        os.close(fd)
        main(src, tmp)
        os.replace(tmp, src)
        return src
    main(src, dst)
    return dst

def main(src, dst):
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
                    xml = clean_text(xml)
                    xml = fix_paragraphs(xml, resolve, default_style, warnings, item.filename)
                data = xml.encode("utf-8")
            elif item.filename == "word/settings.xml":
                xml = data.decode("utf-8")
                xml = re.sub(r"<w:themeFontLang\b[^>]*/>",
                             lambda m: re.sub(r'\s*w:bidi="[^"]*"', "", m.group(0)).replace("/>", ' w:bidi="th-TH"/>'), xml)
                data = xml.encode("utf-8")
            zout.writestr(item, data)
    for w in warnings:
        print("WARN", w)
    print("Wrote", dst)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    args = [a for a in sys.argv[1:] if a != "--inplace"]
    if "--inplace" in sys.argv:
        fix_file(args[0])
    else:
        main(args[0], args[1] if len(args) > 1 else re.sub(r"\.docx$", "", args[0]) + ".fixed.docx")
