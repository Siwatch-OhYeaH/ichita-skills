/**
 * ichita-slide-lib.cjs — Ichita Branded PPTX Slide Builder Library
 *
 * PptxGenJS wrapper that produces consistent, brand-compliant Ichita presentations.
 *
 * Usage:
 *   const { createPresentation, slides, blocks, COLORS, FONTS } = require("./ichita-slide-lib.cjs");
 *   const pres = createPresentation({ title: "My Presentation" });
 *   slides.cover(pres, { title: "Ichita Solution Overview", subtitle: "Liquid Sugar Refinery" });
 *   slides.content(pres, { title: "Key Benefits" });
 *   pres.writeFile({ fileName: "output.pptx" });
 */

"use strict";

const path = require("path");

// Lazy-load pptxgenjs — resolve from multiple possible locations
// (ichita-skills has no local node_modules; pptxgenjs lives in the caller's env)
function _requirePptxgen() {
  // 1. Try standard resolution (caller's node_modules or global)
  try { return require("pptxgenjs"); } catch (_) {}
  // 2. Try davinci-oracle node_modules (common dev environment)
  try {
    return require(path.resolve(__dirname, "../../../../davinci-oracle/node_modules/pptxgenjs"));
  } catch (_) {}
  // 3. Try global npm/fnm prefix
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
  green:        "34A853",   // Success / positive
  red:          "E83E3E",   // Warning / negative
  orange:       "FFA000",   // Emphasis (use sparingly)
  offWhite:     "F8FAFB",   // Card backgrounds
  altRow:       "F0F4F5",   // Table alternating rows
};

/** Chart color sequence */
const CHART_COLORS = ["2978FF", "263338", "82B0FF", "788F9C", "34A853", "E83E3E"];

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
 * Use when adding text that may contain Thai glyphs to ensure correct font rendering.
 * @param {string} text  Text to inspect for Thai characters
 * @param {string} [defaultFace]  Fallback font face for non-Thai text (default: FONTS.body)
 * @returns {string}  Font face name to use
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

/** Slide dimensions (inches) */
const SLIDE = {
  w: 10,
  h: 5.625,
};

/** Margins */
const MARGIN = {
  top:    0.5,
  right:  0.5,
  bottom: 0.5,
  left:   0.5,
};

/** Body content area (below title) on content slides */
const CONTENT_AREA = {
  x: MARGIN.left,
  y: 1.2,  // below title + accent bar
  w: SLIDE.w - MARGIN.left - MARGIN.right,
  h: SLIDE.h - 1.2 - MARGIN.bottom - 0.35,  // leave room for footer/logo
};

/** Title position on content slides */
const TITLE_POS = {
  x: 2.7,
  y: 0.1,
  w: 6.95,
  h: 0.45,
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
// HELPERS
// ---------------------------------------------------------------------------

/** Add footer to a slide */
function _addFooter(slide, opts = {}) {
  const { dark = false } = opts;
  slide.addText("www.ichita.co.th", {
    x: SLIDE.w - MARGIN.right - 2.0,
    y: SLIDE.h - 0.28,
    w: 1.95,
    h: 0.2,
    fontSize: SIZES.footer,
    fontFace: FONTS.body,
    color: COLORS.blueGrey02,
    align: "right",
  });
}

/** Add logo to a slide */
function _addLogo(slide, opts = {}) {
  const { dark = false } = opts;
  const logoPath = dark ? ASSETS.logoWhite : ASSETS.logoDark;
  try {
    slide.addImage({
      path: logoPath,
      x: MARGIN.left,
      y: SLIDE.h - 0.38,
      w: 1.2,
      h: 0.25,
    });
  } catch (e) {
    // Asset not found — skip logo silently (file may not exist in all envs)
  }
}

/** Add top accent line (blue, full width) */
function _addTopAccentLine(slide) {
  slide.addShape("rect", {
    x: 0, y: 0,
    w: SLIDE.w, h: 0.06,
    fill: { color: COLORS.blue },
    line: { color: COLORS.blue, width: 0 },
  });
}

/** Add content frame background image */
function _addContentFrame(slide) {
  try {
    slide.addImage({
      path: ASSETS.contentFrame,
      x: 0, y: 0,
      w: SLIDE.w, h: SLIDE.h,
    });
  } catch (e) {
    // Fall back to plain white
    slide.background = { color: COLORS.white };
  }
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
  pres.layout = "LAYOUT_WIDE";   // 10" x 5.625"
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
   * cover — dark bg, accent bars, white text
   * @param {PptxGenJS} pres
   * @param {object} opts
   * @param {string} opts.title
   * @param {string} [opts.subtitle]
   * @param {string} [opts.date]
   */
  cover(pres, opts = {}) {
    const { title = "", subtitle = "", date = "" } = opts;
    const slide = pres.addSlide();
    slide.background = { color: COLORS.blueGrey03 };

    // Try dark bg image
    try {
      slide.addImage({
        path: ASSETS.darkBg,
        x: 0, y: 0,
        w: SLIDE.w, h: SLIDE.h,
      });
    } catch (e) { /* use solid bg */ }

    // Top accent line — blue, full width
    _addTopAccentLine(slide);

    // Left accent bar — blue, 0.08" wide, full height
    slide.addShape("rect", {
      x: 0.6, y: 0,
      w: 0.08, h: SLIDE.h,
      fill: { color: COLORS.blue },
      line: { color: COLORS.blue, width: 0 },
    });

    // Title
    slide.addText(title, {
      x: 1.0, y: 1.3,
      w: 8.0, h: 1.0,
      fontSize: SIZES.coverTitle,
      fontFace: FONTS.heading,
      bold: true,
      color: COLORS.white,
      wrap: true,
    });

    // Subtitle
    if (subtitle) {
      slide.addText(subtitle, {
        x: 1.0, y: 3.3,
        w: 7.5, h: 0.45,
        fontSize: SIZES.sectionHeader,
        fontFace: FONTS.body,
        color: COLORS.blue,
        wrap: true,
      });
    }

    // Date
    if (date) {
      slide.addText(date, {
        x: 1.0, y: 3.85,
        w: 4.0, h: 0.3,
        fontSize: SIZES.label,
        fontFace: FONTS.body,
        color: COLORS.blueGrey02,
      });
    }

    // Note: dark bg image already contains ICHITA brand mark — no extra logo needed
    _addFooter(slide, { dark: true });

    return slide;
  },

  /**
   * sectionDivider — grey1 bg, big Betatron number, title
   * @param {PptxGenJS} pres
   * @param {object} opts
   * @param {string|number} opts.number   Section number
   * @param {string} opts.title
   * @param {string} [opts.subtitle]
   */
  sectionDivider(pres, opts = {}) {
    const { number = "", title = "", subtitle = "" } = opts;
    const slide = pres.addSlide();
    slide.background = { color: COLORS.blueGrey01 };

    // Big section number — Betatron, right-aligned, blue
    slide.addText(String(number), {
      x: 0, y: 0.5,
      w: SLIDE.w - MARGIN.right,
      h: 2.0,
      fontSize: SIZES.sectionNumber,
      fontFace: FONTS.display,
      color: COLORS.blue,
      align: "right",
    });

    // Title
    slide.addText(title, {
      x: MARGIN.left, y: 2.8,
      w: 7.5, h: 0.8,
      fontSize: 28,
      fontFace: FONTS.heading,
      bold: true,
      color: COLORS.blueGrey03,
      wrap: true,
    });

    // Subtitle
    if (subtitle) {
      slide.addText(subtitle, {
        x: MARGIN.left, y: 3.65,
        w: 7.5, h: 0.5,
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

    _addLogo(slide, { dark: false });
    _addFooter(slide);

    return slide;
  },

  /**
   * content — white bg with content frame image, returns slide for custom content
   * @param {PptxGenJS} pres
   * @param {object} opts
   * @param {string} opts.title
   */
  content(pres, opts = {}) {
    const { title = "" } = opts;
    const slide = pres.addSlide();
    slide.background = { color: COLORS.white };

    _addContentFrame(slide);

    // Title — centered in header area
    slide.addText(title, {
      x: TITLE_POS.x, y: TITLE_POS.y,
      w: TITLE_POS.w, h: TITLE_POS.h,
      fontSize: SIZES.slideTitle,
      fontFace: FONTS.heading,
      bold: true,
      color: COLORS.blueGrey03,
      align: "center",
    });

    _addLogo(slide, { dark: false });
    _addFooter(slide);

    return slide;
  },

  /**
   * twoColumn — frame bg, two equal zones. Callback pattern for content.
   * @param {PptxGenJS} pres
   * @param {object} opts
   * @param {string} opts.title
   * @param {Function} opts.leftContent   (slide, {x, y, w, h}) => void
   * @param {Function} opts.rightContent  (slide, {x, y, w, h}) => void
   */
  twoColumn(pres, opts = {}) {
    const { title = "", leftContent, rightContent } = opts;
    const slide = slides.content(pres, { title });

    const contentY = 1.2;
    const contentH = SLIDE.h - contentY - MARGIN.bottom - 0.35;
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
   * grid — frame bg, N equal columns. Callback per card.
   * @param {PptxGenJS} pres
   * @param {object} opts
   * @param {string} opts.title
   * @param {number} opts.cols
   * @param {Function[]} opts.cards  Array of (slide, {x, y, w, h}) => void
   */
  grid(pres, opts = {}) {
    const { title = "", cols = 3, cards = [] } = opts;
    const slide = slides.content(pres, { title });

    const contentY = 1.2;
    const contentH = SLIDE.h - contentY - MARGIN.bottom - 0.35;
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
   * grid2x2 — frame bg, 4 cards in 2 rows × 2 cols
   * @param {PptxGenJS} pres
   * @param {object} opts
   * @param {string} opts.title
   * @param {Function[]} opts.cards  Array of 4 (slide, {x, y, w, h}) => void
   */
  grid2x2(pres, opts = {}) {
    const { title = "", cards = [] } = opts;
    const slide = slides.content(pres, { title });

    const contentY = 1.2;
    const contentH = SLIDE.h - contentY - MARGIN.bottom - 0.35;
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
   * kpi — grey1 bg, big Betatron number
   * @param {PptxGenJS} pres
   * @param {object} opts
   * @param {string} opts.value    Main KPI value (e.g. "99.7%")
   * @param {string} opts.label    KPI label
   * @param {string} [opts.context] Small context text below
   */
  kpi(pres, opts = {}) {
    const { value = "", label = "", context = "" } = opts;
    const slide = pres.addSlide();
    slide.background = { color: COLORS.blueGrey01 };

    // Big KPI value — Betatron, centered
    slide.addText(value, {
      x: 0, y: 1.2,
      w: SLIDE.w, h: 2.2,
      fontSize: 80,
      fontFace: FONTS.display,
      color: COLORS.blue,
      align: "center",
    });

    // Label
    slide.addText(label, {
      x: MARGIN.left, y: 3.6,
      w: CONTENT_AREA.w, h: 0.5,
      fontSize: SIZES.sectionHeader,
      fontFace: FONTS.heading,
      bold: true,
      color: COLORS.blueGrey03,
      align: "center",
    });

    // Context
    if (context) {
      slide.addText(context, {
        x: MARGIN.left, y: 4.15,
        w: CONTENT_AREA.w, h: 0.35,
        fontSize: SIZES.label,
        fontFace: FONTS.body,
        color: COLORS.blueGrey02,
        align: "center",
      });
    }

    _addLogo(slide, { dark: false });
    _addFooter(slide);

    return slide;
  },

  /**
   * comparison — frame bg, two labeled columns with divider
   * Callback pattern: leftContent/rightContent receive zone bounds.
   * @param {PptxGenJS} pres
   * @param {object} opts
   * @param {string} opts.title
   * @param {string} opts.leftLabel
   * @param {string} opts.rightLabel
   * @param {string} [opts.leftColor]    Left label color (default: red)
   * @param {string} [opts.rightColor]   Right label color (default: green)
   * @param {Function} opts.leftContent   (slide, {x, y, w, h}) => void
   * @param {Function} opts.rightContent  (slide, {x, y, w, h}) => void
   */
  comparison(pres, opts = {}) {
    const { title = "", leftLabel = "", rightLabel = "", leftColor, rightColor, leftContent, rightContent } = opts;
    const slide = slides.content(pres, { title });

    const labelY = 1.1;
    const labelH = 0.35;
    const contentY = labelY + labelH + 0.1;
    const contentH = SLIDE.h - contentY - MARGIN.bottom - 0.35;
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
      color: leftColor || COLORS.red,
      align: "center",
    });

    // Right column label
    slide.addText(rightLabel, {
      x: MARGIN.left + colW + colGap, y: labelY,
      w: colW, h: labelH,
      fontSize: SIZES.sectionHeader,
      fontFace: FONTS.heading,
      bold: true,
      color: rightColor || COLORS.green,
      align: "center",
    });

    // Vertical divider
    slide.addShape("line", {
      x: MARGIN.left + colW + colGap / 2, y: labelY,
      w: 0, h: contentH + labelH + 0.1,
      line: { color: COLORS.blueGrey01, width: 1.5 },
    });

    const leftZone  = { x: MARGIN.left, y: contentY, w: colW, h: contentH };
    const rightZone = { x: MARGIN.left + colW + colGap, y: contentY, w: colW, h: contentH };

    if (typeof leftContent  === "function") leftContent(slide, leftZone);
    if (typeof rightContent === "function") rightContent(slide, rightZone);

    return slide;
  },

  /**
   * timeline — frame bg, horizontal steps with connecting line
   * @param {PptxGenJS} pres
   * @param {object} opts
   * @param {string} opts.title
   * @param {Array<{title: string, number?: string, description?: string}>} opts.steps
   */
  timeline(pres, opts = {}) {
    const { title = "", steps = [] } = opts;
    const slide = slides.content(pres, { title });

    if (steps.length === 0) return slide;

    const lineY = 2.6;
    const dotR  = 0.18;
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
        w: stepW - 0.1, h: 0.35,
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
          x: cx - stepW / 2 + 0.05, y: lineY + dotR + 0.5,
          w: stepW - 0.1, h: 0.8,
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
   * closing — dark bg, centered title and optional subtitle/contact
   * @param {PptxGenJS} pres
   * @param {object} opts
   * @param {string} opts.title
   * @param {string} [opts.subtitle]
   * @param {string} [opts.contact]
   */
  closing(pres, opts = {}) {
    const { title = "", subtitle = "", contact = "" } = opts;
    const slide = pres.addSlide();
    slide.background = { color: COLORS.blueGrey03 };

    // Try dark bg image
    try {
      slide.addImage({
        path: ASSETS.darkBg,
        x: 0, y: 0,
        w: SLIDE.w, h: SLIDE.h,
      });
    } catch (e) { /* use solid bg */ }

    // Top accent line
    _addTopAccentLine(slide);

    // Centered title
    slide.addText(title, {
      x: MARGIN.left, y: 1.5,
      w: CONTENT_AREA.w, h: 1.2,
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
        x: MARGIN.left, y: 2.9,
        w: CONTENT_AREA.w, h: 0.5,
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
        x: MARGIN.left, y: 3.5,
        w: CONTENT_AREA.w, h: 0.4,
        fontSize: SIZES.label,
        fontFace: FONTS.body,
        color: COLORS.blueGrey02,
        align: "center",
      });
    }

    // Note: dark bg image already contains ICHITA brand mark — no extra logo needed
    _addFooter(slide, { dark: true });

    return slide;
  },
};

// ---------------------------------------------------------------------------
// BLOCKS — reusable components for custom slides
// ---------------------------------------------------------------------------

const blocks = {

  /**
   * statCard — rounded card with big Betatron number
   * @param {object} slide   PptxGenJS slide object
   * @param {object} opts
   * @param {string} opts.value         The KPI/stat value
   * @param {string} opts.label         Card label
   * @param {number} opts.x
   * @param {number} opts.y
   * @param {number} opts.w
   * @param {number} opts.h
   * @param {string} [opts.valueColor]  Override value color (default: COLORS.blue)
   */
  statCard(slide, opts = {}) {
    const {
      value = "",
      label = "",
      x = 0, y = 0, w = 2.5, h = 1.5,
      valueColor = COLORS.blue,
    } = opts;

    // Card background
    slide.addShape("roundRect", {
      x, y, w, h,
      rectRadius: 0.1,
      fill: { color: COLORS.offWhite },
      line: { color: COLORS.blueGrey01, width: 1 },
    });

    // Value — Betatron display font
    slide.addText(value, {
      x: x + 0.1, y: y + 0.1,
      w: w - 0.2, h: h * 0.6,
      fontSize: SIZES.statValue,
      fontFace: FONTS.display,
      color: valueColor,
      align: "center",
      valign: "middle",
    });

    // Label
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
   * @param {object} slide
   * @param {object} opts
   * @param {Array<{title: string, description?: string}>} opts.items
   * @param {number} opts.x
   * @param {number} opts.y
   * @param {number} opts.w
   * @param {number} opts.h
   * @param {string} [opts.dotColor]   Dot accent color (default: COLORS.blue)
   */
  featureList(slide, opts = {}) {
    const {
      items = [],
      x = 0, y = 0, w = 4.0, h = 3.0,
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

      // Dot
      slide.addShape("ellipse", {
        x: x + dotPad, y: rowY + rowH * 0.2,
        w: dotSize, h: dotSize,
        fill: { color: dotColor },
        line: { color: dotColor, width: 0 },
      });

      // Title
      slide.addText(item.title || "", {
        x: textX, y: rowY + 0.05,
        w: textW, h: titleH,
        fontSize: SIZES.body,
        fontFace: FONTS.heading,
        bold: true,
        color: COLORS.blueGrey03,
        wrap: true,
      });

      // Description
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
   * insightBar — bottom callout strip with blue accent line
   * @param {object} slide
   * @param {object} opts
   * @param {string} opts.text
   * @param {number} [opts.y]   Y position (default: near bottom)
   */
  insightBar(slide, opts = {}) {
    const {
      text = "",
      y = SLIDE.h - 1.05,
    } = opts;

    const barH = 0.55;

    // Background strip
    slide.addShape("rect", {
      x: 0, y,
      w: SLIDE.w, h: barH,
      fill: { color: COLORS.offWhite },
      line: { color: COLORS.offWhite, width: 0 },
    });

    // Blue accent left line
    slide.addShape("rect", {
      x: 0, y,
      w: 0.06, h: barH,
      fill: { color: COLORS.blue },
      line: { color: COLORS.blue, width: 0 },
    });

    // Text
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
   * @param {object} slide
   * @param {object} opts
   * @param {string[]} opts.headers
   * @param {string[][]} opts.rows
   * @param {number} opts.x
   * @param {number} opts.y
   * @param {number} opts.w
   * @param {number[]} [opts.colWidths]   Array of fractional widths (sum = 1.0)
   */
  table(slide, opts = {}) {
    const {
      headers = [],
      rows = [],
      x = MARGIN.left, y = 1.2,
      w = CONTENT_AREA.w,
      colWidths,
    } = opts;

    if (headers.length === 0 && rows.length === 0) return;

    const cols = headers.length || (rows[0] ? rows[0].length : 1);
    const defaultFrac = 1 / cols;
    const colWArr = colWidths
      ? colWidths.map(f => f * w)
      : Array(cols).fill(defaultFrac * w);

    const rowH = 0.32;
    const headerH = 0.38;

    // Header row
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

    // Data rows
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
   * processFlow — horizontal boxes with arrows
   * @param {object} slide
   * @param {object} opts
   * @param {string[]} opts.steps
   * @param {number} opts.x
   * @param {number} opts.y
   * @param {number} opts.w
   * @param {number} [opts.h]       Box height (default: 0.6)
   * @param {string} [opts.color]   Box fill color (default: COLORS.blue)
   */
  processFlow(slide, opts = {}) {
    const {
      steps = [],
      x = MARGIN.left, y = 2.0,
      w = CONTENT_AREA.w,
      h = 0.6,
      color = COLORS.blue,
    } = opts;

    if (steps.length === 0) return;

    const arrowW = 0.25;
    const totalArrows = steps.length - 1;
    const boxW = (w - totalArrows * arrowW) / steps.length;

    steps.forEach((step, i) => {
      const boxX = x + i * (boxW + arrowW);

      // Box
      slide.addShape("roundRect", {
        x: boxX, y,
        w: boxW, h,
        rectRadius: 0.06,
        fill: { color },
        line: { color, width: 0 },
      });

      // Step label
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

      // Arrow between steps
      if (i < steps.length - 1) {
        const arrowX = boxX + boxW;
        slide.addShape("line", {
          x: arrowX, y: y + h / 2,
          w: arrowW, h: 0,
          line: { color: COLORS.blueGrey02, width: 1.5, endArrowType: "open" },
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
