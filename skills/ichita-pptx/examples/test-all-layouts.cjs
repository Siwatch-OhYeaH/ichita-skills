/**
 * test-all-layouts.cjs — Ichita Slide Library Visual QA Test Deck
 *
 * Generates a PPTX with every layout type and block component.
 * Use this for visual inspection of brand consistency.
 *
 * Usage:
 *   node skills/ichita-pptx/examples/test-all-layouts.cjs test-output/test-all-layouts.pptx
 */

"use strict";

const path = require("path");
const { createPresentation, slides, blocks, COLORS, FONTS } = require(
  path.resolve(__dirname, "../scripts/ichita-slide-lib.cjs")
);

const outputPath = process.argv[2] || path.resolve(__dirname, "../../../test-output/test-all-layouts.pptx");

console.log("Ichita Slide Library — Test All Layouts");
console.log("Output:", outputPath);
console.log("Building 14 slides...\n");

// ---------------------------------------------------------------------------
// Initialize presentation
// ---------------------------------------------------------------------------
const pres = createPresentation({
  title: "Ichita Slide Library Test Deck",
  subject: "All layout types and block components — Visual QA",
  author: "Davinci Oracle",
});

// ---------------------------------------------------------------------------
// Slide 1: Cover
// ---------------------------------------------------------------------------
console.log("  [01] Cover");
slides.cover(pres, {
  title: "Ichita Slide Library\nLayout Test Deck",
  subtitle: "All layout types and block components",
  date: "April 2026",
});

// ---------------------------------------------------------------------------
// Slide 2: Section Divider — 01 Core Layouts
// ---------------------------------------------------------------------------
console.log("  [02] Section Divider — Core Layouts");
slides.sectionDivider(pres, {
  number: "01",
  title: "Core Layouts",
  subtitle: "Cover, Content, Two-Column, Grid, KPI",
});

// ---------------------------------------------------------------------------
// Slide 3: Content — body text + insightBar
// ---------------------------------------------------------------------------
console.log("  [03] Content (body text + insightBar)");
const slide3 = slides.content(pres, {
  title: "Membrane Filtration Technology",
});

slide3.addText(
  "Ichita delivers integrated membrane separation systems for liquid purification across " +
  "water treatment, liquid sugar, starch-tapioca syrup, biochemical, and ethanol applications.\n\n" +
  "Our portfolio covers UF, NF, RO, and EDI — from laboratory pilot scale through full commercial " +
  "EPC turn-key installations. Each system is engineered to the process, not sized off the shelf.",
  {
    x: 0.5,
    y: 1.25,
    w: 9.0,
    h: 2.6,
    fontSize: 12,
    fontFace: "Aeonik",
    color: COLORS.blueGrey03,
    wrap: true,
    valign: "top",
  }
);

blocks.insightBar(slide3, {
  text: "Key principle: separation performance is defined at the system level, not by any single membrane unit.",
});

// ---------------------------------------------------------------------------
// Slide 4: Two-Column — featureList + 2 statCards
// ---------------------------------------------------------------------------
console.log("  [04] Two-Column (featureList + statCards)");
slides.twoColumn(pres, {
  title: "Core Technology Offering",
  leftContent: (slide, zone) => {
    blocks.featureList(slide, {
      items: [
        {
          title: "Ultrafiltration (UF)",
          description: "Pre-treatment for RO/NF; removes suspended solids, bacteria, and colloids. MWCO 5–100 kDa.",
        },
        {
          title: "Nanofiltration (NF) — Microdynadir",
          description: "Selective ion removal and colour reduction. Operates between RO and UF pressure ranges.",
        },
        {
          title: "Reverse Osmosis (RO) — CSM",
          description: "High-rejection desalination and demineralisation. TDS reduction > 98%.",
        },
      ],
      x: zone.x,
      y: zone.y,
      w: zone.w,
      h: zone.h,
      dotColor: COLORS.blue,
    });
  },
  rightContent: (slide, zone) => {
    const cardH = (zone.h - 0.2) / 2;
    blocks.statCard(slide, {
      value: "98%+",
      label: "TDS Rejection (RO)",
      x: zone.x,
      y: zone.y,
      w: zone.w,
      h: cardH,
      valueColor: COLORS.blue,
    });
    blocks.statCard(slide, {
      value: "5 kDa",
      label: "Min MWCO (UF)",
      x: zone.x,
      y: zone.y + cardH + 0.2,
      w: zone.w,
      h: cardH,
      valueColor: COLORS.blueGrey03,
    });
  },
});

// ---------------------------------------------------------------------------
// Slide 5: 3-Column Grid — 3 statCards
// ---------------------------------------------------------------------------
console.log("  [05] 3-Column Grid (statCards)");
slides.grid(pres, {
  title: "Project Portfolio at a Glance",
  cols: 3,
  cards: [
    (slide, zone) => blocks.statCard(slide, {
      value: "120+",
      label: "Completed Projects",
      x: zone.x, y: zone.y, w: zone.w, h: zone.h,
      valueColor: COLORS.blue,
    }),
    (slide, zone) => blocks.statCard(slide, {
      value: "20+",
      label: "Years of Operation",
      x: zone.x, y: zone.y, w: zone.w, h: zone.h,
      valueColor: COLORS.blueGrey03,
    }),
    (slide, zone) => blocks.statCard(slide, {
      value: "99.2%",
      label: "System Uptime (avg)",
      x: zone.x, y: zone.y, w: zone.w, h: zone.h,
      valueColor: COLORS.blue,
    }),
  ],
});

// ---------------------------------------------------------------------------
// Slide 6: 2×2 Grid — 4 statCards
// ---------------------------------------------------------------------------
console.log("  [06] 2x2 Grid (4 statCards)");
slides.grid2x2(pres, {
  title: "Membrane Technology Coverage",
  cards: [
    (slide, zone) => blocks.statCard(slide, {
      value: "UF",
      label: "Ultrafiltration — 5–100 kDa",
      x: zone.x, y: zone.y, w: zone.w, h: zone.h,
      valueColor: COLORS.blue,
    }),
    (slide, zone) => blocks.statCard(slide, {
      value: "NF",
      label: "Nanofiltration — Selective ions",
      x: zone.x, y: zone.y, w: zone.w, h: zone.h,
      valueColor: COLORS.blueLight,
    }),
    (slide, zone) => blocks.statCard(slide, {
      value: "RO",
      label: "Reverse Osmosis — 98%+ TDS",
      x: zone.x, y: zone.y, w: zone.w, h: zone.h,
      valueColor: COLORS.blueGrey03,
    }),
    (slide, zone) => blocks.statCard(slide, {
      value: "EDI",
      label: "Electrodeionisation — UPW",
      x: zone.x, y: zone.y, w: zone.w, h: zone.h,
      valueColor: COLORS.blueGrey02,
    }),
  ],
});

// ---------------------------------------------------------------------------
// Slide 7: KPI
// ---------------------------------------------------------------------------
console.log("  [07] KPI slide");
slides.kpi(pres, {
  value: "15–20%",
  label: "Sugar Recovery Improvement",
  context: "Typical improvement after Ichita chromatographic SMB integration — customer results may vary.",
});

// ---------------------------------------------------------------------------
// Slide 8: Section Divider — 02 Advanced Layouts
// ---------------------------------------------------------------------------
console.log("  [08] Section Divider — Advanced Layouts");
slides.sectionDivider(pres, {
  number: "02",
  title: "Advanced Layouts",
  subtitle: "Comparison, Timeline, Table, Process Flow",
});

// ---------------------------------------------------------------------------
// Slide 9: Comparison — before/after featureLists
// ---------------------------------------------------------------------------
console.log("  [09] Comparison (before/after featureLists)");
slides.comparison(pres, {
  title: "Before vs After Membrane Upgrade",
  leftLabel: "Before — Conventional Filter",
  rightLabel: "After — UF + NF System",
  leftContent: (slide, zone) => {
    blocks.featureList(slide, {
      items: [
        { title: "Sand filter pre-treatment", description: "Requires frequent backwash; inconsistent effluent quality." },
        { title: "High chemical dosing", description: "Coagulant and flocculant costs escalate with feed variability." },
        { title: "Manual QC sampling", description: "Lab turnaround 4–8 hrs; no real-time control feedback." },
      ],
      x: zone.x, y: zone.y, w: zone.w, h: zone.h,
      dotColor: COLORS.blueGrey02,
    });
  },
  rightContent: (slide, zone) => {
    blocks.featureList(slide, {
      items: [
        { title: "UF membrane pre-treatment", description: "Consistent SDI < 2; continuous operation with CIP." },
        { title: "60–70% chemical reduction", description: "NF removes colour and hardness without secondary dosing." },
        { title: "Inline turbidity + conductivity", description: "Real-time monitoring; automatic alarm and divert." },
      ],
      x: zone.x, y: zone.y, w: zone.w, h: zone.h,
      dotColor: COLORS.blue,
    });
  },
});

// ---------------------------------------------------------------------------
// Slide 10: Timeline — 5 project phases
// ---------------------------------------------------------------------------
console.log("  [10] Timeline (5 steps)");
slides.timeline(pres, {
  title: "EPC Project Delivery Timeline",
  steps: [
    { number: "1", title: "Assessment", description: "Site survey, feed analysis, process audit." },
    { number: "2", title: "Design", description: "P&ID, equipment sizing, hydraulic modelling." },
    { number: "3", title: "Fabrication", description: "Skid build, membrane loading, FAT." },
    { number: "4", title: "Installation", description: "Civil interface, piping, electrical, controls." },
    { number: "5", title: "Handover", description: "SAT, operator training, performance guarantee." },
  ],
});

// ---------------------------------------------------------------------------
// Slide 11: Content + table
// ---------------------------------------------------------------------------
console.log("  [11] Content + table (process parameters)");
const slide11 = slides.content(pres, {
  title: "UPW System — Process Parameters",
});

blocks.table(slide11, {
  headers: ["Parameter", "UF Permeate", "NF Permeate", "RO Permeate", "EDI Product"],
  rows: [
    ["Turbidity (NTU)",  "< 0.1",   "< 0.05",  "< 0.01",  "< 0.01"],
    ["Conductivity (µS/cm)", "≤ 50",  "≤ 20",    "≤ 2",     "< 0.055"],
    ["TDS (mg/L)",       "≤ 35",   "≤ 15",    "≤ 1.5",   "< 0.05"],
    ["SDI (15 min)",     "< 2",    "N/A",     "< 1",     "N/A"],
    ["TOC (µg/L)",       "< 500",  "< 200",   "< 100",   "< 5"],
  ],
  x: 0.5,
  y: 1.2,
  w: 9.0,
  colWidths: [0.22, 0.19, 0.19, 0.20, 0.20],
});

// ---------------------------------------------------------------------------
// Slide 12: Content + processFlow
// ---------------------------------------------------------------------------
console.log("  [12] Content + processFlow (UPW system) + insightBar");
const slide12 = slides.content(pres, {
  title: "UPW Treatment Train",
});

blocks.processFlow(slide12, {
  steps: ["Raw Water", "UF", "NF", "RO", "EDI", "UPW"],
  x: 0.5,
  y: 1.9,
  w: 9.0,
  h: 0.7,
  color: COLORS.blue,
});

blocks.insightBar(slide12, {
  text: "Each stage is engineered as a system — not a product sale. Integration ensures guaranteed effluent quality.",
});

// ---------------------------------------------------------------------------
// Slide 13: Closing
// ---------------------------------------------------------------------------
console.log("  [13] Closing");
slides.closing(pres, {
  title: "Thank You",
  subtitle: "Innovative · Reliable · Partnership",
  contact: "www.ichita.co.th  |  info@ichita.co.th  |  +66 (0) 2-xxx-xxxx",
});

// ---------------------------------------------------------------------------
// Slide 14: Thai-text smoke test (verifies TH Aeonik wiring)
// ---------------------------------------------------------------------------
console.log("  [14] Thai Smoke Test (TH Aeonik)");
const thaiSlide = pres.addSlide();
thaiSlide.background = { color: COLORS.white };
thaiSlide.addText("ภาษาไทย — Thai Glyph Smoke Test", {
  x: 0.5, y: 0.4, w: 9, h: 0.6,
  fontSize: 24, fontFace: FONTS.thai, bold: true, color: COLORS.blueGrey03,
});
thaiSlide.addText("ระบบกรอง UF + NF ของ Ichita ผลิตน้ำเชื่อมใสคุณภาพอาหาร", {
  x: 0.5, y: 1.2, w: 9, h: 0.5,
  fontSize: 16, fontFace: FONTS.thai, color: COLORS.blueGrey03,
});
thaiSlide.addText("Mixed text: 99.2% efficiency / ประสิทธิภาพ 99.2%", {
  x: 0.5, y: 2.0, w: 9, h: 0.5,
  fontSize: 14, fontFace: FONTS.thai, color: COLORS.blueGrey02,
});

// ---------------------------------------------------------------------------
// Write output
// ---------------------------------------------------------------------------
console.log("\nWriting PPTX to:", outputPath);
pres.writeFile({ fileName: outputPath })
  .then(() => {
    const fs = require("fs");
    const stat = fs.statSync(outputPath);
    console.log("Done. File size:", (stat.size / 1024).toFixed(1), "KB");
    console.log("14 slides generated successfully.");
  })
  .catch((err) => {
    console.error("ERROR:", err.message);
    process.exit(1);
  });
