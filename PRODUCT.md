# Product

## Register

product

## Users
Two roles at a small institution (school / department library):
- **Members** (students/staff) — provisioned by an admin, not self-registered. They log in, search the catalogue, borrow and return books, and track due dates. Often low digital literacy; the interface must be obvious and forgiving.
- **Administrator** — seeded at setup. Manages books, member accounts, and all borrowing activity from a single dashboard.

## Product Purpose
PRESTIGE replaces manual, paper-based library operations with a centralised web system: searchable catalogue, automated borrow/return with 14-day due dates, on-page-load overdue flagging, and an admin dashboard. It is a final-year academic prototype for demonstration — clarity and reliability over feature breadth. Success = an admin can provision a member, that member can log in (forced password change), search, borrow (availability updates), and overdue items flag automatically.

## Brand Personality
Trustworthy, calm, institutional-but-friendly. Three words: **credible, clear, approachable.** It should feel like a well-run modern library — not a sterile enterprise tool, not a toy.

## Anti-references
- Generic bootstrap admin template (flat gray tables, no identity).
- Overloaded enterprise ILS with hundreds of controls.
- Anything that hides the primary action (borrow / return) behind chrome.

## Design Principles
- **The task disappears into the tool.** Borrow, return, search are one obvious click.
- **State is always legible.** Availability, due dates, and overdue status are unmistakable at a glance (color + text, never color alone).
- **Earned familiarity.** Standard nav, standard tables, standard forms — no invented affordances.
- **Forgiving for low digital literacy.** Big targets, clear labels, plain-language errors.

## Accessibility & Inclusion
- WCAG AA contrast on all text and controls; status conveyed by text/icon plus color (color-blind safe).
- Full keyboard operability; visible focus rings.
- `prefers-reduced-motion` respected on every animation.
- Must run acceptably on modest hardware and flaky connectivity (no heavy assets required for core flows).
