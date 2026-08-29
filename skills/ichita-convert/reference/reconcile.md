# Reconcile — getting a Word edit back into the record

The workflow: we emit a branded DOCX, a colleague edits it in Word because the
template is already there, and they may print and deliver straight from Word.
Markdown is still the record — but only if their edits come back.

```bash
python3 scripts/convert.py reconcile EDITED.docx CURRENT.md \
    [--accept theirs|ours|interactive]
```

**The model is Word's own: show the difference and let the human decide.**
Nothing is overwritten silently. The failure mode of a silent merge is losing
an edit nobody knew about until the client asks why it is missing.

---

## The sidecar

`convert.py` writes `<name>.docx.ichita-convert.json` beside every DOCX it
emits, at the moment the two files agree.

```json
{
  "tool_version": 1,
  "timestamp": "2026-08-06T01:00:00+00:00",
  "md":   { "path": "proposal.md",   "sha256": "…" },
  "docx": { "path": "proposal.docx", "sha256": "…" },
  "font_mode": "auto",
  "base_md_gz_b64": "…"
}
```

`base_md_gz_b64` is a gzipped copy of the Markdown as it was when the DOCX was
written — the **merge base**. Without it a three-way merge is impossible and
the best this tool could do is a two-way diff, which cannot tell an edit from a
revert.

**What is deliberately not in there: any model of the DOCX's formatting.** A
formatting-delta sidecar would be a second schema of the brand's styling, kept
in step with both the Markdown and the emitter, and the first time it drifted
it would produce a confidently-wrong restore. Provenance and a snapshot cannot
drift; a model of the styling can.

Keep the sidecar next to the DOCX. If it is lost, reconcile still runs but says
so and falls back to a labelled two-way diff.

---

## The three cases

The DOCX is always read with `--track-changes=all`, so a tracked-but-unaccepted
edit is visible here rather than silently dropped.

### Nothing changed

```
proposal.docx matches the Markdown it was made from. Nothing to reconcile.
```

### Fast-forward — the record has not moved

The Word edits are the only change, so there is nothing to conflict with. The
diff is printed and the record is written.

```
Fast-forward: record.md is unchanged since edited.docx was emitted.
  @@ -45,5 +45,5 @@
  -Pricing is ex-works Chonburi. Payment 30/60/10 … Validity 60 days …
  +Pricing is ex-works Chonburi. Payment 40/50/10 … Validity 90 days …
  wrote record.md (2 changed line(s))
```

`--accept ours` discards the Word edits instead.

### Both moved

Both diffs are printed against the base, the conflicting hunks are counted, and
**nothing is written** without `--accept`.

```
Both sides changed since edited.docx was emitted.
--- what changed in the Markdown record (record.md) ---
  -| Recovery | 85 | 82 | % |
  +| Recovery | 87 | 82 | % |
  -… Validity 60 days …
  +… Validity 45 days …
--- what changed in Word (edited.docx) ---
  -… Payment 30/60/10 … Validity 60 days …
  +… Payment 40/50/10 … Validity 90 days …

1 conflicting hunk(s).
Nothing written. Choose with --accept theirs | ours | interactive.
```

| `--accept` | Effect |
|---|---|
| `theirs` | take the Word version wholesale |
| `ours` | keep the Markdown, discard the Word edits |
| `interactive` | write the three-way merge with `<<<<<<<` / `>>>>>>>` markers |

`interactive` keeps every non-conflicting change from both sides — in the
example above the `Recovery 87` edit survives untouched and only the commercial
terms are marked. Resolve the markers by hand.

Exit code is `1` when there is an unresolved difference and `0` when the record
is up to date or was written.

---

## Wrapping is normalised before comparing

A human writes Markdown wrapped at 90 columns; every inbound conversion emits
it unwrapped. Diffed as-is, **one changed word reports the whole document as
rewritten** — the first version of this printed 19 changed lines for a
two-word edit, and the actual change was invisible in the noise.

Both sides are unwrapped before diffing and merging, so the comparison is on
content. Whether the record *moved* is still decided by hashing the raw bytes,
because that is a fact about the file rather than about its wrapping.

Consequence: a merged file is written unwrapped. That is the tool's canonical
form.

---

## What this does not do

- **It does not preserve formatting a human applied in Word.** If they bolded a
  cell or changed a colour, that lives in the DOCX and dies in the conversion.
  Markdown holds structure and text. Formatting is the brand's job, applied at
  render time — that is the point of the separation.
- **It does not merge images.** `--extract-media` pulls them out beside the
  Markdown, but a replaced image will not be noticed as a change.
- **It cannot tell a rename from a delete-plus-insert.** Line-wise merge, the
  same as git's.
