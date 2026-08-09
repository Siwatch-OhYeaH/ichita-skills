#!/usr/bin/env python3
"""
TH Aeonik's shipped family structure — the single authority on face naming.

WHAT THIS SHIPS — Siwatch, 2026-08-09
-------------------------------------
Ten weights, each drawn once, in one Windows Settings card:

    Air 100   Thin 200   Light 300   Book 350   Regular 400
    Medium 500   SemiBold 600   Bold 700   ExtraBold 800   Black 900

x roman and italic = 20 files, 20 distinct outline sets, SIX nameID1 families.
Every face carries `nameID16 = "TH Aeonik"` and a distinct `nameID17`, so
Windows Settings shows one card listing all ten styles, and every face carries
its own true `usWeightClass`, so no two members of that typographic family
compete for one weight.

    nameID1 (Word's dropdown)   Regular slot   Bold slot        card shows
    TH Aeonik Air               Air 100        - none -         Air
    TH Aeonik Thin              Thin 200       - none -         Thin
    TH Aeonik Light             Light 300      ExtraBold 800    Light, ExtraBold
    TH Aeonik Book              Book 350       SemiBold 600     Book, SemiBold
    TH Aeonik                   Regular 400    Bold 700         Regular, Bold
    TH Aeonik Medium            Medium 500     Black 900        Medium, Black

THE THREE THINGS THIS STRUCTURE IS SOLVING, AND WHY IT LOOKS ODD
----------------------------------------------------------------
1. NO DUPLICATE OUTLINES. Until 2026-08-08 six of the 24 shipped faces were the
   same outlines under a second name, because Light and Book both bolded to
   Medium and Medium and SemiBold both bolded to Black. Putting those in the
   typographic family made three faces claim weight 500 and two claim 900, and
   a `TH Aeonik` request at 700 could resolve to Medium's outlines — a Thai PDF
   that silently renders one weight light. The old fix was to keep bold slots
   OUT of nameID16 and declare them all 700, which cost five extra Settings
   cards. The real fix is to stop shipping duplicates: every bold slot is now a
   weight somebody drew.

2. AIR AND THIN HOLD NO BOLD SLOT, ON PURPOSE. An unqualified fontconfig query
   defaults to fc weight 80 and the nearest member of the nameID1 family wins,
   so a family's plain face resolves only while it sits closer to 80 than its
   own bold. Air is fc 0, distance 80; any bold it could take would need fc
   above 160, i.e. weight 600 or heavier — a jump from stem 7.8 to 130.9, which
   is not a bold, it is a different typeface. Measured 2026-08-07: pairing Air
   with Thin makes bare `TH Aeonik Air` resolve to Thin, +199.3% ink, and
   LibreOffice picked it for the plain-Air row of the acceptance sheet.

   So Air and Thin stand alone and Word synthesises their bold. §4b calls that
   the worst thing that can happen to this typeface — because double-striking
   spends counter aperture, and below ~47 units a Thai counter fills under any
   rasteriser. That reason does not reach these two:

       face    counter aperture      APERTURE_FLOOR
       Air              113.3                  46.5
       Thin              97.7                  46.5
       Bold              50.8                  46.5   <- why the rule exists

   These are the only two weights in the family where synthesis costs nothing.
   `check()` asserts the exemption is exactly {Air, Thin}, so a family that
   loses its bold by accident still fails.

3. LIGHT BOLDS HEAVIER THAN BOOK DOES. Light's bold is ExtraBold 800 and Book's
   is SemiBold 600, which reads backwards in this table and is deliberate. Book
   350 is the body weight for Thai and mixed documents, so Ctrl+B on body copy
   has to land near Regular's own 1.73x rather than at 2.31x:

       Regular 400 -> Bold 700       Latin 1.73x   Thai 1.72x
       Book    350 -> SemiBold 600   Latin 1.82x   Thai 1.85x
       Book    350 -> ExtraBold 800  Latin 2.31x   Thai 2.09x   rejected
       Light   300 -> ExtraBold 800  Latin 3.15x                display weight

   fontconfig only requires each of Light's and Book's bolds to come from
   {600, 800}; which gets which is a design choice and this is it.

A BOLD SLOT NOW DECLARES ITS TRUE WEIGHT
----------------------------------------
Until 2026-08-08 every bold slot declared `usWeightClass` 700 and `panose` 8
whatever its outlines weighed, and dropped nameID16/17. Both halves are now
reversed, and the reason the old rule existed is gone with the duplicates: the
typographic family holds exactly one face per weight because there IS exactly
one face per weight.

What links Word's Ctrl+B is `nameID1`/`nameID2` plus the `macStyle` bold bit —
never `usWeightClass` — and those are unchanged. `_face()` derives fsSelection
and macStyle from nameID2, so a bold slot still declares itself Bold in every
field Word reads. LINUX CANNOT CONFIRM THIS. It is measured in Word before the
build is accepted; see `build_style_link_doc.py` and §4b.

TWO LATIN WEIGHTS HERE ARE NOT COTYPE'S DRAWING
-----------------------------------------------
Book 350, SemiBold 600 and ExtraBold 800 have no Aeonik source — not in the
v1.000 desktop cut, not in the v2.000 web cut — and Aeonik is not interpolatable
in ANY adjacent pair (Light->Regular alone has 184 of 657 glyphs structurally
incompatible, 6 of the 10 digits among them). `build_aeonik_semibold.py`
derives all three with `changeWeight`, thinning from the heavier neighbour
because thinning opens counters where growing spends them. Every other Latin
here is CoType's own charstrings. §4c records what synthesis costs.

METADATA IS ICHITA'S, ATTRIBUTION IS NOT
----------------------------------------
Siwatch, 2026-08-09: mark the identity fields as ICHITA internal use so nobody
is confused about what this file is. Nine fields say ICHITA. `nameID0` does not,
and that is the same decision rather than an exception to it — it carries
CoType's copyright, Bai Jamjuree's notice verbatim as SIL OFL 1.1 clause 2
asks, and ICHITA's copyright on the build. Writing ICHITA over that field would
assert ownership of outlines we did not draw.

The fonts are INTERNAL. Installing them and embedding them in a PDF is use, and
OFL permits embedding explicitly. Handing the `.otf` files to a client, a
printer or a contractor is redistribution, where OFL clause 5 ("must be
distributed entirely under this license") and CoType's commercial EULA cannot
both be satisfied. `nameID13` says so inside every file.

USAGE
-----
    python3 th_style_link.py --check     # read-only report, exit 1 on any fault
    python3 th_style_link.py             # derive the 20 shipped faces in place

`build_th_aeonik.py` imports FACES for its own metadata step. Running this
standalone over an already-built directory produces exactly the same result,
which is what makes it usable while the pristine Aeonik v1.000 source is off
the machine.
"""

import argparse
import datetime
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


# ---------------------------------------------------------------------------
# Identity — the fields that say whose font this is
#
# Nine of these say ICHITA. nameID0 states facts instead, because OFL 1.1
# clause 2 asks that a copy carry the Bai notice and because CoType's copyright
# over their charstrings exists whatever we write here. See the module
# docstring.
# ---------------------------------------------------------------------------

VERSION = "1.000"          # TH Aeonik's own first release, not Aeonik's version

COPYRIGHT = (
    "Aeonik (c) 2018 CoType Foundry, used under licence. "
    "Thai derived from Bai Jamjuree: "
    "Copyright 2018 Bai Jamjuree (https://github.com/cadsondemak/Bai-Jamjuree), "
    "SIL Open Font License 1.1. "
    "TH Aeonik build (c) 2026 ICHITA Technology Co., Ltd. "
    "INTERNAL USE ONLY - NOT FOR REDISTRIBUTION."
)
TRADEMARK = (
    "TH Aeonik is an internal typeface of ICHITA Technology Co., Ltd. "
    "Aeonik is a trademark of CoType Foundry."
)
MANUFACTURER = "ICHITA Technology Co., Ltd."
DESIGNER = "ICHITA Technology Co., Ltd."
DESCRIPTION = (
    "Thai and Latin harmonised on one baseline and one set of metrics, for "
    "ICHITA Technology Co., Ltd. Internal use only; not for redistribution."
)
VENDOR_URL = "https://ichitaglobal.com"
LICENSE = (
    "ICHITA internal use only. Not for redistribution, resale or transfer "
    "outside ICHITA Technology Co., Ltd. Contains components licensed from "
    "CoType Foundry and components under the SIL Open Font License 1.1; see "
    "NOTICE.txt and OFL.txt distributed with these fonts."
)
# nameID14 is the licence URL. There is no internal notice page to point at,
# and a licence field that 404s is worse than an absent one, so it is removed
# rather than filled with the vendor URL. nameID13 carries the whole statement.
LICENSE_URL = None

# Unregistered with Microsoft's vendor ID registry. achVendID is informational
# — nothing matches on it — and leaving CoType's there would be one more field
# claiming this is their font.
VENDOR_ID = "ICHT"


def build_stamp():
    """Today, as the build date that goes in nameID3 and nameID5.

    Derived rather than pinned to a constant. The failure this closes is a
    STALE INSTALL reading as a font defect, which has happened twice here, and
    a constant somebody forgets to bump is exactly the same failure with an
    extra step. `check()` therefore asserts the SHAPE of the version string and
    reports the date, rather than demanding today's.
    """
    return datetime.date.today().isoformat()


# ---------------------------------------------------------------------------
# The 20 shipped faces
#
# Keys are BUILD keys — they name the outline recipe (the Latin source in
# build_th_aeonik.WEIGHTS, the Thai pairing and embolden in
# th_thai_prep.BUILD_TABLE) and MUST NOT be renamed. Renaming the identifier a
# dozen modules key on is what broke 12 scripts on 2026-08-06.
#
# The filename is now `TH-Aeonik-<build key>.otf` for every face, with no
# exceptions. That was not true while bold slots were named after the family
# they served (Thin shipped as TH-Aeonik-AirBold, Black as
# TH-Aeonik-MediumBold), and `legacy` below is what renames them.
# ---------------------------------------------------------------------------

def _face(*, key, id1, id2, id17, weight, panose, legacy=None):
    """One shipped face.

    fsSelection and macStyle are DERIVED from nameID2 rather than written by
    hand. They were hand-written per face until 2026-08-06, which is three
    chances per face to typo a bit that nothing on Linux would catch.

    nameID4 is derived the same way: the RIBBI full name is the family plus the
    style, with "Regular" contributing nothing. That is what makes
    `TH-Aeonik-ExtraBold.otf` announce itself as "TH Aeonik Light Bold" to
    Word's style linker while announcing "ExtraBold" to the Settings card.
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
    file = f"TH-Aeonik-{key}"
    return {
        "file": file, "legacy": legacy,
        "nameID1": id1, "nameID2": id2,
        "nameID4": id1 if id2 == "Regular" else f"{id1} {id2}",
        "nameID6": file,
        "nameID16": "TH Aeonik", "nameID17": id17,
        "fsSelection": fs, "macStyle": mac,
        "weightClass": weight, "panose_bWeight": panose,
    }


def _pair(key, id1, id2, id17, weight, panose, legacy=None):
    """A face and its italic, which differ only in the three derived fields."""
    lg = (legacy, legacy + "Italic") if legacy else (None, None)
    return {
        key: _face(key=key, id1=id1, id2=id2, id17=id17,
                   weight=weight, panose=panose, legacy=lg[0]),
        key + "Italic": _face(
            key=key + "Italic", id1=id1,
            id2="Bold Italic" if id2 == "Bold" else "Italic",
            id17=id17 + " Italic", weight=weight, panose=panose, legacy=lg[1]),
    }


# PANOSE bWeight is a 2..11 ladder (2 Very Light .. 10 Black). It is
# informational here — nothing matches on it — but it is now a real ten-step
# ladder, so it is written as one. Book and Regular share 5 because PANOSE has
# one "Book" step and both belong in it.
FACES = {
    # --- TH Aeonik Air --- plain only; see docstring point 2 ----------------
    **_pair("Air", "TH Aeonik Air", "Regular", "Air", 100, 2),

    # --- TH Aeonik Thin --- plain only ---------------------------------------
    # Was `TH-Aeonik-AirBold.otf`: the same outlines, declared 700, serving as
    # Air's bold slot and absent from the Settings card. Siwatch asked for Thin
    # back as a style in its own right on 2026-08-09, and it cannot be both.
    **_pair("Thin", "TH Aeonik Thin", "Regular", "Thin", 200, 3,
            legacy="TH-Aeonik-AirBold"),

    # --- TH Aeonik Light ----------------------------------------------------
    **_pair("Light", "TH Aeonik Light", "Regular", "Light", 300, 4),
    # Light's bold is the HEAVIER of the two available, and Book's is the
    # lighter. Backwards on the page, right for the reader — see docstring
    # point 3. Its Latin is synthetic.
    **_pair("ExtraBold", "TH Aeonik Light", "Bold", "ExtraBold", 800, 9),

    # --- TH Aeonik Book -----------------------------------------------------
    # The body weight for Thai and mixed documents. Its Thai is Bai Jamjuree
    # Regular UNDISTORTED — the only entry in BUILD_TABLE at embolden 0.0 — and
    # the Latin was drawn to fit it, which is the reverse of every other face.
    **_pair("Book", "TH Aeonik Book", "Regular", "Book", 350, 5),
    **_pair("SemiBold", "TH Aeonik Book", "Bold", "SemiBold", 600, 7),

    # --- TH Aeonik ----------------------------------------------------------
    **_pair("Regular", "TH Aeonik", "Regular", "Regular", 400, 5),
    **_pair("Bold", "TH Aeonik", "Bold", "Bold", 700, 8),

    # --- TH Aeonik Medium ---------------------------------------------------
    **_pair("Medium", "TH Aeonik Medium", "Regular", "Medium", 500, 6),
    # Was `TH-Aeonik-MediumBold.otf`, declared 700. It is Black, it weighs 900,
    # and now it says so.
    **_pair("Black", "TH Aeonik Medium", "Bold", "Black", 900, 10,
            legacy="TH-Aeonik-MediumBold"),
}

# Backwards-compatible name. There is no longer any difference between "the
# faces with outlines" and "the faces that ship" — that difference WAS the
# duplicate problem.
SHIPPED = FACES

# The two families that hold no bold slot, and the only two allowed to.
# Asserted in both directions: a third family losing its bold is a fault, and
# so is one of these gaining one.
NO_BOLD_SLOT = {"TH Aeonik Air", "TH Aeonik Thin"}

# The duplicate faces retired on 2026-08-09. install-fonts.sh globs the
# directory, so one of these left behind is not clutter — it is a face that
# reappears in somebody's font menu declaring a weight that now belongs to a
# different outline.
RETIRED_FILES = [
    "TH-Aeonik-LightBold.otf", "TH-Aeonik-LightBoldItalic.otf",
    "TH-Aeonik-BookBold.otf", "TH-Aeonik-BookBoldItalic.otf",
    "TH-Aeonik-SemiBoldBold.otf", "TH-Aeonik-SemiBoldBoldItalic.otf",
]


def outline_files():
    """The 20 files that carry distinct outlines — what a measuring script wants."""
    return [cfg["file"] + ".otf" for cfg in FACES.values()]


def shipped_files():
    """All 20 files that get installed. Same set; see SHIPPED."""
    return outline_files()


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

def set_name(nt, nid, val, pid=3, peid=1, lid=0x0409):
    if val is None:
        nt.removeNames(nameID=nid, platformID=pid, platEncID=peid, langID=lid)
        return
    nt.setName(val, nid, pid, peid, lid)


def apply_face_metadata(font, key, cfg=None, stamp=None):
    """Write one face's identity: name table, OS/2, head, CFF name.

    Shared by the builder's own metadata step and by the standalone pass, so
    there is exactly one implementation of what a TH Aeonik face is called.
    """
    cfg = cfg or SHIPPED[key]
    stamp = stamp or build_stamp()
    nt = font["name"]

    for nid in (1, 2, 4, 6, 16, 17):
        val = cfg[f"nameID{nid}"]
        set_name(nt, nid, val)
        set_name(nt, nid, val, pid=1, peid=0, lid=0)

    identity = {
        0: COPYRIGHT,
        3: f"ICHITA: {cfg['nameID4']}: {VERSION}: {stamp}",
        5: f"Version {VERSION}; build {stamp}",
        7: TRADEMARK,
        8: MANUFACTURER,
        9: DESIGNER,
        10: DESCRIPTION,
        11: VENDOR_URL,
        13: LICENSE,
        14: LICENSE_URL,
    }
    for nid, val in identity.items():
        set_name(nt, nid, val)
        set_name(nt, nid, val, pid=1, peid=0, lid=0)

    os2 = font["OS/2"]
    os2.fsType = 0
    os2.achVendID = VENDOR_ID
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
    font["head"].fontRevision = float(VERSION)

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
    """Re-apply the shipped identity to the 20 faces, renaming as needed."""
    faults = []
    stamp = build_stamp()
    for key, cfg in FACES.items():
        src = _resolve_source(out_dir, cfg)
        if src is None:
            faults.append(f"{key}: no source file "
                          f"({cfg['file']}.otf or {cfg.get('legacy')}.otf)")
            continue
        dst = out_dir / f"{cfg['file']}.otf"
        before = outline_digest(src)

        font = TTFont(str(src))
        apply_face_metadata(font, key, cfg, stamp)
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


def retire_duplicates(out_dir, verbose=True):
    """Delete the six duplicate faces the ten-weight deck replaced."""
    for name in RETIRED_FILES:
        p = out_dir / name
        if p.exists():
            p.unlink()
            if verbose:
                print(f"  removed {name}  (duplicate outlines, retired 2026-08-09)")
    return []


def apply_all(out_dir=OUTPUT_DIR, verbose=True):
    if verbose:
        print(f"Shipped faces -> {out_dir}")
        print("\n[1/2] Outline faces")
    faults = restyle_outline_faces(out_dir, verbose)
    if verbose:
        print("\n[2/2] Retired duplicates")
    faults += retire_duplicates(out_dir, verbose)
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
    slots = {}          # (usWeightClass, italic) -> key

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

        # Identity. Checked for CONTENT, not just presence — nameID13 pointing
        # at This Is Our Shop's EULA was present and wrong for nine builds.
        for nid, want in ((0, COPYRIGHT), (7, TRADEMARK), (8, MANUFACTURER),
                          (9, DESIGNER), (10, DESCRIPTION), (11, VENDOR_URL),
                          (13, LICENSE), (14, LICENSE_URL)):
            got = nt.getDebugName(nid)
            if (got or None) != want:
                faults.append(f"{key}: nameID{nid} is {(got or '')[:40]!r}..., "
                              f"want the ICHITA text")
        if os2.achVendID != VENDOR_ID:
            faults.append(f"{key}: achVendID {os2.achVendID!r}, want {VENDOR_ID!r}")

        # The version is asserted by SHAPE, and the build date is reported
        # rather than demanded — see build_stamp(). What must not drift is the
        # release number, and nameID3 must agree with nameID5.
        v5 = nt.getDebugName(5) or ""
        v3 = nt.getDebugName(3) or ""
        prefix = f"Version {VERSION}; build "
        if not v5.startswith(prefix) or len(v5) != len(prefix) + 10:
            faults.append(f"{key}: nameID5 is {v5!r}, want "
                          f"{prefix!r} + a YYYY-MM-DD date")
        elif not v3.endswith(v5[len(prefix):]):
            faults.append(f"{key}: nameID3 {v3!r} disagrees with nameID5 {v5!r} "
                          f"— one of them is from an older build")
        if abs(head.fontRevision - float(VERSION)) > 1e-6:
            faults.append(f"{key}: head.fontRevision {head.fontRevision}, "
                          f"want {float(VERSION)}")

        for nid in (3, 4, 6):
            val = nt.getDebugName(nid)
            if val in seen[nid]:
                faults.append(f"{key}: nameID{nid} {val!r} collides with "
                              f"{seen[nid][val]} — Windows will shadow one of them")
            seen[nid][val] = key

        # THE INVARIANT THIS WHOLE STRUCTURE EXISTS FOR. A typographic family
        # resolves correctly only while every member holds a unique
        # (weight, slant); nothing asserted it before 2026-08-09, and shipping
        # three faces at 500 is what forced six Settings cards.
        slot = (os2.usWeightClass, bool(os2.fsSelection & ITALIC))
        if slot in slots:
            faults.append(
                f"{key}: weight {slot[0]}{' italic' if slot[1] else ''} is "
                f"already taken by {slots[slot]} — two faces in one typographic "
                f"family cannot share a weight")
        slots[slot] = key

        families.setdefault(cfg["nameID1"], {})[cfg["nameID2"]] = key
        font.close()

    # A family holds a real bold, or Word synthesises one. Air and Thin are
    # exempt because their counter aperture is more than double the floor, and
    # the exemption is asserted BOTH ways so it stays a decision.
    for fam, members in sorted(families.items()):
        exempt = fam in NO_BOLD_SLOT
        has_bold = "Bold" in members
        if not exempt and "Regular" in members and not has_bold:
            faults.append(f"family {fam!r} has no Bold member — Word will "
                          f"double-strike it")
        if not exempt and "Italic" in members and "Bold Italic" not in members:
            faults.append(f"family {fam!r} has no Bold Italic member")
        if exempt and has_bold:
            faults.append(f"family {fam!r} is in NO_BOLD_SLOT but has a Bold "
                          f"member — one of the two is wrong")
        extra = set(members) - {"Regular", "Italic", "Bold", "Bold Italic"}
        if extra:
            faults.append(f"family {fam!r} has non-RIBBI nameID2 {sorted(extra)}")

    missing_exempt = NO_BOLD_SLOT - set(families)
    if missing_exempt:
        faults.append(f"NO_BOLD_SLOT names {sorted(missing_exempt)}, which ship "
                      f"no faces — the exemption is stale")

    # Anything in the directory that is not a shipped face is stale.
    # install-fonts.sh globs the directory, so an orphan is not clutter — it is
    # a retired face that reappears in somebody's font menu.
    expected = set(shipped_files())
    for p in sorted(out_dir.glob("*.otf")):
        if p.name not in expected:
            faults.append(f"{p.name} is not a shipped face — delete it, or "
                          f"install-fonts.sh will put a retired face back "
                          f"in the font menu")

    if verbose:
        for fam, members in sorted(families.items()):
            line = "  ".join(f"{s}={members[s]}" for s in
                             ("Regular", "Italic", "Bold", "Bold Italic")
                             if s in members)
            tail = "   (no bold slot, by design)" if fam in NO_BOLD_SLOT else ""
            print(f"  {fam:20s} {line}{tail}")
        print()
        if faults:
            print(f"FAIL — {len(faults)} fault(s)")
            for f in faults:
                print(f"  - {f}")
        else:
            ladder = " ".join(str(w) for w, i in sorted(slots) if not i)
            print(f"OK — {len(SHIPPED)} shipped faces, "
                  f"{len(FACES)} outline sets, {len(families)} families, "
                  f"no shared (weight, slant)")
            print(f"     weights {ladder}")
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
