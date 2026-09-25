# Thai in Word (.docx) — generation rules

## The symptom
Every Thai word underlined red, and justified lines stretched letter-by-letter
(`ใ น โ อ ก า ส`) while Latin is fine.

## The cause
The characters are correct. The run is not **marked as Thai**. python-docx, docx.js and most
generators ship `<w:lang w:val="en-US" w:bidi="ar-SA"/>` (or nothing), and no `<w:cs/>`.
Word needs both: `<w:cs/>` on the run says "this is complex-script text", and `w:bidi`
names that language. Without `<w:cs/>`, Word 16 proofs the Thai in the run's *Latin*
language — measured 2026-09-24 on Windows Word: 119 Thai words flagged with
`w:bidi="th-TH"` on every run, 0 once the Thai runs also carried `<w:cs/>`.
Result:
- **Red underline** — no Thai dictionary is applied.
- **Stretched letters** — Thai has no spaces between words; Word finds word boundaries
  only when the run is tagged Thai. Untagged, a whole Thai sentence is one unbreakable
  "word", so the line before it is left short and `Justify` spreads the gap across letters.

## Required on every Thai-containing .docx

0. **Complex-script flag** — `<w:cs/>` on every run of Thai text, and only on Thai: split a
   mixed run at the Thai/Latin boundary (Word itself writes `การเตรียม ` and `Ecosorb ` as two
   runs). `<w:cs/>` on a Latin run would proof it as Thai. Place it after `szCs` and before `lang`.
1. **Language** — docDefaults *and* every run:
   `<w:lang w:val="en-US" w:bidi="th-TH"/>`; settings: `<w:themeFontLang w:val="en-US" w:bidi="th-TH"/>`.
2. **Complex-script font slot** — `<w:rFonts w:ascii="TH Aeonik Book" w:hAnsi="TH Aeonik Book" w:cs="TH Aeonik Book"/>`.
   Never `w:cstheme` (theme overrides the explicit font).
3. **Complex-script twins** — `<w:szCs>` = `<w:sz>`; `<w:bCs/>` with every `<w:b/>`; `<w:iCs/>` with `<w:i/>`.
   Without them Thai ignores size and bold.
4. **Alignment** — justified Thai paragraphs use `<w:jc w:val="thaiDistribute"/>` (Word: *Thai Distributed*, Ctrl+Shift+J), never `both` — except a paragraph that is mostly English: there Thai Distributed stretches the one Thai word letter by letter, so it keeps `both` (seminar invitation, Word 16, 2026-09-25). Left-aligned is also fine.
5. **Line spacing** — `w:lineRule="auto"` (Multiple). Word's Single is already TH Aeonik's 1.536 em
   box, so any Multiple ≥ 1.0 clears the marks; the 1.75 em Thai body is Multiple 1.14 (`w:line="273"`).
   Never *Exactly* below 1.536 × the size. (PowerPoint is different: fixed 1.2 em, so Thai there
   needs Multiple ≥ 1.3.)
6. **Order** — children of `<w:rPr>` in schema order (`rFonts b bCs i iCs … color … sz szCs … cs lang`);
   an element appended out of place may be ignored.
7. **Text** — one paragraph per paragraph: no `<w:br/>` inside running Thai; no ZWSP or soft
   hyphen (TH Aeonik has no glyphs); no manual spaces to fake word breaks.
8. **Tracking** — `<w:spacing w:val="0"/>` on every Thai run, overriding a tracked style
   (`fonts.md` §3: letter-spacing on Thai separates words, not letters).
9. **Compatibility mode** — `settings.xml` declares `compatibilityMode` 15 (14 also works).
   With none, Word uses its oldest layout and does not break Thai lines between words: the
   rest of a Thai run drops to the next line whole and *Thai Distributed* stretches the line
   before it letter by letter. Measured 2026-09-25 on `ICHITA-Report-Template.docx`, which
   shipped that way until then.

## Line breaks — what the reader sees

Word breaks Thai at its dictionary's word boundaries and Latin at spaces, hyphens and after an
en dash. Each of these reads wrong; each has a fix that survives a re-layout:

| Break | Fix |
|---|---|
| number from unit `12–15 / m³/h`, `< / 10`, `Brix / 0–1`, title from name `Mr / Siwatch` | **no-break space U+00A0** — the fixer adds it (glue). TH Aeonik has no NBSP glyph, yet Word and LibreOffice both hold the join and the PDF embeds no fallback font (measured 2026-09-24) |
| at a hyphen `High- / Value` | `<w:noBreakHyphen/>` — the fixer puts it in every letter-hyphen-letter word and for U+2011 (TH Aeonik has no U+2011 glyph); NBSP does not stop it. Measured 2026-09-25: Word moves `High-Value` down whole, hyphen drawn |
| after an en dash `12– / 15` | nothing prevents it — widen the column, or shorten the text |
| a name wider than its cell, NBSP-joined | breaks mid-word — seminar agenda build, 2026-09-24. Name, role, company each on their own line |
| inside a Thai phrase `ให้เข้า / กัน`, `ผู้ / ซื้อ` | a paragraph break of your own at the phrase boundary (`\n` → new paragraph in the cell); never NBSP, never ZWSP |
| one word alone on the last line | break the line yourself one phrase earlier |

LibreOffice uses its own Thai dictionary, so its breaks differ from Word's (`(เฉลี่ย / )` only
there). A PDF made by LibreOffice needs its own read.

## QC — before anyone says "done"

```bash
python3 skills/ichita-docx/scripts/word_qc.py FILE.docx --pdf FILE.pdf --png DIR
```

Word (from WSL, hidden, alerts off): pages (`--pages N` makes any other count a FAIL) and
every spelling flag, Thai and Latin listed; tables wider than the text block are reported. On a
fixed file a Thai flag is a word Word does not know or a misspelling (เรซิ่น → เรซิน) — a
person decides. Then the delivery PDF (LibreOffice: brand fonts, Thai text layer intact —
checked), a line check on both layouts, and page images of both. **Read every image, every
line**: Thai split mid-word is not detectable by script. Never Save as PDF from Word
(Calibri), and never deliver Word's Print to PDF — its Thai text layer drops tone marks and ำ
(measured 2026-09-24: ้ 76 → 47, ำ 25 → 0).

## python-docx

Whatever the generator, finish with `fix_thai_docx.py` — it does 0 (run splitting), which the
snippets below do not:

```python
doc.save(OUT)
from fix_thai_docx import fix_file; fix_file(OUT)   # skills/ichita-docx/scripts on sys.path
```

```python
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

FONT = "TH Aeonik Book"

def thai_rpr(rPr, size_pt=None, bold=False):
    f = rPr.find(qn("w:rFonts"))
    if f is None: f = OxmlElement("w:rFonts"); rPr.insert(0, f)
    for k in ("ascii", "hAnsi", "cs", "eastAsia"): f.set(qn("w:" + k), FONT)
    for k in ("asciiTheme", "hAnsiTheme", "cstheme", "eastAsiaTheme"): f.attrib.pop(qn("w:" + k), None)
    if bold:
        for t in ("w:b", "w:bCs"): rPr.append(OxmlElement(t))
    if size_pt:
        for t in ("w:sz", "w:szCs"):
            e = OxmlElement(t); e.set(qn("w:val"), str(int(size_pt * 2))); rPr.append(e)
    for old in rPr.findall(qn("w:lang")): rPr.remove(old)
    lang = OxmlElement("w:lang"); lang.set(qn("w:val"), "en-US"); lang.set(qn("w:bidi"), "th-TH"); rPr.append(lang)

doc = Document()
thai_rpr(doc.styles.element.find(qn("w:docDefaults")).find(qn("w:rPrDefault")).find(qn("w:rPr")), 11)
for s in doc.styles:                       # headings etc. carry their own theme fonts
    if s.element.rPr is not None: thai_rpr(s.element.rPr)
tfl = doc.settings.element.find(qn("w:themeFontLang"))
if tfl is not None: tfl.set(qn("w:bidi"), "th-TH")

p = doc.add_paragraph()
p.paragraph_format.alignment = None
jc = OxmlElement("w:jc"); jc.set(qn("w:val"), "thaiDistribute"); p._p.get_or_add_pPr().append(jc)
r = p.add_run("บริษัท อิชิตะ จำกัด มีความยินดี…"); thai_rpr(r._r.get_or_add_rPr())
```

## docx (JavaScript)

```js
const run = { font: { ascii: "TH Aeonik Book", hAnsi: "TH Aeonik Book", cs: "TH Aeonik Book" },
              language: { value: "en-US", bidirectional: "th-TH" } };
new Document({
  styles: { default: { document: { run: { ...run, size: 22, sizeComplexScript: 22 } } } },
  sections: [{ children: [ new Paragraph({ alignment: AlignmentType.THAI_DISTRIBUTE,
    children: [ new TextRun({ ...run, text: "…", bold: true, boldComplexScript: true }) ] }) ] }]
});
```

## Already have a broken file?

- **One click in Word:** import `office/FixThai.bas` once (Alt+F11 → File → Import File, into *Normal*), add the `FixThai` macro to the Quick Access Toolbar. It does what "paste as plain text" does — resets the language tag to Thai — but keeps formatting and fixes alignment too.
- **Script:** `python office/fix_thai_docx.py letter.docx` → `letter.fixed.docx` (applies 0–4, 6–9 and the glue).
- **By hand in Word:** Ctrl+A → Review → Language → Set Proofing Language → **Thai** → OK;
  then Home → **Thai Distributed** (Ctrl+Shift+J). Replace any Shift+Enter inside paragraphs with Enter.
- If Thai is still flagged after tagging, install the Thai proofing tools:
  File → Options → Language → add **Thai**.

Best route: start from `ICHITA-Report-Template.docx` — it already carries all of the above.
