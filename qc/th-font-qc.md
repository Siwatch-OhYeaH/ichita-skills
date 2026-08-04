# TH font QC — 2026-08-04

Print-path counterpart to `test-output/th-font-specimen.html`. The specimen proves the fonts in a browser; this document proves them in Word and in a printed PDF, which is where the defects have actually shown up.

Every section states the pass condition. Where a check can be made mechanically it is, by `scripts/qc_check_th_font_doc.py` — do not sign these off by eye.

## 1. Line pitch — the open issue

Reported symptom: too much space between lines, top to bottom.

Measured vertical metrics of the shipped fonts against the Latin source each was built from:

| font | hhea asc/desc/gap | hhea line | typo asc/desc/gap | winAsc+winDesc | USE_TYPO |
|---|---|---|---|---|---|
| TH Aeonik | 1000/-200/0 | 1200 (1.200 em) | 1000/-200/0 | **1800** (1.800 em) | True |
| Aeonik (source) | 1000/-200/0 | 1200 (1.200 em) | 700/-200/300 | **1200** (1.200 em) | False |
| TH Slussen | 1210/-415/0 | 1625 (1.625 em) | 1210/-415/0 | **1980** (1.980 em) | True |
| Slussen (source) | 1074/-272/166 | 1512 (1.512 em) | 1074/-272/166 | **1596** (1.596 em) | True |
| Bai Jamjuree | 1000/-250/0 | 1250 (1.250 em) | 1000/-250/0 | **1786** (1.786 em) | True |


A font declares its line box three separate ways and different renderers believe different ones. `usWinAscent`/`usWinDescent` must stay wide enough to avoid clipping Thai — the tone marks reach +1206 and the below-vowels −488 — but if the renderer uses that pair for *leading* as well, every line inherits the Thai extremes even on a pure-Latin line.

**The discriminator.** TH Slussen's typo and hhea metrics are identical to source Slussen; only `usWinDescent` changed. So:

— loose pitch in **both** families → the renderer is on the win metrics

— loose pitch in **Aeonik only** → the renderer is on the typo metrics, and Aeonik's `USE_TYPO_METRICS` flip is the whole cause


### 1a. Single line spacing — diagnostic

Six lines per block: Latin, Latin, Thai, Thai, Latin, Latin. **Pass = all six baselines evenly spaced, and the block heights match the Latin baseline block.** If the Thai lines push apart, or a whole block is taller than the Latin one, that block's font is leading off the wrong metric.

::: {custom-style="QCPitchLabel"}
TH Aeonik — Single (source: Aeonik)
:::

::: {custom-style="QCPitchAeonikSingle"}
Latin only line one with no tall or deep marks at all
:::

::: {custom-style="QCPitchAeonikSingle"}
Latin only line two with no tall or deep marks at all
:::

::: {custom-style="QCPitchAeonikSingle"}
ปูผู้ญี่ปุ่นซึ่งหนึ่งน้ำเชื่อมกรุ๊ปเกี๊ยวฟั้นปั่น
:::

::: {custom-style="QCPitchAeonikSingle"}
ปูผู้ญี่ปุ่นซึ่งหนึ่งน้ำเชื่อมกรุ๊ปเกี๊ยวฟั้นปั่น
:::

::: {custom-style="QCPitchAeonikSingle"}
Latin only line three with no tall or deep marks at all
:::

::: {custom-style="QCPitchAeonikSingle"}
Latin only line four with no tall or deep marks at all
:::

::: {custom-style="QCPitchLabel"}
TH Slussen — Single (source: Slussen)
:::

::: {custom-style="QCPitchSlussenSingle"}
Latin only line one with no tall or deep marks at all
:::

::: {custom-style="QCPitchSlussenSingle"}
Latin only line two with no tall or deep marks at all
:::

::: {custom-style="QCPitchSlussenSingle"}
ปูผู้ญี่ปุ่นซึ่งหนึ่งน้ำเชื่อมกรุ๊ปเกี๊ยวฟั้นปั่น
:::

::: {custom-style="QCPitchSlussenSingle"}
ปูผู้ญี่ปุ่นซึ่งหนึ่งน้ำเชื่อมกรุ๊ปเกี๊ยวฟั้นปั่น
:::

::: {custom-style="QCPitchSlussenSingle"}
Latin only line three with no tall or deep marks at all
:::

::: {custom-style="QCPitchSlussenSingle"}
Latin only line four with no tall or deep marks at all
:::

::: {custom-style="QCPitchLabel"}
Bai Jamjuree — Single (source: (Thai reference))
:::

::: {custom-style="QCPitchBaiSingle"}
Latin only line one with no tall or deep marks at all
:::

::: {custom-style="QCPitchBaiSingle"}
Latin only line two with no tall or deep marks at all
:::

::: {custom-style="QCPitchBaiSingle"}
ปูผู้ญี่ปุ่นซึ่งหนึ่งน้ำเชื่อมกรุ๊ปเกี๊ยวฟั้นปั่น
:::

::: {custom-style="QCPitchBaiSingle"}
ปูผู้ญี่ปุ่นซึ่งหนึ่งน้ำเชื่อมกรุ๊ปเกี๊ยวฟั้นปั่น
:::

::: {custom-style="QCPitchBaiSingle"}
Latin only line three with no tall or deep marks at all
:::

::: {custom-style="QCPitchBaiSingle"}
Latin only line four with no tall or deep marks at all
:::

::: {custom-style="QCPitchLabel"}
Aeonik — Single (source: (Latin baseline))
:::

::: {custom-style="QCPitchLatinSingle"}
Latin only line one with no tall or deep marks at all
:::

::: {custom-style="QCPitchLatinSingle"}
Latin only line two with no tall or deep marks at all
:::

::: {custom-style="QCPitchLatinSingle"}
Latin only line three with no tall or deep marks at all
:::

::: {custom-style="QCPitchLatinSingle"}
Latin only line four with no tall or deep marks at all
:::

::: {custom-style="QCPitchLatinSingle"}
Latin only line five with no tall or deep marks at all
:::

::: {custom-style="QCPitchLatinSingle"}
Latin only line six with no tall or deep marks at all
:::


### 1b. Exactly 14 pt — proposed fix

Same text, leading pinned to 14 pt so the font's declared metrics are bypassed. **Pass = uniform pitch and no clipped Thai marks.** If this reads correctly while 1a does not, the glyphs are fine and the defect is purely metadata.

::: {custom-style="QCPitchLabel"}
TH Aeonik — Exactly 14 pt
:::

::: {custom-style="QCPitchAeonikExact"}
Latin only line one with no tall or deep marks at all
:::

::: {custom-style="QCPitchAeonikExact"}
Latin only line two with no tall or deep marks at all
:::

::: {custom-style="QCPitchAeonikExact"}
ปูผู้ญี่ปุ่นซึ่งหนึ่งน้ำเชื่อมกรุ๊ปเกี๊ยวฟั้นปั่น
:::

::: {custom-style="QCPitchAeonikExact"}
ปูผู้ญี่ปุ่นซึ่งหนึ่งน้ำเชื่อมกรุ๊ปเกี๊ยวฟั้นปั่น
:::

::: {custom-style="QCPitchAeonikExact"}
Latin only line three with no tall or deep marks at all
:::

::: {custom-style="QCPitchAeonikExact"}
Latin only line four with no tall or deep marks at all
:::

::: {custom-style="QCPitchLabel"}
TH Slussen — Exactly 14 pt
:::

::: {custom-style="QCPitchSlussenExact"}
Latin only line one with no tall or deep marks at all
:::

::: {custom-style="QCPitchSlussenExact"}
Latin only line two with no tall or deep marks at all
:::

::: {custom-style="QCPitchSlussenExact"}
ปูผู้ญี่ปุ่นซึ่งหนึ่งน้ำเชื่อมกรุ๊ปเกี๊ยวฟั้นปั่น
:::

::: {custom-style="QCPitchSlussenExact"}
ปูผู้ญี่ปุ่นซึ่งหนึ่งน้ำเชื่อมกรุ๊ปเกี๊ยวฟั้นปั่น
:::

::: {custom-style="QCPitchSlussenExact"}
Latin only line three with no tall or deep marks at all
:::

::: {custom-style="QCPitchSlussenExact"}
Latin only line four with no tall or deep marks at all
:::

::: {custom-style="QCPitchLabel"}
Bai Jamjuree — Exactly 14 pt
:::

::: {custom-style="QCPitchBaiExact"}
Latin only line one with no tall or deep marks at all
:::

::: {custom-style="QCPitchBaiExact"}
Latin only line two with no tall or deep marks at all
:::

::: {custom-style="QCPitchBaiExact"}
ปูผู้ญี่ปุ่นซึ่งหนึ่งน้ำเชื่อมกรุ๊ปเกี๊ยวฟั้นปั่น
:::

::: {custom-style="QCPitchBaiExact"}
ปูผู้ญี่ปุ่นซึ่งหนึ่งน้ำเชื่อมกรุ๊ปเกี๊ยวฟั้นปั่น
:::

::: {custom-style="QCPitchBaiExact"}
Latin only line three with no tall or deep marks at all
:::

::: {custom-style="QCPitchBaiExact"}
Latin only line four with no tall or deep marks at all
:::

::: {custom-style="QCPitchLabel"}
Aeonik — Exactly 14 pt
:::

::: {custom-style="QCPitchLatinExact"}
Latin only line one with no tall or deep marks at all
:::

::: {custom-style="QCPitchLatinExact"}
Latin only line two with no tall or deep marks at all
:::

::: {custom-style="QCPitchLatinExact"}
Latin only line three with no tall or deep marks at all
:::

::: {custom-style="QCPitchLatinExact"}
Latin only line four with no tall or deep marks at all
:::

::: {custom-style="QCPitchLatinExact"}
Latin only line five with no tall or deep marks at all
:::

::: {custom-style="QCPitchLatinExact"}
Latin only line six with no tall or deep marks at all
:::


## 2. Letters

**Pass = every slot filled, no tofu boxes, no fallback glyph in a visibly different style.**


### 2.1 TH Aeonik


Thai consonants — 44


::: {custom-style="QCGridAeonik"}
ก  ข  ฃ  ค  ฅ  ฆ  ง  จ  ฉ  ช  ซ  ฌ  ญ  ฎ  ฏ
:::
::: {custom-style="QCGridAeonik"}
ฐ  ฑ  ฒ  ณ  ด  ต  ถ  ท  ธ  น  บ  ป  ผ  ฝ  พ
:::
::: {custom-style="QCGridAeonik"}
ฟ  ภ  ม  ย  ร  ล  ว  ศ  ษ  ส  ห  ฬ  อ  ฮ
:::


Thai vowels and signs


::: {custom-style="QCGridAeonik"}
ะ  า  ำ  เ  แ  โ  ใ  ไ  ๅ  ๆ  ฯ
:::


Latin uppercase


::: {custom-style="QCGridAeonik"}
A  B  C  D  E  F  G  H  I  J  K  L  M  N  O  P  Q  R  S  T  U  V  W  X  Y  Z
:::


Latin lowercase


::: {custom-style="QCGridAeonik"}
a  b  c  d  e  f  g  h  i  j  k  l  m  n  o  p  q  r  s  t  u  v  w  x  y  z
:::


### 2.2 TH Slussen


Thai consonants — 44


::: {custom-style="QCGridSlussen"}
ก  ข  ฃ  ค  ฅ  ฆ  ง  จ  ฉ  ช  ซ  ฌ  ญ  ฎ  ฏ
:::
::: {custom-style="QCGridSlussen"}
ฐ  ฑ  ฒ  ณ  ด  ต  ถ  ท  ธ  น  บ  ป  ผ  ฝ  พ
:::
::: {custom-style="QCGridSlussen"}
ฟ  ภ  ม  ย  ร  ล  ว  ศ  ษ  ส  ห  ฬ  อ  ฮ
:::


Thai vowels and signs


::: {custom-style="QCGridSlussen"}
ะ  า  ำ  เ  แ  โ  ใ  ไ  ๅ  ๆ  ฯ
:::


Latin uppercase


::: {custom-style="QCGridSlussen"}
A  B  C  D  E  F  G  H  I  J  K  L  M  N  O  P  Q  R  S  T  U  V  W  X  Y  Z
:::


Latin lowercase


::: {custom-style="QCGridSlussen"}
a  b  c  d  e  f  g  h  i  j  k  l  m  n  o  p  q  r  s  t  u  v  w  x  y  z
:::


## 3. Symbols and digits

**Pass = all present; Thai and Latin digits the same height and weight as the surrounding text.**


**TH Aeonik**


Latin digits


::: {custom-style="QCGridAeonik"}
0  1  2  3  4  5  6  7  8  9
:::

Thai digits


::: {custom-style="QCGridAeonik"}
๐  ๑  ๒  ๓  ๔  ๕  ๖  ๗  ๘  ๙
:::

Punctuation and symbols


::: {custom-style="QCGridAeonik"}
\.  \,  \:  \;  \!  \?  \'  \"  \(  \)  \[  \]  \{  \}  \/  \\  \-  –  —  \_
:::
::: {custom-style="QCGridAeonik"}
\@  \#  \$  \%  \&  \*  \+  \=  \<  \>  \~  \^  \|  °  €  £  ¥  §  ¶  †
:::
::: {custom-style="QCGridAeonik"}
‡
:::


**TH Slussen**


Latin digits


::: {custom-style="QCGridSlussen"}
0  1  2  3  4  5  6  7  8  9
:::

Thai digits


::: {custom-style="QCGridSlussen"}
๐  ๑  ๒  ๓  ๔  ๕  ๖  ๗  ๘  ๙
:::

Punctuation and symbols


::: {custom-style="QCGridSlussen"}
\.  \,  \:  \;  \!  \?  \'  \"  \(  \)  \[  \]  \{  \}  \/  \\  \-  –  —  \_
:::
::: {custom-style="QCGridSlussen"}
\@  \#  \$  \%  \&  \*  \+  \=  \<  \>  \~  \^  \|  °  €  £  ¥  §  ¶  †
:::
::: {custom-style="QCGridSlussen"}
‡
:::


## 4. Syllables and mark stacking

The hardest part of a merged Thai font. **Pass = tone mark sits directly above its vowel, not beside or on top of it; below-vowels clear the baseline; nothing collides with the line above.**


**TH Aeonik**


Two- and three-level clusters


::: {custom-style="QCGridAeonik"}
น้ำเชื่อม  ฟั้น  ญี่  ผู้  ซึ่ง  หนึ่ง  ปั่น  เกี๊ยว
:::

Tone and vowel ramp on a single base


::: {custom-style="QCGridAeonik"}
ก่ ก้ ก๊ ก๋ ก์ กั กิ กี กึ กื กุ กู
:::

Mark inventory on ก


::: {custom-style="QCGridAeonik"}
กั  กิ  กี  กึ  กื  กุ  กู  ก็  ก่  ก้  ก๊  ก๋  ก์  กํ
:::


**TH Slussen**


Two- and three-level clusters


::: {custom-style="QCGridSlussen"}
น้ำเชื่อม  ฟั้น  ญี่  ผู้  ซึ่ง  หนึ่ง  ปั่น  เกี๊ยว
:::

Tone and vowel ramp on a single base


::: {custom-style="QCGridSlussen"}
ก่ ก้ ก๊ ก๋ ก์ กั กิ กี กึ กื กุ กู
:::

Mark inventory on ก


::: {custom-style="QCGridSlussen"}
กั  กิ  กี  กึ  กื  กุ  กู  ก็  ก่  ก้  ก๊  ก๋  ก์  กํ
:::


## 5. Size ramp

**Pass = legible and correctly proportioned at every size; no clipping at 8–11 pt, no mark collision at 36–72 pt.** The one thing the CFF→glyf conversion genuinely risked is Latin at 9–11 pt, where Slussen's original stem hints were dropped — look hardest there.


**TH Aeonik**


::: {custom-style="QCSizeAeonik8"}
8 pt — The quick brown fox jumps over the lazy dog — น้ำเชื่อมฟั้นญี่
:::

::: {custom-style="QCSizeAeonik9"}
9 pt — The quick brown fox jumps over the lazy dog — น้ำเชื่อมฟั้นญี่
:::

::: {custom-style="QCSizeAeonik10"}
10 pt — The quick brown fox jumps over the lazy dog — น้ำเชื่อมฟั้นญี่
:::

::: {custom-style="QCSizeAeonik11"}
11 pt — The quick brown fox jumps over the lazy dog — น้ำเชื่อมฟั้นญี่
:::

::: {custom-style="QCSizeAeonik12"}
12 pt — The quick brown fox jumps over the lazy dog — น้ำเชื่อมฟั้นญี่
:::

::: {custom-style="QCSizeAeonik14"}
14 pt — The quick brown fox jumps over the lazy dog — น้ำเชื่อมฟั้นญี่
:::

::: {custom-style="QCSizeAeonik16"}
16 pt — The quick brown fox jumps over the lazy dog — น้ำเชื่อมฟั้นญี่
:::

::: {custom-style="QCSizeAeonik18"}
18 pt — The quick brown fox jumps over the lazy dog — น้ำเชื่อมฟั้นญี่
:::

::: {custom-style="QCSizeAeonik24"}
24 pt — The quick brown fox jumps over the lazy dog — น้ำเชื่อมฟั้นญี่
:::

::: {custom-style="QCSizeAeonik36"}
36 pt — The quick brown fox jumps over the lazy dog — น้ำเชื่อมฟั้นญี่
:::

::: {custom-style="QCSizeAeonik48"}
48 pt — The quick brown fox jumps over the lazy dog — น้ำเชื่อมฟั้นญี่
:::

::: {custom-style="QCSizeAeonik72"}
72 pt — The quick brown fox jumps over the lazy dog — น้ำเชื่อมฟั้นญี่
:::


**TH Slussen**


::: {custom-style="QCSizeSlussen8"}
8 pt — The quick brown fox jumps over the lazy dog — น้ำเชื่อมฟั้นญี่
:::

::: {custom-style="QCSizeSlussen9"}
9 pt — The quick brown fox jumps over the lazy dog — น้ำเชื่อมฟั้นญี่
:::

::: {custom-style="QCSizeSlussen10"}
10 pt — The quick brown fox jumps over the lazy dog — น้ำเชื่อมฟั้นญี่
:::

::: {custom-style="QCSizeSlussen11"}
11 pt — The quick brown fox jumps over the lazy dog — น้ำเชื่อมฟั้นญี่
:::

::: {custom-style="QCSizeSlussen12"}
12 pt — The quick brown fox jumps over the lazy dog — น้ำเชื่อมฟั้นญี่
:::

::: {custom-style="QCSizeSlussen14"}
14 pt — The quick brown fox jumps over the lazy dog — น้ำเชื่อมฟั้นญี่
:::

::: {custom-style="QCSizeSlussen16"}
16 pt — The quick brown fox jumps over the lazy dog — น้ำเชื่อมฟั้นญี่
:::

::: {custom-style="QCSizeSlussen18"}
18 pt — The quick brown fox jumps over the lazy dog — น้ำเชื่อมฟั้นญี่
:::

::: {custom-style="QCSizeSlussen24"}
24 pt — The quick brown fox jumps over the lazy dog — น้ำเชื่อมฟั้นญี่
:::

::: {custom-style="QCSizeSlussen36"}
36 pt — The quick brown fox jumps over the lazy dog — น้ำเชื่อมฟั้นญี่
:::

::: {custom-style="QCSizeSlussen48"}
48 pt — The quick brown fox jumps over the lazy dog — น้ำเชื่อมฟั้นญี่
:::

::: {custom-style="QCSizeSlussen72"}
72 pt — The quick brown fox jumps over the lazy dog — น้ำเชื่อมฟั้นญี่
:::


## 6. Style — roman and italic

TH Aeonik ships italics; TH Slussen does not. **Pass = the italic rows are genuinely slanted drawn forms, and Word is not faking a slant on the upright.** A synthesised oblique on Thai is a defect.


[TH Aeonik Light]{custom-style="QCAeonikLight"} — [The quick brown fox jumps over the lazy dog]{custom-style="QCAeonikLight"} [เป็นมนุษย์สุดประเสริฐเลิศคุณค่า กว่าบรรดาฝูงสัตว์เดรัจฉาน]{custom-style="QCAeonikLight"}


[TH Aeonik Light Italic]{custom-style="QCAeonikLightItalic"} — [The quick brown fox jumps over the lazy dog]{custom-style="QCAeonikLightItalic"} [เป็นมนุษย์สุดประเสริฐเลิศคุณค่า กว่าบรรดาฝูงสัตว์เดรัจฉาน]{custom-style="QCAeonikLightItalic"}


[TH Aeonik Regular]{custom-style="QCAeonikRegular"} — [The quick brown fox jumps over the lazy dog]{custom-style="QCAeonikRegular"} [เป็นมนุษย์สุดประเสริฐเลิศคุณค่า กว่าบรรดาฝูงสัตว์เดรัจฉาน]{custom-style="QCAeonikRegular"}


[TH Aeonik Regular Italic]{custom-style="QCAeonikItalic"} — [The quick brown fox jumps over the lazy dog]{custom-style="QCAeonikItalic"} [เป็นมนุษย์สุดประเสริฐเลิศคุณค่า กว่าบรรดาฝูงสัตว์เดรัจฉาน]{custom-style="QCAeonikItalic"}


[TH Aeonik Bold]{custom-style="QCAeonikBold"} — [The quick brown fox jumps over the lazy dog]{custom-style="QCAeonikBold"} [เป็นมนุษย์สุดประเสริฐเลิศคุณค่า กว่าบรรดาฝูงสัตว์เดรัจฉาน]{custom-style="QCAeonikBold"}


[TH Aeonik Bold Italic]{custom-style="QCAeonikBoldItalic"} — [The quick brown fox jumps over the lazy dog]{custom-style="QCAeonikBoldItalic"} [เป็นมนุษย์สุดประเสริฐเลิศคุณค่า กว่าบรรดาฝูงสัตว์เดรัจฉาน]{custom-style="QCAeonikBoldItalic"}


## 7. Weight

**Pass = each step visibly heavier than the one above, in Thai as well as Latin, with no two steps identical.** TH Slussen Medium and SemiBold must be distinct — they register as separate families and are the pair most likely to collapse.

::: {custom-style="QCWeightAeonikLight"}
TH Aeonik Light 300 — Handgloves 123 — น้ำเชื่อมผู้ที่ซึ่งหนึ่ง
:::

::: {custom-style="QCWeightAeonikRegular"}
TH Aeonik Regular 400 — Handgloves 123 — น้ำเชื่อมผู้ที่ซึ่งหนึ่ง
:::

::: {custom-style="QCWeightAeonikBold"}
TH Aeonik Bold 700 — Handgloves 123 — น้ำเชื่อมผู้ที่ซึ่งหนึ่ง
:::

::: {custom-style="QCWeightSlussenRegular"}
TH Slussen Regular 400 — Handgloves 123 — น้ำเชื่อมผู้ที่ซึ่งหนึ่ง
:::

::: {custom-style="QCWeightSlussenMedium"}
TH Slussen Medium 500 — Handgloves 123 — น้ำเชื่อมผู้ที่ซึ่งหนึ่ง
:::

::: {custom-style="QCWeightSlussenSemiBold"}
TH Slussen SemiBold 600 — Handgloves 123 — น้ำเชื่อมผู้ที่ซึ่งหนึ่ง
:::

::: {custom-style="QCWeightSlussenBold"}
TH Slussen Bold 700 — Handgloves 123 — น้ำเชื่อมผู้ที่ซึ่งหนึ่ง
:::


## 8. Horizontal spacing

**Pass = the word space is the Latin one (it is taken from the Latin source deliberately, not from Bai Jamjuree), kern pairs are not gappy, and mixed Thai/Latin runs sit on a common baseline with even colour.**


**TH Aeonik**


Kern pairs


::: {custom-style="QCGridAeonik"}
Ta  To  Ya  Wo  AV  LT  P\.  r\,  fi  fl  ffi
:::

Mixed script


::: {custom-style="QCGridAeonik"}
ICHITA อิชิตะ — รายงาน Q3 ปี 2026 (Revenue +12.5%)
:::

Word-space ruler — the pipes must be evenly spaced


::: {custom-style="QCGridAeonik"}
| a | b | c | d | e | f | g | h |
:::

::: {custom-style="QCGridAeonik"}
| ก | ข | ค | ง | จ | ฉ | ช | ซ |
:::


**TH Slussen**


Kern pairs


::: {custom-style="QCGridSlussen"}
Ta  To  Ya  Wo  AV  LT  P\.  r\,  fi  fl  ffi
:::

Mixed script


::: {custom-style="QCGridSlussen"}
ICHITA อิชิตะ — รายงาน Q3 ปี 2026 (Revenue +12.5%)
:::

Word-space ruler — the pipes must be evenly spaced


::: {custom-style="QCGridSlussen"}
| a | b | c | d | e | f | g | h |
:::

::: {custom-style="QCGridSlussen"}
| ก | ข | ค | ง | จ | ฉ | ช | ซ |
:::


---

Generated by `scripts/build_th_font_qc.py` on 2026-08-04. Verify with `scripts/qc_check_th_font_doc.py`.
