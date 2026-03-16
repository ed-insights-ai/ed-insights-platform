# ADR-005: SideArm CMS Scraper Variant Strategy

**Date:** 2026-03-16
**Status:** Accepted
**Supersedes:** ADR-003 (StatCrew + SideArm scraper strategy)

## Context

After scraping all confirmed GAC soccer programs and reverse-engineering their
athletics sites, we discovered that SideArm Sports CMS — the most common
platform — comes in two distinct variants, and that some schools we originally
assumed were "SideArm Legacy" don't actually host their soccer programs on
SideArm at all.

**Source of truth for GAC program membership:** GAC standings API
`greatamericanconference.com/services/standings.ashx?path=msoc&year=YEAR`

**Actual GAC soccer universe:** 7 men's programs + 7 women's programs = **14 total**
(not 28 as originally configured in `schools.toml`)

### SideArm Variants

**Variant 1: StatCrew (Harding only)**
- Static HTML pages hosted at `sidearmstats.com`
- Pattern: `/msoc/stats/{year}/{opponent}/boxscore.htm`
- Fully SSR; simple `requests` + `BeautifulSoup` works
- Both Harding M and Harding W use this

**Variant 2: SideArm New (Nuxt 3 / Vue)**
- Modern platform; schedule HTML contains boxscore links in initial HTTP response
- Pattern: `/sports/mens-soccer/stats/{year}/{opponent}/boxscore/{id}`
- `requests` + regex on the schedule page captures all boxscore URLs
- Also exposes undocumented JSON API: `GET /api/v2/Schedule/{scheduleId}`
- **12 of 14 GAC programs use this variant** (verified via link count on schedule page)

**Variant 3: SideArm Legacy (KnockoutJS)**
- Older SPA; `/sports/{sport}/schedule/{year}` redirects → `/index.aspx`
- Schedule data loaded via client-side XHR at runtime; not in initial HTML
- Boxscore URLs use pattern: `/boxscore.aspx?id={game_id}`
- No `/api/v2/` endpoint
- **2 of 14 GAC programs use this: NSU (men's), NWOSU men's originally — now confirmed NWOSU women's is New**
- Confirmed Legacy via: URL redirect chain + zero boxscore links in HTML

**"No soccer on SideArm" (separate from variant)**
- Some schools listed in original `schools.toml` simply don't register soccer on their SideArm site at all
- Confirmed via `GET /services/sportnames.ashx` — returns all sports registered on a SideArm site
- ATU, HSU, SOSU, SAU, UAM: no soccer whatsoever on SideArm (neither men's nor women's)
- ECU, SWOSU: have women's soccer on SideArm (wsoc), NO men's soccer
- Separately confirmed: none of these schools appear in GAC standings for either sport
- **These were config errors in the original `schools.toml` — these schools do not play GAC soccer**

### Discovery Tools

| Tool | Purpose |
|---|---|
| `GET /services/sportnames.ashx` | Lists all sports registered on a SideArm site. Reliable probe. |
| `GET /services/adaptive_components.ashx` | Serves component data per sport — potentially useful for Legacy schedule data |
| `GET /api/v2/Sports` | Modern SideArm only. Returns sport list with `scheduleId`. |
| `GET /api/v2/Schedule/{id}` | Full season JSON with boxscore URLs. Preferred over HTML scraping. |
| GAC standings API | Authoritative source for which schools play in GAC soccer |

## Decision

**Three-tier scraper strategy** with `scraper` + `data_status` fields per school in `schools.toml`:

### Tier 1: `scraper = "statcrew"`
- Harding M (`HU`) and Harding W (`HUW`)
- Working, no changes needed

### Tier 2: `scraper = "sidearm"` (SideArm New)
- 11 programs confirmed working
- Current implementation: regex on schedule HTML
- Enhancement path: use `/api/v2/Schedule/{id}` JSON when available (cleaner, more stable)

### Tier 3: `scraper = "sidearm_legacy"` + `enabled = false`
- NSU men's (`NSU`) — confirmed Legacy via redirect chain
- Set `data_status = "unverified"`, `enabled = false` until scraper is implemented
- Implementation options: reverse-engineer KnockoutJS XHR endpoint, or Playwright fallback

### `data_status` field (new)
Separates "can we scrape it" from "does the sport exist":
- `verified` — URL confirmed, sport confirmed present, scraper end-to-end tested
- `unverified` — config set but not tested
- `absent` — sport not on this platform (different source needed)

## GAC Coverage (verified 2026-03-16)

| Program | Abbr | Scraper | Status |
|---|---|---|---|
| Harding (M) | HU | statcrew | ✅ verified |
| Fort Hays State | FHSU | sidearm | ✅ verified |
| Newman | NU | sidearm | ✅ verified |
| Northeastern State | NSU | sidearm_legacy | ⚠️ not yet implemented |
| Ouachita Baptist (M) | OBU | sidearm | ✅ verified |
| Rogers State | RSU | sidearm | ✅ verified |
| Southern Nazarene (M) | SNU | sidearm | ✅ verified |
| Harding (W) | HUW | statcrew | ✅ verified |
| East Central | ECU | sidearm | ✅ verified |
| Northwestern Oklahoma State | NWOSU | sidearm | ✅ verified |
| Oklahoma Baptist | OKBU | sidearm | ✅ verified |
| Ouachita Baptist (W) | OBUW | sidearm | ✅ verified |
| Southern Nazarene (W) | SNUW | sidearm | ✅ verified |
| Southwestern Oklahoma State | SWOSU | sidearm | ✅ verified |

**13/14 programs ready to scrape. 1 blocked (NSU — Legacy SideArm).**

## Consequences

**Good:**
- `schools.toml` now reflects reality — 14 real programs, no phantom entries
- 13/14 programs can be scraped immediately
- `data_status` field makes config correctness explicit and auditable
- `/services/sportnames.ashx` documented as a discovery tool for future school onboarding

**Bad:**
- NSU men's data unavailable until Legacy scraper built
- 10 years × 1 school = ~150 games missing from men's dataset
- If SideArm migrates Legacy sites to Nuxt 3, NSU will silently become scrapeable — need to recheck

**Explicitly out of scope:**
- Schools that don't play GAC soccer (ATU, HSU, SOSU, SAU, UAM etc. — removed from config)
- Tracking opponents outside of GAC (see ADR-006)
- Automated discovery pipeline for 300+ schools (future work)
