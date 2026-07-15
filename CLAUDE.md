# CLAUDE.md — PRESTIGE

Project guidance for Claude Code. **Read this entire file before doing any work in this repo.**

**Project name: PRESTIGE** — a Web-Based Digital Library System.

---

## What we're building

A centralised, web-based Digital Library System that replaces manual, paper-based library operations. Members can search a book catalogue, borrow and return books, and track due dates remotely. Administrators manage the book collection, member accounts, and borrowing activity from a single dashboard.

This is a **final-year academic project** — a functional prototype suitable for demonstration and evaluation, not a large-scale commercial deployment.

See `PRESTIGE PRD.md` (product requirements) and `PRESTIGE TRD.md` (technical requirements) for full detail. **These two documents are the single source of truth.** If anything in this file conflicts with the PRD or TRD, the PRD/TRD wins.

---

## ⚠️ CRITICAL GROUND RULE — DO NOT ASSUME, ASK FIRST

**Never assume the user's intent, preference, or decision on anything that is not explicitly stated in the PRD, TRD, or a direct user instruction.**

Before making any design, implementation, or structural decision that is not already covered by the requirements documents, you MUST:

1. **STOP and ASK the user.** Describe what you need to decide, present the options clearly (with a recommendation if you have one), and wait for their answer.
2. **Do not "best-effort" fill gaps.** If a requirement is ambiguous, incomplete, or could be interpreted multiple ways — ask. Do not silently pick one interpretation and move on.
3. **Do not add features, pages, or behaviors not in the PRD/TRD** without asking first. "Nice-to-have" additions must be proposed and approved before implementation.
4. **Do not change the tech stack** (Flask, SQLite, Jinja, plain CSS, Werkzeug) without explicit user approval.
5. **Do not skip steps.** If you're unsure whether to proceed, ask. If you think a step is unnecessary, explain why and ask before skipping it.

Examples of things you MUST ask about (not exhaustive):
- Colour scheme, fonts, visual style, branding for the UI
- How the admin's initial/seed account should be configured (credentials, setup flow)
- Whether the temporary password should be auto-generated or manually entered by admin
- Specific CSS framework preferences (or confirm plain CSS)
- Any hosting/deployment choices
- Loan period configuration (hardcode 14 days vs. make configurable?)
- How overdue flagging should be visually presented to the user
- Flash message wording, error message tone
- Folder/file naming conventions within the project structure

---

## Tech stack (locked — do not change without asking)

| Layer | Technology | Notes |
|---|---|---|
| **Backend** | Python, Flask | Single Flask application, layered architecture |
| **Database** | SQLite | Single file, accessed via Python's `sqlite3` module — no ORM |
| **Frontend** | HTML, CSS, Jinja2 templates | Server-rendered pages, standard form submissions |
| **Auth** | Flask sessions + Werkzeug `generate_password_hash` / `check_password_hash` | Signed-cookie sessions, secret key from environment |
| **Styling** | Single plain CSS file | No frontend build pipeline, no CSS framework unless user approves |
| **Dev server** | Flask built-in dev server | Sufficient for demonstration |

---

## Architecture summary (from TRD)

The system follows a **simple layered architecture** within a single Flask app:

1. **Web/Routing layer** — handles HTTP requests, renders Jinja templates
2. **Business logic layer** — authentication, catalogue search, borrowing/return rules, admin operations
3. **Data access layer** — parameterized SQL queries to SQLite

No separate frontend framework. No REST API layer. All interaction through server-rendered pages and standard form submissions.

---

## Project structure (from TRD)

The TRD specifies this general structure. **Before creating the folder layout, confirm the exact file/folder names with the user.**

- Main application file (route registration)
- Database module (connection + initialisation logic)
- Auth module (authentication + access-control helpers)
- Templates grouped by purpose:
  - Authentication pages (login, password change)
  - Member-facing pages (catalogue, search, loan views)
  - Admin pages (dashboard, book management, member management, transaction reports)
- Single static folder with one CSS file
- SQLite database file (auto-generated on first run)

---

## Data model (from PRD)

Three core entities:

**Users**
- `id`, `student_staff_id` (unique, used as login username), `full_name`, `email` (optional), `department_class` (optional), `password_hash`, `role` (member/admin), `must_change_password` (boolean), `date_created`

**Books**
- `id`, `title`, `author`, `category`, `isbn`, `total_copies`, `available_copies`

**Transactions**
- `id`, `user_id` (FK → Users), `book_id` (FK → Books), `borrow_date`, `due_date`, `return_date` (nullable), `status` (borrowed/returned/overdue)

---

## Business rules (from TRD — follow exactly)

1. **Loan period:** 14 days from borrow date (default). Ask user before making this configurable.
2. **Borrowing:** Only if `available_copies > 0`. Borrowing decrements `available_copies` by 1 and creates a transaction with status `borrowed`.
3. **Returning:** Increments `available_copies` by 1, sets `return_date`, updates status to `returned`.
4. **Overdue detection:** No background scheduler. Check on page load — any `borrowed` transaction past its `due_date` without a `return_date` is reclassified as `overdue` at that moment.
5. **First-login password change:** New accounts flagged `must_change_password = true`. System redirects to password-setup before allowing any other access.
6. **Admin access control:** Enforced on every admin-facing route at the request level, not just in the UI.
7. **Member accounts:** Created only by admin. No public self-registration. Members cannot self-elevate to admin.

---

## Security requirements (from TRD — non-negotiable)

- **Passwords:** Hashed with Werkzeug, never stored plain or reversibly encrypted
- **Session secret:** Loaded from environment variable, never hardcoded
- **SQL queries:** Parameterized statements only — no string-built queries, ever
- **Sessions:** Minimal non-sensitive identifiers in session cookies
- **CSRF:** Every data-modifying form must include CSRF protection
- **Input validation:** All user input validated server-side before database writes (required fields present, identifiers in expected format, copy counts never negative)

---

## Error handling (from TRD)

- **Failed login:** Single generic error message — do not reveal whether a given ID exists
- **No copies available:** Block borrow with clear message, do not create a transaction
- **Unauthorised admin access:** Redirect away, do not expose any admin interface
- **Unexpected errors:** Generic message to user, detailed logging internally

---

## Key user flows (from PRD — these must all work)

1. **Account Provisioning** → Admin creates member (Student/Staff ID, name, temp password) → member receives credentials
2. **First Login** → Member logs in with temp password → forced to set new password → redirected to catalogue
3. **Search & Borrow** → Member searches → selects available book → borrows → due date generated → confirmation
4. **Return** → Member or admin marks book as returned → availability updated → status changed
5. **Overdue Handling** → System checks due dates on page load → flags overdue → visible to admin and member
6. **Admin Management** → Admin logs in → manages books → manages members → views transaction reports

---

## Scope boundaries

### In scope (build these)
- Admin-provisioned member accounts (no public self-registration)
- First-login password setup for new members
- Searchable book catalogue (title, author, category)
- Borrow and return with due-date tracking
- Overdue detection and flagging
- Admin dashboard: add/edit/remove books, add/manage members, view/manage all transactions
- Basic reporting (currently borrowed books, overdue books)

### Out of scope (do NOT build unless user explicitly asks)
- Public self-registration
- E-book hosting/reading or file uploads
- Payment gateway / fine processing
- RFID or barcode hardware integration
- Multi-branch library networks
- Native mobile app

---

## Use skills — invoke them when the situation matches

Skills are specialized workflows. **If a skill applies to the task, use it — this is not optional.** Announce "Using [skill] to [purpose]" and follow it. When multiple apply, process skills (brainstorming, debugging, planning) run first and set the approach; implementation skills (frontend design, output) carry it out.

### Trigger map for this project

| When you're about to... | Invoke |
|---|---|
| Build/design a new feature, page, or component | `brainstorming` FIRST, then plan/implement |
| Turn requirements into a step-by-step implementation plan | `writing-plans` |
| Execute a written plan with review checkpoints | `executing-plans` |
| Implement any route, database function, or template | `test-driven-development` (write the failing test first) |
| Hit a bug, failing test, or unexpected behavior | `systematic-debugging` FIRST, before proposing fixes |
| Build/polish the frontend UI (dashboard, forms, catalogue, member views) | `impeccable` (premium, polished UI design) |
| Generate long/exhaustive code without truncation or placeholders | `output-skill` |
| Finish a feature / before claiming it works | `verification-before-completion` (run it, show evidence) |
| Want the work reviewed before submission | `requesting-code-review` |
| Receive review feedback | `receiving-code-review` |
| Wrap up a branch / decide merge vs PR | `finishing-a-development-branch` |

### Skill rules
- The **skill check comes before** clarifying questions or exploring files — check first, then act.
- Skills evolve; read the current version each time rather than relying on memory.
- User instructions and this CLAUDE.md take precedence over a skill if they ever conflict.
- For UI/frontend work, **`impeccable` is the default skill** — the interface should feel polished and professional, not a raw academic wireframe. This is a demonstration piece.

---

## Step-by-step build order

Follow this sequence. **At each step, confirm with the user before proceeding to the next.**

### Phase 1 — Project setup
1. Confirm the exact folder/file structure with the user
2. Set up the Flask application skeleton (app factory or single module — ask user preference)
3. Create the database initialisation module with the schema from the data model above
4. Create the seed/admin account setup (ask user for preferred admin credentials approach)
5. Verify: app starts, database creates, admin can log in

### Phase 2 — Authentication & user management
6. Implement login route (Student/Staff ID + password)
7. Implement first-login password change flow
8. Implement logout
9. Implement role-based access control decorators/helpers
10. Verify: admin login, member login, forced password change, route protection all work

### Phase 3 — Book catalogue
11. Implement book listing/search page (title, author, category)
12. Implement admin add/edit/remove book routes
13. Verify: books appear, search works, availability shows correctly

### Phase 4 — Borrowing & returns
14. Implement borrow flow (availability check, due date, transaction creation)
15. Implement return flow (availability update, status change)
16. Implement overdue detection (on-page-load check)
17. Implement member's "my loans" view
18. Verify: full borrow/return/overdue cycle works end-to-end

### Phase 5 — Admin dashboard & reports
19. Implement admin dashboard with statistics (total books, members, overdue count)
20. Implement member management (add, view, edit, deactivate)
21. Implement transaction report view (filterable by status)
22. Verify: all admin flows work

### Phase 6 — UI polish & final review
23. Apply `impeccable` skill to polish all templates and CSS
24. Run full end-to-end verification of all user flows
25. Final review against PRD success criteria (Section 12)

---

## Working conventions

- **Ask before acting** on anything ambiguous — this is the single most important rule.
- **No placeholders.** Every template, route, and function should be complete and functional.
- **Keep it simple.** This is a small-scale academic prototype. Favour clarity over cleverness.
- **Server-side rendering only.** No JavaScript frameworks, no AJAX calls, no client-side routing unless the user asks.
- **One CSS file.** All styles in one static stylesheet. Make it clean and well-organised, but don't over-engineer.
- **Parameterized queries everywhere.** No exceptions. No string concatenation for SQL.
- **Test as you go.** Don't build three features and then test — verify each one works before moving on.
- **Comment your code.** Especially database queries, access control checks, and business logic.
- **PROGRESS.md must be kept updated.** After completing any task from the build plan, immediately update `PROGRESS.md` — change the status, add notes, and update the "Last updated" timestamp at the top of the file. Also log any decisions made in the Decisions Log section. This is not optional.
