# Bitrix Sales Design System

**Version 1.0**

Bitrix Sales is a professional SaaS platform with a clean, modern aesthetic. This design system documents its visual foundations, component library, and UI patterns — providing a single source of truth for building consistent Bitrix Sales experiences.

## Sources

The following reference materials were used to build this design system:

- **Screenshots** `uploads/1.webp` – `uploads/8.webp` — design system slides covering typography, colors, spacing, iconography, buttons, inputs, navigation, and other elements (Version 1.0 of the Tokens system, produced by varti-studio.com)
- No Figma file or codebase was provided. All color values and measurements are extracted from screenshots; see **Caveats** at the bottom.

---

## Products

| Product | Description |
| --- | --- |
| **Bitrix Sales Web App** | Dashboard SaaS application with sidebar navigation, analytics, calendar, notifications |
| **Bitrix Sales Marketing Site** | Public-facing website with top navbar (Work, Product, Download, Resources, About) |

---

## Content Fundamentals

**Tone**: Professional, clear, and approachable. Bitrix Sales' copy is direct and action-oriented without being terse or cold. Think "expert colleague," not "enterprise manual."

**Voice characteristics**:

- Confident but never boastful
- Instructional without being condescending
- Clean, economical language — no filler words
- No emoji in UI copy (emoji are not part of the brand voice)

**Casing**:

- **Headlines**: Sentence case (capitalize first word only)
- **Navigation items**: Title Case (Dashboard, Calendar, Analytics…)
- **Buttons/CTAs**: Title Case ("Sign In", "Button Text", "Try it now")
- **Labels & placeholders**: Sentence case ("Text placeholder", "Help text")
- **Error messages**: Sentence case, concise ("Please try again later")

**Perspective**: Uses "you" to address the user directly. First person ("I") is avoided in UI copy.

**Examples seen in design**:

- "Buttons are clickable elements that are used to trigger actions."
- "Text input is an interactive field that allows users to enter text and data."
- "Click to upload or drag and drop"
- "Information text — Review the changes and feel free to contact us if you have any questions."

---

## Visual Foundations

### Colors

**Primary palette**: Vivid indigo-blue (#3040CC at base 500). Used for CTAs, active states, links, focus rings, and all primary interactive elements. The primary scale ranges from near-white lavender (#EEF1FF at 50) to deep navy (#080D42 at 900).

**Secondary / Warm Orange**: Golden-amber (#E07818 at 500). Used for secondary accents, highlights, and warm contrast against the blue primary.

**Secondary palette**: Blue (cyan family), Yellow (golden), Red (error/danger), Green (success). Each has a 10-step scale (50–900).

**Neutral**: Blue-grey neutral scale (#6880AB base) — not a cold grey, slightly warm-blue. Used for text hierarchy, borders, and backgrounds.

**Content**: Pure black (#000000) and white (#FFFFFF) for text and surfaces.

**Background surfaces**: Two near-white backgrounds — Neutral Grey (#F3F4F4) and Neutral Sand (#F1F1F3). Very subtle distinction; Grey is slightly cooler.

**Dark mode**: Components and slides show dark variants (near-black #0A0A0A backgrounds with white text, used in component headers/hero sections). Full dark-mode token set not documented — light is canonical.

### Typography

**Font**: Manrope exclusively across all weights (Light 300, Regular 400, Medium 500, SemiBold 600, Bold 700, ExtraBold 800). A clean geometric sans-serif with slight humanist warmth.

**Type scale**:

- H1: 72px / Bold / 120% leading
- H2: 64px / Bold / 120% leading
- H3: 48px / Bold / 140% leading
- H4: 32px / Bold / 140% leading
- H5: 32px / Medium / 140% leading
- Subtitle 1: 24px / Bold / 100% leading
- Subtitle 2: 24px / Medium / 100% leading
- Body 1–4: 14px at Bold/Medium/Regular/Light / 150% leading

### Spacing

Base unit is **2px**, with a practical rhythm of 8px. Standard spacing values: 2, 4, 8, 12, 16, 20, 24, 32, 40, 48px. Component padding follows this scale (buttons: 20px horizontal, 8px gap; cards: 16–24px; inputs: 16px horizontal / 10px vertical).

### Grid

- **Desktop**: 1440px max-width, 12 columns, 30px gutters, 68px margins
- **Mobile**: 375px, 4 columns, 16px gutters, 16px margins

### Corner Radii

- Buttons: 8px (md)
- Inputs / Selects: 8px (md)
- Cards: 12–16px (lg–xl)
- Badges / Chips: 6px (sm) or full-pill (9999px)
- Modal / Dialog: 16px (xl)

### Shadows

Subtle, single-layer drop shadows. Never harsh or multi-layered. Cards use `--shadow-md` (0 4px 12px rgba(0,0,0,0.09)). Elevated modals use `--shadow-xl`.

### Backgrounds & Imagery

- **Background surfaces**: Flat #F3F4F4 / #F1F1F3 — no textures or patterns
- **Hero/presentation sections**: Dark near-black (#0A0A0A) with colorful blob-gradient overlays (deep blue, purple, cyan)
- **Card imagery**: Abstract aurora/gradient images (deep blue/purple gradients), used in notification cards and hero thumbnails
- **No photography** used in component UI; imagery is always abstract/gradient

### Animations & Motion

- Transitions are fast (150–200ms ease). No bouncy or springy animations in form elements.
- `--transition-fast: 150ms ease` — hover states on buttons/links
- `--transition-base: 200ms ease` — state changes (focus, expand)
- `--transition-slow: 300ms ease` — panels, modals, sidebars

### Hover & Press States

- **Buttons**: Background darkens one step on hover (primary 500→600), scales slightly on press (not confirmed, likely opacity change)
- **Nav items**: Background fill on hover using brand subtle (#EEF1FF)
- **Links**: Color slightly darkens, no underline in nav
- **Input focus**: Blue border `--color-primary-500` + blue focus ring glow

### Borders

- Default borders: 1px `--color-neutral-200` (light grey)
- Focus borders: 1px `--color-primary-500` (brand blue)
- Error borders: 1px `--color-red-400`
- No heavy borders; borders are subtle and functional

### Transparency & Blur

- No frosted glass / backdrop-blur effects seen
- Overlays use white with shadow rather than blur
- Dark hero sections use color with opacity for gradient blobs

---

## Iconography

Icons follow the **Untitled UI Icons** library (https://www.untitledui.com/icons) — a thin, 1.5px stroke outline icon set at \~20px size. The style is clean, geometric, and minimal — consistent stroke weight throughout.

**Icon characteristics**:

- Stroke weight: \~1.5px
- Corner style: slightly rounded line caps
- Size: 16px (small), 20px (default), 24px (large)
- Color: inherits from parent text color (currentColor)
- On dark backgrounds: white strokes on dark tile backgrounds (from iconography slide)

**Icons seen in navigation sidebar**: Dashboard (home), Calendar, Bell (notifications), Bar chart (analytics), Settings (gear), Question mark (support), Arrow-right (logout), Search, User

**Icons seen in other components**: Star, Pencil/edit, Eye/hide, Filter, Expand, Mail, Heart, Home, Info circle, Link, External link, Wrench, Trash, Upload/share, X (close), Chat, Download cloud, Bookmark, Pin/push

**Usage in this design system**: Lucide Icons (https://lucide.dev) is used as a near-identical substitute for Untitled UI Icons — same stroke weight, geometric style. **⚠️ Substitution flag**: If you have Untitled UI Icons files, replace the Lucide CDN reference with the actual icon font/sprite.

**Emoji**: Not used in UI copy or as icons. Bitrix Sales' iconography is exclusively SVG/icon-font based.

---

## File Index

```
bitrix-sales-design-system/
├── styles.css                         # Global CSS entry point (import this)
├── tokens/
│   ├── colors.css                     # Full color palette + semantic aliases
│   ├── typography.css                 # Type scale, font weights, @font-face
│   ├── spacing.css                    # Spacing scale + grid tokens
│   └── effects.css                    # Shadows, radii, transitions, z-index
├── assets/
│   ├── logo.svg                       # Bitrix Sales wordmark (dark)
│   ├── logo-white.svg                 # Bitrix Sales wordmark (white, for dark BGs)
│   ├── logo-icon.svg                  # BS icon in blue rounded square
│   └── gradient-bg.svg                # Abstract aurora gradient background
├── guidelines/
│   ├── colors-primary.card.html       # Primary blue scale specimen
│   ├── colors-secondary-warm.card.html # Warm orange scale
│   ├── colors-secondary-cool.card.html # Blue, Yellow, Red, Green scales
│   ├── colors-neutral.card.html       # Neutral + content + background
│   ├── typography-display.card.html   # H1–H5 + subtitle specimens
│   ├── typography-body.card.html      # Body 1–4 + label + caption
│   ├── spacing-tokens.card.html       # Spacing scale tokens
│   ├── spacing-in-use.card.html       # Spacing applied to components
│   ├── effects.card.html              # Shadows, radii, focus rings
│   └── brand.card.html                # Logo, gradients, brand marks
├── components/
│   ├── core/
│   │   ├── Button.jsx + .d.ts + .prompt.md
│   │   ├── Input.jsx + .d.ts + .prompt.md
│   │   ├── Badge.jsx + .d.ts + .prompt.md
│   │   ├── Avatar.jsx + .d.ts + .prompt.md
│   │   ├── Card.jsx + .d.ts + .prompt.md
│   │   └── forms.card.html            # All core components showcase
│   ├── navigation/
│   │   ├── Navbar.jsx + .d.ts + .prompt.md
│   │   ├── Sidebar.jsx + .d.ts + .prompt.md
│   │   └── navigation.card.html
│   └── feedback/
│       ├── Alert.jsx + .d.ts + .prompt.md
│       └── feedback.card.html
└── ui_kits/
    └── webapp/
        ├── README.md
        └── index.html                 # Interactive dashboard prototype
```

---

## Caveats

1. **Font files**: Manrope is loaded from Google Fonts CDN. If the product uses locally-hosted font files, replace the `@import` in `tokens/typography.css` with your `@font-face` declarations pointing to the actual `.woff2` files.

2. **Exact color values**: Colors are extracted from screenshot analysis. Some values may differ by a few points from the original Figma variables. If you have access to the Figma file at varti-studio.com, replace values in `tokens/colors.css` with the exact exported tokens.

3. **Icon library**: The "Untitled icons library" mentioned in the design system is a commercial product. Lucide Icons is used as a visual substitute (same 1.5px stroke, geometric style). Replace with actual Untitled UI Icons files if available.

4. **No Figma or codebase access**: This system was built entirely from screenshot analysis. Some nuanced spacing, exact shadow values, or component states may differ from production.
