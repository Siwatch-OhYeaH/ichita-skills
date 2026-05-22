# Ichita HTML→PNG Slide Template — Canonical Chrome

These two files **are** the Ichita slide template for any deck built as HTML pages
rendered to PNG (the html→png build path). They are the real master backgrounds,
extracted from the production Ichita template. **Use them as-is. Never redraw the
chrome in CSS.**

| File | Use |
|------|-----|
| `ichita-content-bg.png` | Content-slide background. Transparent PNG: the dark navy frame, top-left ICHITA logo notch, thin border and bottom-left chamfer are **opaque**; the white card interior is **transparent**. |
| `ichita-cover-bg.jpg` | Full dark-navy cover / closing background (ICHITA logo bottom-centre). |

## How to use (1280×720 canvas)

```css
.slide { position:relative; width:1280px; height:720px; overflow:hidden;
         background:#FFFFFF; }            /* white shows through the card area */
.slide::before { content:''; position:absolute; inset:0; z-index:1;
  background-image:url('ichita-content-bg.png');
  background-size:1280px 720px; pointer-events:none; }
/* all slide content sits at z-index:2 or above */
```

- **Safe content zone:** `left:44 top:92 right:44 bottom:50` (≈ 1192 × 578).
  Stay inside it — content outside collides with the dark frame / notch / chamfer.
- **Title:** top-right, `left:430` (clears the notch) to `right:42`, dark navy
  `#263338`, Aeonik Bold ~32px, one line ≤ 40 chars.
- **Colours:** navy `#263338` · blue `#2978FF` · green `#2FA24D` · amber `#F5A623`
  · red `#E83E3E`. Fonts: Aeonik everything.

## Why this exists

2026-05-22 — a session restyling the TNCC sweetener deck hand-redrew this chrome in
CSS, inverted it (white-background slide, no dark frame), and shipped a deck with the
Ichita identity deleted. The chrome is **not** something to interpret from a
screenshot — it is this file. Drop it in as the background; do not reconstruct it.
