# Product Beads Document: EDInsights.AI Platform

## Goal
Build the next-generation EDInsights.AI website as a Next.js 14 application with
Supabase authentication (local Docker), marketing landing pages adapted from the
existing site, and a protected dashboard shell — serving as both the company's
public face and the entry point to a future sports analytics data platform.

## Scope
- **In scope**:
  - Next.js 14 App Router project with TypeScript, Tailwind CSS, shadcn/ui
  - Local Supabase setup (Docker) with auth (sign up, login, logout)
  - Public marketing pages: Home (landing), About
  - Protected dashboard shell behind auth
  - Public teaser soccer stats/visualizations on the landing page
  - Responsive design, dark mode support
  - Docker Compose setup: Next.js + local Supabase, `docker compose up` runs everything

- **Out of scope**:
  - Full data platform / analytics dashboard functionality
  - AI chat interface (future work)
  - Payment/billing integration
  - Real data ingestion pipeline
  - Mobile app
  - Opportunities/internship page (outdated, not relevant to new direction)
  - Production Supabase cloud deployment
  - Hosting/deployment to Vercel or any cloud provider

## Codebase Context
- **Current repo state**: Empty — just a README.md
- **Reference site**: `ed-insights-ai/edinsights-web` (Vite + React SPA)
  - 4 pages: Index, About, Opportunities, NotFound
  - 7 custom components: Header, Footer, SectionHeading, ValueCard, TechItem, AnimatedDataBackground, DataDots
  - 48 shadcn/ui components, lucide-react icons, Tailwind CSS
  - Color scheme: primary blue (#1a365d), secondary teal, accent orange, highlight
  - Sports analytics theme throughout
- **Target stack**: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, Supabase (local Docker), Recharts, TanStack Query
- **Naming conventions**: PascalCase components, kebab-case routes, `@/` path aliases
- **Deploy target**: Local Docker Compose only (no cloud hosting)
- **Runtime**: `docker compose up` starts Next.js + Supabase together

## Retro Lessons Applied
No prior retros — this is the first cycle.

## Workflow
- **Landing strategy**: PR-per-bead (merge request strategy in Gas Town)
- **Review approach**: Human review of each PR before merge

## Dependency Graph

```
Bead 1 (Next.js scaffolding + shadcn + Tailwind)
  ├── Bead 2 (Supabase local auth setup)
  │     └── Bead 4 (Protected dashboard shell)
  │           └── Bead 6 (Teaser stats on landing page)
  └── Bead 3 (Public pages: landing + about)
        └── Bead 5 (Visual polish + animations)
              └── Bead 6 (Teaser stats on landing page)
```

## Parallel Lanes
- **Lane A** (Auth): Bead 2 → Bead 4
- **Lane B** (Content): Bead 3 → Bead 5
- **Merge point**: Bead 6 (depends on Bead 4 + Bead 5)

## Beads

### Bead 1: Next.js 14 project scaffolding with Tailwind, shadcn/ui, and Docker
- **Type**: task | **Priority**: 1 | **Effort**: L
- **Description**: Initialize a Next.js 14 App Router project using `npx create-next-app@14` to pin the version. Install and configure Tailwind CSS v3 with a custom color theme matching the EDInsights brand (primary: #1a365d dark blue, secondary: teal, accent: orange). Initialize shadcn/ui and add core components (button, card, input, label, navigation-menu, sheet, toast, avatar, dropdown-menu). Install lucide-react for icons. Set up the `@/` path alias. Create the app layout with a placeholder Header component (logo + nav links: Home, About, Sign In) and Footer component (copyright, social links). Create route stubs for `/` (home), `/about`, `/login`, `/signup`, `/dashboard`, and a catch-all `not-found.tsx` for 404s. Each route should render a minimal placeholder. Create a `Dockerfile` for the Next.js app and a `docker-compose.yml` that runs the app in development mode with hot reload (volume mount `./src`). Update `README.md` with setup instructions: prerequisites (Node 18+, Docker), `npm install`, `npm run dev`, `docker compose up`. The app must start with both `npm run dev` (local) and `docker compose up` (containerized).
- **Inputs**: Empty repo with README.md
- **Outputs**:
  - `package.json` with Next.js 14 (pinned), TypeScript, Tailwind, shadcn/ui, lucide-react
  - `tailwind.config.ts` with EDInsights color theme
  - `src/app/layout.tsx` with Header and Footer
  - `src/components/Header.tsx`, `src/components/Footer.tsx`
  - Route stubs: `src/app/page.tsx`, `src/app/about/page.tsx`, `src/app/login/page.tsx`, `src/app/signup/page.tsx`, `src/app/dashboard/page.tsx`, `src/app/not-found.tsx`
  - `components.json` (shadcn config)
  - `Dockerfile` for Next.js dev
  - `docker-compose.yml` with Next.js service
  - `README.md` with setup instructions
- **Acceptance**: `npm run dev` starts without errors. `docker compose up` starts the app in a container with hot reload. All 5 routes plus 404 render. Navigation links work. Tailwind classes apply correctly. Header and Footer appear on every page.
- **Dependencies**: none

### Bead 2: Supabase local auth with sign up, login, and protected routes
- **Type**: feature | **Priority**: 1 | **Effort**: L
- **Description**: Set up local Supabase using `supabase init` and `supabase start` (runs alongside the Docker Compose Next.js app). Document in README that the developer runs `supabase start` first, then `docker compose up` (or `npm run dev`). Install `@supabase/supabase-js` and `@supabase/ssr`. Create a Supabase client helper at `src/lib/supabase/client.ts` (browser) and `src/lib/supabase/server.ts` (server component). Build a `/login` page with email/password form using shadcn/ui form components and react-hook-form with zod validation. Build a `/signup` page with email/password/confirm-password form. Implement auth state management — on successful login redirect to `/dashboard`, on logout redirect to `/`. Create a Next.js middleware at `src/middleware.ts` that protects `/dashboard` routes (redirect unauthenticated users to `/login`). Add a user avatar/dropdown in the Header that shows Sign In when logged out, and email + Sign Out when logged in. Store Supabase connection env vars in `.env.local` (pointing to local Docker instance, typically `http://127.0.0.1:54321`).
- **Inputs**: Working Next.js project from Bead 1 with Header, routes, and shadcn/ui components
- **Outputs**:
  - `supabase/` directory with config and migrations
  - `src/lib/supabase/client.ts`, `src/lib/supabase/server.ts`
  - `src/app/login/page.tsx` — login form with validation
  - `src/app/signup/page.tsx` — signup form with validation
  - `src/middleware.ts` — route protection
  - Updated `Header.tsx` with auth-aware user menu
  - `.env.local` with local Supabase credentials
  - `.env.example` documenting required vars
- **Acceptance**: Auth forms render correctly with validation errors on invalid input. Supabase client code compiles without errors. Middleware redirects are configured (unauthenticated `/dashboard` access redirects to `/login`). When Supabase is running: user can sign up, log in (redirected to `/dashboard`), and sign out (returns to `/`). Header shows correct auth state. `.env.example` documents all required vars.
- **Dependencies**: blocks: Bead 1

### Bead 3: Public landing page and about page with EDInsights content
- **Type**: feature | **Priority**: 1 | **Effort**: L
- **Description**: Build the public home page at `src/app/page.tsx` adapted from the reference site's design. Hero section with "Empowered Data / AI Insights / Real Results" headline, subtitle about sports analytics, and two CTA buttons ("Get Started" linking to `/signup`, "Learn More" linking to `/about`). Below the hero: a "Where Data Science Meets Athletic Performance" section with 3 ValueCard components (Enhanced Performance 37%, Strategic Advantage 86%, Complete Dashboard 12K+) using lucide-react icons (BarChart, LineChart, LayoutDashboard). Below that: a "Cutting-Edge Technology" section on dark background with two columns — left showing bullet points (Python & AI, Machine Learning, Pattern Detection), right showing numbered steps (Data Collection, AI Processing, Actionable Insights). Build the About page at `src/app/about/page.tsx` with mission statement, core values cards (Data-Driven Excellence, Innovation, Accessibility), and a 3-step approach section (Data Collection & Cleaning, Advanced AI Processing, Actionable Insights Delivery). Create reusable components: `SectionHeading.tsx`, `ValueCard.tsx`. Use consistent Tailwind styling matching the EDInsights brand colors. Both pages use the shared layout Header and Footer.
- **Inputs**: Working Next.js project from Bead 1 with Header, Footer, Tailwind theme, shadcn/ui
- **Outputs**:
  - `src/app/page.tsx` — full landing page with hero, vision, and technology sections
  - `src/app/about/page.tsx` — full about page with mission, values, and approach
  - `src/components/SectionHeading.tsx`
  - `src/components/ValueCard.tsx`
- **Acceptance**: Home page renders all 3 sections with correct content and styling. About page renders mission, values, and approach sections. Both are responsive (mobile stacked, desktop side-by-side/grid). CTA buttons navigate correctly. Brand colors are consistent.
- **Dependencies**: blocks: Bead 1

### Bead 4: Protected dashboard shell with sidebar navigation
- **Type**: feature | **Priority**: 2 | **Effort**: M
- **Description**: Create a dashboard layout at `src/app/dashboard/layout.tsx` that wraps all `/dashboard/*` routes. Use the Supabase server client from `src/lib/supabase/server.ts` to fetch the authenticated user in the layout. The layout includes a collapsible sidebar (using shadcn/ui sheet or a custom sidebar component) with navigation items: Overview, Teams, Players, Analytics, Settings. Each nav item has a lucide-react icon. The sidebar collapses to icons-only on smaller screens. The main content area shows a top bar with page title and user avatar/menu. Create placeholder pages: `src/app/dashboard/page.tsx` (Overview — welcome message with user's email), `src/app/dashboard/teams/page.tsx`, `src/app/dashboard/players/page.tsx`, `src/app/dashboard/analytics/page.tsx`. Each placeholder shows the page name and a "Coming Soon" card. The dashboard layout should feel like a real analytics app — clean, professional, with the EDInsights brand colors. The sidebar active state should highlight the current route.
- **Inputs**: Auth system from Bead 2 (protected routes, user session), shadcn/ui components
- **Outputs**:
  - `src/app/dashboard/layout.tsx` — dashboard shell with sidebar
  - `src/components/DashboardSidebar.tsx`
  - `src/components/DashboardTopbar.tsx`
  - `src/app/dashboard/page.tsx` — overview with welcome message
  - `src/app/dashboard/teams/page.tsx` — placeholder
  - `src/app/dashboard/players/page.tsx` — placeholder
  - `src/app/dashboard/analytics/page.tsx` — placeholder
- **Acceptance**: Authenticated users see the sidebar navigation. All 4 dashboard routes render with correct active state in sidebar. Sidebar collapses on mobile. User email displayed in overview. Unauthenticated users still redirected to login.
- **Dependencies**: blocks: Bead 2

### Bead 5: Visual polish — animations, backgrounds, and responsive refinement
- **Type**: task | **Priority**: 3 | **Effort**: M
- **Description**: Add visual polish to the public pages. Create an `AnimatedDataBackground.tsx` component — a subtle animated gradient or CSS-based particle effect for use behind the hero section. Create a `DataDots.tsx` component — floating dot pattern overlay using CSS animations (no heavy JS libraries). Add fade-in-up animations on scroll for the hero text, value cards, and technology section using CSS `@keyframes` and Tailwind's `animate-` utilities. Add smooth hover transitions on all buttons and cards (scale, shadow, color shifts). Add a gradient color bar at the top of ValueCard and other card components. Add a subtle grid pattern overlay on the vision section background. Ensure all animations use CSS transforms (not layout properties) for performance. Review and fix any responsive issues across mobile (375px), tablet (768px), and desktop (1280px+). Add dark mode support using Tailwind's `dark:` variants on the landing and about pages.
- **Inputs**: Completed public pages from Bead 3 with all sections and components
- **Outputs**:
  - `src/components/AnimatedDataBackground.tsx`
  - `src/components/DataDots.tsx`
  - Updated `src/app/page.tsx` with animation classes and background components
  - Updated `src/app/about/page.tsx` with animation classes
  - Updated `tailwind.config.ts` with custom animation keyframes
  - Updated component styles with hover transitions and dark mode
- **Acceptance**: Hero section has visible animated background. Cards animate in on page load. Buttons and cards have smooth hover effects. No layout shift from animations. Pages look correct at 375px, 768px, and 1280px widths. Dark mode responds to system preference via Tailwind `darkMode: 'media'` (no toggle required — keep it simple for now).
- **Dependencies**: blocks: Bead 3

### Bead 6: Public teaser stats with Recharts visualizations
- **Type**: feature | **Priority**: 2 | **Effort**: L
- **Description**: Add a "Platform Preview" section to the home page between the Vision and Technology sections. This section shows sample NCAA D2 soccer statistics as a teaser for what authenticated users will access. Create a `StatsPreview.tsx` component that displays: (1) A Recharts bar chart showing "Top 5 Teams by Goals Scored" with mock data for 5 NCAA D2 soccer teams, (2) A Recharts line chart showing "Season Performance Trend" with mock data across 10 match weeks, (3) A stats summary row with 4 stat cards: Total Teams (200+), Players Tracked (5,000+), Matches Analyzed (1,500+), Seasons of Data (3). Below the charts, add a CTA: "Sign up to explore the full dataset" linking to `/signup`. Install `recharts` as a dependency. Use the EDInsights brand colors for chart fills and strokes. The charts should be responsive (full width on mobile, side-by-side on desktop). Add a blurred overlay or fade-out effect at the bottom of the charts to suggest there's more behind the login wall. Also add a simple stats card to the dashboard overview page (`/dashboard`) showing the same 4 summary stats, proving the authenticated experience has real content.
- **Inputs**: Public pages from Bead 3/5 (home page with sections), dashboard shell from Bead 4
- **Outputs**:
  - `src/components/StatsPreview.tsx` — chart section with mock data
  - `src/lib/mock-data.ts` — mock NCAA D2 soccer statistics
  - Updated `src/app/page.tsx` with StatsPreview section
  - Updated `src/app/dashboard/page.tsx` with summary stats cards
  - `recharts` added to package.json
- **Acceptance**: Home page shows 2 charts with mock soccer data and 4 stat cards. Charts are responsive. Blurred/faded overlay creates teaser effect. CTA links to signup. Dashboard overview shows summary stats. Charts render without console errors.
- **Dependencies**: blocks: Bead 4, blocks: Bead 5

## Risks and Ambiguity
- **Docker requirement**: Local Supabase requires Docker. If the polecat's environment doesn't have Docker, Bead 2 will need adjustment (could mock auth instead).
- **Next.js 14 vs 15**: The plan says 14 but 15 may be latest by now. The polecat might default to latest — descriptions should specify 14 if that's the target.
- **shadcn/ui + Next.js App Router**: Some shadcn components need "use client" directive. Beads should mention this where relevant.
- **Recharts SSR**: Recharts needs client-side rendering in Next.js. Bead 6 should use dynamic imports or "use client".

## bd Commands (Ready to Execute)

```bash
# Bead 1: Next.js 14 project scaffolding with Tailwind, shadcn/ui, and Docker
bd create "Next.js 14 project scaffolding with Tailwind, shadcn/ui, and Docker" \
  --description="Initialize Next.js 14 App Router using npx create-next-app@14 with TypeScript. Install Tailwind CSS v3 with custom EDInsights brand colors (primary: #1a365d, secondary: teal, accent: orange). Initialize shadcn/ui, add core components (button, card, input, label, navigation-menu, sheet, toast, avatar, dropdown-menu). Install lucide-react. Set up @/ path alias. Create app layout with Header (logo + nav: Home, About, Sign In) and Footer (copyright, links). Create route stubs for /, /about, /login, /signup, /dashboard plus not-found.tsx for 404. Create Dockerfile for Next.js dev and docker-compose.yml with hot reload via volume mount. Update README.md with setup instructions (prerequisites, npm install, npm run dev, docker compose up). Outputs: package.json (Next.js 14 pinned), tailwind.config.ts, layout.tsx, Header.tsx, Footer.tsx, 6 route pages, Dockerfile, docker-compose.yml, README.md. Acceptance: npm run dev and docker compose up both start clean, all routes + 404 render, nav works, Tailwind applies, Header/Footer on every page." \
  -t task -p 1 --json

# Bead 2: Supabase local auth with sign up, login, and protected routes
bd create "Supabase local auth with sign up, login, and protected routes" \
  --description="Set up local Supabase using supabase init + supabase start (runs alongside Docker Compose Next.js app). Document in README: run supabase start first, then docker compose up or npm run dev. Install @supabase/supabase-js and @supabase/ssr. Create client helpers at src/lib/supabase/client.ts (browser) and src/lib/supabase/server.ts (server). Build /login page with email/password form using shadcn form + react-hook-form + zod validation. Build /signup page with email/password/confirm. Implement middleware at src/middleware.ts protecting /dashboard routes. Add auth-aware user menu in Header (Sign In when logged out, email + Sign Out when logged in). Store env vars in .env.local pointing to local Docker (127.0.0.1:54321). Outputs: supabase/ dir, src/lib/supabase/*.ts, login + signup pages, middleware.ts, updated Header, .env.local + .env.example, updated README. Acceptance: Auth forms render with validation, Supabase client compiles, middleware configured, .env.example documents all vars. With Supabase running: signup, login, redirect, signout all work." \
  -t feature -p 1 --json
# bd dep add <bead-2-id> <bead-1-id>

# Bead 3: Public landing page and about page with EDInsights content
bd create "Public landing page and about page with EDInsights content" \
  --description="Build home page at src/app/page.tsx adapted from reference site. Hero section: 'Empowered Data / AI Insights / Real Results' headline, sports analytics subtitle, CTAs to /signup and /about. Vision section: 3 ValueCard components (Enhanced Performance 37%, Strategic Advantage 86%, Complete Dashboard 12K+) with lucide-react icons. Technology section: dark bg, two columns — left with bullet points (Python & AI, ML, Pattern Detection), right with numbered steps (Collection, Processing, Insights). Build About page at src/app/about/page.tsx: mission statement, 3 core values cards, 3-step approach section. Create reusable SectionHeading.tsx and ValueCard.tsx. Use EDInsights brand colors consistently. Outputs: src/app/page.tsx, src/app/about/page.tsx, SectionHeading.tsx, ValueCard.tsx. Acceptance: Home shows all 3 sections, About shows mission/values/approach, responsive layout, CTAs navigate correctly, brand colors consistent." \
  -t feature -p 1 --json
# bd dep add <bead-3-id> <bead-1-id>

# Bead 4: Protected dashboard shell with sidebar navigation
bd create "Protected dashboard shell with sidebar navigation" \
  --description="Create dashboard layout at src/app/dashboard/layout.tsx wrapping all /dashboard/* routes. Use Supabase server client from src/lib/supabase/server.ts to fetch authenticated user in layout. Collapsible sidebar with nav items: Overview, Teams, Players, Analytics, Settings — each with lucide-react icon. Sidebar collapses to icons-only on small screens. Main area has top bar with page title and user avatar/menu. Create placeholder pages: /dashboard (Overview with welcome + user email), /dashboard/teams, /dashboard/players, /dashboard/analytics — each showing page name and 'Coming Soon' card. Use shadcn/ui components. Active route highlighted in sidebar. Professional analytics app feel with EDInsights brand colors. Outputs: dashboard/layout.tsx, DashboardSidebar.tsx, DashboardTopbar.tsx, 4 dashboard route pages. Acceptance: Authed users see sidebar nav, all 4 routes render with active state, sidebar collapses on mobile, user email in overview, unauthed still redirected." \
  -t feature -p 2 --json
# bd dep add <bead-4-id> <bead-2-id>

# Bead 5: Visual polish — animations, backgrounds, and responsive refinement
bd create "Visual polish with animations, backgrounds, and dark mode" \
  --description="Add visual polish to public pages. Create AnimatedDataBackground.tsx — subtle CSS animated gradient for hero section. Create DataDots.tsx — floating dot pattern using CSS @keyframes (no heavy JS). Add fade-in-up animations on scroll for hero text, value cards, technology section using Tailwind animate- utilities and custom keyframes in tailwind.config.ts. Smooth hover transitions on buttons and cards (scale, shadow, color). Gradient color bar on card tops. Grid pattern overlay on vision section. All animations use CSS transforms for performance. Fix responsive issues at 375px, 768px, 1280px+. Add dark mode via Tailwind darkMode: media — responds to system preference, no toggle needed. Apply dark: variants on landing and about pages. Outputs: AnimatedDataBackground.tsx, DataDots.tsx, updated page.tsx + about/page.tsx, updated tailwind.config.ts. Acceptance: Hero has animated bg, cards animate in, hover effects smooth, no layout shift, correct at 3 breakpoints, dark mode responds to system preference." \
  -t task -p 3 --json
# bd dep add <bead-5-id> <bead-3-id>

# Bead 6: Public teaser stats with Recharts visualizations
bd create "Public teaser stats with Recharts NCAA D2 soccer visualizations" \
  --description="Add 'Platform Preview' section to home page between Vision and Technology sections. Create StatsPreview.tsx showing mock NCAA D2 soccer data: (1) Recharts bar chart 'Top 5 Teams by Goals Scored' with 5 mock teams, (2) Recharts line chart 'Season Performance Trend' across 10 match weeks, (3) Stats summary row: Total Teams 200+, Players Tracked 5000+, Matches Analyzed 1500+, Seasons of Data 3. Install recharts. Use brand colors for chart fills/strokes. Charts responsive (stacked mobile, side-by-side desktop). Add blurred overlay/fade at chart bottom as teaser. CTA: 'Sign up to explore the full dataset' -> /signup. Also add summary stats cards to dashboard overview page. Create mock data file at src/lib/mock-data.ts. Use 'use client' directive for chart components (Recharts needs client rendering in Next.js). Outputs: StatsPreview.tsx, mock-data.ts, updated page.tsx, updated dashboard/page.tsx, recharts in package.json. Acceptance: Home shows 2 charts + 4 stat cards, charts responsive, teaser blur effect visible, CTA works, dashboard overview has stats, no console errors." \
  -t feature -p 2 --json
# bd dep add <bead-6-id> <bead-4-id>
# bd dep add <bead-6-id> <bead-5-id>
```
