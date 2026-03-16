# Bead 2: Core Component Library

## Overview
Build the reusable stat display components that every page will use. These are pure UI components with no API calls — they receive data as props. All use the Bead 1 design tokens.

## Prerequisite
Bead 1 (design tokens) must be merged first.

## New Files to Create
All in `apps/web/src/components/stats/`:

```
apps/web/src/components/stats/
├── ContextualMetricCard.tsx
├── FormBadgeStrip.tsx
├── DeltaBadge.tsx
├── InlineSparkline.tsx
└── index.ts          ← re-exports all
```

## Component Specifications

### 1. DeltaBadge.tsx
Props:
```typescript
interface DeltaBadgeProps {
  value: number;           // e.g. 0.4 or -1.2
  unit?: string;           // e.g. "%" or "" — appended after value
  baseline?: string;       // e.g. "vs Conference Avg" — shown as tooltip or secondary text
  showIcon?: boolean;      // default true — show ▲/▼/— icon
}
```

Behavior:
- value > 0: use `delta-positive` class, show ▲ icon
- value < 0: use `delta-negative` class, show ▼ icon  
- value === 0: use `delta-neutral` class, show — icon
- Format: always show sign (+0.4, -1.2, ±0)
- Use `tabular-nums` on the number

Example output: `[+0.4 ▲]` in emerald pill

### 2. ContextualMetricCard.tsx
The core stat card from DESIGN.md section 2.

Props:
```typescript
interface ContextualMetricCardProps {
  label: string;           // e.g. "GOALS / GAME" — will be uppercased
  value: string | number;  // e.g. 2.14 or "14.2%"
  delta?: number;          // e.g. 0.4 — passed to DeltaBadge
  deltaUnit?: string;      // e.g. "" or "%"
  baseline?: string;       // e.g. "vs Conference Avg"
  sparklineData?: number[]; // optional — renders InlineSparkline if provided
  className?: string;
}
```

Layout (matches DESIGN.md bento card spec):
```
┌──────────────────┐
│ LABEL            │  ← stat-label class
│                  │
│ value            │  ← stat-value class (tabular-nums)
│ [DeltaBadge]     │  ← if delta provided
│ baseline text    │  ← text-xs text-slate-400
│ [sparkline]      │  ← if sparklineData provided
└──────────────────┘
```

Use `bento-card` class on the outer div. Internal padding: `p-5`.

### 3. FormBadgeStrip.tsx
Win/Loss/Draw strip from DESIGN.md section 2.

Props:
```typescript
interface FormResult {
  result: "W" | "L" | "D";
  gameId?: number;         // if provided, badge is a link to /dashboard/games/[gameId]
}

interface FormBadgeStripProps {
  results: FormResult[];   // ordered oldest → newest; renders newest on right
  maxDisplay?: number;     // default 5
  size?: "sm" | "md";      // sm=w-6 h-6, md=w-7 h-7 (default md)
}
```

Badge colors:
- W: `bg-emerald-500 text-white`
- L: `bg-rose-500 text-white`
- D: `bg-amber-500 text-white`

Style: `rounded-md font-bold text-xs flex items-center justify-center`
Clickable if `gameId` is provided (wrap in `<Link href="/dashboard/games/{gameId}">`).
Strip is `flex gap-1`.

### 4. InlineSparkline.tsx
Tiny trend line for tables and cards.

Props:
```typescript
interface InlineSparklineProps {
  data: number[];          // array of values, left=oldest right=newest
  width?: number;          // default 40
  height?: number;         // default 16
  color?: string;          // default "data-primary" teal #0D9488
  className?: string;
}
```

Implementation: Use Recharts `<LineChart>` with `width/height` props, no axes, no tooltip, no dots on line (just the line). Minimal chart — purely visual trend indicator.

### 5. index.ts
Re-export everything:
```typescript
export { ContextualMetricCard } from "./ContextualMetricCard";
export { FormBadgeStrip } from "./FormBadgeStrip";
export { DeltaBadge } from "./DeltaBadge";
export { InlineSparkline } from "./InlineSparkline";
```

## Out of Scope
- No API calls in any component
- No new routes
- No changes to existing components
- No shadcn/ui chart integration yet (InlineSparkline uses bare Recharts)

## Validation
- `cd apps/web && npm run lint` — no TypeScript/lint errors
- `cd apps/web && npm run build` — clean build
- All 4 components exist in `apps/web/src/components/stats/`

## Commit
`feat(web): add core stats component library — ContextualMetricCard, FormBadgeStrip, DeltaBadge, InlineSparkline`

## When done
```bash
openclaw system event --text "Done: Bead 2 core components — ContextualMetricCard, FormBadgeStrip, DeltaBadge, InlineSparkline built" --mode now
```
