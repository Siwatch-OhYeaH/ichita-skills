# ICHITA Brand Fonts

## Aeonik (Primary — Body & Headlines)

14 weights in `aeonik/`:

| Weight | Regular | Italic |
|--------|---------|--------|
| Air | Aeonik-Air.otf | Aeonik-AirItalic.otf |
| Thin | Aeonik-Thin.otf | Aeonik-ThinItalic.otf |
| Light | Aeonik-Light.otf | Aeonik-LightItalic.otf |
| Regular | Aeonik-Regular.otf | Aeonik-RegularItalic.otf |
| Medium | Aeonik-Medium.otf | Aeonik-MediumItalic.otf |
| Bold | Aeonik-Bold.otf | Aeonik-BoldItalic.otf |
| Black | Aeonik-Black.otf | Aeonik-BlackItalic.otf |

## Betatron (Display — Logo-style headlines)

1 weight in `betatron/`:

| Weight | File |
|--------|------|
| Regular | Betatron-Regular.otf |

## Bai Jamjuree (Thai — Body & Headlines)

12 weights in `bai-jamjuree/` (OFL licensed):

| Weight | Regular | Italic |
|--------|---------|--------|
| ExtraLight | BaiJamjuree-ExtraLight.ttf | BaiJamjuree-ExtraLightItalic.ttf |
| Light | BaiJamjuree-Light.ttf | BaiJamjuree-LightItalic.ttf |
| Regular | BaiJamjuree-Regular.ttf | BaiJamjuree-Italic.ttf |
| Medium | BaiJamjuree-Medium.ttf | BaiJamjuree-MediumItalic.ttf |
| SemiBold | BaiJamjuree-SemiBold.ttf | BaiJamjuree-SemiBoldItalic.ttf |
| Bold | BaiJamjuree-Bold.ttf | BaiJamjuree-BoldItalic.ttf |

## Installation

### Windows

```powershell
# Option 1: Double-click each .otf file → "Install"
# Option 2: Select all → right-click → "Install for all users"
```

### macOS

```bash
cp assets/fonts/aeonik/*.otf ~/Library/Fonts/
cp assets/fonts/bai-jamjuree/*.ttf ~/Library/Fonts/
cp assets/fonts/betatron/*.otf ~/Library/Fonts/
```

### Linux

```bash
mkdir -p ~/.local/share/fonts
cp assets/fonts/aeonik/*.otf ~/.local/share/fonts/
cp assets/fonts/bai-jamjuree/*.ttf ~/.local/share/fonts/
cp assets/fonts/betatron/*.otf ~/.local/share/fonts/
fc-cache -fv
```

## Usage in Brand

Per `ichita-defaults.md`:
- **Headings**: Aeonik Bold / Medium
- **Body**: Aeonik Regular
- **Captions**: Aeonik Light
- **Display/Logo**: Betatron Regular
- **Thai text**: Bai Jamjuree (pairs well with Aeonik for Thai/English mixed content)
