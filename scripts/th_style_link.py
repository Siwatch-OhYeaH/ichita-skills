#!/usr/bin/env python3
"""
TH Aeonik's shipped family structure — the single authority on face naming.

WHY THIS FILE EXISTS
--------------------
Until 2026-08-06 TH Aeonik inherited CoType's family layout: one RIBBI family
(`TH Aeonik`) plus five weights that each took their own nameID1 with only
Regular and Italic. Five of the six families in Word's dropdown therefore had no
bold member, so Ctrl+B on `TH Aeonik Light` made Word DOUBLE-STRIKE the outline.

Synthetic bold is the worst thing that can happen to this typeface. It spends
counter aperture, and below ~47 units a Thai counter fills under any rasteriser
(THAI-LATIN-FONT-ENGINEERING.md §4). The generators were never exposed to it —
they emit `TH Aeonik` + `w:b` and get the real Bold — so the defect only ever
reached the layer Siwatch actually exercises, which is typing in plain Word.

Siwatch's decision, 2026-08-06: every family gets a real bold member, and Black
is retired into Medium's bold slot. Extended 2026-08-07 — a SemiBold was added
and the Thin family retired on the same principle.

    TH Aeonik Air       R=Air       I=AirItalic       B=Thin    BI=ThinItalic
    TH Aeonik Light     R=Light     I=LightItalic     B=Medium  BI=MediumItalic
    TH Aeonik           R=Regular   I=RegularItalic   B=Bold    BI=BoldItalic
    TH Aeonik Medium    R=Medium    I=MediumItalic    B=Black   BI=BlackItalic
    TH Aeonik SemiBold  R=SemiBold  I=SemiBoldItalic  B=Black   BI=BlackItalic

20 shipped files, 16 distinct outline sets, 5 families. Three weights exist as
outlines but no longer name a family of their own:

  * **Black** — retired 2026-08-06. It is Medium's bold, and SemiBold's too.
  * **Thin** — retired 2026-08-07. Air's bold already IS Thin, so a Thin entry
    in the dropdown reached outlines you get by pressing Ctrl+B on Air.
    Siwatch: "thin is not necessary, because we can get thin by bold the new
    air, and get bold thin by the light font."
  * Neither name survives in any field, including the typographic layer.

**SemiBold's Latin is synthetic.** CoType never drew an Aeonik SemiBold and
there is no source for one, so `build_aeonik_semibold.py` derives it from
Medium. Every other Latin here is CoType's own bytes. Siwatch accepted the cost
on 2026-08-07; §4c records exactly what it is.

The Black outlines now fill TWO families' bold slots — promoted into
`TH Aeonik Medium` and aliased into `TH Aeonik SemiBold`. Siwatch's call: both
families keep a real bold, and no further weight had to be drawn.

THIS IS A METADATA-ONLY TRANSFORM. Not one outline moves. Measured on the
shipped faces before the change (th_metrics.stem, 512 px/em):

    face      Thai    Latin
    Air        7.3      7.8
    Thin      20.5     22.9
    Light     48.8     51.8
    Regular   79.1     83.0
    Medium   102.5    110.4
    Bold     134.8    143.6
    Black    134.8    175.8

Thai Bold and Thai Black are IDENTICAL — both sit on Bai Jamjuree's counter
floor. So promoting Black into Medium's bold slot buys +22% in the Latin and
nothing at all in the Thai. That is the documented cap (§4), it is why this
change needs no weight solving, and it is why every write here asserts that the
CharStrings came through untouched.

A BOLD SLOT IS A BOLD SLOT — TWO RULES, NO EXCEPTIONS
-----------------------------------------------------
Every face filling a family's Bold or Bold Italic slot obeys both rules, whether
its outlines are unique (`_promoted`) or a duplicate of another shipped face
(`_alias`). The two were treated differently until 2026-08-07 and it caused a
defect; see `_promoted` for the measurement.

  1. NO nameID16/17. The typographic family `TH Aeonik` then holds exactly one
     face per weight. Otherwise fontconfig sees several bold-flagged faces in
     it, and a weasyprint or LibreOffice request for `TH Aeonik` at 700 can
     resolve to Medium's outlines instead of Bold's — a Thai PDF that silently
     renders one weight light. It is also how CoType names its own
     Aeonik-Bold.otf (measured: both fields empty).
  2. usWeightClass 700, panose 8 — the face declares itself Bold in every
     field even when its outlines weigh 200 or 900. Within its own nameID1
     family it IS the bold, and there is no competing face for a weight query
     to pick wrongly.

Rule 2 costs nothing in CSS: `@font-face { font-weight: 200 }` is a descriptor
that declares how the resource is matched and overrides the file's OS/2, so
ichita.css still reaches every weight by number.

Rule 2 IS the one thing Word could disagree with, because the outlines under it
are not weight 700. Word links on nameID1/nameID2 + the macStyle bold bit, not
on usWeightClass, so this should hold — but LINUX CANNOT SEE IT. It is measured
in Word before the build is accepted; if Word synthesises anyway, the retry is
the face's true weight. See docs/THAI-LATIN-FONT-ENGINEERING.md §4b.

USAGE
-----
    python3 th_style_link.py --check     # read-only report, exit 1 on any fault
    python3 th_style_link.py             # derive the 20 shipped faces in place

`build_th_aeonik.py` imports FACES for its own metadata step and calls
`write_aliases()` at the end of a full build. Running this standalone over an
already-built directory produces exactly the same result, which is what makes it
usable while the pristine Aeonik v1.000 source is unavailable.
"""

import argparse
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).parent.parent
OUTPUT_DIR = ROOT / "assets" / "fonts" / "th-aeonik"

# OS/2 fsSelection bits
ITALIC = 1 << 0
BOLD = 1 << 5
REGULAR = 1 << 6
USE_TYPO = 1 << 7

# head.macStyle bits
MAC_BOLD = 1 << 0
MAC_ITALIC = 1 << 1


def _face(*, file, id1, id2, id4, id6, id16, id17, weight, panose,
          source=None, legacy=None, kind="outline"):
    """One shipped face.

    fsSelection and macStyle are DERIVED from nameID2 rather than written by
    hand. They were hand-written per face until 2026-08-06, which is three
    chances per face to typo a bit that nothing on Linux would catch.
    """
    fs = USE_TYPO
    mac = 0
    if id2 == "Regular":
        fs |= REGULAR
    if "Italic" in id2:
        fs |= ITALIC
        mac |= MAC_ITALIC
    if "Bold" in id2:
        fs |= BOLD
        mac |= MAC_BOLD
    return {
        "file": file, "source": source, "legacy": legacy, "kind": kind,
        "nameID1": id1, "nameID2": id2, "nameID4": id4, "nameID6": id6,
        "nameID16": id16, "nameID17": id17,
        "fsSelection": fs, "macStyle": mac,
        "weightClass": weight, "panose_bWeight": panose,
    }


def _plain(label, key, weight, panose, italic=False):
    """A weight that owns its own nameID1 and holds the Regular/Italic slot."""
    fam = f"TH Aeonik {label}"
    return _face(
        file=f"TH-Aeonik-{key}",
        id1=fam,
        id2="Italic" if italic else "Regular",
        id4=fam + (" Italic" if italic else ""),
        id6=f"TH-Aeonik-{key}",
        id16="TH Aeonik",
        id17=f"{label} Italic" if italic else label,
        weight=weight, panose=panose,
    )


def _promoted(label, key, file, legacy, italic=False):
    """A real, distinct weight that now serves as some family's bold slot.

    Metadata-identical to an alias, and that is a CORRECTION made 2026-08-07.
    Promoted faces used to keep nameID16/17 and their true usWeightClass, on the
    reasoning that the outlines really are that weight and ichita.css selects
    them by number. Both halves were wrong:

      * MEASURED DEFECT. `fc-match "TH Aeonik Air"` returned AirBold. Air
        declares 100 and its promoted bold declared 200; fontconfig maps those
        to thin(0) and extralight(40), and a default request sits at
        regular(80) — so the BOLD was the closer match. LibreOffice picked it
        for the plain-Air line of the acceptance sheet, which is why
        TH-Aeonik-Air embedded nowhere in the PDF. Asking for Air quietly got
        Thin.
      * CSS never needed it. `@font-face { font-weight: 200 }` is a descriptor:
        it declares how the resource is matched and overrides whatever the
        file's OS/2 says. ichita.css is unaffected.

    So a bold slot is a bold slot regardless of what its outlines weigh, and it
    stays out of the typographic family for the same reason aliases do — one
    face per weight in `TH Aeonik`, no ambiguous match.
    """
    fam = f"TH Aeonik {label}"
    style = "Bold Italic" if italic else "Bold"
    return _face(
        file=file, legacy=legacy, kind="promoted",
        id1=fam, id2=style,
        id4=f"{fam} {style}", id6=file,
        id16=None, id17=None,
        weight=700, panose=8,
    )


# ---------------------------------------------------------------------------
# The 14 outline faces. Keys are BUILD keys — they name the outline recipe (the
# Latin source in build_th_aeonik.WEIGHTS, the Thai pairing and embolden in
# th_thai_prep.BUILD_TABLE) and MUST NOT be renamed. Renaming the identifier a
# dozen modules key on is what broke 12 scripts on 2026-08-06. Only "file" and
# the name fields move; the weight solve is untouched by this whole change.
# ---------------------------------------------------------------------------

FACES = {
    "Air":         _plain("Air", "Air", 100, 2),
    "AirItalic":   _plain("Air", "AirItalic", 100, 2, italic=True),

    # PROMOTED, 2026-08-07. `TH Aeonik Thin` is retired as a family for the same
    # reason `TH Aeonik Black` was: Air's bold already IS Thin, so a separate
    # Thin entry in the dropdown reaches outlines you can get by pressing
    # Ctrl+B on Air. Siwatch: "thin is not necessary, because we can get thin by
    # bold the new air, and get bold thin by the light font."
    #
    # The OUTLINES are untouched and still ship — they are what Air bolds to.
    # usWeightClass stays 200, its true weight, exactly as MediumBold keeps 900.
    "Thin": _promoted("Air", "Thin",
                      "TH-Aeonik-AirBold", "TH-Aeonik-Thin"),
    "ThinItalic": _promoted("Air", "ThinItalic",
                            "TH-Aeonik-AirBoldItalic", "TH-Aeonik-ThinItalic",
                            italic=True),

    "Light":       _plain("Light", "Light", 300, 4),
    "LightItalic": _plain("Light", "LightItalic", 300, 4, italic=True),
    "Medium":      _plain("Medium", "Medium", 500, 6),
    "MediumItalic": _plain("Medium", "MediumItalic", 500, 6, italic=True),

    # Added 2026-08-07. Its LATIN IS SYNTHETIC — CoType never drew an Aeonik
    # SemiBold, so build_aeonik_semibold.py derives one from Medium. Every
    # other Latin in this family is CoType's own bytes. §4c.
    "SemiBold":    _plain("SemiBold", "SemiBold", 600, 7),
    "SemiBoldItalic": _plain("SemiBold", "SemiBoldItalic", 600, 7, italic=True),

    # The RIBBI family itself.
    "Regular": _face(
        file="TH-Aeonik-Regular",
        id1="TH Aeonik", id2="Regular",
        id4="TH Aeonik", id6="TH-Aeonik-Regular",
        id16="TH Aeonik", id17="Regular", weight=400, panose=5),
    "RegularItalic": _face(
        file="TH-Aeonik-RegularItalic",
        id1="TH Aeonik", id2="Italic",
        id4="TH Aeonik Italic", id6="TH-Aeonik-RegularItalic",
        id16="TH Aeonik", id17="Regular Italic", weight=400, panose=5),
    "Bold": _face(
        file="TH-Aeonik-Bold",
        id1="TH Aeonik", id2="Bold",
        id4="TH Aeonik Bold", id6="TH-Aeonik-Bold",
        id16="TH Aeonik", id17="Bold", weight=700, panose=8),
    "BoldItalic": _face(
        file="TH-Aeonik-BoldItalic",
        id1="TH Aeonik", id2="Bold Italic",
        id4="TH Aeonik Bold Italic", id6="TH-Aeonik-BoldItalic",
        id16="TH Aeonik", id17="Bold Italic", weight=700, panose=8),

    # PROMOTED. The Black outlines, shipped as TH Aeonik Medium's bold. Keeps
    # usWeightClass 900 and its place in the typographic family; `legacy` names
    # the file this replaces, which must not be left beside it.
    "Black": _promoted("Medium", "Black",
                       "TH-Aeonik-MediumBold", "TH-Aeonik-Black"),
    "BlackItalic": _promoted("Medium", "BlackItalic",
                             "TH-Aeonik-MediumBoldItalic",
                             "TH-Aeonik-BlackItalic", italic=True),
}


def _alias(label, key, source, italic=False):
    """A duplicate face that exists only to fill a family's bold slot.

    No nameID16/17, and it declares itself Bold in every field. See the module
    docstring for why both of those matter.
    """
    fam = f"TH Aeonik {label}"
    style = "Bold Italic" if italic else "Bold"
    return _face(
        file=f"TH-Aeonik-{key}", source=source, kind="alias",
        id1=fam, id2=style,
        id4=f"{fam} {style}", id6=f"TH-Aeonik-{key}",
        id16=None, id17=None,
        weight=700, panose=8,
    )


ALIASES = {
    # AirBold / AirBoldItalic were aliases of Thin until 2026-08-07. They are
    # now the PROMOTED Thin faces themselves (see FACES above), so the family
    # gets its real bold without a duplicate file. ThinBold / ThinBoldItalic
    # went with the Thin family.
    "LightBold":      _alias("Light", "LightBold", "Medium"),
    "LightBoldItalic": _alias("Light", "LightBoldItalic", "MediumItalic", italic=True),

    # Siwatch, 2026-08-07: SemiBold's bold is Black, and Medium KEEPS Black too.
    # So the Black outlines now fill two families' bold slots — once promoted
    # (TH Aeonik Medium, keeping nameID16/17) and once aliased here. That is a
    # deliberate duplicate, not an oversight: it is the only way both families
    # get a real bold without drawing another weight.
    "SemiBoldBold":   _alias("SemiBold", "SemiBoldBold", "Black"),
    "SemiBoldBoldItalic": _alias("SemiBold", "SemiBoldBoldItalic", "BlackItalic",
                                 italic=True),
}

SHIPPED = {**FACES, **ALIASES}


def outline_files():
    """The 14 files that carry distinct outlines — what a measuring script wants."""
    return [cfg["file"] + ".otf" for cfg in FACES.values()]


def shipped_files():
    """All 20 files that get installed."""
    return [cfg["file"] + ".otf" for cfg in SHIPPED.values()]


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

def set_name(nt, nid, val, pid=3, peid=1, lid=0x0409):
    if val is None:
        nt.removeNames(nameID=nid, platformID=pid, platEncID=peid, langID=lid)
        return
    nt.setName(val, nid, pid, peid, lid)


def apply_face_metadata(font, key, cfg=None):
    """Write one face's identity: name table, OS/2, head.macStyle, CFF name.

    Shared by the builder's own metadata step and by the standalone pass, so
    there is exactly one implementation of what a TH Aeonik face is called.
    """
    cfg = cfg or SHIPPED[key]
    nt = font["name"]

    for nid in (1, 2, 4, 6, 16, 17):
        val = cfg[f"nameID{nid}"]
        set_name(nt, nid, val)
        set_name(nt, nid, val, pid=1, peid=0, lid=0)

    uid = f"THAeonik-{key}"
    set_name(nt, 3, uid)
    set_name(nt, 3, uid, pid=1, peid=0, lid=0)

    os2 = font["OS/2"]
    os2.fsType = 0
    if os2.version < 4:
        os2.version = 4
        for attr, default in [("sxHeight", 0), ("sCapHeight", 0),
                              ("usDefaultChar", 0), ("usBreakChar", 32),
                              ("usMaxContext", 0)]:
            if not hasattr(os2, attr):
                setattr(os2, attr, default)
    os2.fsSelection = cfg["fsSelection"]
    os2.usWeightClass = cfg["weightClass"]
    os2.panose.bWeight = cfg["panose_bWeight"]

    font["head"].macStyle = cfg["macStyle"]

    # The CFF has its own copy of the PostScript name and Windows reads it.
    if "CFF " in font:
        font["CFF "].cff.fontNames[0] = cfg["nameID6"]


# ---------------------------------------------------------------------------
# Outline identity
#
# The whole claim of this module is "no outline moves". That claim is worthless
# unless it is checked on the bytes that get written, so every write is followed
# by a re-read and a comparison against the source.
# ---------------------------------------------------------------------------

def outline_digest(path):
    """(charstring bytes, advance widths) for every glyph, as a comparable dict.

    Reads CFF charstring bytecode rather than drawing the outlines: it is the
    actual shipped representation, and it catches a re-rounded coordinate that a
    pen replay would hide.
    """
    font = TTFont(str(path))
    cff = font["CFF "].cff
    charstrings = cff[cff.fontNames[0]].CharStrings
    hmtx = font["hmtx"]
    out = {}
    for g in font.getGlyphOrder():
        cs = charstrings[g]
        if cs.bytecode is None:
            cs.compile()
        out[g] = (cs.bytecode, hmtx[g])
    font.close()
    return out


def _diff_outlines(before, after):
    if before.keys() != after.keys():
        only_b = sorted(set(before) - set(after))[:5]
        only_a = sorted(set(after) - set(before))[:5]
        return f"glyph set changed (missing {only_b}, added {only_a})"
    moved = [g for g in before if before[g] != after[g]]
    if moved:
        return f"{len(moved)} glyphs changed, e.g. {moved[:5]}"
    return None


# ---------------------------------------------------------------------------
# The pass
# ---------------------------------------------------------------------------

def _resolve_source(out_dir, cfg):
    """Where this face's outlines currently live, tolerating the pre-rename name.

    Raises when BOTH names are present. That is not pedantry — retiring Thin on
    2026-08-07 hit it directly: `TH-Aeonik-AirBold.otf` already existed as an
    ALIAS of Thin from the previous structure, so preferring the new name would
    have read a derived artifact as if it were the pipeline's output and left
    `TH-Aeonik-Thin.otf` orphaned on disk. The two files happened to be
    identical that time. Next time they will not be, and the whole point of
    this module is that an unavailable source is recoverable while a quietly
    wrong one is not.
    """
    new = out_dir / f"{cfg['file']}.otf"
    old = out_dir / f"{cfg['legacy']}.otf" if cfg.get("legacy") else None
    if old is not None and old.exists() and new.exists():
        raise SystemExit(
            f"ERROR: both {old.name} and {new.name} are present, and they are "
            f"the same face under two names.\nDelete whichever is not the "
            f"current build output before re-running — this script will not "
            f"guess.")
    if new.exists():
        return new
    if old is not None and old.exists():
        return old
    return None


def restyle_outline_faces(out_dir, verbose=True):
    """Re-apply the shipped identity to the 14 outline faces, renaming as needed."""
    faults = []
    for key, cfg in FACES.items():
        src = _resolve_source(out_dir, cfg)
        if src is None:
            faults.append(f"{key}: no source file "
                          f"({cfg['file']}.otf or {cfg.get('legacy')}.otf)")
            continue
        dst = out_dir / f"{cfg['file']}.otf"
        before = outline_digest(src)

        font = TTFont(str(src))
        apply_face_metadata(font, key, cfg)
        font.save(str(dst))
        font.close()

        drift = _diff_outlines(before, outline_digest(dst))
        if drift:
            faults.append(f"{key}: outlines changed — {drift}")
            continue

        if src != dst and src.exists():
            src.unlink()
            if verbose:
                print(f"  {key:16s} {src.name} -> {dst.name}  (removed the old file)")
        elif verbose:
            print(f"  {key:16s} {dst.name}")
    return faults


def write_aliases(out_dir, verbose=True):
    """Write the six duplicate faces that fill the Air/Thin/Light bold slots."""
    faults = []
    for key, cfg in ALIASES.items():
        src_cfg = FACES[cfg["source"]]
        src = out_dir / f"{src_cfg['file']}.otf"
        if not src.exists():
            faults.append(f"{key}: source {src.name} is missing")
            continue
        dst = out_dir / f"{cfg['file']}.otf"
        before = outline_digest(src)

        font = TTFont(str(src))
        apply_face_metadata(font, key, cfg)
        font.save(str(dst))
        font.close()

        drift = _diff_outlines(before, outline_digest(dst))
        if drift:
            faults.append(f"{key}: not a faithful duplicate of "
                          f"{cfg['source']} — {drift}")
            continue
        if verbose:
            print(f"  {key:16s} {dst.name}  = {cfg['source']} outlines, "
                  f"'{cfg['nameID1']}' Bold slot")
    return faults


def apply_all(out_dir=OUTPUT_DIR, verbose=True):
    if verbose:
        print(f"Shipped faces -> {out_dir}")
        print("\n[1/2] Outline faces")
    faults = restyle_outline_faces(out_dir, verbose)
    if verbose:
        print("\n[2/2] Style-link aliases")
    faults += write_aliases(out_dir, verbose)
    return faults


# ---------------------------------------------------------------------------
# Read-only check
# ---------------------------------------------------------------------------

def check(out_dir=OUTPUT_DIR, verbose=True):
    """Verify the shipped set on disk. A face that cannot be read is a FAULT.

    A check that returns 'fine' when it could not run is a silent no-op, which
    is how three overflow checks shipped with the defect they existed to catch
    (ichita-convert post-mortem, 2026-08-06).
    """
    faults = []
    seen = {3: {}, 4: {}, 6: {}}
    families = {}

    for key, cfg in SHIPPED.items():
        path = out_dir / f"{cfg['file']}.otf"
        if not path.exists():
            faults.append(f"{key}: {path.name} is missing")
            continue
        try:
            font = TTFont(str(path))
        except Exception as exc:
            faults.append(f"{key}: unreadable — {exc}")
            continue

        nt = font["name"]
        for nid in (1, 2, 4, 6, 16, 17):
            want = cfg[f"nameID{nid}"]
            got = nt.getDebugName(nid)
            if (got or None) != want:
                faults.append(f"{key}: nameID{nid} is {got!r}, want {want!r}")

        os2, head = font["OS/2"], font["head"]
        if os2.fsSelection != cfg["fsSelection"]:
            faults.append(f"{key}: fsSelection 0x{os2.fsSelection:04X}, "
                          f"want 0x{cfg['fsSelection']:04X}")
        if head.macStyle != cfg["macStyle"]:
            faults.append(f"{key}: macStyle {head.macStyle}, want {cfg['macStyle']}")
        if os2.usWeightClass != cfg["weightClass"]:
            faults.append(f"{key}: usWeightClass {os2.usWeightClass}, "
                          f"want {cfg['weightClass']}")

        for nid in (3, 4, 6):
            val = nt.getDebugName(nid)
            if val in seen[nid]:
                faults.append(f"{key}: nameID{nid} {val!r} collides with "
                              f"{seen[nid][val]} — Windows will shadow one of them")
            seen[nid][val] = key

        families.setdefault(cfg["nameID1"], {})[cfg["nameID2"]] = key
        font.close()

    # Every family must hold a real bold, or Word synthesises one.
    for fam, members in sorted(families.items()):
        if "Regular" in members and "Bold" not in members:
            faults.append(f"family {fam!r} has no Bold member — Word will "
                          f"double-strike it")
        if "Italic" in members and "Bold Italic" not in members:
            faults.append(f"family {fam!r} has no Bold Italic member")
        extra = set(members) - {"Regular", "Italic", "Bold", "Bold Italic"}
        if extra:
            faults.append(f"family {fam!r} has non-RIBBI nameID2 {sorted(extra)}")

    # An alias must be exactly its source.
    for key, cfg in ALIASES.items():
        src = out_dir / f"{FACES[cfg['source']]['file']}.otf"
        dst = out_dir / f"{cfg['file']}.otf"
        if not (src.exists() and dst.exists()):
            faults.append(f"{key}: cannot compare against {cfg['source']} — "
                          f"a missing file is not a pass")
            continue
        drift = _diff_outlines(outline_digest(src), outline_digest(dst))
        if drift:
            faults.append(f"{key}: differs from {cfg['source']} — {drift}")

    # Anything in the directory that is not a shipped face is stale. This used
    # to be a hardcoded list of the two retired Black files, which of course
    # said nothing when Thin was retired the next day and left four orphans
    # behind. install-fonts.sh globs the directory, so an orphan is not clutter
    # — it is a retired family that reappears in somebody's font menu.
    expected = set(shipped_files())
    for p in sorted(out_dir.glob("*.otf")):
        if p.name not in expected:
            faults.append(f"{p.name} is not a shipped face — delete it, or "
                          f"install-fonts.sh will put a retired family back "
                          f"in the font menu")

    if verbose:
        for fam, members in sorted(families.items()):
            slots = "  ".join(f"{s}={members[s]}" for s in
                              ("Regular", "Italic", "Bold", "Bold Italic")
                              if s in members)
            print(f"  {fam:20s} {slots}")
        print()
        if faults:
            print(f"FAIL — {len(faults)} fault(s)")
            for f in faults:
                print(f"  - {f}")
        else:
            print(f"OK — {len(SHIPPED)} shipped faces, "
                  f"{len(FACES)} outline sets, {len(families)} families, "
                  f"every family has a real bold")
    return faults


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--dir", default=str(OUTPUT_DIR),
                    help="directory holding the built faces")
    ap.add_argument("--check", action="store_true",
                    help="read-only report; makes no changes")
    args = ap.parse_args()
    out_dir = Path(args.dir)

    if not out_dir.is_dir():
        print(f"ERROR: {out_dir} is not a directory", file=sys.stderr)
        return 2

    if args.check:
        return 1 if check(out_dir) else 0

    faults = apply_all(out_dir)
    print()
    if faults:
        print(f"FAIL — {len(faults)} fault(s)", file=sys.stderr)
        for f in faults:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("Now verifying what was written:\n")
    return 1 if check(out_dir) else 0


if __name__ == "__main__":
    sys.exit(main())
