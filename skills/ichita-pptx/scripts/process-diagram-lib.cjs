/**
 * process-diagram-lib.js — Process Diagram Helper Library for PptxGenJS
 *
 * Draws unit operations, streams, and annotations for process flow diagrams.
 * Every unit function returns connection points for stream routing.
 *
 * Usage:
 *   const { units, streams, layout, annotations } = require("./process-diagram-lib");
 *   const pptxgen = require("pptxgenjs");
 *   const pres = new pptxgen();
 *   const slide = pres.addSlide();
 *   const tank = units.tank(slide, pres, 1.0, 1.5, { label: "Feed Tank" });
 *   const reactor = units.reactor(slide, pres, 3.5, 1.5, { label: "Reactor" });
 *   streams.connect(slide, pres, tank.out, reactor.in, { label: "Feed" });
 */

// ---------------------------------------------------------------------------
// Defaults
// ---------------------------------------------------------------------------
const DEFAULTS = {
  w: 1.2,
  h: 0.9,
  color: "2978FF",       // ICHITA blue
  textColor: "FFFFFF",
  labelSize: 8,
  borderColor: "263338",
  borderWidth: 1.5,
  streamColor: "263338",
  streamWidth: 1.5,
  streamLabelSize: 8,
  streamLabelColor: "788F9C",
  annotationSize: 7,
  annotationColor: "788F9C",
  fontFace: "Aeonik",
};

// Factory: shadow for unit boxes
const unitShadow = () => ({
  type: "outer", blur: 3, offset: 1, angle: 135, color: "000000", opacity: 0.10,
});

// ---------------------------------------------------------------------------
// Connection point helper — calculates in/out/top/bottom from bounding box
// ---------------------------------------------------------------------------
function connPoints(x, y, w, h, extras) {
  return {
    x, y, w, h,
    in:     { x: x,         y: y + h / 2 },
    out:    { x: x + w,     y: y + h / 2 },
    top:    { x: x + w / 2, y: y },
    bottom: { x: x + w / 2, y: y + h },
    ...extras,
  };
}

// Merge user opts over defaults
function o(userOpts, extra) {
  return { ...DEFAULTS, ...extra, ...userOpts };
}

// ---------------------------------------------------------------------------
// UNITS — each draws shapes on slide and returns connection points
// ---------------------------------------------------------------------------
const units = {

  /**
   * block — simple colored rectangle with centered label.
   * Good for block diagrams.
   */
  block(slide, pres, x, y, opts = {}) {
    const p = o(opts);
    const { w, h, color, textColor, label, labelSize, fontFace, borderColor, borderWidth } = p;
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h,
      fill: { color },
      line: { color: borderColor, width: borderWidth },
      shadow: unitShadow(),
    });
    if (label) {
      slide.addText(label, {
        x, y, w, h,
        fontSize: labelSize, fontFace, color: textColor,
        bold: true, align: "center", valign: "middle", margin: 0,
        lineSpacingMultiple: 0.9,
      });
    }
    return connPoints(x, y, w, h);
  },

  /**
   * tank — rectangle with thicker border, optional rounded top.
   */
  tank(slide, pres, x, y, opts = {}) {
    const p = o(opts, { h: 1.0 });
    const { w, h, color, textColor, label, labelSize, fontFace, borderColor, borderWidth } = p;
    // Main body
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h,
      fill: { color },
      line: { color: borderColor, width: borderWidth + 0.5 },
      shadow: unitShadow(),
    });
    // Liquid level indicator (horizontal line at 60% height)
    const lvlY = y + h * 0.4;
    slide.addShape(pres.shapes.LINE, {
      x: x + 0.05, y: lvlY, w: w - 0.1, h: 0,
      line: { color: textColor, width: 0.5, dashType: "dash" },
    });
    if (label) {
      slide.addText(label, {
        x, y: y + h * 0.5, w, h: h * 0.45,
        fontSize: labelSize, fontFace, color: textColor,
        bold: true, align: "center", valign: "middle", margin: 0,
      });
    }
    return connPoints(x, y, w, h);
  },

  /**
   * reactor — rectangle with agitator symbol (vertical line + angled blades).
   */
  reactor(slide, pres, x, y, opts = {}) {
    const p = o(opts, { h: 1.0 });
    const { w, h, color, textColor, label, labelSize, fontFace, borderColor, borderWidth } = p;
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h,
      fill: { color },
      line: { color: borderColor, width: borderWidth },
      shadow: unitShadow(),
    });
    // Agitator shaft (vertical line from top)
    const cx = x + w / 2;
    slide.addShape(pres.shapes.LINE, {
      x: cx, y: y - 0.12, w: 0, h: h * 0.45,
      line: { color: borderColor, width: 1.5 },
    });
    // Motor circle at top of shaft
    slide.addShape(pres.shapes.OVAL, {
      x: cx - 0.08, y: y - 0.22, w: 0.16, h: 0.10,
      fill: { color: borderColor },
    });
    if (label) {
      slide.addText(label, {
        x, y: y + h * 0.45, w, h: h * 0.5,
        fontSize: labelSize, fontFace, color: textColor,
        bold: true, align: "center", valign: "middle", margin: 0,
      });
    }
    return connPoints(x, y, w, h, { top: { x: cx, y: y - 0.22 } });
  },

  /**
   * column — tall thin rectangle for IX / chromatography columns.
   */
  column(slide, pres, x, y, opts = {}) {
    const p = o(opts, { w: 0.7, h: 1.4 });
    const { w, h, color, textColor, label, labelSize, fontFace, borderColor, borderWidth } = p;
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h,
      fill: { color },
      line: { color: borderColor, width: borderWidth },
      shadow: unitShadow(),
    });
    // Bed dividers (horizontal dashes at 1/3 and 2/3)
    [0.33, 0.66].forEach(frac => {
      slide.addShape(pres.shapes.LINE, {
        x: x + 0.05, y: y + h * frac, w: w - 0.1, h: 0,
        line: { color: textColor, width: 0.5, dashType: "dash" },
      });
    });
    if (label) {
      slide.addText(label, {
        x: x - 0.15, y: y + h + 0.02, w: w + 0.3, h: 0.22,
        fontSize: labelSize - 1, fontFace, color: borderColor,
        bold: true, align: "center", valign: "top", margin: 0,
      });
    }
    return connPoints(x, y, w, h);
  },

  /**
   * heatExchanger — circle with crossing diagonal lines.
   */
  heatExchanger(slide, pres, x, y, opts = {}) {
    const p = o(opts, { w: 0.7, h: 0.7 });
    const { w, h, color, textColor, label, labelSize, fontFace, borderColor, borderWidth } = p;
    slide.addShape(pres.shapes.OVAL, {
      x, y, w, h,
      fill: { color },
      line: { color: borderColor, width: borderWidth },
      shadow: unitShadow(),
    });
    // Cross lines inside circle
    const pad = 0.12;
    slide.addShape(pres.shapes.LINE, {
      x: x + pad, y: y + pad, w: w - pad * 2, h: h - pad * 2,
      line: { color: textColor, width: 1 },
    });
    slide.addShape(pres.shapes.LINE, {
      x: x + pad, y: y + h - pad, w: w - pad * 2, h: -(h - pad * 2),
      line: { color: textColor, width: 1 },
    });
    if (label) {
      slide.addText(label, {
        x: x - 0.2, y: y + h + 0.02, w: w + 0.4, h: 0.22,
        fontSize: labelSize - 1, fontFace, color: borderColor,
        bold: true, align: "center", valign: "top", margin: 0,
      });
    }
    return connPoints(x, y, w, h);
  },

  /**
   * pump — circle with triangle arrow inside.
   */
  pump(slide, pres, x, y, opts = {}) {
    const p = o(opts, { w: 0.45, h: 0.45, color: "788F9C" });
    const { w, h, color, textColor, label, labelSize, fontFace, borderColor, borderWidth } = p;
    slide.addShape(pres.shapes.OVAL, {
      x, y, w, h,
      fill: { color },
      line: { color: borderColor, width: borderWidth },
    });
    // Triangle arrow indicator (right-pointing)
    slide.addText("\u25B6", {
      x, y, w, h,
      fontSize: Math.round(w * 14), fontFace, color: textColor,
      align: "center", valign: "middle", margin: 0,
    });
    if (label) {
      slide.addText(label, {
        x: x - 0.2, y: y + h + 0.01, w: w + 0.4, h: 0.18,
        fontSize: labelSize - 2, fontFace, color: borderColor,
        align: "center", valign: "top", margin: 0,
      });
    }
    return connPoints(x, y, w, h);
  },

  /**
   * filter — rectangle with dashed horizontal midline.
   */
  filter(slide, pres, x, y, opts = {}) {
    const p = o(opts);
    const { w, h, color, textColor, label, labelSize, fontFace, borderColor, borderWidth } = p;
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h,
      fill: { color },
      line: { color: borderColor, width: borderWidth },
      shadow: unitShadow(),
    });
    // Dashed midline (filter media)
    slide.addShape(pres.shapes.LINE, {
      x: x + 0.05, y: y + h / 2, w: w - 0.1, h: 0,
      line: { color: textColor, width: 1, dashType: "dash" },
    });
    if (label) {
      slide.addText(label, {
        x, y, w, h,
        fontSize: labelSize, fontFace, color: textColor,
        bold: true, align: "center", valign: "middle", margin: 0,
      });
    }
    return connPoints(x, y, w, h);
  },

  /**
   * evaporator — tall rectangle with wavy interior lines (steam indication).
   */
  evaporator(slide, pres, x, y, opts = {}) {
    const p = o(opts, { w: 1.0, h: 1.2 });
    const { w, h, color, textColor, label, labelSize, fontFace, borderColor, borderWidth } = p;
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h,
      fill: { color },
      line: { color: borderColor, width: borderWidth },
      shadow: unitShadow(),
    });
    // Steam indication — "~" text at top
    slide.addText("~ ~ ~", {
      x, y: y + 0.05, w, h: 0.2,
      fontSize: 8, fontFace, color: textColor,
      align: "center", valign: "top", margin: 0,
    });
    // Vapor exit point
    const extras = { vapor: { x: x + w / 2, y } };
    if (label) {
      slide.addText(label, {
        x, y: y + h * 0.35, w, h: h * 0.6,
        fontSize: labelSize, fontFace, color: textColor,
        bold: true, align: "center", valign: "middle", margin: 0,
      });
    }
    return connPoints(x, y, w, h, extras);
  },

  /**
   * crystallizer — rectangle with small diamond shapes inside.
   */
  crystallizer(slide, pres, x, y, opts = {}) {
    const p = o(opts, { h: 1.0 });
    const { w, h, color, textColor, label, labelSize, fontFace, borderColor, borderWidth } = p;
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h,
      fill: { color },
      line: { color: borderColor, width: borderWidth },
      shadow: unitShadow(),
    });
    // Crystal symbols (diamond chars)
    slide.addText("\u25C7 \u25C7 \u25C7", {
      x, y: y + 0.05, w, h: 0.25,
      fontSize: 8, fontFace, color: textColor,
      align: "center", valign: "middle", margin: 0,
    });
    if (label) {
      slide.addText(label, {
        x, y: y + h * 0.4, w, h: h * 0.55,
        fontSize: labelSize, fontFace, color: textColor,
        bold: true, align: "center", valign: "middle", margin: 0,
      });
    }
    return connPoints(x, y, w, h);
  },

  /**
   * dryer — rectangle with wavy top line and heat arrows.
   */
  dryer(slide, pres, x, y, opts = {}) {
    const p = o(opts);
    const { w, h, color, textColor, label, labelSize, fontFace, borderColor, borderWidth } = p;
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h,
      fill: { color },
      line: { color: borderColor, width: borderWidth },
      shadow: unitShadow(),
    });
    // Heat arrows (upward)
    slide.addText("\u2191 \u2191 \u2191", {
      x, y: y + 0.02, w, h: 0.2,
      fontSize: 7, fontFace, color: textColor,
      align: "center", valign: "top", margin: 0,
    });
    if (label) {
      slide.addText(label, {
        x, y: y + h * 0.25, w, h: h * 0.7,
        fontSize: labelSize, fontFace, color: textColor,
        bold: true, align: "center", valign: "middle", margin: 0,
      });
    }
    return connPoints(x, y, w, h);
  },

  /**
   * membrane — rectangle with vertical dashed line (permeate/retentate split).
   */
  membrane(slide, pres, x, y, opts = {}) {
    const p = o(opts);
    const { w, h, color, textColor, label, labelSize, fontFace, borderColor, borderWidth } = p;
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h,
      fill: { color },
      line: { color: borderColor, width: borderWidth },
      shadow: unitShadow(),
    });
    // Vertical membrane line at 60% width
    const memX = x + w * 0.6;
    slide.addShape(pres.shapes.LINE, {
      x: memX, y: y + 0.05, w: 0, h: h - 0.1,
      line: { color: textColor, width: 1, dashType: "dash" },
    });
    const extras = {
      permeate:  { x: x + w, y: y + h * 0.3 },
      retentate: { x: x + w, y: y + h * 0.7 },
    };
    if (label) {
      slide.addText(label, {
        x, y, w: w * 0.55, h,
        fontSize: labelSize, fontFace, color: textColor,
        bold: true, align: "center", valign: "middle", margin: 0,
      });
    }
    return connPoints(x, y, w, h, extras);
  },

  /**
   * smbSystem — multi-column group representing SMB chromatography.
   * Draws numCols small columns + surrounding box.
   */
  smbSystem(slide, pres, x, y, opts = {}) {
    const p = o(opts, { w: 2.0, h: 1.4, numCols: 4 });
    const { w, h, color, textColor, label, labelSize, fontFace, borderColor, borderWidth, numCols } = p;
    // Surrounding dashed box
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h,
      fill: { color: "FFFFFF" },
      line: { color: borderColor, width: 1, dashType: "dash" },
      shadow: unitShadow(),
    });
    // Individual columns inside
    const colW = 0.3;
    const colH = h * 0.6;
    const gap = (w - numCols * colW) / (numCols + 1);
    const colY = y + (h - colH) / 2;
    for (let i = 0; i < numCols; i++) {
      const colX = x + gap + i * (colW + gap);
      slide.addShape(pres.shapes.RECTANGLE, {
        x: colX, y: colY, w: colW, h: colH,
        fill: { color },
        line: { color: borderColor, width: 1 },
      });
    }
    // Label below
    if (label) {
      slide.addText(label, {
        x: x - 0.1, y: y + h + 0.02, w: w + 0.2, h: 0.22,
        fontSize: labelSize, fontFace, color: borderColor,
        bold: true, align: "center", valign: "top", margin: 0,
      });
    }
    const extras = {
      extract:   { x: x + w, y: y + h * 0.3 },
      raffinate: { x: x + w, y: y + h * 0.7 },
      feed:      { x: x,     y: y + h * 0.5 },
      eluent:    { x: x,     y: y + h * 0.2 },
    };
    return connPoints(x, y, w, h, extras);
  },

  /**
   * carbonColumn — tall rectangle with dots (GAC/PAC).
   */
  carbonColumn(slide, pres, x, y, opts = {}) {
    const p = o(opts, { w: 0.8, h: 1.2, color: "36454F" });
    const { w, h, color, textColor, label, labelSize, fontFace, borderColor, borderWidth } = p;
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h,
      fill: { color },
      line: { color: borderColor, width: borderWidth },
      shadow: unitShadow(),
    });
    // Carbon bed dots
    slide.addText("\u2022 \u2022 \u2022\n\u2022 \u2022 \u2022", {
      x, y: y + h * 0.15, w, h: h * 0.4,
      fontSize: 7, fontFace, color: textColor,
      align: "center", valign: "middle", margin: 0,
    });
    if (label) {
      slide.addText(label, {
        x: x - 0.15, y: y + h + 0.02, w: w + 0.3, h: 0.22,
        fontSize: labelSize - 1, fontFace, color: borderColor,
        bold: true, align: "center", valign: "top", margin: 0,
      });
    }
    return connPoints(x, y, w, h);
  },

  /**
   * mixer — small square with "X" cross inside.
   */
  mixer(slide, pres, x, y, opts = {}) {
    const p = o(opts, { w: 0.5, h: 0.5 });
    const { w, h, color, textColor, label, labelSize, fontFace, borderColor, borderWidth } = p;
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h,
      fill: { color },
      line: { color: borderColor, width: borderWidth },
    });
    slide.addText("\u2715", {
      x, y, w, h,
      fontSize: 12, fontFace, color: textColor,
      align: "center", valign: "middle", margin: 0,
    });
    if (label) {
      slide.addText(label, {
        x: x - 0.15, y: y + h + 0.01, w: w + 0.3, h: 0.18,
        fontSize: labelSize - 2, fontFace, color: borderColor,
        align: "center", valign: "top", margin: 0,
      });
    }
    return connPoints(x, y, w, h);
  },
};

// ---------------------------------------------------------------------------
// STREAMS — draw connecting lines with arrows between units
// ---------------------------------------------------------------------------
const streams = {

  /**
   * connect — draw a line from point A to point B.
   * Auto-detects straight vs L-bend routing.
   * opts: { label, color, width, labelSize, labelColor, bendDirection }
   * bendDirection: "horizontal-first" (default) or "vertical-first"
   */
  connect(slide, pres, from, to, opts = {}) {
    const color = opts.color || DEFAULTS.streamColor;
    const width = opts.width || DEFAULTS.streamWidth;
    const arrowEnd = "triangle";
    const tolerance = 0.05;
    const sameY = Math.abs(from.y - to.y) < tolerance;
    const sameX = Math.abs(from.x - to.x) < tolerance;

    if (sameY) {
      // Straight horizontal
      const minX = Math.min(from.x, to.x);
      const lineW = Math.abs(to.x - from.x);
      slide.addShape(pres.shapes.LINE, {
        x: minX, y: from.y, w: lineW, h: 0,
        line: { color, width },
        lineHead: from.x < to.x ? undefined : arrowEnd,
        lineTail: from.x < to.x ? arrowEnd : undefined,
      });
    } else if (sameX) {
      // Straight vertical
      const minY = Math.min(from.y, to.y);
      const lineH = Math.abs(to.y - from.y);
      slide.addShape(pres.shapes.LINE, {
        x: from.x, y: minY, w: 0, h: lineH,
        line: { color, width },
        lineHead: from.y < to.y ? undefined : arrowEnd,
        lineTail: from.y < to.y ? arrowEnd : undefined,
      });
    } else {
      // L-bend: horizontal first, then vertical
      const bendDir = opts.bendDirection || "horizontal-first";
      if (bendDir === "horizontal-first") {
        // Horizontal segment: from → (to.x, from.y)
        const seg1MinX = Math.min(from.x, to.x);
        slide.addShape(pres.shapes.LINE, {
          x: seg1MinX, y: from.y, w: Math.abs(to.x - from.x), h: 0,
          line: { color, width },
        });
        // Vertical segment: (to.x, from.y) → to
        const seg2MinY = Math.min(from.y, to.y);
        slide.addShape(pres.shapes.LINE, {
          x: to.x, y: seg2MinY, w: 0, h: Math.abs(to.y - from.y),
          line: { color, width },
          lineHead: from.y < to.y ? undefined : arrowEnd,
          lineTail: from.y < to.y ? arrowEnd : undefined,
        });
      } else {
        // Vertical first, then horizontal
        const seg1MinY = Math.min(from.y, to.y);
        slide.addShape(pres.shapes.LINE, {
          x: from.x, y: seg1MinY, w: 0, h: Math.abs(to.y - from.y),
          line: { color, width },
        });
        const seg2MinX = Math.min(from.x, to.x);
        slide.addShape(pres.shapes.LINE, {
          x: seg2MinX, y: to.y, w: Math.abs(to.x - from.x), h: 0,
          line: { color, width },
          lineHead: from.x < to.x ? undefined : arrowEnd,
          lineTail: from.x < to.x ? arrowEnd : undefined,
        });
      }
    }

    // Label at midpoint
    if (opts.label) {
      const midX = (from.x + to.x) / 2;
      const midY = (from.y + to.y) / 2;
      streams.label(slide, pres, midX, midY, opts.label, opts);
    }
  },

  /**
   * recycle — U-shaped or L-shaped return line routing below (or above) the main flow.
   * from: start connection point (usually .bottom or .out of downstream unit)
   * to:   end connection point (usually .in or .top of upstream unit)
   * opts.routeY: Y position to route the horizontal segment through
   *              (default: max(from.y, to.y) + 0.5 — routes below both units)
   * opts.routeAbove: if true, routes above instead of below
   */
  recycle(slide, pres, from, to, opts = {}) {
    const color = opts.color || DEFAULTS.streamColor;
    const width = opts.width || DEFAULTS.streamWidth;
    const arrowEnd = "triangle";

    const routeY = opts.routeY != null
      ? opts.routeY
      : opts.routeAbove
        ? Math.min(from.y, to.y) - 0.4
        : Math.max(from.y, to.y) + 0.5;

    // Segment 1: vertical from `from` to routeY
    const seg1MinY = Math.min(from.y, routeY);
    slide.addShape(pres.shapes.LINE, {
      x: from.x, y: seg1MinY, w: 0, h: Math.abs(routeY - from.y),
      line: { color, width },
    });

    // Segment 2: horizontal at routeY from from.x to to.x
    const seg2MinX = Math.min(from.x, to.x);
    slide.addShape(pres.shapes.LINE, {
      x: seg2MinX, y: routeY, w: Math.abs(to.x - from.x), h: 0,
      line: { color, width },
    });

    // Segment 3: vertical from routeY to `to`
    const seg3MinY = Math.min(routeY, to.y);
    slide.addShape(pres.shapes.LINE, {
      x: to.x, y: seg3MinY, w: 0, h: Math.abs(to.y - routeY),
      line: { color, width },
      lineHead: routeY < to.y ? undefined : arrowEnd,
      lineTail: routeY < to.y ? arrowEnd : undefined,
    });

    // Label on horizontal segment
    if (opts.label) {
      const midX = (from.x + to.x) / 2;
      streams.label(slide, pres, midX, routeY, opts.label, {
        ...opts,
        labelAbove: !opts.routeAbove, // label above the line when routing below
      });
    }
  },

  /**
   * branch — one source splits to multiple targets.
   * Draws one line from source, then branches to each target.
   */
  branch(slide, pres, from, targets, opts = {}) {
    const color = opts.color || DEFAULTS.streamColor;
    const width = opts.width || DEFAULTS.streamWidth;
    const arrowEnd = "triangle";

    // Calculate branch point (midway X between from and closest target)
    const midX = opts.branchX || (from.x + Math.min(...targets.map(t => t.x))) / 2;

    // Main stem: horizontal from source to branch point
    slide.addShape(pres.shapes.LINE, {
      x: from.x, y: from.y, w: midX - from.x, h: 0,
      line: { color, width },
    });

    // Vertical range of targets
    const minTY = Math.min(...targets.map(t => t.y));
    const maxTY = Math.max(...targets.map(t => t.y));

    // Vertical backbone at branch point
    if (targets.length > 1) {
      slide.addShape(pres.shapes.LINE, {
        x: midX, y: minTY, w: 0, h: maxTY - minTY,
        line: { color, width },
      });
    }

    // Individual branches from backbone to each target
    targets.forEach((t, i) => {
      slide.addShape(pres.shapes.LINE, {
        x: midX, y: t.y, w: t.x - midX, h: 0,
        line: { color, width },
        lineTail: arrowEnd,
      });
      // Optional per-target labels
      if (opts.labels && opts.labels[i]) {
        const lx = (midX + t.x) / 2;
        streams.label(slide, pres, lx, t.y, opts.labels[i], opts);
      }
    });
  },

  /**
   * label — place a stream annotation text near a point.
   */
  label(slide, pres, x, y, text, opts = {}) {
    const fontSize = opts.labelSize || DEFAULTS.streamLabelSize;
    const color = opts.labelColor || DEFAULTS.streamLabelColor;
    const fontFace = opts.fontFace || DEFAULTS.fontFace;
    const above = opts.labelAbove !== false;
    const labelW = Math.max(text.length * 0.07, 0.9);
    slide.addText(text, {
      x: x - labelW / 2,
      y: above ? y - 0.26 : y + 0.06,
      w: labelW,
      h: 0.22,
      fontSize, fontFace, color,
      align: "center", valign: "middle", margin: 0,
    });
  },
};

// ---------------------------------------------------------------------------
// LAYOUT — auto-positioning helpers
// ---------------------------------------------------------------------------
const layout = {

  /**
   * linear — position units in a single row, evenly spaced.
   * Returns array of { x, y } positions.
   * unitDefs: array of { w, h } (dimensions of each unit).
   */
  linear(unitDefs, slideWidth = 10, startX = 0.4, startY = 1.5, gap = 0.6) {
    const positions = [];
    let currentX = startX;
    unitDefs.forEach(u => {
      positions.push({ x: currentX, y: startY });
      currentX += (u.w || DEFAULTS.w) + gap;
    });
    // If exceeds slide, compress gap
    const totalW = currentX - gap - startX;
    if (totalW + startX > slideWidth - 0.4) {
      const availW = slideWidth - startX - 0.4;
      const unitsTotalW = unitDefs.reduce((s, u) => s + (u.w || DEFAULTS.w), 0);
      const newGap = (availW - unitsTotalW) / Math.max(unitDefs.length - 1, 1);
      let cx = startX;
      positions.length = 0;
      unitDefs.forEach(u => {
        positions.push({ x: cx, y: startY });
        cx += (u.w || DEFAULTS.w) + Math.max(newGap, 0.2);
      });
    }
    return positions;
  },

  /**
   * grid — position units in rows and columns.
   * Returns 2D array of { x, y } positions.
   */
  grid(numUnits, cols = 4, startX = 0.4, startY = 1.0, gapX = 0.5, gapY = 0.5, unitW, unitH) {
    const w = unitW || DEFAULTS.w;
    const h = unitH || DEFAULTS.h;
    const positions = [];
    for (let i = 0; i < numUnits; i++) {
      const col = i % cols;
      const row = Math.floor(i / cols);
      positions.push({
        x: startX + col * (w + gapX),
        y: startY + row * (h + gapY),
      });
    }
    return positions;
  },

  /**
   * verifyFits — check that placed units + labels stay within slide bounds.
   * Prints warnings to console if any element overflows.
   *
   * placedUnits: array of { x, w, label? } (from connPoints or manual layout)
   * opts: { slideWidth, labelLeft, labelRight, name }
   *   slideWidth  — slide width in inches (default 10 for 16:9)
   *   labelLeft   — width of label to the left of first unit (e.g. "Raw Water")
   *   labelRight  — width of label to the right of last unit (e.g. "Ultra Pure Water")
   *   name        — diagram name for log messages
   *
   * Returns { ok, warnings } — ok is true if no overflow detected.
   */
  verifyFits(placedUnits, opts = {}) {
    const slideW = opts.slideWidth || 10;
    const labelL = opts.labelLeft || 0;
    const labelR = opts.labelRight || 0;
    const name = opts.name || "layout";
    const warnings = [];

    if (placedUnits.length === 0) return { ok: true, warnings };

    // Find leftmost and rightmost edges
    let leftEdge = Infinity;
    let rightEdge = -Infinity;
    placedUnits.forEach((u, i) => {
      const x = u.x != null ? u.x : 0;
      const w = u.w != null ? u.w : DEFAULTS.w;
      if (x < leftEdge) leftEdge = x;
      if (x + w > rightEdge) rightEdge = x + w;
    });

    // Check left overflow (including left label)
    const effectiveLeft = leftEdge - labelL;
    if (effectiveLeft < 0) {
      warnings.push(`Left overflow: leftmost edge at ${effectiveLeft.toFixed(2)}" (need >= 0)`);
    }

    // Check right overflow (including right label)
    const effectiveRight = rightEdge + labelR;
    if (effectiveRight > slideW) {
      warnings.push(`Right overflow: rightmost edge at ${effectiveRight.toFixed(2)}" (slide is ${slideW}")`);
    }

    // Print warnings
    if (warnings.length > 0) {
      console.warn(`⚠ [${name}] Layout overflow detected:`);
      warnings.forEach(w => console.warn(`   ${w}`));
    }

    return { ok: warnings.length === 0, warnings };
  },

  /**
   * multiRow — lay out units left-to-right, wrapping to next row when exceeding maxWidth.
   * Returns array of { x, y, row } positions.
   */
  multiRow(unitDefs, maxWidth = 9.2, startX = 0.4, startY = 1.2, gapX = 0.5, gapY = 0.8) {
    const positions = [];
    let cx = startX;
    let cy = startY;
    let row = 0;
    unitDefs.forEach(u => {
      const w = u.w || DEFAULTS.w;
      if (cx + w > startX + maxWidth && cx > startX) {
        row++;
        cx = startX;
        cy += (u.h || DEFAULTS.h) + gapY;
      }
      positions.push({ x: cx, y: cy, row });
      cx += w + gapX;
    });
    return positions;
  },
};

// ---------------------------------------------------------------------------
// ANNOTATIONS — process conditions and mass balance labels
// ---------------------------------------------------------------------------
const annotations = {

  /**
   * conditions — small text box with process conditions.
   * lines: array of strings, e.g. ["T: 95 C", "pH: 5.0", "Brix: 42%"]
   */
  conditions(slide, pres, x, y, lines, opts = {}) {
    const fontSize = opts.fontSize || DEFAULTS.annotationSize;
    const color = opts.color || DEFAULTS.annotationColor;
    const fontFace = opts.fontFace || DEFAULTS.fontFace;
    const bg = opts.bg || "F8FAFB";
    const text = lines.join("\n");
    const h = Math.max(lines.length * 0.16, 0.3);
    const w = opts.w || Math.max(...lines.map(l => l.length * 0.055), 0.8);
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h,
      fill: { color: bg },
      line: { color: "CFD9DB", width: 0.5 },
    });
    slide.addText(text, {
      x, y, w, h,
      fontSize, fontFace, color,
      align: "left", valign: "middle",
      margin: [2, 4, 2, 4],
      lineSpacingMultiple: 0.85,
    });
  },

  /**
   * massBalance — annotated flow rate and composition box.
   * data: { stream, flow, brix, purity, temp, ... }
   */
  massBalance(slide, pres, x, y, data, opts = {}) {
    const lines = [];
    if (data.stream) lines.push(data.stream);
    if (data.flow)   lines.push(`Flow: ${data.flow}`);
    if (data.brix)   lines.push(`Brix: ${data.brix}`);
    if (data.purity) lines.push(`Purity: ${data.purity}`);
    if (data.temp)   lines.push(`Temp: ${data.temp}`);
    if (data.pH)     lines.push(`pH: ${data.pH}`);
    annotations.conditions(slide, pres, x, y, lines, opts);
  },

  /**
   * title — slide title for process diagram slides.
   */
  title(slide, pres, text, opts = {}) {
    const fontFace = opts.fontFace || "Aeonik";
    const color = opts.color || "263338";
    slide.addText(text, {
      x: 0.5, y: 0.15, w: 9, h: 0.5,
      fontSize: opts.fontSize || 24, fontFace, color,
      bold: true, margin: 0,
    });
  },

  /**
   * legend — color legend for different stream types or unit categories.
   * items: [{ label, color }]
   */
  legend(slide, pres, x, y, items, opts = {}) {
    const fontSize = opts.fontSize || 7;
    const fontFace = opts.fontFace || DEFAULTS.fontFace;
    items.forEach((item, i) => {
      const iy = y + i * 0.2;
      slide.addShape(pres.shapes.RECTANGLE, {
        x, y: iy + 0.03, w: 0.14, h: 0.14,
        fill: { color: item.color },
      });
      slide.addText(item.label, {
        x: x + 0.2, y: iy, w: 1.2, h: 0.2,
        fontSize, fontFace, color: "263338",
        align: "left", valign: "middle", margin: 0,
      });
    });
  },
};

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------
module.exports = { units, streams, layout, annotations, DEFAULTS };
