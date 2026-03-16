# EDInsights.AI — UI Design Document

> **Status:** Design complete, data ingestion in progress. Ready to build Phase 1 after GAC full scrape completes.
>
> **Live mockups:** `docs/mockups/` — open any `.html` in a browser to review

---

## Core Design Philosophy

**Context beats raw data.** Every number on every page carries context: delta vs conference average, rank, form trend. "2.14 goals/game" is useless. "2.14 G/G · +0.4 vs GAC avg · 3rd in conference ↑" is actionable.

---

## Critical Design Constraints

### Gender is Global — Never Per-Page
- Men's Soccer (GAC) = **16 teams** (12 full members + 4 affiliates: FHSU, Newman, NSU, Rogers State — men's only, joined GAC 2019)
- Women's Soccer (GAC) = **12 teams** (full members only, no affiliates)
- Gender toggle lives in the **header only**, affects every page simultaneously
- **Teal bar** = Men's mode. **Purple bar** = Women's mode. Always visible below header.
- Never mix men's and women's data on the same view

---

## Navigation Architecture — 3-Level Hierarchy

```
L1: Conference Level  (/conference/gac)
    ├── Overview         — standings, KPIs, goal leaders, goals/game chart
    ├── All Players      — cross-school leaderboard
    └── All Teams        — browse/filter all schools

        ↓ click any team row

L2: Team Level  (/team/[abbr])
    ├── War Room         — season dashboard (DEFAULT)
    ├── Schedule         — results + upcoming
    ├── Roster & Stats   — sortable player table
    ├── Analytics        — trends, splits, multi-season
    └── Game Detail      — per-game deep dive (/team/[abbr]/games/[id])

        ↓ click any player name

L3: Player Level  (/player/[id])
    └── Profile          — Trading Card (career stats, radar chart, game log)
```

### Persona Entry Points
- **Coach / Staff** → lands on Team War Room (affiliated school, no config needed)
- **Scout / Analyst** → lands on Conference Overview (browse all teams)
- **Athlete / Fan** → direct link to Player Profile

### Sidebar Behavior
- **At L1 (conference):** GAC identity card + conference nav + team quick-pick list
- **At L2 (team):** `← Back to GAC` + team identity card (name, record, conf position) + team nav + other teams quick-jump
- **At L3 (player):** `← Back to Roster` link
- Breadcrumb in header always shows: `GAC › Harding › War Room`

---

## Color System

| Token | Hex | Usage |
|-------|-----|-------|
| `brand-primary` | `#0F172A` | Header, logo, body text |
| `brand-accent` | `#EA580C` | CTAs, conference level accent |
| `data-primary` | `#0D9488` | MY team data, nav active, Men's mode bar |
| `data-opponent` | `#F97316` | Opponent data. ALWAYS. No exceptions. |
| `data-positive` | `#10B981` | Above avg · wins · improving |
| `data-negative` | `#F43F5E` | Below avg · losses · declining |
| `data-neutral` | `#F59E0B` | Draws · warnings |
| `women-accent` | `#7C3AED` | Women's mode indicator only |

**Rule:** Teal is always "us/my team". Orange is always "opponent/other team". Green means good, red means bad. Never deviate.

**Typography:** All numeric data uses `font-variant-numeric: tabular-nums`. Inter font throughout.

---

## Page Templates

### Template A — Conference Overview (`/conference/gac`)
**Primary question:** *"Where does every team stand and who are the top performers?"*

**Layout:**
- Hero banner: season state (IN-SEASON vs POST-SEASON), top 3 callouts
- KPI row: Leader, Top Scoring, Conf Avg G/G, Top Player
- Left (7/12): Full standings table
- Right (5/12): Goal leaders (tabbed: Goals/Assists/Points/Clean Sheets) + Goals/Game bar chart

**In-Season extras:**
- Playoff zone + Bubble zone markers in standings table
- `GR` column (goal rate vs conf avg)
- Discipline Table: yellow cards, red cards, suspension watch per team
- Hot/Cold teams: last 5 games momentum
- Season Storylines: 4 narrative cards (title race, player watch, suspension risk, team form)

**Post-Season:** Same page, banner flips to "Season Complete", champion/golden boot/best defense callouts

### Template B — War Room (`/team/[abbr]`)
**Primary question:** *"How is my season going and what do I need to know today?"*

**Layout (Bento Grid):**
- Row 1: Season Record + Form Badges (left) | Smart Insights card (right, teal bg)
- Row 2: 3 Contextual Metric Cards (left) | Next Match Scouting Card (right)
- Row 3: Season Trend Chart GF vs GA (left) | Top Contributors mini-leaderboard (right)

### Template C — Schedule & Results (`/team/[abbr]/schedule`)
**Primary question:** *"What happened this season and what's coming?"*

Timeline table: date, opponent, H/A badge, result badge (W/L/D), score. NEXT game highlighted. Filterable by result/venue/conf.

### Template D — Roster & Stats (`/team/[abbr]/roster`)
**Primary question:** *"Who on my squad is doing what, ranked by what matters?"*

Sortable table: #, Name, Pos, GP, G, A, Shots, SOG, Min, G/90, Conv%. Position tab filter. Every name links to Player Profile.

### Template E — Game Detail (`/team/[abbr]/games/[id]`)
**Primary question:** *"What happened in this game and what does it mean?"*

Score hero + Momentum Timeline (0-90 min, goals as colored circles) + Territorial Dominance bar + Player stats table + Pre-game context card.

### Template F — Player Profile (`/player/[id]`)
**Primary question:** *"Who is this player, how do they rank, and how have they developed?"*

Identity header + 4 KPI cards (G/90, A/90, Conv%, Goal Involvement) vs GAC avg + 9-axis Radar Chart (percentile rank vs conference) + Career stats table (season-by-season) + Game log (amber highlight for exceptional games).

---

## Component Inventory

| Component | Used In | Notes |
|-----------|---------|-------|
| Contextual Metric Card | War Room (×6), Player Profile (×4) | value + delta badge + sparkline + conf avg |
| Form Badge Strip | War Room, Standings, Scouting Card | W=emerald, L=rose, D=amber, compact variant for tables |
| Delta Badge | All stat cards | `+0.4 ▲` emerald / `−1.2 ▼` rose / `±0 —` slate |
| GD Badge | Standings | `+28` emerald, `−13` rose, rounded-full |
| Inline Sparkline | Stat cards (full width), tables (40×16px) | Dashed line = conf avg |
| Smart Insight Item | War Room | SQL-generated narrative, NOT LLM. Icon + bold text + subtext |
| Next Match Scouting | War Room | Opponent record, key threat, H2H history, full-width button |
| Momentum Timeline | Game Detail | 0-90 min, D3.js, teal circles=us, rose=opponent |
| Radar Chart | Player Profile | 9 axes, percentile rank vs conf, Nivo library (Phase 3) |

---

## Visualization Tech Stack

| Layer | Library | Use Case |
|-------|---------|---------|
| KPI cards, sparklines | shadcn/ui charts (Recharts) | Start here — Tailwind-native |
| Line/bar/area charts | Recharts | Trend charts, splits |
| Radar/pizza charts | Nivo (`@nivo/radar`) | Player profiles (Phase 3) |
| Pitch overlays, timeline | D3.js | Game detail momentum only |

---

## Conference Page — In-Season vs Post-Season

Same page (`/conference/gac`), same URL. A `season_status` field (derived from whether the current date is within the season window) drives the mode.

**In-Season emphasis:**
- Drama: who's leading, how tight is the race, games remaining
- Discipline: yellow card counts, suspension watch list
- Form: hot/cold streaks, momentum
- Player chase: "Grudis is 4th, 5 back, 3 games left"

**Post-Season emphasis:**
- Final records: champion, runner-up, relegated
- Season awards: golden boot, best defense, most improved
- Historical record: how does this season compare to prior years

**No separate pages.** The page adapts. The stories are different; the structure is the same.

---

## Build Order

### Phase 1 — Foundation + Core Pages
1. App shell (header + context-aware sidebar + gender bar)
2. Color tokens + tabular-nums typography system in Tailwind config
3. Component library: Contextual Metric Card, Form Badge, Delta Badge, Sparkline
4. `conferences` table + GAC seed data in DB
5. Derived metrics on existing API endpoints (G/G, conv%, clean sheets, per-90)
6. Conference Overview page (Template A) with real data
7. War Room page (Template B) with real data
8. Sidebar L1↔L2 context switch

### Phase 2 — Full Team Experience
9. Schedule & Results (Template C)
10. Roster & Stats (Template D)
11. Game Detail (Template E)
12. Smart Insights rule engine (SQL-based, 6 templates)
13. Conference All Players leaderboard
14. Discipline table (yellow/red card data — already in dataset)

### Phase 3 — Player + Intelligence
15. Player Profile Trading Card (Template F) with Nivo radar chart
16. `player_profiles` table + deduplication + backfill
17. Analytics page (multi-season trends, splits)

### Phase 4 — Personalization
18. `user_preferences` table + onboarding flow
19. JWT verification in API
20. FilterContext + URL-driven state

### Phase 5 — AI
21. Rule-based insight → LLM-generated upgrade
22. Text-to-SQL chat panel
23. Match outcome predictions

---

## Data Status (as of 2026-03-16)

| School | Men's | Women's | Seasons |
|--------|-------|---------|---------|
| Harding (HU) | ✅ | ✅ | 2016–2025 |
| Ouachita Baptist (OBU) | ✅ | ✅ | 2016–2025 |
| All other 12 GAC full members | 🔄 scraping | 🔄 scraping | 2016–2025 |
| FHSU, Newman, NSU, Rogers State (affiliates) | 🔄 scraping | N/A | 2019–2025 |

**Total programs when complete:** 28 (16 men's + 12 women's)
**Scraper:** SideArm Sports adapter (working). StatCrew for HU.
**Key data available:** games, player_stats (per-game), team_stats, events (goals, yellow cards, red cards, substitutions)
**Discipline data:** 697 yellow cards, 44 red cards in existing 4-program dataset. Full conference will have much more.

---

## Mockup Files

All in `docs/mockups/` — open in browser:

| File | What it shows |
|------|---------------|
| `wireframes.html` | **Start here** — full design blueprint, site map, all 6 templates, component inventory |
| `shell.html` | **Interactive** — click teams to see L1↔L2 sidebar switch, all pages stubbed |
| `conference-full.html` | Conference page with In-Season/Post-Season toggle |
| `dashboard.html` | War Room (Team level) |
| `standings.html` | Conference standings data grid |
| `player.html` | Player Trading Card profile |
| `nav-map.html` | Navigation architecture diagram |
