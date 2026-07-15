# PROGRESS.md — PRESTIGE

**Last updated:** 2026-07-14 15:05 UTC+1

Status legend: `[ ]` Pending  `[~]` In progress  `[x]` Done

---

## Phase 1 — Project Setup

| # | Task | Status | Notes |
|---|---|---|---|
| 1.1 | Confirm folder/file structure with user | [x] | Single-module app.py, templates grouped by role, one static/style.css, .env config |
| 1.2 | Set up Flask application skeleton | [x] | app.py with all routes registered, auth decorators, error handler |
| 1.3 | Create database initialisation module with schema | [x] | db.py with users/books/transactions tables, all CRUD queries |
| 1.4 | Create seed/admin account setup | [x] | Admin seeded from .env (ADMIN_ID, ADMIN_PASSWORD), must_change_password=0 |
| 1.5 | Verify: app starts, DB creates, admin can log in | [x] | Flask starts on :5000, login page 200, admin login redirects to /admin |

## Phase 2 — Authentication & User Management

| # | Task | Status | Notes |
|---|---|---|---|
| 2.1 | Implement login route (Student/Staff ID + password) | [x] | Generic error message, session-based, parameterized lookup |
| 2.2 | Implement first-login password change flow | [x] | Forced redirect to /change-password when must_change_password=1 |
| 2.3 | Implement logout | [x] | session.clear() → redirect to login |
| 2.4 | Implement role-based access control decorators/helpers | [x] | @login_required + @admin_required + @csrf_protect decorators |
| 2.5 | Verify: admin login, member login, forced password change, route protection | [x] | CSRF on all forms, member blocked from /admin (→ /login), member accesses catalogue ✓ |

## Phase 3 — Book Catalogue

| # | Task | Status | Notes |
|---|---|---|---|
| 3.1 | Implement book listing/search page (title, author, category) | [x] | /catalogue with search bar, LIKE on title/author/category |
| 3.2 | Implement admin add/edit/remove book routes | [x] | /admin/books with inline edit, add form, remove with confirm |
| 3.3 | Verify: books appear, search works, availability shows correctly | [x] | 5 books seeded, search filters correctly, edit/remove verified |

## Phase 4 — Borrowing & Returns

| # | Task | Status | Notes |
|---|---|---|---|
| 4.1 | Implement borrow flow (availability check, due date, transaction) | [x] | Decrements available_copies, creates txn with 14-day due date |
| 4.2 | Implement return flow (availability update, status change) | [x] | Restores available_copies, sets return_date + status |
| 4.3 | Implement overdue detection (on-page-load check) | [x] | mark_overdue_transactions() called on relevant pages |
| 4.4 | Implement member's "my loans" view | [x] | /my-loans shows all transactions with status badges |
| 4.5 | Verify: full borrow/return/overdue cycle works end-to-end | [x] | Borrow→decrement, return→restore, overdue→reclassify all verified |

## Phase 5 — Admin Dashboard & Reports

| # | Task | Status | Notes |
|---|---|---|---|
| 5.1 | Implement admin dashboard with statistics | [x] | /admin shows total books, members, borrowed, overdue counts |
| 5.2 | Implement member management (add, view, edit, deactivate) | [x] | /admin/members with add/edit forms, toggle active/inactive |
| 5.3 | Implement transaction report view (filterable by status) | [x] | /admin/transactions filterable by borrowed/returned/overdue |
| 5.4 | Verify: all admin flows work | [x] | Stats, edit, toggle active, transaction filter all verified |

## Phase 6 — UI Polish & Final Review

| # | Task | Status | Notes |
|---|---|---|---|
| 6.1 | Apply `impeccable` skill to polish all templates and CSS | [x] | Full redesign: SHOT 2 split-screen auth (SHOT 3 artwork), SHOT 1 dark-sidebar + pastel-card app shell, teal accent. New style.css (OKLCH tokens), base.html app shell, auth_base.html split-screen, all pages rebuilt. PRODUCT.md + DESIGN.md written. |
| 6.2 | Run full end-to-end verification of all user flows | [x] | Browser click-through PASS: admin provisions member → member first-login forced password change → catalogue → borrow (Clean Code 3→2, 14-day due) → my-loans shows Borrowed → return (status Returned, avail 2→3) → overdue backdate reclassifies to Overdue on page load (member my-loans + admin dashboard count + admin transactions filter all show Overdue). Test data cleaned up. |
| 6.3 | Final review against PRD success criteria (Section 12) | [ ] | |

---

## Decisions Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-07-14 | Project renamed from "HAWK PRO" to "PRESTIGE" | User preference |
| 2026-07-14 | CSRF via session tokens + custom decorator | Per TRD requirement; avoids Flask-WTF dependency; `secrets.token_hex(32)` per form
| 2026-07-14 | UI direction: SHOT 2 auth + SHOT 1 app, pastel stat cards, teal accent, SHOT 3 login image | User-selected via clarifying questions |
| 2026-07-14 | Bug fix: `load_dotenv()` added to app.py | `python app.py` crashed (SESSION_SECRET unset) because .env was only auto-loaded by `flask run`, not direct execution |
| 2026-07-14 | Bug fix: manage_books edit form had malformed nesting (`</details>` closed before `</form>`) | Rewrote as a floating `.inline-edit` popover with correct tag nesting |
| 2026-07-14 | Fonts: Inter via Google Fonts with system-ui fallback | Matches SHOT geometric sans; degrades gracefully offline per portability requirement |
| 2026-07-14 | Added in-app overdue badge on sidebar Transactions link (admin) | User-requested; passive alternative to email alerts (out of scope). Context processor + db.get_overdue_count() |
| 2026-07-14 | Added admin Account page (`/account`) beyond base PRD | User-requested: click sidebar chip → edit own profile + password; super admin also gets configurable loan period (settings table) and admin management (create/remove admins). Seeded `admin` = super admin (protected, promoted on migrate). New `is_super_admin` column + `settings` table. Super-admin-only actions gated by DB record, not just session. |
| 2026-07-14 | Added static/app.js (small vanilla JS, no framework) | User-requested password show/hide toggles + live match checker (native setCustomValidity blocks mismatched submit). Also powers inline edit rows. First client-side JS in project; kept minimal per SSR constraint. |
| 2026-07-14 | Bug fix: admin edit popover was clipped by table overflow | Members/books "Edit" used an absolutely-positioned popover inside `.table-wrap { overflow:hidden }`, so it was cut off (esp. short tables). Replaced with an inline expanding full-width edit `<tr>` toggled by app.js — no clipping, works on mobile. Removed dead `.inline-edit`/`.inline-details` CSS. |
| 2026-07-14 | Added admin "Reset password" for members | User-requested; only recovery path since there's no email/self-service reset. Admin types a new temp password (min 6) → member forced to change on next login (must_change_password=1). db.reset_member_password(); action=reset_password in manage_members; inline reset row per member. |
| 2026-07-14 | Added super-admin "Reset password" for other admins | Same temp-password flow on the Account → Administrators table; super admins are protected, self uses Security panel. db.reset_admin_password() guards role='admin' AND is_super_admin=0; action=reset_admin. |
| 2026-07-14 | Added collapsible sidebar (desktop) | User-requested. Toggle button collapses sidebar to a 76px icon-only rail; state persisted in localStorage (inline head script applies it pre-paint to avoid FOUC). Labels wrapped in .nav-label + title tooltips; overdue badge becomes a dot when collapsed. Only on ≥901px (≤900px already collapses to a top bar). |
| 2026-07-15 | Return now requires admin confirmation (guardrail) | User-requested. Member "Return" = a *request* (new transactions.return_requested flag); availability NOT restored and status not changed until an admin confirms. Admin's own Return stays immediate. Member can cancel a pending request. NOTE: this refines PRD FR14 ("member or admin can mark returned") — member marking is now a request, admin confirms. New routes: request_return, cancel_return; db.request_return/cancel_return_request; return_book() clears the flag. Transactions page gets a "Return requested" filter + "Confirm return" button; dashboard "Pending Returns" card; sidebar badge switched from overdue → pending-returns count. |

## Issues / Blockers

| # | Description | Status |
|---|---|---|
| | | |
