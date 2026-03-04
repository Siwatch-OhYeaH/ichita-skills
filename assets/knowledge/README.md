# Ichita Knowledge Database

Knowledge that Claude doesn't have by default — Ichita-specific data, Thai market context, proprietary information.

## Structure

```
knowledge/
├── water-technology/     ← Water treatment systems
│   ├── pretreatment/     ← Sand filter, carbon filter, clarifier
│   ├── membranes/        ← MF, UF, RO
│   ├── ion-exchange/     ← Softener, resin, demin, EDI
│   └── mbr/              ← Membrane bioreactor
│
├── process-solutions/    ← Product-specific processes
│   ├── sugar-refining/   ← White sugar from raw
│   ├── liquid-sugar/     ← Liquid sugar production
│   ├── fruit-juice/      ← Juice processing
│   ├── pineapple-peel-syrup/
│   ├── yeast-extract/
│   └── dairy/
│
├── specialty/            ← Advanced separation
│   ├── chromatography/   ← SMB systems
│   ├── enzyme/           ← Enzyme reactions
│   ├── sugar-inversion/  ← Inversion processes
│   ├── concentration/    ← Membrane concentration
│   └── nuosep-hp/        ← Ichita's adsorbent resin
│
└── common/               ← Shared reference data
    ├── thailand-utilities.md
    ├── vendors.md
    └── pricing.md
```

## How to Add Knowledge

1. Find the right category folder
2. Create a markdown file with clear, structured data
3. Focus on what Claude DOESN'T know:
   - Ichita's preferred suppliers and part numbers
   - Thai market pricing (update date!)
   - Real project data and lessons learned
   - Proprietary product specs and dosing
   - Local regulations and standards
4. Include the date and source of information
5. Update the category's `index.md` to reference new files

## Format Convention

Each knowledge file should include:
- **Title** with date of last update
- **Source** (who provided this data)
- **Data** in tables where possible
- **Notes** on limitations or assumptions

## Auto-Loading

These files are referenced by `.claude/instructions/ichita-engineering.instructions.md` and loaded when working on engineering tasks.
