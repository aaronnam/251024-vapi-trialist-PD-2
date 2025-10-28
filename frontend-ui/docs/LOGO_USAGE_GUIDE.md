# PandaDoc Voice Agent - Logo Usage Guide

## Available Logo Assets

You have three logo variants in `frontend-ui/logos/`:

### 1. Full Horizontal Logo (Primary)
**File**: `Emerald_black_pd_brandmark.png`

**Description**: Complete PandaDoc logo with emerald green "pd" symbol and black "PandaDoc" wordmark with ® symbol.

**Best For**:
- Main header/navigation logo
- Landing pages
- Marketing materials
- Desktop applications
- Anywhere brand recognition is primary goal

**Usage Specs**:
- **Minimum Width**: 120px (ensures readability)
- **Recommended Width**: 180-200px for desktop, 140-160px for mobile
- **Background**: Light backgrounds (white, light gray, Sand-10)
- **Clear Space**: Minimum padding of 16px on all sides

---

### 2. Symbol Only (Square Icon)
**File**: `Emerald_white_pd_symbol_brandmark.png`

**Description**: White "pd" symbol on emerald green square background with ® symbol.

**Best For**:
- Favicon (browser tab icon)
- Mobile app icon
- Small UI elements (< 40px)
- Avatar/profile images
- Loading states
- Social media profile pictures

**Usage Specs**:
- **Sizes**: 16x16, 32x32, 64x64, 512x512 (generate these from source)
- **Format**: PNG with transparency for overlays
- **Background**: Self-contained (emerald background included)
- **Minimum Size**: 24px (for UI elements)

---

### 3. Panda Mascot (Character Icon)
**File**: `panda-logo-2.png`

**Description**: Geometric panda face illustration - playful, friendly mascot design.

**Best For**:
- Empty states ("No conversations yet" screens)
- Loading animations (friendly waiting experience)
- Error pages (404, 500) with personality
- Onboarding illustrations
- Tutorial/help sections
- Internal tools (less formal contexts)

**NOT Recommended For**:
- Primary branding
- Official marketing materials
- External-facing professional contexts
- Main navigation logo

**Usage Specs**:
- **Size**: 64px-128px for illustrations
- **Context**: Casual, friendly moments in the UX
- **Tone**: Adds personality without replacing official branding

---

## Implementation Recommendations

### For Voice Agent Frontend UI

#### Header/Navigation (Desktop)
```tsx
// Use full horizontal logo
<img
  src="/logos/Emerald_black_pd_brandmark.png"
  alt="PandaDoc"
  width={180}
  height="auto"
  className="header-logo"
/>
```

**CSS**:
```css
.header-logo {
  width: 180px;
  height: auto;
  padding: 16px;
}
```

#### Header/Navigation (Mobile)
```tsx
// Use symbol only on mobile for space efficiency
<img
  src="/logos/Emerald_white_pd_symbol_brandmark.png"
  alt="PandaDoc"
  width={40}
  height={40}
  className="header-logo-mobile"
/>
```

**CSS**:
```css
@media (max-width: 768px) {
  .header-logo {
    display: none;
  }
  .header-logo-mobile {
    display: block;
    width: 40px;
    height: 40px;
  }
}
```

#### Favicon
```html
<!-- In public/index.html or app/layout.tsx -->
<link rel="icon" type="image/png" sizes="32x32" href="/logos/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/logos/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/logos/apple-touch-icon.png">
```

**Note**: You'll need to generate these sizes from `Emerald_white_pd_symbol_brandmark.png`.

#### Loading State
```tsx
// Option 1: Professional (symbol)
<div className="loading-state">
  <img
    src="/logos/Emerald_white_pd_symbol_brandmark.png"
    width={64}
    height={64}
    className="loading-spinner"
  />
  <p>Connecting to your assistant...</p>
</div>

// Option 2: Friendly (panda mascot)
<div className="loading-state">
  <img
    src="/logos/panda-logo-2.png"
    width={96}
    height={96}
    className="loading-mascot"
  />
  <p>Waking up your PandaDoc assistant...</p>
</div>
```

**CSS**:
```css
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loading-spinner {
  animation: spin 2s linear infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.loading-mascot {
  animation: bounce 1.5s ease-in-out infinite;
}
```

#### Error/Empty States
```tsx
// Use panda mascot for friendly, approachable errors
<div className="empty-state">
  <img
    src="/logos/panda-logo-2.png"
    width={128}
    height={128}
    alt="PandaDoc Assistant"
  />
  <h2>No conversations yet</h2>
  <p>Start your first voice session to get help with your trial!</p>
  <button>Start Call</button>
</div>
```

---

## Logo Preparation Tasks

### Generate Additional Sizes

You'll want to create these from `Emerald_white_pd_symbol_brandmark.png`:

```bash
# Using ImageMagick or similar tool
convert Emerald_white_pd_symbol_brandmark.png -resize 16x16 favicon-16x16.png
convert Emerald_white_pd_symbol_brandmark.png -resize 32x32 favicon-32x32.png
convert Emerald_white_pd_symbol_brandmark.png -resize 180x180 apple-touch-icon.png
convert Emerald_white_pd_symbol_brandmark.png -resize 512x512 icon-512x512.png
```

Or use an online tool like [favicon.io](https://favicon.io) or [realfavicongenerator.net](https://realfavicongenerator.net/).

### Optimize File Sizes

The PNG files might be large. Optimize them:

```bash
# Using ImageOptim, TinyPNG, or similar
# Target: < 50KB for full logo, < 20KB for symbol
```

### Create SVG Versions (Optional but Recommended)

SVG versions scale perfectly and are smaller. If you have the source files:
- **Full logo SVG**: For crisp rendering at any size
- **Symbol SVG**: For icon use cases

Benefits of SVG:
- Perfect scaling (no pixelation)
- Smaller file size
- Can be colored dynamically with CSS

---

## App Config Integration

Update `app-config.ts`:

```typescript
export const appConfig: AppConfig = {
  companyName: "PandaDoc",

  // Logo configuration
  logo: "/logos/Emerald_black_pd_brandmark.png",      // Light mode
  logoDark: "/logos/Emerald_white_pd_symbol_brandmark.png",  // Dark mode (if needed)

  // For smaller UI elements
  logoSmall: "/logos/Emerald_white_pd_symbol_brandmark.png",

  // Optional: Mascot for friendly moments
  mascot: "/logos/panda-logo-2.png",

  agents: {
    agent: {
      displayName: "PandaDoc Assistant",
      description: "I'm here to help you succeed with your PandaDoc trial",

      // Avatar options:
      avatarImage: "/logos/Emerald_white_pd_symbol_brandmark.png",  // Professional
      // avatarImage: "/logos/panda-logo-2.png",  // Friendly alternative

      avatarBgColor: "#24856F",  // Emerald primary
      avatarTextColor: "#FFFFFF",
    }
  },
};
```

---

## Usage Decision Matrix

| Use Case | Recommended Logo | Rationale |
|----------|------------------|-----------|
| **Main Header** | Full horizontal logo | Maximum brand recognition |
| **Mobile Header** | Symbol only | Space efficiency |
| **Browser Tab** | Symbol only | Standard favicon size |
| **App Icon** | Symbol only | Works at small sizes |
| **Loading State** | Symbol (professional) or Panda (friendly) | Depends on tone |
| **404 Error** | Panda mascot | Softens negative experience |
| **Empty State** | Panda mascot | Welcoming, approachable |
| **Success Modal** | Symbol only | Clean, professional |
| **Agent Avatar** | Symbol only | Consistent branding |
| **Email Footer** | Full horizontal logo | Brand reinforcement |

---

## Brand Consistency Guidelines

### DO:
- ✅ Use full horizontal logo when space allows (desktop header)
- ✅ Use symbol-only version for small spaces (< 60px)
- ✅ Use panda mascot for friendly, casual moments
- ✅ Maintain clear space around all logos
- ✅ Use logos on approved background colors (white, light gray, emerald)
- ✅ Keep logos at original aspect ratio

### DON'T:
- ❌ Stretch or squash logos
- ❌ Change logo colors (use provided versions)
- ❌ Add effects (shadows, gradients, outlines) unless explicitly approved
- ❌ Use low-resolution logos (ensure crisp rendering)
- ❌ Place logos on busy backgrounds
- ❌ Use panda mascot as primary branding

---

## Accessibility Considerations

### Alt Text
```tsx
// Descriptive for screen readers
<img src="/logos/Emerald_black_pd_brandmark.png" alt="PandaDoc logo" />

// Decorative (part of navigation with text)
<img src="/logos/Emerald_white_pd_symbol_brandmark.png" alt="" aria-hidden="true" />

// Functional (clickable link)
<a href="/">
  <img src="/logos/Emerald_black_pd_brandmark.png" alt="PandaDoc - Go to homepage" />
</a>
```

### Contrast
All logos meet WCAG AA standards:
- Full logo on white: ✅ High contrast
- Symbol on emerald background: ✅ Self-contained contrast
- Panda mascot on white: ✅ High contrast

---

## Quick Start Checklist

- [ ] Copy all logos to `pandadoc-voice-ui/public/logos/`
- [ ] Generate favicon sizes (16x16, 32x32, 180x180, 512x512)
- [ ] Update `app-config.ts` with logo paths
- [ ] Add favicon links to `<head>` in layout
- [ ] Test logo rendering on light/dark backgrounds
- [ ] Verify mobile responsiveness (switch to symbol on small screens)
- [ ] Optimize PNG file sizes (< 50KB)
- [ ] Add appropriate alt text for accessibility

---

## Summary Recommendations

**Primary Usage**:
- **Desktop Header**: Full horizontal logo (`Emerald_black_pd_brandmark.png`)
- **Mobile Header**: Symbol only (`Emerald_white_pd_symbol_brandmark.png`)
- **Favicon**: Symbol only (generate from `Emerald_white_pd_symbol_brandmark.png`)
- **Agent Avatar**: Symbol only
- **Friendly Moments**: Panda mascot (`panda-logo-2.png`)

**This approach provides**:
- Professional branding where it matters
- Space efficiency on mobile
- Personality in casual interactions
- Consistent brand identity throughout the app

The voice agent frontend will feel both professional and approachable, perfectly aligned with PandaDoc's brand while creating a welcoming user experience.
