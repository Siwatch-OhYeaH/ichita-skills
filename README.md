# ichita-skills

Private Claude Code plugin for ICHITA Technology — document skills (PPTX, DOCX, PDF) with brand templates and assets.

## Skills

| Skill | Command | Description |
|-------|---------|-------------|
| PPTX | `/ichita-skills:pptx` | Create and edit PowerPoint presentations with ICHITA brand templates |
| DOCX | `/ichita-skills:docx` | Create and edit Word documents with tracked changes support |
| PDF | `/ichita-skills:pdf` | PDF processing, form filling, and manipulation |

## Setup (Admin)

1. Push this repo to `Siwatch-OhYeaH/ichita-skills` (private)
2. Go to Claude.ai → Admin Settings → Claude Code → Managed settings
3. Add:

```json
{
  "extraKnownMarketplaces": {
    "ichita": {
      "source": {
        "source": "github",
        "repo": "Siwatch-OhYeaH/ichita-skills"
      }
    }
  },
  "enabledPlugins": {
    "ichita-skills@ichita": true
  }
}
```

## Team Members

Skills are auto-available after admin setup. No action required.

## Structure

```
├── .claude-plugin/     # Plugin metadata
├── skills/
│   ├── pptx/           # PowerPoint skill + scripts + OOXML schemas
│   ├── docx/           # Word document skill + scripts + OOXML schemas
│   └── pdf/            # PDF skill + scripts
├── assets/
│   ├── brand/          # Brand guidelines, defaults
│   ├── templates/      # PPTX/DOCX templates
│   ├── logos/          # ICHITA logos
│   ├── icons/          # Icon assets
│   ├── partner-logos/  # Partner brand logos
│   └── equipment-photos/
└── knowledge/          # Company profile, brand guidelines
```

## License

Proprietary — ICHITA Technology Co., Ltd.
