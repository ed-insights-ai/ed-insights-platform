# Bead 1: Design Tokens & Visual System

## Overview
Wire up the DESIGN.md color token system into Tailwind + CSS. Everything else (components, pages) builds on top of this. No new components — pure configuration.

## Files to Modify
- `apps/web/tailwind.config.ts`
- `apps/web/src/app/globals.css`

## Implementation

### 1. tailwind.config.ts — Add design tokens

Add these color tokens to the `theme.extend.colors` section (keep all existing colors):

```
// Data visualization tokens (from DESIGN.md)
"data-primary": "#0D9488",       // teal — our team, chart primary, active nav
"data-opponent": "#F97316",      // bright orange — opponent data series
"data-positive": "#10B981",      // emerald — over-performing, positive deltas, wins
"data-negative": "#F43F5E",      // rose — under-performing, negative deltas, losses
"data-neutral": "#F59E0B",       // amber — draws, neutral deltas, warnings

// Background tokens
"app-bg": "#F8FAFC",             // slate-50 — page background
"card-bg": "#FFFFFF",            // white — card surfaces
"surface-muted": "#F1F5F9",      // slate-100 — nested containers, sidebar active states

// Dark mode equivalents (add as nested object)
// "app-bg-dark": "#020617"      — slate-950
// "card-bg-dark": "#0F172A"     — slate-900
// "surface-muted-dark": "#1E293B" — slate-800

// Brand tokens (from DESIGN.md)
"brand-primary": "#0F172A",      // navy — logo, headers, primary text
"brand-accent": "#EA580C",       // deep orange — CTAs, homepage hero
```

Use nested objects for the data tokens so Tailwind generates utilities like `bg-data-primary`, `text-data-positive`, `border-data-negative`:

```typescript
colors: {
  // ... existing colors ...
  "data": {
    primary: "#0D9488",
    opponent: "#F97316",
    positive: "#10B981",
    negative: "#F43F5E",
    neutral: "#F59E0B",
  },
  "brand": {
    primary: "#0F172A",
    accent: "#EA580C",
  },
  "app-bg": "#F8FAFC",
  "card-bg": "#FFFFFF",
  "surface-muted": "#F1F5F9",
}
```

### 2. globals.css — Add CSS custom properties + typography utilities

Add to `:root`:
```css
/* Design token CSS vars */
--data-primary: #0D9488;
--data-opponent: #F97316;
--data-positive: #10B981;
--data-negative: #F43F5E;
--data-neutral: #F59E0B;
--brand-primary: #0F172A;
--brand-accent: #EA580C;
--app-bg: #F8FAFC;
--card-bg: #FFFFFF;
--surface-muted: #F1F5F9;
```

Add dark mode CSS vars under `@media (prefers-color-scheme: dark)`:
```css
--app-bg: #020617;
--card-bg: #0F172A;
--surface-muted: #1E293B;
```

Add Tailwind utility layer for the design system's typography rules:
```css
@layer components {
  /* Bento card base — use on every data card */
  .bento-card {
    @apply rounded-xl border border-slate-200 bg-card-bg shadow-sm;
  }
  .bento-card-dark {
    @apply dark:border-slate-700 dark:bg-card-bg;
  }

  /* Section label — uppercase, tracked, muted */
  .stat-label {
    @apply text-xs font-bold uppercase tracking-wider text-slate-500;
  }

  /* KPI value — large bold tabular */
  .stat-value {
    @apply text-2xl font-extrabold tabular-nums text-slate-900;
  }

  /* Table header style */
  .table-header {
    @apply text-xs font-bold uppercase tracking-wider text-slate-500;
  }

  /* Delta badge variants */
  .delta-positive {
    @apply inline-flex items-center gap-0.5 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700;
  }
  .delta-negative {
    @apply inline-flex items-center gap-0.5 rounded-full bg-rose-50 px-2 py-0.5 text-xs font-semibold text-rose-700;
  }
  .delta-neutral {
    @apply inline-flex items-center gap-0.5 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-600;
  }
}
```

### 3. Update page background

In the `body` base style or in the dashboard layout, switch the page background from `bg-gray-50` to `bg-app-bg`. Update `apps/web/src/app/dashboard/layout.tsx` main element: change `bg-gray-50` → `bg-app-bg`.

## Out of Scope
- No new components
- No route changes
- No changes to existing component logic

## Validation
- `cd apps/web && npm run lint` — no errors
- `cd apps/web && npm run build` — no errors
- Visually: the design tokens exist in Tailwind output (use `grep` to verify utility classes)

## Commit
`feat(web): add design token system — data colors, bento card, typography utilities`

## When done
```bash
openclaw system event --text "Done: Bead 1 design tokens — data-* colors, bento-card, stat-label utilities live" --mode now
```
