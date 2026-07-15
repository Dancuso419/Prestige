TECHNICAL REQUIREMENTS DOCUMENT (TRD) 

**Project: Web-Based Digital Library System**

**1\. Purpose**

This document translates the PRD into concrete technical specifications, describing the architecture, data requirements, business rules, routes, and security approach needed to build the system using Flask and SQLite, with development assisted by Claude Code.

**2\. System Architecture**

The system follows a simple layered architecture within a single Flask application. Requests originate from the client's browser and reach the web application layer, which handles routing and renders server-side templates. Beneath this sits the business logic layer, responsible for authentication, catalogue search, borrowing/return rules, and admin operations. This layer communicates with a data access layer that issues parameterized queries to the underlying SQLite database, where all records for users, books, and transactions are stored.

No separate frontend framework or REST API layer is used for this version — all interaction happens through server-rendered pages and standard form submissions, keeping the stack minimal and consistent with the project's emphasis on simplicity.

**3\. Technology Stack**

The backend is built in Python using the Flask framework. Data is stored in SQLite, accessed directly through Python's built-in database module rather than an ORM, again to keep the codebase simple and easy for a single developer to maintain. Passwords are hashed using Werkzeug's security utilities rather than any custom or reversible encryption. User sessions are managed using Flask's built-in signed-cookie session mechanism, secured with a secret key. Page rendering uses Jinja templates, and styling is handled with a single plain CSS file rather than a frontend build pipeline. For local development and demonstration, Flask's built-in development server is sufficient.

**4\. Project Structure**

The project is organised into a main application file responsible for route registration, a dedicated module for database connection and initialisation logic, and a separate module handling authentication and access-control helpers. Templates are grouped by purpose — authentication pages, the member-facing catalogue and loan views, and a distinct set of admin templates covering the dashboard, book management, member management, and transaction reports. A single static folder holds the stylesheet used across all pages. The SQLite database itself is stored as a single file within the project, generated automatically the first time the application initialises.

**5\. Data Requirements**

Three core entities are required to support the system. A **Users** entity stores each person's institutional identifier (used as their login), full name, optional contact and department details, their hashed password, their role (member or admin), and a flag indicating whether they still need to set their own password after being provisioned by an admin. A **Books** entity stores each title's descriptive details (title, author, category, identifier), along with how many total and currently available copies exist. A **Transactions** entity links a user and a book together, recording when the book was borrowed, when it is due, when (if at all) it was returned, and its current status — borrowed, returned, or overdue. Each transaction is tied back to exactly one user and one book, allowing the system to reconstruct a full borrowing history per member or per title at any time.

**6\. Business Logic Rules**

A standard loan period is defined (an initial default of fourteen days from the borrow date), used to automatically calculate each transaction's due date. A book can only be borrowed if it currently has at least one available copy; borrowing reduces the available count by one and creates a new transaction record marked as borrowed. Returning a book restores the available count by one, sets the return date, and updates the transaction's status accordingly. Rather than relying on a background scheduler, the system checks for overdue items whenever a relevant page is loaded — any borrowed transaction whose due date has passed and has not been returned is automatically reclassified as overdue at that point. Any account newly created by an admin is flagged to require a password change, and the system enforces this by redirecting such users to a password-setup step before they can access anything else. Access to all administrative functionality is restricted to accounts with the admin role, enforced consistently across every admin-facing route rather than left to the interface alone.

**7\. Functional Routes Required**

At a high level, the system needs routes covering: authentication (login, logout, and the forced first-login password change); the member-facing catalogue and search; borrowing and returning a book; a member's view of their own current and past loans; and, on the administrative side, a dashboard overview, full book management (adding, editing, and removing titles), full member management (provisioning new accounts and viewing member details), and a transaction report view that can be filtered by status. Each route's access level (public, authenticated member, or admin-only) is enforced at the point of request, not assumed from the interface alone.

**8\. Security Requirements**

Passwords must never be stored in plain or reversible form — only as securely generated hashes. The application's session secret must be loaded from environment configuration rather than hardcoded into the codebase. All database queries must use parameterized statements to eliminate SQL injection risk; string-built queries are not acceptable. Session-based cookies are used to track authentication state, and only minimal, non-sensitive identifiers are kept in that session. Every form that modifies data must include CSRF protection, and all user input must be validated server-side (required fields present, identifiers in the expected format, copy counts never negative) before anything is written to the database.

**9\. Error Handling**

Failed login attempts should show a single generic error message rather than indicating which specific field was incorrect, to avoid revealing whether a given ID exists in the system. Attempting to borrow a book with no available copies should be blocked with a clear message and must not create a transaction record. Attempting to access an admin-only route without the correct role should redirect the user away rather than expose any part of the admin interface. Any unexpected server-side error should be caught and shown as a generic failure message to the user, while relevant details are logged internally for debugging rather than displayed on the page.

