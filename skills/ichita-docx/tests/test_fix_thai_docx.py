"""fix_thai_docx: Thai runs carry <w:cs/> and nothing else does; the text survives; it is idempotent.

The acceptance measurement is in Word (word_qc.py). These tests pin the XML the fixer
writes, which is what that measurement depends on."""
import re, sys, zipfile, xml.dom.minidom
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fix_thai_docx as F

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
THAI = re.compile("[฀-๿]")


def body(xml):
    return f'<w:document {W}><w:body>{xml}</w:body></w:document>'


def runs(xml):
    """[(has_cs, text)] for every innermost run."""
    out = []
    for m in re.finditer(r"<w:r(?:\s[^>]*)?>((?:(?!<w:r[\s>]).)*?)</w:r>", xml, re.S):
        text = "".join(re.findall(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", m.group(1), re.S))
        if text:
            out.append(("<w:cs/>" in m.group(1), text))
    return out


def fixed(xml):
    return F.split_thai_runs(F.fix_runs(xml))


def text_of(xml):
    return "".join(re.findall(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", xml, re.S))


def test_mixed_run_is_split_and_only_thai_is_cs():
    src = body('<w:p><w:r><w:rPr><w:b/><w:sz w:val="20"/></w:rPr>'
               '<w:t>การเตรียม Ecosorb / Filter aid และการจัดการ Slurry waste</w:t></w:r></w:p>')
    out = fixed(src)
    xml.dom.minidom.parseString(out)
    assert text_of(out) == text_of(src)
    rs = runs(out)
    assert [t for cs, t in rs if cs] == ["การเตรียม ", "และการจัดการ "]
    assert all(THAI.search(t) for cs, t in rs if cs)
    assert not any(THAI.search(t) for cs, t in rs if not cs)


def test_brackets_stay_with_the_thai():
    out = fixed(body('<w:p><w:r><w:t>Filter aid 5 kg (เฉลี่ย)</w:t></w:r></w:p>'))
    assert runs(out) == [(False, "Filter aid 5 kg "), (True, "(เฉลี่ย)")]


def test_idempotent():
    once = fixed(body('<w:p><w:r><w:t>Liquid Sugar Plant · คิดที่กำลังผลิต 200 t DS/วัน</w:t></w:r></w:p>'))
    assert fixed(once) == once


def test_rpr_children_in_schema_order():
    out = F.fix_runs(body('<w:p><w:r><w:rPr><w:rFonts w:ascii="TH Aeonik"/><w:b/><w:color w:val="263338"/>'
                          '<w:sz w:val="20"/><w:szCs w:val="20"/><w:bCs/></w:rPr><w:t>ไทย</w:t></w:r></w:p>'))
    rpr = re.search(r"<w:rPr>(.*?)</w:rPr>", out).group(1)
    names = re.findall(r"<w:(\w+)", rpr)
    assert names == ["rFonts", "b", "bCs", "color", "sz", "szCs", "lang"]


def test_cs_sits_before_lang():
    out = fixed(body('<w:p><w:r><w:rPr><w:sz w:val="20"/></w:rPr><w:t>ไทย</w:t></w:r></w:p>'))
    rpr = re.search(r"<w:rPr>(.*?)</w:rPr>", out).group(1)
    assert re.findall(r"<w:(\w+)", rpr)[-2:] == ["cs", "lang"]


def test_tab_and_break_keep_their_place():
    src = body('<w:p><w:r><w:t>ข้อ</w:t><w:tab/><w:t>Item</w:t><w:br/><w:t>ไทย</w:t></w:r></w:p>')
    out = fixed(src)
    xml.dom.minidom.parseString(out)
    seq = re.findall(r"<w:(tab|br)/>|<w:t[^>]*>([^<]*)</w:t>", out)
    assert [a or b for a, b in seq] == ["ข้อ", "tab", "Item", "br", "ไทย"]


def test_text_box_runs_are_reached():
    inner = '<w:txbxContent><w:p><w:r><w:t>กล่อง box</w:t></w:r></w:p></w:txbxContent>'
    src = body(f'<w:p><w:r><w:rPr><w:b/></w:rPr><w:pict><v:shape xmlns:v="urn:v"><v:textbox>{inner}'
               '</v:textbox></v:shape></w:pict></w:r></w:p>')
    out = fixed(src)
    xml.dom.minidom.parseString(out.replace('<w:document ', '<w:document xmlns:v="urn:v" ', 1))
    assert (True, "กล่อง ") in runs(out) and (False, "box") in runs(out)


def test_entities_and_hyperlinks():
    src = body('<w:p><w:hyperlink><w:r><w:t>R&amp;D ฝ่ายวิจัย &lt;TH&gt;</w:t></w:r></w:hyperlink></w:p>')
    out = fixed(src)
    xml.dom.minidom.parseString(out)
    assert text_of(out) == text_of(src)
    assert (True, "ฝ่ายวิจัย ") in runs(out)


def test_latin_only_untouched_by_split():
    src = F.fix_runs(body('<w:p><w:r><w:t>English only</w:t></w:r></w:p>'))
    assert F.split_thai_runs(src) == src


def test_whole_file(tmp_path):
    docx = tmp_path / "t.docx"
    with zipfile.ZipFile(docx, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("word/document.xml", body('<w:p><w:r><w:t>ทดสอบ test</w:t></w:r></w:p>'))
        z.writestr("word/styles.xml", f'<w:styles {W}><w:docDefaults><w:rPrDefault><w:rPr>'
                   '<w:lang w:val="en-US" w:bidi="ar-SA"/></w:rPr></w:rPrDefault></w:docDefaults></w:styles>')
        z.writestr("word/settings.xml", f'<w:settings {W}><w:themeFontLang w:val="en-US"/></w:settings>')
    F.fix_file(str(docx))
    z = zipfile.ZipFile(docx)
    doc, sty, st = (z.read(n).decode() for n in ("word/document.xml", "word/styles.xml", "word/settings.xml"))
    assert runs(doc) == [(True, "ทดสอบ "), (False, "test")]
    assert 'w:bidi="th-TH"' in sty and "ar-SA" not in sty
    assert 'w:bidi="th-TH"' in st
    assert sorted(p.name for p in tmp_path.iterdir()) == ["t.docx"]      # no temp file left


def test_tracked_change_stays_well_formed():
    src = body('<w:p><w:r><w:rPr><w:b/><w:rPrChange w:id="1" w:author="a"><w:rPr><w:i/></w:rPr>'
               '</w:rPrChange></w:rPr><w:t>แก้ไข edit</w:t></w:r></w:p>')
    out = fixed(src)
    xml.dom.minidom.parseString(out)
    assert text_of(out) == text_of(src)
    assert (True, "แก้ไข ") in runs(out) and (False, "edit") in runs(out)
    assert out.count("<w:rPrChange") == 2            # carried onto both pieces, untouched
    assert "<w:i/></w:rPr></w:rPrChange>" in out


def test_glue_binds_what_must_not_break_and_nothing_else():
    g = F.glue_text
    nb = " "
    assert g("NaOH 12–15 m³/h") == f"NaOH 12–15{nb}m³/h"
    assert g("48–60 นาที") == f"48–60{nb}นาที"
    assert g("EC &lt; 10 µS/cm") == f"EC &lt;{nb}10{nb}µS/cm"
    assert g("(Brix 0–1)") == f"(Brix{nb}0–1)"
    assert g("Mr Siwatch") == f"Mr{nb}Siwatch"
    for keep in ("คุณภาพ ดี", "5 more items", "at 4 hours", "set point 4 and", "50%"):
        assert g(keep) == keep


def test_nbsp_is_kept():
    out = F.clean_text(body("<w:p><w:r><w:t>10 µS/cm</w:t></w:r></w:p>"))
    assert "10 µS/cm" in out


def test_no_glue_leaves_text_alone():
    out = F.clean_text(body("<w:p><w:r><w:t>12 m³/h</w:t></w:r></w:p>"), glue=False)
    assert "12 m³/h" in out


def test_thai_tracking_is_zero_even_under_a_tracked_style():
    out = fixed(body('<w:p><w:r><w:rPr><w:caps/><w:spacing w:val="19"/></w:rPr><w:t>EYEBROW ป้าย</w:t></w:r></w:p>'))
    rs = re.findall(r"<w:r>(<w:rPr>.*?</w:rPr>)<w:t[^>]*>([^<]*)</w:t>", out)
    thai = [r for r, t in rs if THAI.search(t)][0]
    latin = [r for r, t in rs if not THAI.search(t)][0]
    assert '<w:spacing w:val="0"/>' in thai and 'w:val="19"' not in thai
    assert '<w:spacing w:val="19"/>' in latin
    assert re.findall(r"<w:(\w+)", thai)[1:] == ["rFonts", "caps", "spacing", "cs", "lang"]


def test_theme_font_lang_inserted_in_schema_place():
    assert F.fix_settings(f'<w:settings {W}><w:compat/><w:rsids/></w:settings>').endswith(
        '<w:rsids/><w:themeFontLang w:val="en-US" w:bidi="th-TH"/></w:settings>')
    assert "compatibilityMode" in F.fix_settings(f'<w:settings {W}><w:compat/><w:rsids/></w:settings>')
    out = F.fix_settings(f'<w:settings {W}><w:compat/><w:clrSchemeMapping w:bg1="light1"/></w:settings>')
    assert out.index("themeFontLang") < out.index("clrSchemeMapping")
    assert 'w:bidi="th-TH"' in F.fix_settings(f'<w:settings {W}><w:themeFontLang w:val="en-US" w:bidi="ar-SA"/></w:settings>')


def test_earlier_pass_gets_thai_tracking():
    old = body('<w:p><w:r><w:rPr><w:spacing w:val="19"/><w:cs/><w:lang w:bidi="th-TH"/></w:rPr><w:t>ไทย</w:t></w:r></w:p>')
    out = F.split_thai_runs(old)
    assert '<w:spacing w:val="0"/>' in out and 'w:val="19"' not in out
    assert F.split_thai_runs(out) == out


def test_compat_mode_added_when_missing_and_kept_when_set():
    out = F.fix_settings(f'<w:settings {W}><w:defaultTabStop w:val="720"/></w:settings>')
    assert out.index("<w:compat>") < out.index("<w:themeFontLang")
    assert 'w:name="compatibilityMode"' in out and 'w:val="15"' in out
    kept = F.fix_settings(f'<w:settings {W}><w:compat><w:compatSetting w:name="compatibilityMode" '
                          'w:uri="http://schemas.microsoft.com/office/word" w:val="14"/></w:compat></w:settings>')
    assert kept.count("compatibilityMode") == 1 and 'w:val="14"' in kept
    warn = []
    F.fix_settings(f'<w:settings {W}><w:compat><w:compatSetting w:name="compatibilityMode" '
                   'w:uri="http://schemas.microsoft.com/office/word" w:val="11"/></w:compat></w:settings>', warn)
    assert warn and "11" in warn[0]


def test_compat_mode_any_attribute_order():
    docxjs = f'<w:settings {W}><w:compat><w:compatSetting w:val="15" w:name="compatibilityMode" w:uri="u"/></w:compat></w:settings>'
    assert F.compat_mode(docxjs) == 15
    assert F.fix_settings(docxjs).count("compatibilityMode") == 1


def test_hyphenated_latin_gets_no_break_hyphen():
    out = F.split_thai_runs(F.clean_text(F.fix_runs(body('<w:p><w:r><w:t>High-Value ผลิตภัณฑ์ 12-15</w:t></w:r></w:p>'))))
    xml.dom.minidom.parseString(out)
    assert "High</w:t><w:noBreakHyphen/><w:t" in out
    assert "12-15" in out                      # a range keeps its plain hyphen


def test_mostly_latin_justified_paragraph_keeps_justify():
    src = body('<w:p><w:pPr><w:jc w:val="both"/></w:pPr><w:r><w:t>Under the concept ภายใต้แนวคิด of the long English sentence</w:t></w:r></w:p>')
    warn = []
    out = F.fix_paragraphs(src, lambda s: None, None, warn, "doc")
    assert '<w:jc w:val="both"/>' in out and warn
    th = body('<w:p><w:pPr><w:jc w:val="both"/></w:pPr><w:r><w:t>ข้อความภาษาไทยยาวมาก with a word</w:t></w:r></w:p>')
    assert "thaiDistribute" in F.fix_paragraphs(th, lambda s: None, None, [], "doc")
