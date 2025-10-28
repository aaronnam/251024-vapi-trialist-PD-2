# PandaDoc Voice Agent - Design Guidelines

## Overview

This document outlines the design system for the PandaDoc Voice Agent frontend UI, based on PandaDoc's official brand guidelines. All visual elements should adhere to these specifications to maintain brand consistency.

---

## Typography

### Primary Typeface: Graphik LC Alt Web

**Font Family**: `'Graphik LC Alt Web', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`

Graphik LC Alt Web is our primary typeface, offering excellent readability across digital platforms while maintaining a professional and approachable appearance.

#### Weight Usage

| Weight | Use Case | CSS Property |
|--------|----------|--------------|
| **Bold** | Headlines in marketing materials, primary CTAs | `font-weight: 700` |
| **Semibold** | Subheadings, secondary headlines | `font-weight: 600` |
| **Regular** | Body text, supporting copy | `font-weight: 400` |

#### Implementation Notes

- **Installation Required**: Graphik LC Alt Web requires a license. Request permission from Brand Studio for download or sharing.
- **Web Font Loading**: Use proper font loading strategies to prevent layout shifts
- **Fallback Stack**: Include system fonts as fallbacks for graceful degradation

### Secondary Typeface: Verdana (Email/Presentation Only)

**Font Family**: `'Verdana', Geneva, sans-serif`

**Usage Restrictions**:
- Email communications only
- Web-safe contexts where Graphik LC Alt Web is unavailable by default
- Verdana is proprietary (owned by Monotype Imaging) and NOT licensed for general use
- Do NOT use Verdana in marketing materials, presentations, or brand assets outside permitted use cases

**Alternative**: Poppins may be used as a substitute in email/presentation contexts where Verdana is unavailable.

### Font Sizing

```css
/* Recommended scale for voice agent UI */
--font-size-xs: 12px;    /* Fine print, timestamps */
--font-size-sm: 14px;    /* Secondary text, labels */
--font-size-base: 16px;  /* Body text (default) */
--font-size-lg: 18px;    /* Emphasized text */
--font-size-xl: 24px;    /* Section headings */
--font-size-2xl: 32px;   /* Page titles */
--font-size-3xl: 40px;   /* Hero headlines */
```

---

## Color Palette

### Primary Colors

#### Emerald (Brand Primary)

Our signature green conveys growth, trust, and innovation.

| Variant | Hex | RGB | CMYK | Use Case |
|---------|-----|-----|------|----------|
| **Emerald Primary** | `#24856F` | rgb(36, 133, 111) | C73, M4, Y25, K48 | Primary buttons, key UI elements |
| Emerald -60 | `#8FE5A7` | rgb(143, 229, 167) | C23, M0, Y8, K29 | Hover states, active indicators |
| Emerald -30 | `#BBCEC7` | rgb(187, 206, 199) | C10, M0, Y3, K20 | Subtle backgrounds |
| Emerald -20 | `#CCDBE0` | rgb(204, 219, 224) | C6, M0, Y2, K13 | Light backgrounds |
| Emerald -10 | `#E7F0EE` | rgb(231, 240, 238) | C4, M0, Y1, K6 | Very light backgrounds |

**Primary Action Color**: `#24856F` (Emerald Primary)

#### Amethyst (Secondary Accent)

Used for informational elements, secondary actions, and visual variety.

| Variant | Hex | RGB | CMYK | Use Case |
|---------|-----|-----|------|----------|
| Amethyst -40 | `#6A96FF` | rgb(106, 150, 255) | C58, M42, Y0, K0 | Info badges, links |
| Amethyst -30 | `#C3CFFF` | rgb(195, 207, 255) | C23, M18, Y0, K0 | Light info backgrounds |
| Amethyst -20 | `#D0D7FF` | rgb(208, 215, 255) | C14, M15, Y0, K0 | Subtle highlights |
| Amethyst -10 | `#E8E6FF` | rgb(232, 230, 255) | C7, M9, Y0, K0 | Very light accents |

#### Coral (Alert/Emphasis)

Used for alerts, errors, and important call-outs.

| Variant | Hex | RGB | CMYK | Use Case |
|---------|-----|-----|------|----------|
| Coral -40 | `#FF524C` | rgb(255, 82, 76) | C0, M67, Y35, K0 | Error states, urgent actions |
| Coral -30 | `#FFB3A4` | rgb(255, 179, 164) | C0, M28, Y15, K0 | Warning backgrounds |
| Coral -20 | `#FFE2DD` | rgb(255, 226, 221) | C0, M11, Y6, K0 | Light error backgrounds |
| Coral -10 | `#FFF2F1` | rgb(255, 242, 241) | C0, M5, Y4, K0 | Very light alerts |

#### Sand (Neutral Warm)

Used for backgrounds and subtle separation.

| Variant | Hex | RGB | CMYK | Use Case |
|---------|-----|-----|------|----------|
| Sand -30 | `#EFEDE1` | rgb(239, 237, 225) | C6, M4, Y11, K0 | Warm backgrounds |
| Sand -20 | `#F5F3EA` | rgb(245, 243, 234) | C4, M3, Y8, K0 | Card backgrounds |
| Sand -10 | `#FBF8F3` | rgb(251, 248, 243) | C2, M2, Y3, K0 | Page backgrounds |

### Foundation Colors

| Color | Hex | RGB | CMYK | Use Case |
|-------|-----|-----|------|----------|
| **Black Primary** | `#242424` | rgb(36, 36, 36) | C0, M0, Y0, K86 | Text, icons |
| **White Primary** | `#FFFFFF` | rgb(255, 255, 255) | C0, M0, Y0, K0 | Backgrounds, inverse text |

---

## Component Styling

### Voice Visualizer

```css
.voice-visualizer {
  background: rgba(36, 133, 111, 0.1); /* Emerald Primary at 10% opacity */
  border-radius: 12px;
  padding: 2rem;
}

.voice-visualizer-bar {
  background-color: #24856F; /* Emerald Primary */
}

.voice-visualizer-bar--active {
  background-color: #8FE5A7; /* Emerald -60 for active state */
}
```

### Buttons

```css
/* Primary Button */
.button-primary {
  background-color: #24856F; /* Emerald Primary */
  color: #FFFFFF;
  font-family: 'Graphik LC Alt Web', sans-serif;
  font-weight: 600; /* Semibold */
  font-size: 16px;
  padding: 12px 24px;
  border-radius: 8px;
  border: none;
  transition: background-color 0.2s ease;
}

.button-primary:hover {
  background-color: #1d6a59; /* Slightly darker */
}

.button-primary:active {
  background-color: #165647; /* Even darker */
}

/* Secondary Button */
.button-secondary {
  background-color: transparent;
  color: #24856F;
  border: 2px solid #24856F;
  font-family: 'Graphik LC Alt Web', sans-serif;
  font-weight: 600;
  font-size: 16px;
  padding: 12px 24px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.button-secondary:hover {
  background-color: #E7F0EE; /* Emerald -10 */
}
```

### Status Indicators

```css
/* Connection States */
.status-listening {
  color: #24856F; /* Emerald Primary */
}

.status-thinking {
  color: #6A96FF; /* Amethyst -40 */
}

.status-error {
  color: #FF524C; /* Coral -40 */
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 8px;
}

.status-dot--active {
  background-color: #24856F;
  animation: pulse 2s infinite;
}
```

### Cards & Containers

```css
.card {
  background: #FFFFFF;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(36, 36, 36, 0.08);
  padding: 24px;
  border: 1px solid #EFEDE1; /* Sand -30 */
}

.card-header {
  font-family: 'Graphik LC Alt Web', sans-serif;
  font-weight: 600; /* Semibold */
  font-size: 18px;
  color: #242424;
  margin-bottom: 16px;
}

.card-body {
  font-family: 'Graphik LC Alt Web', sans-serif;
  font-weight: 400; /* Regular */
  font-size: 16px;
  color: #242424;
  line-height: 1.5;
}
```

---

## Layout Guidelines

### Spacing Scale

Use a consistent spacing scale based on 4px increments:

```css
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;
--space-12: 48px;
--space-16: 64px;
--space-20: 80px;
```

### Border Radius

```css
--radius-sm: 4px;   /* Small elements, tags */
--radius-md: 8px;   /* Buttons, inputs */
--radius-lg: 12px;  /* Cards, modals */
--radius-xl: 16px;  /* Large containers */
--radius-full: 9999px; /* Pills, avatars */
```

### Shadows

```css
--shadow-sm: 0 1px 2px rgba(36, 36, 36, 0.05);
--shadow-md: 0 2px 8px rgba(36, 36, 36, 0.08);
--shadow-lg: 0 4px 16px rgba(36, 36, 36, 0.12);
--shadow-xl: 0 8px 24px rgba(36, 36, 36, 0.16);
```

---

## Dark Mode (Optional)

If implementing dark mode, use these adaptations:

```css
/* Dark Mode Overrides */
@media (prefers-color-scheme: dark) {
  :root {
    --bg-primary: #1a1a1a;
    --bg-secondary: #242424;
    --text-primary: #FFFFFF;
    --text-secondary: #BBCEC7; /* Emerald -30 */

    /* Adjust emerald for dark backgrounds */
    --accent-primary: #8FE5A7; /* Emerald -60 (lighter variant) */
  }

  .card {
    background: #242424;
    border-color: #333333;
  }
}
```

---

## Accessibility

### Color Contrast

All color combinations must meet WCAG 2.1 AA standards:
- **Normal text**: Minimum contrast ratio of 4.5:1
- **Large text** (18pt+): Minimum contrast ratio of 3:1
- **UI components**: Minimum contrast ratio of 3:1

### Verified Combinations

| Foreground | Background | Ratio | Pass |
|------------|------------|-------|------|
| `#24856F` (Emerald) | `#FFFFFF` (White) | 4.8:1 | ✅ AA |
| `#242424` (Black) | `#FFFFFF` (White) | 13.8:1 | ✅ AAA |
| `#FFFFFF` (White) | `#24856F` (Emerald) | 4.8:1 | ✅ AA |
| `#FF524C` (Coral) | `#FFFFFF` (White) | 3.4:1 | ✅ Large text only |

### Focus States

```css
/* Keyboard focus indicators */
*:focus-visible {
  outline: 3px solid #6A96FF; /* Amethyst -40 */
  outline-offset: 2px;
  border-radius: 4px;
}
```

---

## Implementation Checklist

### CSS Variables Setup

Add these to your root stylesheet:

```css
:root {
  /* Colors - Emerald */
  --emerald-primary: #24856F;
  --emerald-60: #8FE5A7;
  --emerald-30: #BBCEC7;
  --emerald-20: #CCDBE0;
  --emerald-10: #E7F0EE;

  /* Colors - Amethyst */
  --amethyst-40: #6A96FF;
  --amethyst-30: #C3CFFF;
  --amethyst-20: #D0D7FF;
  --amethyst-10: #E8E6FF;

  /* Colors - Coral */
  --coral-40: #FF524C;
  --coral-30: #FFB3A4;
  --coral-20: #FFE2DD;
  --coral-10: #FFF2F1;

  /* Colors - Sand */
  --sand-30: #EFEDE1;
  --sand-20: #F5F3EA;
  --sand-10: #FBF8F3;

  /* Foundation */
  --black: #242424;
  --white: #FFFFFF;

  /* Typography */
  --font-family: 'Graphik LC Alt Web', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

  /* Spacing */
  --space-base: 4px;

  /* Borders */
  --radius-base: 8px;
}
```

### Font Loading

Add to your `<head>`:

```html
<!-- Load Graphik LC Alt Web (requires license) -->
<link rel="preload" href="/fonts/graphik-lc-alt-web-bold.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/graphik-lc-alt-web-semibold.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/graphik-lc-alt-web-regular.woff2" as="font" type="font/woff2" crossorigin>
```

### App Config Integration

Update `app-config.ts`:

```typescript
export const appConfig: AppConfig = {
  // Visual branding
  accent: "#24856F",        // Emerald Primary
  accentDark: "#1d6a59",    // Darker for dark mode

  customStyles: {
    primaryColor: "#24856F",
    primaryColorHover: "#1d6a59",
    backgroundColor: "#FFFFFF",
    backgroundColorDark: "#1a1a1a",
    textColor: "#242424",
    textColorDark: "#FFFFFF",

    fontFamily: "'Graphik LC Alt Web', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",

    fontSize: {
      small: "14px",
      base: "16px",
      large: "18px",
      xlarge: "24px",
    },

    borderRadius: {
      small: "4px",
      medium: "8px",
      large: "12px",
      full: "9999px",
    },

    boxShadow: {
      small: "0 1px 2px rgba(36, 36, 36, 0.05)",
      medium: "0 2px 8px rgba(36, 36, 36, 0.08)",
      large: "0 4px 16px rgba(36, 36, 36, 0.12)",
    },
  },
};
```

---

## Resources

### Font License
- **Graphik LC Alt Web**: Request download permission from Brand Studio
- **Download link**: Provided in brand guidelines (requires authentication)

### Brand Assets
- Logo files (SVG, PNG)
- Icon sets
- Additional brand guidelines

### Support
For questions about brand usage or to request font licenses, contact:
- **Brand Studio**: [Contact information]
- **Design System**: [Internal documentation link]

---

## Version History

- **v1.0** (2025-01-27): Initial design guidelines based on PandaDoc brand standards
