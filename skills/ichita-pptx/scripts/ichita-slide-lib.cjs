/**
 * ichita-slide-lib.cjs — Ichita Branded PPTX Slide Builder Library
 *
 * PptxGenJS wrapper that produces consistent, brand-compliant Ichita presentations.
 *
 * Canvas: 13.333" × 7.5" (LAYOUT_WIDE — standard PowerPoint widescreen)
 * Backgrounds: defineSlideMaster with background.path — NOT per-slide addImage.
 *
 * Usage:
 *   const { createPresentation, slides, blocks, COLORS, FONTS } = require("./ichita-slide-lib.cjs");
 *   const pres = createPresentation({ title: "My Presentation" });
 *   slides.cover(pres, { title: "Ichita Solution Overview", subtitle: "Liquid Sugar Refinery" });
 *   slides.content(pres, { title: "Key Benefits" });
 *   pres.writeFile({ fileName: "output.pptx" });
 *
 * Note: scripts/ichita_slide_lib.py (Python sibling) still uses the old 10×5.625
 * constants — needs a follow-up fix with the same rules.
 */

"use strict";

const path = require("path");

// Lazy-load pptxgenjs — resolve from multiple possible locations
// (ichita-skills has no local node_modules; pptxgenjs lives in the caller's env)
function _requirePptxgen() {
  // 1. Try standard resolution (caller's node_modules or global)
  try { return require("pptxgenjs"); } catch (_) {}
  // 2. Try global npm/fnm prefix
  try {
    const { execSync } = require("child_process");
    const globalPrefix = execSync("npm root -g", { encoding: "utf8" }).trim();
    return require(path.join(globalPrefix, "pptxgenjs"));
  } catch (_) {}
  throw new Error(
    "pptxgenjs not found. Install it: npm install -g pptxgenjs  " +
    "or run from a project that has pptxgenjs in its node_modules."
  );
}

// ---------------------------------------------------------------------------
// Repo root — resolve asset paths relative to ichita-skills repo root
// ---------------------------------------------------------------------------
const REPO_ROOT = path.resolve(__dirname, "../../..");

// ---------------------------------------------------------------------------
// BRAND CONSTANTS
// ---------------------------------------------------------------------------

/** Ichita brand color palette — NO # prefix (PptxGenJS format) */
const COLORS = {
  white:        "FFFFFF",
  blue:         "2978FF",   // Primary accent
  blueLight:    "82B0FF",   // Secondary accent
  blueGrey01:   "CFD9DB",   // Main backdrop canvas
  blueGrey02:   "788F9C",   // Muted text, captions
  blueGrey03:   "263338",   // Primary text, dark backgrounds
  blueBlack:    "171C21",   // Darkest background
  offWhite:     "F8FAFB",   // Card backgrounds
  altRow:       "F0F4F5",   // Table alternating rows
};

/** Chart color sequence — brand-only palette */
const CHART_COLORS = ["2978FF", "263338", "82B0FF", "788F9C", "CFD9DB", "171C21"];

/** Ichita brand fonts */
const FONTS = {
  body:     "Aeonik",          // Regular — body text
  emphasis: "Aeonik",          // Medium weight (use bold:true)
  heading:  "Aeonik",          // Bold heading
  display:  "Betatron",        // Display numerals ONLY — KPIs, section numbers
  thai:     "TH Aeonik",       // Thai text — TH Aeonik (canonical fc-list name)
};

/**
 * Detect Thai characters and return the Thai font face — else default body font.
 */
function _thaiFontFace(text, defaultFace) {
  if (typeof text !== "string") return defaultFace || FONTS.body;
  return /[฀-๿]/.test(text) ? FONTS.thai : (defaultFace || FONTS.body);
}

/** Font sizes — minimums enforced */
const SIZES = {
  slideTitle:    24,   // min 22
  sectionHeader: 14,   // min 12
  body:          12,   // min 11
  tableCell:     11,   // min 10
  statValue:     32,   // min 28
  label:         10,
  footer:         9,
  coverTitle:    40,
  closingTitle:  36,
  sectionNumber: 72,
};

/**
 * Slide dimensions (inches) — standard PowerPoint widescreen (LAYOUT_WIDE).
 * The old lib used 10×5.625 but pres.layout="LAYOUT_WIDE" = 13.333×7.5.
 * All positions are now calculated for the real canvas.
 */
const SLIDE = {
  w: 13.333,
  h: 7.5,
};

/** Margins — match reference Powerpoint Template.pptx */
const MARGIN = {
  top:    0.40,
  right:  0.92,
  bottom: 0.75,
  left:   0.92,
};

/**
 * Title area on content slides — matches master placeholder in reference template.
 * (x=0.92, y=0.40, w=11.50, h=1.45)
 */
const TITLE_POS = {
  x: MARGIN.left,        // 0.92
  y: MARGIN.top,         // 0.40
  w: 11.50,
  h: 1.45,
};

/**
 * Body content area on content slides — below title, above footer row.
 * y=2.00 clears the title+accent bar; h=4.20 leaves the footer row (y≈6.95) clear.
 */
const CONTENT_AREA = {
  x: MARGIN.left,
  y: 2.00,
  w: SLIDE.w - MARGIN.left - MARGIN.right,   // 13.333 - 0.92 - 0.92 = 11.493
  h: 4.20,
};

/** Asset paths */
const ASSETS = {
  contentFrame: path.join(REPO_ROOT, "assets/brand/ichita-content-frame.png"),
  darkBg:       path.join(REPO_ROOT, "assets/brand/ichita-dark-bg.jpg"),
  logoDark:     path.join(REPO_ROOT, "assets/logos/ichita-wordmark-dark-on-white.png"),
  logoWhite:    path.join(REPO_ROOT, "assets/logos/ichita-wordmark-white-on-dark.png"),
  logoOnBlue:   path.join(REPO_ROOT, "assets/logos/ichita-wordmark-dark-on-blue.png"),
};

// ---------------------------------------------------------------------------
// SLIDE MASTER SETUP
// ---------------------------------------------------------------------------

/**
 * Define MASTER_CONTENT and MASTER_DARK on the presentation — called once.
 * Uses defineSlideMaster with background.path so the BG image is set at
 * master level (not per-slide addImage), matching the canonical template rule.
 */
function _ensureMasters(pres) {
  if (pres._ichitaMastersDefined) return;

  // MASTER_CONTENT — content-frame BG (16:9, 4047×2253) + logo + footer URL
  pres.defineSlideMaster({
    title: "MASTER_CONTENT",
    background: { path: ASSETS.contentFrame },
    objects: [
      // Ichita wordmark — bottom left, y≈6.95 row
      {
        image: {
          path: ASSETS.logoDark,
          x: MARGIN.left,
          y: SLIDE.h - 0.55,
          w: 1.2,
          h: 0.25,
        },
      },
      // Website URL — bottom right
      {
        text: {
          text: "www.ichita.co.th",
          options: {
            x: SLIDE.w - MARGIN.right - 2.0,
            y: SLIDE.h - 0.30,
            w: 1.95,
            h: 0.2,
            fontSize: SIZES.footer,
            fontFace: FONTS.body,
            color: COLORS.blueGrey02,
            align: "right",
          },
        },
      },
    ],
  });

  // MASTER_DARK — dark BG (2002×1126, perfect 16:9) + footer URL (no logo — dark bg image has brand mark)
  pres.defineSlideMaster({
    title: "MASTER_DARK",
    background: { path: ASSETS.darkBg },
    objects: [
      {
        text: {
          text: "www.ichita.co.th",
          options: {
            x: SLIDE.w - MARGIN.right - 2.0,
            y: SLIDE.h - 0.30,
            w: 1.95,
            h: 0.2,
            fontSize: SIZES.footer,
            fontFace: FONTS.body,
            color: COLORS.blueGrey02,
            align: "right",
          },
        },
      },
    ],
  });

  // MASTER_SECTION — flat color for section dividers and KPI slides
  pres.defineSlideMaster({
    title: "MASTER_SECTION",
    background: { color: COLORS.blueGrey01 },
    objects: [
      {
        image: {
          path: ASSETS.logoDark,
          x: MARGIN.left,
          y: SLIDE.h - 0.55,
          w: 1.2,
          h: 0.25,
        },
      },
      {
        text: {
          text: "www.ichita.co.th",
          options: {
            x: SLIDE.w - MARGIN.right - 2.0,
            y: SLIDE.h - 0.30,
            w: 1.95,
            h: 0.2,
            fontSize: SIZES.footer,
            fontFace: FONTS.body,
            color: COLORS.blueGrey02,
            align: "right",
          },
        },
      },
    ],
  });

  pres._ichitaMastersDefined = true;
}

// ---------------------------------------------------------------------------
// HELPERS (internal — no longer do per-slide chrome; masters handle it)
// ---------------------------------------------------------------------------

/** Add top accent line (blue, full width) — used on dark slides */
function _addTopAccentLine(slide) {
  slide.addShape("rect", {
    x: 0, y: 0,
    w: SLIDE.w, h: 0.06,
    fill: { color: COLORS.blue },
    line: { color: COLORS.blue, width: 0 },
  });
}

// ---------------------------------------------------------------------------
// createPresentation
// ---------------------------------------------------------------------------

/**
 * Create a PptxGenJS instance pre-configured for Ichita.
 * @param {object} opts
 * @param {string} [opts.title]    Presentation title (metadata)
 * @param {string} [opts.subject]  Presentation subject
 * @param {string} [opts.author]   Author name
 * @returns {PptxGenJS}
 */
function createPresentation(opts = {}) {
  const pptxgen = _requirePptxgen();
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";   // 13.333" × 7.5" (standard widescreen)
  if (opts.title)   pres.title   = opts.title;
  if (opts.subject) pres.subject = opts.subject;
  pres.author = opts.author || "Ichita Co., Ltd.";
  return pres;
}

// ---------------------------------------------------------------------------
// SLIDES — layout functions
// ---------------------------------------------------------------------------

const slides = {

  /**
   * cover — dark bg (MASTER_DARK), accent bars, white text
   */
  cover(pres, opts = {}) {
    const { title = "", subtitle = "", date = "" } = opts;
    _ensureMasters(pres);
    const slide = pres.addSlide({ masterName: "MASTER_DARK" });

    // Top accent line — blue, full width
    _addTopAccentLine(slide);

    // Left accent bar — blue, 0.08" wide, full height
    slide.addShape("rect", {
      x: 0.6, y: 0,
      w: 0.08, h: SLIDE.h,
      fill: { color: COLORS.blue },
      line: { color: COLORS.blue, width: 0 },
    });

    // Title — positioned for the wider 13.333" canvas
    slide.addText(title, {
      x: 1.0, y: 1.5,
      w: 10.5, h: 1.4,
      fontSize: SIZES.coverTitle,
      fontFace: FONTS.heading,
      bold: true,
      color: COLORS.white,
      wrap: true,
    });

    // Subtitle
    if (subtitle) {
      slide.addText(subtitle, {
        x: 1.0, y: 3.6,
        w: 10.0, h: 0.55,
        fontSize: SIZES.sectionHeader,
        fontFace: FONTS.body,
        color: COLORS.blue,
        wrap: true,
      });
    }

    // Date
    if (date) {
      slide.addText(date, {
        x: 1.0, y: 4.3,
        w: 6.0, h: 0.35,
        fontSize: SIZES.label,
        fontFace: FONTS.body,
        color: COLORS.blueGrey02,
      });
    }

    // Footer URL is in MASTER_DARK — no _addFooter call needed
    return slide;
  },

  /**
   * sectionDivider — MASTER_SECTION bg, big Betatron number, title
   */
  sectionDivider(pres, opts = {}) {
    const { number = "", title = "", subtitle = "" } = opts;
    _ensureMasters(pres);
    const slide = pres.addSlide({ masterName: "MASTER_SECTION" });

    // Big section number — Betatron, right-aligned, blue
    slide.addText(String(number), {
      x: 0, y: 0.5,
      w: SLIDE.w - MARGIN.right,
      h: 2.5,
      fontSize: SIZES.sectionNumber,
      fontFace: FONTS.display,
      color: COLORS.blue,
      align: "right",
    });

    // Title
    slide.addText(title, {
      x: MARGIN.left, y: 3.2,
      w: 10.0, h: 1.0,
      fontSize: 28,
      fontFace: FONTS.heading,
      bold: true,
      color: COLORS.blueGrey03,
      wrap: true,
    });

    // Subtitle
    if (subtitle) {
      slide.addText(subtitle, {
        x: MARGIN.left, y: 4.3,
        w: 10.0, h: 0.6,
        fontSize: SIZES.sectionHeader,
        fontFace: FONTS.body,
        color: COLORS.blueGrey02,
        wrap: true,
      });
    }

    // Bottom accent line
    slide.addShape("rect", {
      x: 0, y: SLIDE.h - 0.06,
      w: SLIDE.w, h: 0.06,
      fill: { color: COLORS.blue },
      line: { color: COLORS.blue, width: 0 },
    });

    // Logo and footer are in MASTER_SECTION
    return slide;
  },

  /**
   * content — MASTER_CONTENT bg, returns slide for custom content
   */
  content(pres, opts = {}) {
    const { title = "" } = opts;
    _ensureMasters(pres);
    const slide = pres.addSlide({ masterName: "MASTER_CONTENT" });

    // Left accent bar — drawn over the frame so it's full-height regardless of BG
    slide.addShape("rect", {
      x: 0, y: 0.1,
      w: 0.08, h: SLIDE.h - 0.45,
      fill: { color: COLORS.blue },
      line: { color: COLORS.blue, width: 0 },
    });

    // Slide title — positioned per reference template
    slide.addText(title, {
      x: TITLE_POS.x, y: TITLE_POS.y,
      w: TITLE_POS.w, h: TITLE_POS.h,
      fontSize: SIZES.slideTitle,
      fontFace: FONTS.heading,
      bold: true,
      color: COLORS.blueGrey03,
      align: "center",
      valign: "middle",
    });

    // Blue accent line under title
    slide.addShape("rect", {
      x: TITLE_POS.x, y: TITLE_POS.y + TITLE_POS.h - 0.04,
      w: TITLE_POS.w, h: 0.04,
      fill: { color: COLORS.blue },
      line: { color: COLORS.blue, width: 0 },
    });

    // Logo and footer URL are in MASTER_CONTENT
    return slide;
  },

  /**
   * twoColumn — MASTER_CONTENT bg, two equal zones. Callback pattern for content.
   */
  twoColumn(pres, opts = {}) {
    const { title = "", leftContent, rightContent } = opts;
    const slide = slides.content(pres, { title });

    const contentY = CONTENT_AREA.y;
    const contentH = CONTENT_AREA.h;
    const colGap = 0.2;
    const totalW = CONTENT_AREA.w;
    const colW = (totalW - colGap) / 2;

    const leftZone  = { x: MARGIN.left, y: contentY, w: colW, h: contentH };
    const rightZone = { x: MARGIN.left + colW + colGap, y: contentY, w: colW, h: contentH };

    if (typeof leftContent  === "function") leftContent(slide, leftZone);
    if (typeof rightContent === "function") rightContent(slide, rightZone);

    return slide;
  },

  /**
   * grid — MASTER_CONTENT bg, N equal columns. Callback per card.
   */
  grid(pres, opts = {}) {
    const { title = "", cols = 3, cards = [] } = opts;
    const slide = slides.content(pres, { title });

    const contentY = CONTENT_AREA.y;
    const contentH = CONTENT_AREA.h;
    const colGap = 0.15;
    const totalW = CONTENT_AREA.w;
    const colW = (totalW - colGap * (cols - 1)) / cols;

    const totalRows = Math.ceil(cards.length / cols);
    const rowGap = totalRows > 1 ? 0.15 : 0;
    const rowH = (contentH - rowGap * (totalRows - 1)) / totalRows;

    cards.forEach((cardFn, i) => {
      if (typeof cardFn !== "function") return;
      const col = i % cols;
      const row = Math.floor(i / cols);
      const zone = {
        x: MARGIN.left + col * (colW + colGap),
        y: contentY + row * (rowH + rowGap),
        w: colW,
        h: rowH,
      };
      cardFn(slide, zone);
    });

    return slide;
  },

  /**
   * grid2x2 — MASTER_CONTENT bg, 4 cards in 2 rows × 2 cols
   */
  grid2x2(pres, opts = {}) {
    const { title = "", cards = [] } = opts;
    const slide = slides.content(pres, { title });

    const contentY = CONTENT_AREA.y;
    const contentH = CONTENT_AREA.h;
    const colGap = 0.2;
    const rowGap = 0.15;
    const totalW = CONTENT_AREA.w;
    const colW = (totalW - colGap) / 2;
    const rowH = (contentH - rowGap) / 2;

    const positions = [
      { col: 0, row: 0 },
      { col: 1, row: 0 },
      { col: 0, row: 1 },
      { col: 1, row: 1 },
    ];

    cards.slice(0, 4).forEach((cardFn, i) => {
      if (typeof cardFn !== "function") return;
      const { col, row } = positions[i];
      const zone = {
        x: MARGIN.left + col * (colW + colGap),
        y: contentY + row * (rowH + rowGap),
        w: colW,
        h: rowH,
      };
      cardFn(slide, zone);
    });

    return slide;
  },

  /**
   * kpi — MASTER_SECTION bg, big Betatron number
   */
  kpi(pres, opts = {}) {
    const { value = "", label = "", context = "" } = opts;
    _ensureMasters(pres);
    const slide = pres.addSlide({ masterName: "MASTER_SECTION" });

    // Big KPI value — Betatron, centered
    slide.addText(value, {
      x: 0, y: 1.5,
      w: SLIDE.w, h: 2.8,
      fontSize: 80,
      fontFace: FONTS.display,
      color: COLORS.blue,
      align: "center",
    });

    // Label
    slide.addText(label, {
      x: MARGIN.left, y: 4.5,
      w: CONTENT_AREA.w, h: 0.65,
      fontSize: SIZES.sectionHeader,
      fontFace: FONTS.heading,
      bold: true,
      color: COLORS.blueGrey03,
      align: "center",
    });

    // Context
    if (context) {
      slide.addText(context, {
        x: MARGIN.left, y: 5.2,
        w: CONTENT_AREA.w, h: 0.45,
        fontSize: SIZES.label,
        fontFace: FONTS.body,
        color: COLORS.blueGrey02,
        align: "center",
      });
    }

    // Logo and footer are in MASTER_SECTION
    return slide;
  },

  /**
   * comparison — MASTER_CONTENT bg, two labeled columns with divider.
   * Callback pattern: leftContent/rightContent receive zone bounds.
   * contentH is capped at insightBarY - 0.1 to prevent overlap with insightBar.
   */
  comparison(pres, opts = {}) {
    const { title = "", leftLabel = "", rightLabel = "", leftColor, rightColor, leftContent, rightContent } = opts;
    const slide = slides.content(pres, { title });

    const labelY = CONTENT_AREA.y - 0.65;   // 2.00 - 0.65 = 1.35 (clears title bar at y≈1.84)
    const labelH = 0.40;
    const contentY = labelY + labelH + 0.12;
    // Cap content bottom at insightBar top - 0.1 (insightBar default y = SLIDE.h - 1.05 = 6.45)
    const insightBarY = SLIDE.h - 1.05;
    const contentH = Math.min(CONTENT_AREA.y + CONTENT_AREA.h, insightBarY - 0.1) - contentY;
    const colGap = 0.25;
    const totalW = CONTENT_AREA.w;
    const colW = (totalW - colGap) / 2;

    // Left column label
    slide.addText(leftLabel, {
      x: MARGIN.left, y: labelY,
      w: colW, h: labelH,
      fontSize: SIZES.sectionHeader,
      fontFace: FONTS.heading,
      bold: true,
      color: leftColor || COLORS.blueGrey02,
      align: "center",
    });

    // Right column label
    slide.addText(rightLabel, {
      x: MARGIN.left + colW + colGap, y: labelY,
      w: colW, h: labelH,
      fontSize: SIZES.sectionHeader,
      fontFace: FONTS.heading,
      bold: true,
      color: rightColor || COLORS.blue,
      align: "center",
    });

    // Vertical divider
    slide.addShape("line", {
      x: MARGIN.left + colW + colGap / 2, y: labelY,
      w: 0, h: contentH + labelH + 0.12,
      line: { color: COLORS.blueGrey01, width: 1.5 },
    });

    const leftZone  = { x: MARGIN.left, y: contentY, w: colW, h: contentH };
    const rightZone = { x: MARGIN.left + colW + colGap, y: contentY, w: colW, h: contentH };

    if (typeof leftContent  === "function") leftContent(slide, leftZone);
    if (typeof rightContent === "function") rightContent(slide, rightZone);

    return slide;
  },

  /**
   * timeline — MASTER_CONTENT bg, horizontal steps with connecting line
   */
  timeline(pres, opts = {}) {
    const { title = "", steps = [] } = opts;
    const slide = slides.content(pres, { title });

    if (steps.length === 0) return slide;

    const lineY = 3.5;
    const dotR  = 0.22;
    const stepW = CONTENT_AREA.w / steps.length;
    const lineStartX = MARGIN.left + stepW / 2;
    const lineEndX   = MARGIN.left + CONTENT_AREA.w - stepW / 2;

    // Horizontal connecting line
    slide.addShape("line", {
      x: lineStartX, y: lineY,
      w: lineEndX - lineStartX, h: 0,
      line: { color: COLORS.blueGrey01, width: 2 },
    });

    steps.forEach((step, i) => {
      const cx = MARGIN.left + stepW * i + stepW / 2;
      const dotX = cx - dotR;
      const dotY = lineY - dotR;

      // Step dot
      slide.addShape("ellipse", {
        x: dotX, y: dotY,
        w: dotR * 2, h: dotR * 2,
        fill: { color: COLORS.blue },
        line: { color: COLORS.white, width: 2 },
      });

      // Step number inside dot
      slide.addText(step.number || String(i + 1), {
        x: dotX, y: dotY,
        w: dotR * 2, h: dotR * 2,
        fontSize: 9,
        fontFace: FONTS.heading,
        bold: true,
        color: COLORS.white,
        align: "center",
        valign: "middle",
      });

      // Step label
      slide.addText(step.title || step.label || "", {
        x: cx - stepW / 2 + 0.05, y: lineY + dotR + 0.12,
        w: stepW - 0.1, h: 0.45,
        fontSize: SIZES.label,
        fontFace: FONTS.heading,
        bold: true,
        color: COLORS.blueGrey03,
        align: "center",
        wrap: true,
      });

      // Step description
      if (step.description) {
        slide.addText(step.description, {
          x: cx - stepW / 2 + 0.05, y: lineY + dotR + 0.6,
          w: stepW - 0.1, h: 1.0,
          fontSize: 9,
          fontFace: FONTS.body,
          color: COLORS.blueGrey02,
          align: "center",
          wrap: true,
        });
      }
    });

    return slide;
  },

  /**
   * closing — MASTER_DARK bg, centered title and optional subtitle/contact
   */
  closing(pres, opts = {}) {
    const { title = "", subtitle = "", contact = "" } = opts;
    _ensureMasters(pres);
    const slide = pres.addSlide({ masterName: "MASTER_DARK" });

    // Top accent line
    _addTopAccentLine(slide);

    // Centered title
    slide.addText(title, {
      x: MARGIN.left, y: 2.0,
      w: CONTENT_AREA.w, h: 1.5,
      fontSize: SIZES.closingTitle,
      fontFace: FONTS.heading,
      bold: true,
      color: COLORS.white,
      align: "center",
      wrap: true,
    });

    // Subtitle
    if (subtitle) {
      slide.addText(subtitle, {
        x: MARGIN.left, y: 3.7,
        w: CONTENT_AREA.w, h: 0.65,
        fontSize: SIZES.sectionHeader,
        fontFace: FONTS.body,
        color: COLORS.blue,
        align: "center",
        wrap: true,
      });
    }

    // Contact
    if (contact) {
      slide.addText(contact, {
        x: MARGIN.left, y: 4.5,
        w: CONTENT_AREA.w, h: 0.5,
        fontSize: SIZES.label,
        fontFace: FONTS.body,
        color: COLORS.blueGrey02,
        align: "center",
      });
    }

    // Footer URL is in MASTER_DARK
    return slide;
  },
};

// ---------------------------------------------------------------------------
// BLOCKS — reusable components for custom slides
// ---------------------------------------------------------------------------

const blocks = {

  /**
   * statCard — rounded card with big Betatron number
   */
  statCard(slide, opts = {}) {
    const {
      value = "",
      label = "",
      x = 0, y = 0, w = 3.0, h = 1.8,
      valueColor = COLORS.blue,
    } = opts;

    slide.addShape("roundRect", {
      x, y, w, h,
      rectRadius: 0.1,
      fill: { color: COLORS.offWhite },
      line: { color: COLORS.blueGrey01, width: 1 },
    });

    slide.addText(value, {
      x: x + 0.1, y: y + 0.1,
      w: w - 0.2, h: h * 0.6,
      fontSize: SIZES.statValue,
      fontFace: FONTS.display,
      color: valueColor,
      align: "center",
      valign: "middle",
    });

    slide.addText(label, {
      x: x + 0.1, y: y + h * 0.65,
      w: w - 0.2, h: h * 0.3,
      fontSize: SIZES.label,
      fontFace: FONTS.body,
      color: COLORS.blueGrey02,
      align: "center",
      wrap: true,
    });
  },

  /**
   * featureList — dot + title + description rows
   */
  featureList(slide, opts = {}) {
    const {
      items = [],
      x = 0, y = 0, w = 5.0, h = 3.5,
      dotColor = COLORS.blue,
    } = opts;

    if (items.length === 0) return;

    const rowH = h / items.length;
    const dotSize = 0.1;
    const dotPad  = 0.12;
    const textX   = x + dotSize + dotPad * 2;
    const textW   = w - dotSize - dotPad * 2;

    items.forEach((item, i) => {
      const rowY = y + i * rowH;
      const titleH = item.description ? rowH * 0.42 : rowH * 0.6;

      slide.addShape("ellipse", {
        x: x + dotPad, y: rowY + rowH * 0.2,
        w: dotSize, h: dotSize,
        fill: { color: item.dotColor || dotColor },
        line: { color: item.dotColor || dotColor, width: 0 },
      });

      slide.addText(item.title || "", {
        x: textX, y: rowY + 0.05,
        w: textW, h: titleH,
        fontSize: SIZES.body,
        fontFace: FONTS.heading,
        bold: true,
        color: item.titleColor || COLORS.blueGrey03,
        wrap: true,
      });

      if (item.description) {
        slide.addText(item.description, {
          x: textX, y: rowY + titleH + 0.05,
          w: textW, h: rowH - titleH - 0.1,
          fontSize: 10,
          fontFace: FONTS.body,
          color: COLORS.blueGrey02,
          wrap: true,
        });
      }
    });
  },

  /**
   * insightBar — bottom callout strip with blue accent line.
   * Default y = SLIDE.h - 1.05 = 6.45, above footer row at 6.95.
   * contentH in comparison is capped to stay above insightBarY.
   */
  insightBar(slide, opts = {}) {
    const {
      text = "",
      y = SLIDE.h - 1.05,   // 7.5 - 1.05 = 6.45
    } = opts;

    const barH = 0.55;

    slide.addShape("rect", {
      x: 0, y,
      w: SLIDE.w, h: barH,
      fill: { color: COLORS.offWhite },
      line: { color: COLORS.offWhite, width: 0 },
    });

    slide.addShape("rect", {
      x: 0, y,
      w: 0.06, h: barH,
      fill: { color: COLORS.blue },
      line: { color: COLORS.blue, width: 0 },
    });

    slide.addText(text, {
      x: 0.2, y: y + 0.05,
      w: SLIDE.w - 0.4, h: barH - 0.1,
      fontSize: SIZES.body,
      fontFace: FONTS.body,
      color: COLORS.blueGrey03,
      italic: true,
      wrap: true,
    });
  },

  /**
   * table — alternating row table
   */
  table(slide, opts = {}) {
    const {
      headers = [],
      rows = [],
      x = MARGIN.left, y = CONTENT_AREA.y,
      w = CONTENT_AREA.w,
      colWidths,
    } = opts;

    if (headers.length === 0 && rows.length === 0) return;

    const cols = headers.length || (rows[0] ? rows[0].length : 1);
    const defaultFrac = 1 / cols;
    const colWArr = colWidths
      ? colWidths.map(f => f * w)
      : Array(cols).fill(defaultFrac * w);

    const rowH = 0.38;
    const headerH = 0.44;

    if (headers.length > 0) {
      headers.forEach((hdr, ci) => {
        const colX = x + colWArr.slice(0, ci).reduce((a, b) => a + b, 0);
        slide.addShape("rect", {
          x: colX, y,
          w: colWArr[ci], h: headerH,
          fill: { color: COLORS.blueGrey03 },
          line: { color: COLORS.blueGrey03, width: 0 },
        });
        slide.addText(hdr, {
          x: colX + 0.08, y,
          w: colWArr[ci] - 0.08, h: headerH,
          fontSize: SIZES.tableCell,
          fontFace: FONTS.heading,
          bold: true,
          color: COLORS.white,
          valign: "middle",
        });
      });
    }

    rows.forEach((row, ri) => {
      const rowY = y + headerH + ri * rowH;
      const isAlt = ri % 2 === 1;
      row.forEach((cell, ci) => {
        const colX = x + colWArr.slice(0, ci).reduce((a, b) => a + b, 0);
        slide.addShape("rect", {
          x: colX, y: rowY,
          w: colWArr[ci], h: rowH,
          fill: { color: isAlt ? COLORS.altRow : COLORS.white },
          line: { color: COLORS.blueGrey01, width: 0.5 },
        });
        slide.addText(String(cell), {
          x: colX + 0.08, y: rowY,
          w: colWArr[ci] - 0.08, h: rowH,
          fontSize: SIZES.tableCell,
          fontFace: FONTS.body,
          color: COLORS.blueGrey03,
          valign: "middle",
        });
      });
    });
  },

  /**
   * processFlow — horizontal boxes with arrows.
   * With the wider 13.333" canvas, 8-step labels like "Ion exchange" / "Crystallize"
   * fit single-line at 10pt — no abbreviations needed.
   */
  processFlow(slide, opts = {}) {
    const {
      steps = [],
      x = MARGIN.left, y = CONTENT_AREA.y,
      w = CONTENT_AREA.w,
      h = 0.65,
      color = COLORS.blue,
    } = opts;

    if (steps.length === 0) return;

    const arrowW = 0.25;
    const totalArrows = steps.length - 1;
    const boxW = (w - totalArrows * arrowW) / steps.length;

    steps.forEach((step, i) => {
      const boxX = x + i * (boxW + arrowW);

      slide.addShape("roundRect", {
        x: boxX, y,
        w: boxW, h,
        rectRadius: 0.06,
        fill: { color },
        line: { color, width: 0 },
      });

      slide.addText(step, {
        x: boxX + 0.05, y,
        w: boxW - 0.1, h,
        fontSize: 10,
        fontFace: FONTS.body,
        bold: true,
        color: COLORS.white,
        align: "center",
        valign: "middle",
        wrap: true,
      });

      if (i < steps.length - 1) {
        const arrowX = boxX + boxW;
        slide.addShape("line", {
          x: arrowX, y: y + h / 2,
          w: arrowW, h: 0,
          line: { color: COLORS.blueGrey03, width: 1.5, endArrowType: "triangle" },
        });
      }
    });
  },
};

// ---------------------------------------------------------------------------
// EXPORTS
// ---------------------------------------------------------------------------

module.exports = {
  // Constants
  COLORS,
  CHART_COLORS,
  FONTS,
  SIZES,
  SLIDE,
  MARGIN,
  CONTENT_AREA,
  TITLE_POS,
  ASSETS,

  // Factory
  createPresentation,

  // Layouts
  slides,

  // Components
  blocks,

  // Helpers
  _thaiFontFace,
  thaiFontFace: _thaiFontFace,
};
