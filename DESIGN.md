# Design

Visual system for PRESTIGE. References: SHOT 1 (dark-sidebar + pastel stat-card dashboard) for the app shell, SHOT 2 (split-screen login) for auth using SHOT 3 as the login artwork. Accent: emerald/teal.

## Theme
Light app content on a cool off-white, anchored by a near-black left sidebar (SHOT 1). Auth is a full-bleed split screen: illustration left, form right (SHOT 2). Restrained by default; the dashboard stat cards are the one Committed, playful moment (pastels).

## Color (OKLCH)
Tokens live in `static/style.css` `:root`.
- `--bg` `oklch(0.985 0.004 220)` — app background
- `--surface` `#fff` — cards, tables, forms
- `--sidebar` `oklch(0.23 0.012 250)` — dark sidebar
- `--sidebar-ink` `oklch(0.82 0.01 250)` / active `#fff`
- `--ink` `oklch(0.27 0.02 255)` — primary text (AA on surface)
- `--muted` `oklch(0.52 0.02 255)` — secondary text (AA on surface)
- `--border` `oklch(0.92 0.005 250)`
- `--accent` `oklch(0.60 0.09 195)` (teal) / `--accent-strong` `oklch(0.52 0.10 195)` for hover; white text passes AA
- Pastel stat cards: yellow `oklch(0.92 0.09 95)`, pink `oklch(0.89 0.06 350)`, green `oklch(0.90 0.06 155)`, blue `oklch(0.90 0.05 240)`; text always `--ink`
- Semantic: success/green, info/teal-blue, warn+danger/amber+red — used for badges and flash

## Typography
One family: **Inter** (Google Fonts) with `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` fallback for offline. Fixed rem scale (product register), ratio ~1.2. Weights 400/500/600/700. Wordmark PRESTIGE at 600, letter-spacing 0.14em.

## Components
- Buttons: `.btn` (primary=teal, secondary=outline, danger=red, small variant). All have hover/focus/active/disabled.
- Badges: pill, tinted bg + darker same-hue text (available, borrowed, returned, overdue, active/inactive, temporary/set).
- Cards: `.stat-card` (pastel), `.book-card` (catalogue), `.panel` (forms/sections). No nested cards.
- Data tables: `.data-table` — sticky-feeling header, zebra-free, row hover, rounded container.
- Forms: `.form-group` stacked label+input; `<details>` disclosure for add/edit.
- Flash: `.flash` info/success/error.

## Layout
- App shell: fixed 248px sidebar + fluid main (topbar + content). Sidebar collapses to a top bar under 900px.
- Auth: 2-col grid (image | form); collapses to form-only under 820px.
- Catalogue: `repeat(auto-fill, minmax(260px, 1fr))` book-card grid.

## Motion
150–250ms ease-out. Content fade/slide-in on load, card & button hover lifts, sidebar active indicator. Everything gated by `prefers-reduced-motion: reduce`.
