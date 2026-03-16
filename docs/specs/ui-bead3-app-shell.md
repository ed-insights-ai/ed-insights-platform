# Bead 3: App Shell & 3-Level Navigation

## Overview
Restructure the navigation to the 3-level hierarchy defined in DESIGN.md: L1 Conference, L2 Team, L3 Player. Add the gender switch. Rebuild the sidebar to be context-aware. Add routes for conference/explore pages (stubs OK).

## Prerequisite
Bead 1 (design tokens) must be merged first.

## What Changes

### Route Structure
Add these new routes (pages can be stubs returning `<div>Coming soon</div>` for now):
```
/conference/gac              → new file: apps/web/src/app/conference/[abbr]/page.tsx
/explore/teams               → new file: apps/web/src/app/explore/teams/page.tsx
/explore/teams/[abbr]        → new file: apps/web/src/app/explore/teams/[abbr]/page.tsx
/explore/players             → new file: apps/web/src/app/explore/players/page.tsx
```

Keep all existing `/dashboard/*` routes intact.

### Gender Context
Create `apps/web/src/context/GenderContext.tsx`:
```typescript
"use client";

import { createContext, useContext, useState, ReactNode } from "react";

type Gender = "men" | "women";

interface GenderContextValue {
  gender: Gender;
  setGender: (g: Gender) => void;
}

const GenderContext = createContext<GenderContextValue>({
  gender: "men",
  setGender: () => {},
});

export function GenderProvider({ children }: { children: ReactNode }) {
  const [gender, setGender] = useState<Gender>("men");
  return (
    <GenderContext.Provider value={{ gender, setGender }}>
      {children}
    </GenderContext.Provider>
  );
}

export function useGender() {
  return useContext(GenderContext);
}
```

Wrap `apps/web/src/app/dashboard/layout.tsx` with `<GenderProvider>`.

### Gender Switch Component
Create `apps/web/src/components/GenderSwitch.tsx`:

Props: none (reads/writes from GenderContext)

UI: A pill-style toggle button group:
```
[ Men's ◆ ]  [ Women's ◆ ]
```
- Men's active: `bg-data-primary text-white` (teal) with a small teal dot indicator
- Women's active: `bg-purple-600 text-white` with a small purple dot indicator  
- Inactive: `bg-surface-muted text-slate-600`
- Size: compact, fits in sidebar or topbar
- On toggle: calls `setGender()`

### Sidebar Rebuild: DashboardSidebar.tsx
Replace the current flat nav with a 3-section context-aware sidebar.

Keep the collapsible behavior (collapsed/expanded toggle).

**Structure when expanded:**
```
┌────────────────────────────────┐
│ [GenderSwitch]                 │  ← top of sidebar, always visible
├────────────────────────────────┤
│ MY TEAM                        │  ← section label (stat-label class)
│  ◆ War Room     /dashboard     │  ← teal dot = data-primary when active
│  ◆ Schedule     /dashboard/... │
│  ◆ Roster       /dashboard/... │  
│  ◆ Analytics    /dashboard/... │
├────────────────────────────────┤
│ EXPLORE                        │  ← section label
│  ◆ Conference   /conference/gac│
│  ◆ Teams        /explore/teams │
│  ◆ Players      /explore/players│
├────────────────────────────────┤
│ ⚙ Settings     /dashboard/settings│
└────────────────────────────────┘
```

Active nav item style: `bg-surface-muted text-slate-900 font-semibold` with a `3px left border in data-primary teal` (use `border-l-4 border-data-primary`).

Inactive: `text-slate-600 hover:bg-surface-muted hover:text-slate-900`.

Use these Lucide icons:
- War Room: `LayoutDashboard`
- Schedule: `Calendar`
- Roster: `Users`
- Analytics: `BarChart3`
- Conference: `Trophy`
- Teams: `Building2`
- Players: `UserCircle`
- Settings: `Settings`

### Topbar: DashboardTopbar.tsx
Add a breadcrumb to the topbar showing current nav context. Format: `GAC › [Page Name]` for conference-level, or `GAC › Harding › War Room` for team-level.

For now: just show the current `pageTitle` prop with a simple breadcrumb prefix. The topbar already receives `pageTitle` — just render it as `GAC › {pageTitle}`.

Keep the user email display and any existing logout functionality.

### Update dashboard/layout.tsx
- Import and render `GenderProvider` wrapping the layout
- The sidebar and main area layout structure stays the same

### Update dashboard/page.tsx
- Change the page title from "Overview" to "War Room" (the DESIGN.md name for the main dashboard)
- No other logic changes

## Out of Scope
- No real data on stub pages
- No conference standings logic
- No API changes
- Don't build out the explore/conference pages — stubs only

## Validation
- `cd apps/web && npm run lint` — no errors
- `cd apps/web && npm run build` — no errors
- Sidebar shows 3 sections (My Team / Explore / Settings)
- Gender switch renders and toggles between teal and purple states
- `/conference/gac`, `/explore/teams`, `/explore/players` routes exist (stub pages)
- `/dashboard` still loads and shows War Room

## Commit
`feat(web): 3-level nav shell — context-aware sidebar, gender switch, explore route stubs`

## When done
```bash
openclaw system event --text "Done: Bead 3 app shell — 3-level sidebar, gender switch, explore stubs" --mode now
```
