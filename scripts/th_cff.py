#!/usr/bin/env python3
"""Swap a merged font's `glyf` outlines back to CFF, keeping the Latin verbatim.

Shared by build_th_aeonik.py and build_th_slussen.py. It lives here rather than
in each builder because four of the six defects in the 2026-08-01 TH-Slussen
post-mortem were character-for-character copies of TH-Aeonik's, and the one
genuinely new defect was a fix that had simply not been copied along with them.

WHY CFF AT ALL — the 2026-08-02 decision to ship `glyf` is reversed here.
Windows rasterises CFF and TrueType through different engines, so a merged font
in a different format from its Latin source cannot render that Latin identically
no matter how exact the outlines are. Measured 2026-08-04 in DirectWrite, the
renderer Word 2016+ and PowerPoint use, at 11 pt with identical outlines and
identical advances:

    Aeonik      .otf/CFF    stems 2,1 px   ink 11,056
    TH Aeonik   .ttf/glyf   stems 1,1 px   ink  9,310   -15.8%
    Slussen     .otf/CFF    stems 2,2 px   ink 12,485
    TH Slussen  .ttf/glyf   stems 2,2 px   ink  9,940   -20.4%

Siwatch reported it as "TH Aeonik is slightly thinner than Aeonik, especially
Regular". `scripts/win_latin_parity.py` is the acceptance test; nothing on Linux
can see this defect.

WHY THE LATIN IS TAKEN WHOLESALE. `convert_to_cff` does not redraw Latin
outlines — it takes the Latin source's own `CFF ` table and appends only the Thai
to it. That preserves three things a redraw would lose:

  * the charstrings themselves, so the cu2qu cubic->quadratic approximation the
    `glyf` build baked into every Latin glyph is gone (measured: 0 of 656 Aeonik
    Latin outlines differ from the source, against 656 of 656 for a redraw);
  * the Private dict's **BlueValues**, the alignment zones the CFF rasteriser
    uses to snap stems and suppress overshoot at text sizes;
  * **hint operators inside the charstrings** — Slussen carries 2712 of them
    across 1068 glyphs, which the format flip discarded outright. Aeonik carries
    zero, so it never had anything to lose there.

Thai is converted quadratic -> cubic, which is exact: every quadratic Bezier has
an exact cubic form. This is the favourable direction. The old build's
cubic -> quadratic was the approximate one.
"""
from __future__ import annotations

from fontTools.misc.psCharStrings import T2WidthExtractor
from fontTools.pens.t2CharStringPen import T2CharStringPen

# Tables that only mean something for a TrueType outline. `gasp` in particular is
# the grid-fitting/antialiasing hint table: Bai ships one, neither Latin source
# does, and it is meaningless once the outlines are CFF.
_TRUETYPE_ONLY = ("glyf", "loca", "gasp", "cvt ", "fpgm", "prep")


def convert_to_cff(font, latin_cff, thai_names, label="7", kind="Thai"):
    """Replace `font`'s `glyf` outlines with CFF, in place.

    font        the merged font, still in `glyf` (the intermediate working format
                every other pipeline step is written against).
    latin_cff   a PRISTINE `CFF ` table read from the Latin source before the
                merge touched anything. Read it from the file a second time
                rather than deep-copying the working font's, so no mutation in
                the pipeline can reach it.
    thai_names  the set of glyph names the Thai copy wrote.

    `thai_names` must be passed explicitly and cannot be inferred from "is this
    name absent from the Latin CFF". Aeonik already owns `uni0E3F`, the baht
    sign, so treating every name the Latin CFF already has as Latin left
    Aeonik's baht charstring standing against Bai's advance — a 638-vs-622 width
    disagreement, which is precisely the defect this format costs us.
    """
    cff = latin_cff.cff
    top = cff[cff.fontNames[0]]
    charstrings = top.CharStrings
    private = top.Private

    glyph_set = font.getGlyphSet()
    hmtx = font["hmtx"]
    order = font.getGlyphOrder()

    appended = reused = overridden = 0
    for name in order:
        if name in charstrings and name not in thai_names:
            reused += 1
            continue

        advance = hmtx.metrics[name][0]
        # A T2 charstring encodes its width operand RELATIVE to nominalWidthX,
        # and T2CharStringPen emits whatever number it is handed, verbatim.
        # Handing it the raw advance is silently wrong: the width then reads back
        # as nominalWidthX + advance, which is how uni0E01 came out at 1146
        # against an hmtx advance of 568. Taking the width from `hmtx` here is
        # also what makes the two agree by construction rather than by luck.
        # roundTolerance=0.5 -> otRound, i.e. integer coordinates. NOT 0: in
        # fontTools `roundFunc(0)` returns `noRound`, which keeps floats — the
        # opposite of what "zero tolerance" reads like. That left charstrings
        # carrying values such as 95.66666667 (a quad control point at an exact
        # third), encoded as 16.16 fixed point. Integers are what the source glyf
        # coordinates already are and what the Latin charstrings beside them use.
        pen = T2CharStringPen(advance - private.nominalWidthX, glyph_set,
                              roundTolerance=0.5)
        glyph_set[name].draw(pen)
        charstring = pen.getCharString(private=private,
                                       globalSubrs=cff.GlobalSubrs)
        if name in charstrings:
            charstrings[name] = charstring
            overridden += 1
        else:
            charstrings.charStringsIndex.append(charstring)
            charstrings.charStrings[name] = len(charstrings.charStringsIndex) - 1
            appended += 1

    # The charset is the CFF's own glyph-name list and must match the font's
    # glyph order exactly, or every name shifts against its outline.
    top.charset = list(order)

    font["CFF "] = latin_cff
    for tag in _TRUETYPE_ONLY:
        if tag in font:
            del font[tag]

    font.sfntVersion = "OTTO"
    font["maxp"].tableVersion = 0x00005000     # 0.5 — CFF has no glyf maxima
    # post 3.0 stores no glyph names; a CFF font takes them from the charset,
    # which is what both Latin sources ship. The `glyf` stage needs 2.0 because
    # `glyf` has no such fallback and every name would read glyph00001.
    font["post"].formatType = 3.0

    # The CFF carries its own copy of the font's identity and arrived here still
    # naming the Latin source. apply_metadata() cannot do this: it runs before
    # this step, when the font has no CFF table at all.
    def _name(nid, fallback):
        rec = font["name"].getName(nid, 3, 1, 0x0409)
        return rec.toUnicode() if rec else fallback

    ps_name = _name(6, cff.fontNames[0])
    cff.fontNames[0] = ps_name
    for attr, nid in (("FullName", 4), ("FamilyName", 1), ("Weight", 17)):
        if hasattr(top, attr):
            setattr(top, attr, _name(nid, getattr(top, attr)))

    extra = f", {overridden} overridden" if overridden else ""
    print(f"     [{label}] glyf -> CFF: {reused} Latin charstrings verbatim, "
          f"{appended} {kind} appended (quad -> cubic, exact){extra} | "
          f"CFF fontName {ps_name}")


def assert_advance_single_source(font, label="7b"):
    """Every glyph's charstring width must equal its `hmtx` advance.

    CFF can state an advance twice and the two can disagree. Microsoft Print to
    PDF builds the PDF /W array from the charstring rather than from `hmtx`, so a
    disagreement renders correctly in Word and shreds the printed PDF: Thai
    combining marks carry a zero `hmtx` advance, and given a real one in /W every
    tone mark detaches from its consonant and each run overruns the next. That is
    the 2026-08-01 defect which moved this family to `glyf` in the first place.

    `glyf` made the divergence unrepresentable. CFF makes it representable again,
    so it is asserted instead. Verified to FAIL on a font whose `uni0E48` was
    given a 500-unit `hmtx` advance against its zero-width charstring.
    """
    cff = font["CFF "].cff
    top = cff[cff.fontNames[0]]
    charstrings = top.CharStrings
    hmtx = font["hmtx"]

    bad = []
    for name in font.getGlyphOrder():
        charstring = charstrings[name]
        # T2WidthExtractor's first argument is the LOCAL SUBRS index, not the
        # charstrings index. Passing charstrings made `callsubr` index into the
        # wrong table and execute arbitrary glyph programs — which underflowed the
        # operand stack on Slussen (357 global subrs) and, worse, silently PASSED
        # on Aeonik, because the extractor usually satisfies gotWidth before it
        # ever reaches a subroutine call. Take the private dict from the charstring
        # itself so a CID-keyed font with an FDArray resolves its own subrs.
        private = charstring.private or top.Private
        subrs = getattr(private, "Subrs", [])
        extractor = T2WidthExtractor(subrs, cff.GlobalSubrs,
                                     private.nominalWidthX,
                                     private.defaultWidthX)
        extractor.execute(charstring)
        width = extractor.width if extractor.gotWidth else private.defaultWidthX
        if width != hmtx.metrics[name][0]:
            bad.append((name, width, hmtx.metrics[name][0]))

    if bad:
        detail = ", ".join(f"{n} cs={w} hmtx={a}" for n, w, a in bad[:6])
        raise SystemExit(
            f"     !! {len(bad)} glyph(s) state two different advances — the "
            f"printed-PDF defect is back: {detail}")
    print(f"     [{label}] advance single-source: {len(font.getGlyphOrder())} "
          f"glyphs, charstring width == hmtx everywhere")
