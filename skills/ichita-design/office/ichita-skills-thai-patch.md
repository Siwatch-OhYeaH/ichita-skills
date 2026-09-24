# Patch for `Siwatch-OhYeaH/ichita-skills` — Thai-safe .docx on every export

Why: the generators tag *some* Thai runs, but they still justify with `both`, and they
don't cover every run, style, header, table cell or `add_break()`. Any .docx made
outside them (Claude chat / Claude Code using the base `docx` skill with docx.js) has no
Thai tag at all. Result: red underlines and letters stretched apart.

The fix is one post-processor run on **every** .docx after it is saved, whatever made it.

## 1. Add the module
Copy `office/fix_thai_docx.py` from this design system to
`skills/ichita-docx/scripts/fix_thai_docx.py` (standard library only, no new dependency).

## 2. Call it after every save (3 one-line edits)

`skills/ichita-docx/scripts/md_to_docx.py` (~line 1253),
`skills/ichita-docx/scripts/html_to_docx.py` (~line 1050),
`skills/ichita-docx/scripts/rebrand_docx.py` (~line 859):

```python
    doc.save(output_path)            # (dst_doc.save in rebrand_docx.py)
    from fix_thai_docx import fix_file; fix_file(output_path)
```

## 3. Stop justifying Thai with `both`
Anywhere a paragraph gets `WD_ALIGN_PARAGRAPH.JUSTIFY`, the fixer converts it to
`thaiDistribute` when the paragraph has Thai. No code change needed, but don't add
`add_break()` inside Thai paragraphs (html_to_docx.py line 741 does this for `<br>`; the
fixer warns when it finds one).

## 4. Make it mandatory for Claude — add to `skills/ichita-docx/SKILL.md`, top of file

```markdown
## Thai — mandatory final step for EVERY .docx

Whatever produced the file (these scripts, the base docx skill, docx.js, python-docx,
LibreOffice), finish with:

    python skills/ichita-docx/scripts/fix_thai_docx.py OUTPUT.docx --inplace

Without it Word underlines every Thai word red and stretches justified lines letter by
letter (runs are tagged ar-SA, so Word has no Thai dictionary or word breaks).
Never hand over a .docx that has not been through it.
```

Put the same paragraph in `skills/ichita-design/SKILL.md` and the plugin's top-level
`CLAUDE.md` so Claude Code picks it up even when it doesn't use `ichita-docx`.

## 5. Claude chat (claude.ai)
Chat doesn't see the repo. Add this to the Project instructions (or personal preferences):

> For any Word document containing Thai: every run gets `<w:lang w:val="en-US" w:bidi="th-TH"/>`,
> font `w:cs="TH Aeonik Book"` (no `w:cstheme`), `szCs`/`bCs` mirroring `sz`/`b`, justified
> paragraphs `thaiDistribute`, no line breaks inside Thai paragraphs. In docx.js:
> `language: { value: "en-US", bidirectional: "th-TH" }`, `font: { cs: "TH Aeonik Book" }`,
> `sizeComplexScript`, `boldComplexScript`, `AlignmentType.THAI_DISTRIBUTE`.
> Upload `fix_thai_docx.py` to the project and run it on the file before giving it to me.
