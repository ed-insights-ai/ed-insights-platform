# EDInsights.AI -- Platform Design Document

> The #1 destination for NCAA Division II College Soccer Data Insights.

This document defines the product vision, information architecture, analytics strategy, and technical plan for EDInsights.AI. It drives all development priorities.

---

## Vision

EDInsights.AI transforms raw college soccer data into actionable intelligence for coaches, athletes, athletic directors, and analysts. The platform combines deep historical statistics with AI-powered analysis to deliver competitive insights, player evaluations, and predictive analytics that would be impossible without aggregating and normalizing data across hundreds of programs.

**Not gambling.** This is about performance, preparation, and program development.

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

## 2. Information Architecture

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

## 3. Page Designs

### 3.1 My Team Dashboard (`/dashboard`)

The default landing page after login. Always shows the user's affiliated school.

**Content:**
- Season record card (W-L-D, win %, conference record vs overall)
- Conference standing badge ("3rd in GAC")
- Last 5 results strip (W/L/D colored badges with scores, clickable)
- Top 3 performers card (goals + assists leaders)
- Season trend sparkline (goals for vs against, rolling)
- Shot conversion funnel (Shots -> SOG -> Goals)

**Selectors:** Season toggle only. No school selector.

### 3.2 Schedule & Results (`/dashboard/schedule`)

**Content:**
- Full season in vertical timeline format
- Each row: date, opponent, venue (H/A), result badge (W/L/D), score
- Season record summary at top
- Home vs away record split

**Filters:** Home/Away, Result (W/L/D), Conference/Non-conference

### 3.3 Roster & Stats (`/dashboard/roster`)

**Content:**
- Sortable roster table: Jersey #, Name, Position, GP, Goals, Assists, Points (G+A), Shots, SOG, Minutes, Goals/90, Shot Conversion %
- Position filter tabs: All | Forwards | Midfielders | Defenders | Goalkeepers
- Minutes distribution chart
- Click player name -> Player Profile

**Key principle:** Derived metrics (per-90 rates, conversion %) are more valuable than raw totals.

### 3.4 Season Analytics (`/dashboard/analytics`)

**Content:**
- Goals For vs Against trend (line chart, per game)
- Shot funnel visualization
- Home vs Away splits (grouped bar chart)
- Conference vs non-conference performance split
- Multi-season trend (goals/game, win%, shots/game across all available years)
- Territorial Dominance Index distribution

### 3.5 Game Detail (`/dashboard/games/[id]`)

**Existing + enhancements:**
- Momentum timeline: events plotted on match clock (0-90 min), goals as large markers, cards as colored squares
- Territorial Dominance bar (horizontal stacked bar, possession proxy)
- Pre-game context card ("Coming in, School was 8-3-1, 3rd in GAC")
- Player of the match highlight
- Clickable player names -> Player Profile

### 3.6 Conference Standings (`/explore/standings`)

**The most impactful new page.**

**Content:**
- Conference standings table: Rank, School, GP, W, L, D, GF, GA, GD, Points, PPG, Form (last 5)
- Overall vs Conference-only toggle
- Click school -> Team Profile

**Selectors:** Conference, Season, Gender (Men's/Women's)

**Visualization:** Sortable table with form column as colored dots (green/red/yellow).

### 3.7 All Teams (`/explore/teams`)

Grid/list of all schools, filterable by conference. Each card: school name, mascot, conference, current season record, goals scored. Click -> Team Profile.

### 3.8 All Players (`/explore/players`)

Cross-school player leaderboard. This is what scouts need.

**Content:**
- Leaderboard: Rank, Player, School, Position, GP, Goals, Assists, Points, Goals/90, Shot Conv%
- Sortable by any metric
- Minimum games played threshold slider

**Selectors:** Conference (or All), Season, Position, School (optional)

### 3.9 Team Profile (`/explore/teams/[abbr]`)

**Content:**
- School header (name, mascot, conference, logo placeholder)
- Current season record + conference standing
- Multi-season performance chart (win%, goals/game across all years)
- Current roster with season stats
- Recent results
- Head-to-head records against other teams in the system

### 3.10 Player Profile (`/explore/players/[id]`)

**Content:**
- Player header (name, school, position, jersey number)
- Career stats table (season by season)
- Per-game log for selected season
- Radar chart: Goals/90, Assists/90, Shots/90, SOG/90, Minutes/Game (percentile within conference)
- Goal Involvement Index (player's share of team goals)
- "Compare with..." link to player comparison

### 3.11 Head-to-Head (`/compare/teams`)

Two school selectors side by side. Season selector. Side-by-side stat bars. Historical matchup results. Top performer comparison.

### 3.12 Player Comparison (`/compare/players`)

Two player search selectors. Side-by-side stat table. Overlaid radar chart. Season-by-season trajectory comparison.

---

## 4. Derived Metrics & KPIs

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

## 5. Visualization Guide

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

**Principles:**
- Tables for anything that needs scanning/sorting across many entities
- Charts for trends over time and multi-axis comparisons
- Sparklines for inline trend indicators within tables
- No pie charts -- poor for comparison, data doesn't suit them
- Responsive but **desktop-first** (1280px+ primary viewport)

---

## 6. Selector & Filter Design

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

## 7. Technical Plan

### 7.1 Database Schema Evolution

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

### 7.2 New API Endpoints

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

### 7.3 Frontend Architecture

- **FilterContext** provider wraps dashboard layout, reads URL params + user preferences
- **SchoolSeasonSelector** splits into: `SeasonSelector` (My Team), `GlobalFilterBar` (Explore), `CompareSelectors` (Compare)
- Reusable component library in `components/stats/`: `StatCard`, `LeaderboardTable`, `StandingsTable`, `ComparisonChart`, `PlayerCard`, `RadarChart`
- Server Components for page shells; Client Components for interactive data
- No React Query yet -- current fetch+useState is sufficient at this scale

### 7.4 Player Identity Strategy

1. **Phase 1:** Create `player_profiles` table. Deduplicate by (school_id, jersey_number, normalized name). Backfill `player_game_stats.player_profile_id`.
2. **Phase 2:** Fuzzy matching + admin merge UI via `player_profile_aliases`.
3. **Phase 3:** Scrape roster pages for authoritative identity.

### 7.5 User Preferences

- Store in app Postgres (not Supabase metadata) for FK integrity
- API verifies Supabase JWTs via `get_current_user` dependency
- Frontend FilterContext initializes from: URL params -> preferences -> defaults

---

## 8. AI Integration (Future)

### AI Chat Interface
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

## 9. Implementation Phases

### Phase 1 -- Foundation
- Add `conferences` table, `gender`/`conference_id` to `schools`
- Migrate existing data (GAC, infer gender from abbreviation)
- Add derived metrics to existing API responses (goals/game, conversion rates, per-90)
- Add `FilterContext` and `GlobalFilterBar` to frontend
- Enhance game detail with momentum timeline and TDI

### Phase 2 -- Conference & Cross-School
- Conference standings endpoint + materialized view
- Conference standings page (`/explore/standings`)
- Cross-school player leaderboard (`/explore/players`)
- Team profile page (`/explore/teams/[abbr]`)
- Head-to-head comparison tool (`/compare/teams`)

### Phase 3 -- Player Identity & Profiles
- `player_profiles` table + backfill script
- Player search endpoint
- Player profile page (`/explore/players/[id]`)
- Player comparison tool (`/compare/players`)
- Shooting efficiency scatter plot

### Phase 4 -- User Preferences & Personalization
- JWT verification in API
- `user_preferences` table + endpoints
- Onboarding flow (select school, gender)
- Connect preferences to FilterContext
- Enhanced settings page

### Phase 5 -- AI & Predictions
- pgvector extension + embeddings table
- Text-to-SQL chat endpoint
- Frontend chat panel component
- Match outcome prediction model
- Season trajectory projections

---

## 10. Design Principles

1. **My team first, the world second.** The most common path (coach checking their team) must require zero configuration after setup.

2. **Derived metrics over raw totals.** "14 goals" is meaningless. "0.78 goals/game, 3rd in GAC" is actionable. Every stat carries context: rate, rank, or trend.

3. **Everything is a link.** Every school name, player name, score, and stat is clickable. Users pull the thread: Standings -> School -> Player -> Game -> Event.

4. **Data density with escape hatches.** Sports analytics users want dense tables. Show data-rich views by default with chart summaries as entry points.

5. **Progressive disclosure.** Show essential filters by default. Advanced filters behind "More filters." Don't overwhelm, but don't hide power.

6. **URL-driven state.** All filter selections in URL params. Every view is bookmarkable and shareable.
