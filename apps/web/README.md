# Ed Insights Web App

Next.js 14 web application for the Ed Insights higher education athletics analytics platform.

Migrated from [ed-insights-ai/edinsights-sports-ui](https://github.com/ed-insights-ai/edinsights-sports-ui), which remains as a legacy reference repo (read-only).

## Setup

```bash
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Routes

| Route | Description |
|-------|-------------|
| `/` | Landing page |
| `/about` | About page |
| `/login` | Sign in (Supabase auth) |
| `/signup` | Sign up |
| `/dashboard` | Authenticated dashboard (protected) |

## Auth

- **Sign Up** at `/signup` with email and password
- **Sign In** at `/login`
- **Dashboard** at `/dashboard` is protected — unauthenticated users are redirected to `/login`
- **Sign Out** via the user menu in the header

Local Supabase auto-confirms emails by default, so sign-up works immediately without email verification.

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS v3 with custom brand colors
- **Components**: shadcn/ui (Button, Card, Input, Label, Navigation Menu, Sheet, Toast, Avatar, Dropdown Menu)
- **Icons**: Lucide React
- **Auth**: Supabase Auth via `@supabase/ssr`
- **Validation**: Zod + React Hook Form

## Project Structure

```
src/
├── app/
│   ├── about/page.tsx        # About page
│   ├── dashboard/page.tsx    # Dashboard page (protected)
│   ├── login/
│   │   ├── actions.ts        # Server action for sign in
│   │   └── page.tsx          # Sign in page with validation
│   ├── signup/
│   │   ├── actions.ts        # Server action for sign up
│   │   └── page.tsx          # Sign up page with validation
│   ├── globals.css           # Global styles with CSS variables
│   ├── layout.tsx            # Root layout with Header & Footer
│   ├── not-found.tsx         # Custom 404 page
│   └── page.tsx              # Home page
├── components/
│   ├── ui/                   # shadcn/ui components
│   ├── Header.tsx            # Auth-aware header with user menu
│   └── Footer.tsx            # Site footer
├── lib/
│   ├── supabase/
│   │   ├── client.ts         # Browser Supabase client
│   │   └── server.ts         # Server Supabase client
│   └── utils.ts              # Utility functions (cn)
├── middleware.ts              # Auth middleware (protects /dashboard)
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase API URL | `http://127.0.0.1:54321` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anonymous key | Local dev key |

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint
