# EDInsights.AI -- Platform Design Document

> The #1 destination for NCAA Division II College Soccer Data Insights.

This document defines the product vision, information architecture, analytics strategy, and technical plan for EDInsights.AI. It drives all development priorities.

---

## Vision

EDInsights.AI transforms raw college soccer data into actionable intelligence for coaches, athletes, athletic directors, and analysts. The platform combines deep historical statistics with AI-powered analysis to deliver competitive insights, player evaluations, and predictive analytics that would be impossible without aggregating and normalizing data across hundreds of programs.

**Not gambling.** This is about performance, preparation, and program development.

### Brand Ethos: "Precision & Performance"

The visual identity evokes trust, speed, and analytical rigor. The platform should feel like a **premium sports analytics command center** — closer to StatsBomb or Hudl's professional tooling than a generic SaaS dashboard.

Core tenets:
- **Data density over whitespace.** Sports analysts tolerate and prefer higher information density. Tighten paddings; use borders and background fills to compartmentalize data rather than relying on massive whitespace.
- **Context is king.** A number standing alone is useless. Every metric must visually indicate whether it is good or bad compared to a baseline (e.g., "2.14 Goals/Game | +0.4 vs Conference Avg" with a green indicator).
- **The dashboard tells a story.** The UI should surface the narrative of the data immediately — streaks, slumps, matchup advantages — not just present raw tables for the user to interpret.

---

## 1. User Personas

### Coach Martinez -- Head/Assistant Coach
- Checks 2-3x/week. Wants "my team" immediately on login.
- Prepares for upcoming opponents, tracks season trajectory, evaluates player form.
- Needs: opponent scouting, player usage/minutes analysis, trend lines.
- Pain: re-selecting school every visit, no conference standings, no head-to-head history.

### Director Williams -- Athletic Director
- Checks monthly or before board meetings. Executive-level consumer.
- Needs: program benchmarking against conference peers, multi-year trajectories, exportable summaries.
- Pain: no cross-school views, no conference-level dashboards.

### Scout Reyes -- Recruiting Coordinator / Analyst
- Heavy cross-school usage. Evaluates opponents and transfer prospects.
- Needs: cross-school player search, derived metrics (per-90, conversion rates), player comparison tools.
- Pain: players locked to single-school view, no derived metrics, no player profiles.

### Athlete Jordan -- Student-Athlete
- Checks after every game. Tracks personal improvement.
- Needs: personal stats dashboard, conference peer comparison, shareable profile.
- Pain: no individual identity, no personal stats view.

---

## 2. Visual Design System

### Color Palette

The palette is optimized for data visualization, not generic branding. Every color has a functional role.

**Backgrounds:**

| Token | Light Mode | Dark Mode | Usage |
|-------|-----------|-----------|-------|
| `app-bg` | Slate 50 (`#F8FAFC`) | Slate 950 (`#020617`) | Page background |
| `card-bg` | White (`#FFFFFF`) | Slate 900 (`#0F172A`) | Card surfaces — charts and data pop against solid backgrounds |
| `surface-muted` | Slate 100 (`#F1F5F9`) | Slate 800 (`#1E293B`) | Nested containers, input fields, sidebar active states |

**Brand & Data Colors:**

| Token | Hex | Usage |
|-------|-----|-------|
| `brand-primary` | Navy (`#0F172A`) | Logo, headers, primary text — existing brand identity |
| `brand-accent` | Deep Orange (`#EA580C`) | CTAs, homepage hero — existing brand energy |
| `data-primary` | Teal (`#0D9488`) | "My Team" data series, chart primary, active nav indicators |
| `data-opponent` | Bright Orange (`#F97316`) | Opponent data series — visually separates "us" from "them" consistently |
| `data-positive` | Emerald (`#10B981`) | Over-performing, positive deltas, wins |
| `data-negative` | Rose (`#F43F5E`) | Under-performing, negative deltas, losses |
| `data-neutral` | Amber (`#F59E0B`) | Draws, neutral deltas, warnings |

**Application Rules:**
- Every comparison chart uses `data-primary` (teal) for the user's team and `data-opponent` (orange) for the other team. No exceptions.
- Delta indicators (+/- badges) always use `data-positive` / `data-negative`. Never use red/green for non-data-contextual UI.
- Dark mode is offered as a toggle but light mode is the default. Coach Martinez checks this 2-3x/week — light mode is more accessible for casual use.

### Typography

| Role | Font | Weight | Style | Example |
|------|------|--------|-------|---------|
| Data values & KPIs | Inter | Bold (700) or Extrabold (800) | `tabular-nums` | **2.14**, **12-4-2** |
| Section labels | Inter | Bold (700) | `text-xs uppercase tracking-wider text-slate-500` | SEASON RECORD, GOALS / GAME |
| Body text | Inter | Regular (400) or Medium (500) | Default | Player descriptions, insight text |
| Table headers | Inter | Bold (700) | `text-xs uppercase tracking-wider` | GP, GOALS, ASSISTS |
| Table data | Inter | Regular (400) | `tabular-nums` | 16, 4, 0 |

**Critical rule:** All numerical data — tables, KPIs, stat cards, scores — must use `font-variant-numeric: tabular-nums` (Tailwind: `tabular-nums`). This ensures columns align perfectly and numbers don't shift width when values change. Do NOT use a monospace font family; Inter with `tabular-nums` achieves alignment without the terminal aesthetic.

### Layout System: Bento Box Architecture

Pages are constructed using a strict grid of modular cards ("bento boxes"). Each card is a self-contained data widget with a consistent structure:

```
┌─────────────────────────────────────┐
│ SECTION LABEL              Action ▸ │  ← uppercase, tracked, muted color
│                                     │
│  Primary Value    Context           │  ← bold, large, with delta badge
│  2.14            +0.4 vs Avg ▲      │
│                                     │
│  [Visualization / Detail]           │  ← chart, sparkline, or list
└─────────────────────────────────────┘
```

**Grid rules:**
- 12-column grid at 1280px+ viewport (desktop-first)
- Cards use `rounded-xl` borders with subtle `shadow-sm` and `border border-slate-200` (light) or `border-slate-700` (dark)
- Gap between cards: `gap-4` (16px) — tight enough for density, loose enough for scanability
- **Above-the-fold density:** The critical briefing (record, form, key KPIs, next match) must fit in a single viewport without scrolling. Detail views (charts, tables, game logs) live below the fold.
- Cards never have internal padding greater than `p-5` (20px)

### Contextual Metric Cards

The foundational UI component. Every stat card follows this pattern:

```
┌──────────────────┐
│ GOALS / GAME     │  ← label: text-xs uppercase tracking-wider text-slate-500
│                  │
│ 2.14             │  ← value: text-2xl font-extrabold text-slate-900
│ ┌──────┐         │
│ │ +0.4 │ ▲       │  ← delta badge: bg-emerald-100 text-emerald-700 rounded-full
│ └──────┘         │
│ vs Conference Avg│  ← context: text-xs text-slate-400
└──────────────────┘
```

**Rules for delta badges:**
- Positive delta: `bg-emerald-50 text-emerald-700` with up arrow
- Negative delta: `bg-rose-50 text-rose-700` with down arrow
- Neutral / within threshold: `bg-slate-100 text-slate-600` with dash
- The baseline for comparison (conference average, previous season, etc.) must always be labeled

### Form Badges

Win/Loss/Draw indicators used in dashboards, standings, and team profiles:

| Result | Badge Style |
|--------|-------------|
| Win | `bg-emerald-500 text-white` — shows "W" |
| Loss | `bg-rose-500 text-white` — shows "L" |
| Draw | `bg-amber-500 text-white` — shows "D" |

Rendered as a horizontal strip of small rounded squares (`w-7 h-7 rounded-md`), most recent result on the right. Clickable — each badge links to the game detail page.

---

## 3. Information Architecture

### The Two-Context Model

The current single-school-selector model breaks down at scale. Replace with two contexts:

1. **"My Team"** -- User's affiliated school (set during onboarding, persists across sessions). Dashboard, roster, schedule, and analytics default to this school. No school selector needed.
2. **"Explore"** -- Cross-school, cross-conference views. Conference standings, player leaderboards, school profiles, and comparison tools. Full filter bar (Division, Gender, Conference, School, Season).

### Navigation Structure

```
MY TEAM
  Dashboard              -- Season snapshot, record, top performers, recent results
  Schedule & Results     -- Full season timeline with results
  Roster & Stats         -- Sortable roster with derived metrics
  Season Analytics       -- Charts, trends, splits, multi-season comparison

EXPLORE
  Conference Standings   -- League tables, form, rankings
  All Teams              -- Browse/search all schools
  All Players            -- Cross-school leaderboard with per-90 stats
  Team Profile (detail)  -- Deep dive into any school
  Player Profile (detail)-- Career stats, radar chart, game log

COMPARE
  Head-to-Head           -- Side-by-side team comparison with historical matchups
  Player Comparison      -- Overlay player stats with radar charts

AI ASSISTANT (future)    -- Contextual chat panel, not a page

SETTINGS
  Profile & Preferences  -- Default school, gender, conference, theme
```

### Route Structure

```
/dashboard                          -- My Team overview
/dashboard/schedule                 -- My Team schedule & results
/dashboard/roster                   -- My Team roster & stats
/dashboard/analytics                -- My Team season analytics
/dashboard/games/[id]               -- Game detail
/dashboard/projections              -- Predictive analysis (future)

/explore/standings                  -- Conference standings
/explore/teams                      -- All teams browser
/explore/teams/[abbr]               -- Team profile
/explore/players                    -- Cross-school player leaderboard
/explore/players/[id]               -- Player profile

/compare/teams                      -- Head-to-head team comparison
/compare/players                    -- Player comparison

/settings                           -- User preferences
```

---

## 4. Page Designs

### 4.1 My Team Dashboard — "The War Room" (`/dashboard`)

The default landing page after login. Always shows the user's affiliated school. This is the coach's daily briefing — it should surface the story of the season at a glance.

**Layout (Bento Grid):**

```
┌─────────────────────────────────┬───────────────────────────────────┐
│ SEASON RECORD & FORM            │  SMART INSIGHTS (rule-based)      │
│ 12-4-2  │ W W L D W             │  "Shot conversion has dropped 12% │
│ ▲ 3rd in GAC                    │  over the last 3 games."          │
├──────────┬──────────┬───────────┼───────────────────────────────────┤
│GOALS/GAME│CONVERSION│CLEAN SHEET│  NEXT MATCH                       │
│  2.14    │  14.2%   │  6        │  vs Ouachita Baptist              │
│  +0.4 ▲  │  -1.2 ▼  │  +2 ▲    │  Sat, Nov 12 • Home              │
├──────────┴──────────┴───────────┤  Opponent Key Threat: ...         │
│ SEASON TREND: GF vs GA          │  H2H History: ...                 │
│ [Line chart — teal vs orange]   │                                   │
│                                 ├───────────────────────────────────┤
│                                 │ TOP CONTRIBUTORS                  │
│                                 │ 1. Grudis — 4G 0A  ████████░░    │
│                                 │ 2. Hahn  — 2G 0A   ████░░░░░░    │
└─────────────────────────────────┴───────────────────────────────────┘
```

**Row 1 — The Briefing:**
- **Season Record & Form** (left): W-L-D record in large bold type. Conference standing badge ("3rd in GAC" in `data-positive` green). Form badge strip (last 5 W/L/D as colored squares, clickable).
- **Smart Insights** (right): A visually distinct card (`bg-teal-50 border-teal-200` in light mode) showing rule-based natural language insights. These are SQL-driven template strings, NOT LLM-generated. Examples:
  - "Nojus Grudis has scored in 3 consecutive games"
  - "Shot conversion is 3.2% below conference average this month"
  - "Harding's clean sheet rate drops to 0% in away games"

**Row 2 — Key Metrics & Scouting:**
- **3-4 Contextual Metric Cards** (left): Goals/Game, Shot Conversion %, Clean Sheets, SOG Accuracy. Each with delta badge showing +/- vs conference average.
- **Next Match Scouting Card** (right, spans 2 rows): Locked to the next opponent on the schedule. Shows: opponent name, date/venue, opponent record, their most dangerous player/stat, and H2H history summary.

**Row 3 — Trends & Personnel:**
- **Season Trend Chart** (left): Goals For (teal line) vs Goals Against (orange line) per game. Conference average as a dashed reference line.
- **Top Contributors** (right): Mini-leaderboard with horizontal progress bars. Shows Goals + Assists leaders. Each player name is clickable to player profile.

**Selectors:** Season toggle only. No school selector.

### 4.2Schedule & Results (`/dashboard/schedule`)

**Content:**
- Full season in vertical timeline format
- Each row: date, opponent, venue (H/A), result badge (W/L/D), score
- Season record summary at top
- Home vs away record split

**Filters:** Home/Away, Result (W/L/D), Conference/Non-conference

### 4.3Roster & Stats (`/dashboard/roster`)

**Content:**
- Sortable roster table: Jersey #, Name, Position, GP, Goals, Assists, Points (G+A), Shots, SOG, Minutes, Goals/90, Shot Conversion %
- Position filter tabs: All | Forwards | Midfielders | Defenders | Goalkeepers
- Minutes distribution chart
- Click player name -> Player Profile

**Key principle:** Derived metrics (per-90 rates, conversion %) are more valuable than raw totals.

### 4.4Season Analytics (`/dashboard/analytics`)

**Content:**
- Goals For vs Against trend (line chart, per game)
- Shot funnel visualization
- Home vs Away splits (grouped bar chart)
- Conference vs non-conference performance split
- Multi-season trend (goals/game, win%, shots/game across all available years)
- Territorial Dominance Index distribution

### 4.5Game Detail (`/dashboard/games/[id]`)

**Existing + enhancements:**
- Momentum timeline: events plotted on match clock (0-90 min), goals as large markers, cards as colored squares
- Territorial Dominance bar (horizontal stacked bar, possession proxy)
- Pre-game context card ("Coming in, School was 8-3-1, 3rd in GAC")
- Player of the match highlight
- Clickable player names -> Player Profile

### 4.6 Conference Standings — Data Grid (`/explore/standings`)

**The most impactful new page.**

**Content:**
- Conference standings as a **Data Grid** (not a plain table):
  - Pin left column (Team Name) on horizontal scroll
  - Columns: Rank, School, GP, W, L, D, GF, GA, GD, Points, PPG, Form (last 5)
  - GD column uses colored badges: `data-positive` green for positive, `data-negative` red for negative
  - Form column renders as colored badge strip (W/L/D squares), not text
  - Inline sparklines in a "Trend" column showing goals/game over last 5 matches
  - Sortable by any numeric column
- Overall vs Conference-only toggle
- Click school -> Team Profile

**Selectors:** Conference, Season, Gender (Men's/Women's)

### 4.7All Teams (`/explore/teams`)

Grid/list of all schools, filterable by conference. Each card: school name, mascot, conference, current season record, goals scored. Click -> Team Profile.

### 4.8All Players (`/explore/players`)

Cross-school player leaderboard. This is what scouts need.

**Content:**
- Leaderboard: Rank, Player, School, Position, GP, Goals, Assists, Points, Goals/90, Shot Conv%
- Sortable by any metric
- Minimum games played threshold slider

**Selectors:** Conference (or All), Season, Position, School (optional)

### 4.9Team Profile (`/explore/teams/[abbr]`)

**Content:**
- School header (name, mascot, conference, logo placeholder)
- Current season record + conference standing
- Multi-season performance chart (win%, goals/game across all years)
- Current roster with season stats
- Recent results
- Head-to-head records against other teams in the system

### 4.10 Player Profile — "The Trading Card" (`/explore/players/[id]`)

**Layout:**

```
┌────────────────────┬──────────────────────────────────────────────┐
│ PLAYER IDENTITY    │  PERFORMANCE SUMMARY                         │
│                    │  ┌─────────┬─────────┬─────────┬───────────┐ │
│  [Photo/Silhouette]│  │GOALS/90 │ASSISTS90│SHOT CONV│GOAL INVLV%│ │
│  Nojus Grudis      │  │  0.34   │  0.11   │  22.2%  │  28.6%    │ │
│  #9 • FWD          │  │  +0.12▲ │  -0.02▼ │  +4.1▲  │  +8.2▲   │ │
│  Harding (HU)      │  └─────────┴─────────┴─────────┴───────────┘ │
│  Sr. • 16 GP       │                                              │
│                    │  CAREER STATS                                │
│  ┌──────────────┐  │  Season | GP | G | A | Pts | Min | G/90     │
│  │ [9-axis      │  │  ───────┼────┼───┼───┼─────┼─────┼──────    │
│  │  Radar Chart] │  │  24-25 │ 16 │ 4 │ 0 │  4  │1058 │ 0.34    │
│  │              │  │  23-24 │ 18 │ 6 │ 2 │  8  │1320 │ 0.41    │
│  └──────────────┘  │                                              │
│  vs Conference Avg │  GAME LOG (collapsible)                      │
│                    │  [Per-game row with sparkline highlights]     │
└────────────────────┴──────────────────────────────────────────────┘
```

**Left Sidebar (Identity):**
- Player photo placeholder (silhouette if unavailable)
- Name, jersey number, position, school, class year, games played
- 9-axis Radar/Pizza Chart showing percentile rank within conference (see Visualization Guide for axis specification)
- "Compare with..." button linking to player comparison

**Right Main Area (Performance):**
- Contextual metric cards: Goals/90, Assists/90, Shot Conversion %, Goal Involvement Index (player's share of team goals). Each with delta vs conference average.
- Career stats table (season by season) with per-90 derived metrics
- Per-game log for selected season — games with exceptional performances (>2 goal contributions) get a subtle `border-amber-300` highlight
- "Compare with..." link to player comparison

### 4.11Head-to-Head (`/compare/teams`)

Two school selectors side by side. Season selector. Side-by-side stat bars. Historical matchup results. Top performer comparison.

### 4.12Player Comparison (`/compare/players`)

Two player search selectors. Side-by-side stat table. Overlaid radar chart. Season-by-season trajectory comparison.

---

## 5. Derived Metrics & KPIs

### Tier 1 -- Implement First (simple SQL from existing data)

| Metric | Formula | Where |
|--------|---------|-------|
| Goals Per Game | total_goals / GP | Dashboard, Standings |
| Shot Conversion Rate | goals / shots * 100 | Dashboard, Player cards |
| SOG Accuracy | SOG / shots * 100 | Dashboard, Player cards |
| Clean Sheet % | games_with_0_GA / GP * 100 | Dashboard |
| Points Per Game | points / GP | Standings |
| Goal Differential | GF - GA | Standings |
| Home/Away Win % | home_wins / home_GP | School profile |
| Per-90 Stats | (stat / minutes) * 90 | Player leaderboard |
| Goal Contributions | goals + assists | Player leaderboard |

### Tier 2 -- Implement Next (cross-table joins, game-level granularity)

| Metric | Formula | Where |
|--------|---------|-------|
| Goal Involvement Index | (player G+A) / team_goals * 100 | Player profile |
| Territorial Dominance | (shots+corners+SOG) / (both teams total) * 100 | Game detail |
| Form (Last 5) | W/L/D sequence | Standings |
| Home Advantage Index | home_win% - away_win% | School profile |
| Consistency Score | 1 - (stdev(goal_diff) / mean) | School profile |

### Tier 3 -- Implement Later (analytics infrastructure)

| Metric | Formula | Where |
|--------|---------|-------|
| Naive xG | shots * historical_conversion | Game detail |
| Strength of Schedule | avg opponent win% | School profile |
| Clutch Rating | goals in last 15 min / total goals | Player profile |
| Anomaly Detection | stddev-based flagging | Game detail |

---

## 6. Visualization Guide

| Context | Chart Type | Why |
|---------|-----------|-----|
| Conference standings | Sortable data table + sparklines | Coaches scan/sort numbers |
| Team comparison | Radar/spider chart (2-4 teams) | Multi-axis comparison |
| H2H matrix | Color-coded grid table | Compact cross-reference |
| Season trends | Small multiples (2x2 line charts) | Readable per-KPI trends |
| Game momentum | Timeline with event markers (0-90 min) | Most engaging game-level viz |
| Territorial dominance | Horizontal stacked bar | Intuitive possession proxy |
| Shooting efficiency | Scatter plot (accuracy vs conversion, bubble=goals) | Reveals player archetypes |
| Player comparison | Radar chart overlay | Side-by-side profile |
| Season progression | Cumulative line chart | Shows streaks/slumps |
| Minutes distribution | Horizontal bar chart (ranked) | Squad depth at a glance |

**Soccer-Specific Visualizations:**

| Context | Chart Type | Why |
|---------|-----------|-----|
| Player profile | Radar/Pizza chart (9 axes, percentile ranks) | The StatsBomb standard — shows player "shape" across attacking/defending/passing |
| Shot quality | Pitch overlay with xG bubbles | Location + shot quality in one view — domain-specific and visually distinctive |
| Match momentum | 0-90 min horizontal timeline with event markers | Goals as large markers, cards as colored squares — the most engaging game-level viz |
| Player comparison | Overlaid radar charts (2-3 players) | Side-by-side percentile profiles |

**Radar Chart Specification (Player Profile):**
- 9 axes maximum, grouped logically: Attacking (Goals/90, Shots/90, Shot Conv%), Creative (Assists/90, Key Passes/90, xA/90), Defensive (Tackles/90, Interceptions/90, Aerial%)
- Always display **percentile ranks within conference**, not raw numbers (e.g., 85th percentile, not 0.78 goals/90)
- Minimize correlation between adjacent axes
- Fill area with semi-transparent `data-primary` (teal) for the player, `data-opponent` (orange) for comparison

**Sparklines in Tables:**
Every data table (players, teams, standings) should include inline sparklines for key metrics showing the last 5-game trend. Implementation: tiny line charts (40x16px) rendered inline in table cells. These transform flat tables into living documents.

**Reference Lines on Charts:**
When showing any team or player metric over time, overlay:
- Conference average as a dashed line with label
- Conference leader as a dotted line (optional)
This provides instant context — "am I above or below average?" — without requiring the user to look up a separate table.

**Principles:**
- Tables for anything that needs scanning/sorting across many entities
- Charts for trends over time and multi-axis comparisons
- Sparklines for inline trend indicators within tables
- No pie charts -- poor for comparison, data doesn't suit them
- Responsive but **desktop-first** (1280px+ primary viewport)

### Visualization Technology Stack

| Layer | Library | Use For |
|-------|---------|---------|
| KPI Cards & Sparklines | **shadcn/ui charts** (Recharts-based) | Stat cards, delta indicators, inline sparklines — Tailwind-native, copy-paste model |
| Standard Charts | **Recharts** | Line, bar, area, funnel charts — already shadcn-compatible |
| Radar/Pizza Charts | **Nivo** (`@nivo/radar`) | Player profile radar charts, percentile visuals |
| Soccer-Specific | **D3.js** (selective) | Pitch overlays, shot maps, momentum timelines — only for custom visuals no library provides |

**Adoption strategy:** Start with shadcn/ui charts for stat cards and sparklines (Tier 1). Add Nivo for radar charts when player profiles ship (Phase 3). Use D3 only for pitch-overlay visualizations (Phase 3+). Do not adopt all four libraries simultaneously.

---

## 7. Selector & Filter Design

### Hierarchy

```
Division (future) > Gender > Conference > School > Season
```

### Profile-level (set once, persist across sessions)
- Affiliated school -- set during onboarding, changeable in Settings
- Default gender preference (Men's / Women's)
- Stored in `user_preferences` table

### Page-level (in filter bar, change per interaction)
- Season -- defaults to most recent with data
- Conference -- defaults to user's school's conference
- Gender -- defaults to profile preference

### Inline (within a component)
- Position tabs on roster pages
- Home/Away toggle on schedule
- Sort column on tables
- Min-games-played slider on leaderboards

### Implementation
- URL search params as source of truth (`?conference=GAC&season=2025&gender=men`)
- `FilterContext` provider reads: URL params (highest) -> user preferences -> system defaults
- All filtered views are bookmarkable and shareable
- "My Team" pages have NO school selector -- that's the #1 UX improvement

---

## 8. Technical Plan

### 8.1Database Schema Evolution

**New tables:**

```sql
conferences (id, name, abbreviation, division, region)

-- Modify schools: add conference_id FK, gender, logo_url, website_url

player_profiles (id, canonical_name, school_id FK, gender, position, class_year, jersey_number)
player_profile_aliases (id, player_profile_id FK, raw_name, school_id FK)

-- Modify player_game_stats: add player_profile_id FK

user_preferences (id, supabase_user_id UUID UNIQUE, default_school_id FK,
                  default_conference_id FK, default_gender, default_division,
                  favorite_school_ids INTEGER[], theme)
```

**Materialized views** for conference standings and cross-school aggregations, refreshed after pipeline loads.

### 8.2New API Endpoints

| Router | Endpoint | Purpose |
|--------|----------|---------|
| conferences | `GET /api/conferences` | List conferences |
| conferences | `GET /api/conferences/{abbr}/standings` | Conference standings |
| conferences | `GET /api/conferences/{abbr}/leaders` | Cross-school leaderboard |
| compare | `GET /api/compare/schools?ids=1,2` | Side-by-side team stats |
| compare | `GET /api/compare/players?ids=1,2` | Side-by-side player stats |
| players | `GET /api/players/search?q=smith` | Player search |
| players | `GET /api/players/{id}` | Player profile + career |
| players | `GET /api/players/{id}/games` | Player game log |
| derived | `GET /api/stats/derived/team` | Computed team metrics |
| preferences | `GET /api/preferences` | User preferences |
| preferences | `PUT /api/preferences` | Update preferences |
| search | `GET /api/search?q=...` | Universal search |

**Global filter dependency:** All stat endpoints accept `?division=&gender=&conference=&season=` via a shared FastAPI dependency.

### 8.3Frontend Architecture

- **FilterContext** provider wraps dashboard layout, reads URL params + user preferences
- **SchoolSeasonSelector** splits into: `SeasonSelector` (My Team), `GlobalFilterBar` (Explore), `CompareSelectors` (Compare)
- Reusable component library in `components/stats/`: `StatCard`, `LeaderboardTable`, `StandingsTable`, `ComparisonChart`, `PlayerCard`, `RadarChart`
- Server Components for page shells; Client Components for interactive data
- No React Query yet -- current fetch+useState is sufficient at this scale

### 8.4Player Identity Strategy

1. **Phase 1:** Create `player_profiles` table. Deduplicate by (school_id, jersey_number, normalized name). Backfill `player_game_stats.player_profile_id`.
2. **Phase 2:** Fuzzy matching + admin merge UI via `player_profile_aliases`.
3. **Phase 3:** Scrape roster pages for authoritative identity.

### 8.5User Preferences

- Store in app Postgres (not Supabase metadata) for FK integrity
- API verifies Supabase JWTs via `get_current_user` dependency
- Frontend FilterContext initializes from: URL params -> preferences -> defaults

---

## 9. Intelligence Layer

### 9.1 Rule-Based Insight Engine (Pre-AI — Implement Early)

Before LLM integration, the platform can generate compelling natural language insights using pure SQL queries and template strings. This delivers 80% of the "AI-enhanced" perception with minimal infrastructure.

**Architecture:** A FastAPI endpoint (`GET /api/insights/team/{school_id}`) runs a battery of SQL queries and returns an array of insight objects:

```json
{
  "insights": [
    {
      "type": "streak",
      "severity": "positive",
      "text": "Nojus Grudis has scored in 3 consecutive games",
      "metric": "goals",
      "entity": "player",
      "entity_id": 42
    }
  ]
}
```

**Insight Templates:**

| Category | SQL Pattern | Template |
|----------|------------|----------|
| Scoring streak | Count consecutive games with goals > 0 | "{Player} has scored in {N} consecutive games" |
| Form trend | Compare last 3 game avg to season avg | "Shot conversion has dropped {X}% over the last 3 games" |
| Home/away split | Compare home vs away win rates | "Clean sheet rate drops to {X}% in away games" |
| Conference benchmark | Compare team metric to conference avg | "{Metric} is {X}% {above/below} conference average" |
| Opponent weakness | Analyze next opponent's stats | "Next opponent concedes {X}% of goals in the final 20 minutes" |
| Breakout performance | Flag games with >2 stddev from player mean | "{Player} had a career-high {N} shots against {Opponent}" |

**Display:** Rendered in the Smart Insights card on the dashboard. Rotate through 2-3 insights with a subtle fade transition. Each insight is clickable — links to the relevant player profile, game detail, or analytics page.

### 9.2 AI Chat Interface (Future)
- Persistent floating button on every dashboard page, opens slide-over panel
- Contextual: knows what page/school/game you're viewing
- Example: "How did we perform against SWOSU last 3 years?" or "Which midfielder has the best shot conversion?"

### Architecture
- **Text-to-SQL (primary):** LLM generates read-only SQL from natural language. System prompt includes schema description. Safety: read-only transactions, 5s timeout, 100 row limit, table allowlist.
- **RAG over stats (supplementary):** Pre-computed summaries embedded via pgvector. Used for narrative answers.
- LLM calls external API (Claude) from FastAPI backend. No local model.

### Predictive Analytics
- Match outcome prediction (logistic regression on form, H2H, home advantage)
- Season trajectory projection (extrapolate W-L-D based on remaining schedule difficulty)
- Player development curves (per-90 trends across seasons)
- Anomaly detection (flag statistically unusual games/performances)

---

## 10. Implementation Phases

### Phase 1 -- Foundation & Visual Identity

**Data layer:**
- Add `conferences` table, `gender`/`conference_id` to `schools`
- Migrate existing data (GAC, infer gender from abbreviation)
- Add derived metrics to existing API responses (goals/game, conversion rates, per-90)
- Add conference average benchmarks to API responses (for delta indicators)

**Visual system (War Room Tier 1):**
- Implement the Visual Design System (Section 2): color tokens, typography rules, `tabular-nums`
- Replace flat stat cards with Contextual Metric Cards (value + delta badge + baseline label)
- Add Form Badges (W/L/D colored strip) to dashboard overview
- Restructure dashboard to Bento Box grid layout (Section 4.1)
- Eliminate dead whitespace on Teams and Analytics pages
- Add sparklines to player leaderboard table
- Install shadcn/ui charts as the base visualization layer

**Frontend architecture:**
- Add `FilterContext` and `GlobalFilterBar` to frontend
- Enhance game detail with momentum timeline and TDI

### Phase 2 -- Conference, Cross-School & Insights

**Data layer:**
- Conference standings endpoint + materialized view
- Rule-Based Insight Engine API (Section 9.1) — SQL-driven insight templates

**Pages:**
- Conference standings as Data Grid (`/explore/standings`) with pinned columns, form badges, GD coloring, sparklines
- Cross-school player leaderboard (`/explore/players`)
- Team profile page (`/explore/teams/[abbr]`)
- Head-to-head comparison tool (`/compare/teams`)

**Visual system (War Room Tier 2):**
- Smart Insights card on dashboard (renders rule-based insights)
- Next Match Scouting card on dashboard
- Conference average reference lines on all trend charts
- Dark mode toggle

### Phase 3 -- Player Identity, Profiles & Soccer Viz

**Data layer:**
- `player_profiles` table + backfill script
- Player search endpoint

**Pages:**
- Player profile as "Trading Card" layout (`/explore/players/[id]`) — see Section 4.10
- Player comparison tool (`/compare/players`)
- Shooting efficiency scatter plot

**Visualization (War Room Tier 3):**
- Install Nivo for radar/pizza charts
- 9-axis radar chart on player profiles (percentile ranks vs conference)
- Overlaid radar charts on player comparison page
- Pitch-overlay shot maps using D3 (selective)

### Phase 4 -- User Preferences & Personalization
- JWT verification in API
- `user_preferences` table + endpoints
- Onboarding flow (select school, gender)
- Connect preferences to FilterContext
- Enhanced settings page

### Phase 5 -- AI & Predictions
- pgvector extension + embeddings table
- Text-to-SQL chat endpoint
- Frontend chat panel component (slide-over, contextual)
- Upgrade Smart Insights from rule-based to LLM-generated
- Match outcome prediction model
- Season trajectory projections

---

## 11. Design Principles

1. **My team first, the world second.** The most common path (coach checking their team) must require zero configuration after setup.

2. **No number without context.** "14 goals" is meaningless. "0.78 goals/game, +0.4 vs conference avg, 3rd in GAC" is actionable. Every stat carries context: rate, rank, delta, or trend. Use delta badges and reference lines everywhere.

3. **Everything is a link.** Every school name, player name, score, and stat is clickable. Users pull the thread: Standings -> School -> Player -> Game -> Event.

4. **Data density with escape hatches.** Sports analytics users want dense tables. Show data-rich views by default with chart summaries as entry points. Above-the-fold density: the critical briefing fits in one viewport.

5. **Progressive disclosure.** Show essential filters by default. Advanced filters behind "More filters." Don't overwhelm, but don't hide power.

6. **URL-driven state.** All filter selections in URL params. Every view is bookmarkable and shareable.

7. **Built for soccer, not generic dashboards.** Use domain-specific visualizations (radar charts, pitch overlays, momentum timelines, form badges) that signal "this was built by people who understand the sport." Generic bar charts are a last resort.

8. **Teal is us, orange is them.** Maintain absolute consistency in data color semantics. The user's team is always teal; the opponent is always orange. Green means good, red means bad. Never deviate.

### Competitive Context

EDInsights.AI competes for attention (not directly for market share) with Hudl/StatsBomb, Wyscout, and Catapult in the college soccer space. Those platforms have video integration and wearable data that we don't. Our differentiator is **accessibility and intelligence**: making advanced analytics available to Division II programs that can't afford enterprise tooling, and surfacing insights that would require a dedicated analyst to extract manually. The visual design must communicate "serious analytical tool" — not "student project" — to earn trust from coaches and athletic directors.
