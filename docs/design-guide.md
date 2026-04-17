# Design Guide: Brain Training App

**Version:** 1.0
**Date:** 2026-04-16
**Mirrors:** spec-v0.8 §12

---

## Changelog

| Version | Date | Summary |
|---|---|---|
| 1.0 | 2026-04-16 | Extracted from implemented codebase (spec-v0.8) |

---

## 1. Color Palette

Defined in `frontend/src/styles/variables.css` as CSS custom properties.

| Token | Value | Usage |
|---|---|---|
| `--color-primary` | `#4A90C4` | Primary actions, links, active states |
| `--color-primary-hover` | `#3a7ab0` | Hover state of primary |
| `--color-secondary` | `#3D9E72` | Success indicators, domain: Executive Function |
| `--color-accent` | `#F4D35E` | Highlights, domain: Episodic Memory, warnings |
| `--color-danger` | `#D95F5F` | Errors, domain: Attention/Inhibitory Control |
| `--color-surface` | `#FFFFFF` | Card and panel backgrounds |
| `--color-background` | `#F5F7FA` | Page background |
| `--color-text` | `#1A202C` | Body text (contrast ≥7:1 on `--color-background`) |
| `--color-text-muted` | `#718096` | Secondary text, labels, metadata |
| `--color-border` | `#E2E8F0` | Borders, dividers |
| `--color-on-primary` | `#FFFFFF` | Text on primary background |

### Domain color assignments

| Domain | Token | Hex |
|---|---|---|
| Processing Speed | `--color-primary` | `#4A90C4` |
| Working Memory | `--color-accent` | `#F4D35E` |
| Attention & Inhibitory Control | `--color-danger` | `#D95F5F` |
| Executive Function | `--color-secondary` | `#3D9E72` |
| Episodic Memory | `#8B6EBD` (purple, ad hoc) | — |

---

## 2. Typography

Font stack: `system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`

| Token | Size | Weight | Usage |
|---|---|---|---|
| `--text-display` | 2rem | `--weight-bold` | Page titles (Dashboard heading) |
| `--text-heading` | 1.5rem | `--weight-bold` | Section headings, card titles |
| `--text-body` | 1rem | `--weight-regular` | Body text |
| `--text-body-sm` | 0.875rem | `--weight-regular` | Secondary text, labels |
| `--text-caption` | 0.75rem | `--weight-regular` | Metadata, timestamps |

| Token | Value |
|---|---|
| `--weight-regular` | 400 |
| `--weight-medium` | 500 |
| `--weight-bold` | 700 |
| `--tracking-wide` | 0.1em |

---

## 3. Spacing System

All layout spacing uses these tokens. Never use raw pixel values in component specs.

| Token | Value |
|---|---|
| `--space-1` | 0.25rem |
| `--space-2` | 0.5rem |
| `--space-3` | 0.75rem |
| `--space-4` | 1rem |
| `--space-5` | 1.25rem |
| `--space-6` | 1.5rem |
| `--space-8` | 2rem |
| `--space-10` | 2.5rem |
| `--space-12` | 3rem |

---

## 4. Breakpoints

| Token | Value |
|---|---|
| `--bp-tablet` | 768px |
| `--bp-desktop` | 1024px |

**Default styles are mobile.** Tablet and desktop overrides use `@media (min-width: 768px)` and `@media (min-width: 1024px)`.

---

## 5. Border Radius

| Token | Value |
|---|---|
| `--radius-sm` | 4px |
| `--radius-md` | 8px |
| `--radius-lg` | 12px |
| `--radius-full` | 9999px |

---

## 6. Component Library

### Button

Defined in `frontend/src/components/ui/Button.jsx`.

| Variant | Background | Text | Border |
|---|---|---|---|
| `primary` | `--color-primary` | `--color-on-primary` | none |
| `secondary` | transparent | `--color-primary` | `1px solid --color-primary` |
| `ghost` | transparent | `--color-text` | none |
| `danger` | `--color-danger` | `--color-on-primary` | none |

States:
- `hover`: brightness 90%
- `focus`: `2px solid --color-primary`, `outline-offset: 2px`
- `disabled`: 50% opacity, `cursor: not-allowed`

Sizes: `sm` (`--space-2 --space-3`), `md` (`--space-3 --space-4`, default), `lg` (`--space-4 --space-6`)

Minimum touch target: 44×44px on mobile.

### Card

Defined in `frontend/src/components/ui/Card.jsx`.

- Background: `--color-surface`
- Border-radius: `--radius-lg`
- Padding: `--space-6`
- Box-shadow: `0 1px 3px rgba(0,0,0,0.08)`

### ProgressBar

Defined in `frontend/src/components/ui/ProgressBar.jsx`.

- Track: `--color-border`, height `8px`, `--radius-full`
- Fill: `--color-primary` (default), other domain colors for domain-specific bars
- Animated on mount: `transition: width 300ms ease`

### FeedbackWidget

- Floating button, fixed position: `bottom: --space-6`, `right: --space-6`
- z-index: 100 (above content, below modals)
- On mobile: hides when `BottomNav` is visible (offset by `72px` bottom padding on `.dashboard-layout`)

### Sidebar (desktop)

- Width: `240px`
- Background: `--color-surface`
- `display: none` on mobile (< 768px)
- Uses `.dashboard-sidebar` class

### BottomNav (mobile)

- Fixed bottom, full width
- Height: `56px`
- Background: `--color-surface`
- Border-top: `1px solid --color-border`
- `display: none` on desktop (≥ 768px)
- Uses `.bottom-nav` class

---

## 7. Responsive Layout

### Dashboard layout (`.dashboard-layout`)

| Breakpoint | Layout |
|---|---|
| Mobile (< 768px) | `display: block`, sidebar hidden, BottomNav shown, `padding-bottom: 72px` |
| Desktop (≥ 768px) | `display: flex`, sidebar visible, BottomNav hidden |

### Grid columns

| Class | Mobile | Desktop |
|---|---|---|
| `.dashboard-grid-cards` | `1fr` | `repeat(3, 1fr)` |
| `.dashboard-grid-domains` | `1fr` | `repeat(2, 1fr)` |
| `.dashboard-practice-grid` | `repeat(2, 1fr)` | `repeat(3, 1fr)` |

---

## 8. Motion

- Default transition: `150ms ease`
- Respect `prefers-reduced-motion: reduce` — disable all non-essential transitions

---

## 9. Accessibility

- **Contrast:** Body text ≥7:1 on `--color-background`. UI components ≥3:1.
- **Focus:** All interactive elements have `2px solid --color-primary` focus outline
- **Touch targets:** Minimum 44×44px on mobile
- **Screen readers:** Icon-only buttons have `aria-label`
- **Forms:** All inputs have associated `<label>` elements or `aria-label`
