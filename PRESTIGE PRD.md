PRODUCT REQUIREMENTS DOCUMENT (PRD) 

**Project: Web-Based Digital Library System**

**1\. Overview**

This document defines the requirements for a web-based Digital Library System designed to replace manual, paper-based library operations with a centralised, searchable, and automated platform. The system will allow members to search a book catalogue, borrow and return books, and track due dates remotely, while giving administrators tools to manage the book collection, member accounts, and borrowing activity from a single dashboard.

Member accounts are provisioned by the administrator rather than through open self-registration, reflecting how real institutional libraries operate — access is tied to a verified student/staff identity rather than an open sign-up form.

The system is being developed as a small-scale academic project (final year project), built using Python (Flask) and SQLite, with development assisted by an AI coding agent (Claude Code). It is intended as a functional prototype suitable for demonstration and evaluation, not a large-scale commercial deployment.

**2\. Problem Statement**

Many small institutions — schools, departments, and small organisations — continue to rely on manual library processes: physical card catalogues for search, handwritten registers for borrowing records, and manual cross-checking for returns and overdue tracking. This leads to slow book discovery, error-prone record keeping, no remote access to library information, and difficulty generating reports (e.g., overdue lists). Existing digital solutions are often either too complex/costly (enterprise library systems) or hardware-dependent (RFID-based automation), making them impractical for small-scale adoption.

**3\. Goals and Objectives**

* Replace manual cataloguing and circulation record-keeping with a centralised digital system.  
* Enable members to search the book catalogue and see real-time availability.  
* Automate borrowing and return transactions, including due-date tracking and overdue flagging.  
* Provide administrators with a simple dashboard to manage books, members, and borrowing activity.  
* Ensure library access is tied to a verified institutional identity (Student/Staff ID), provisioned by the admin rather than opened to the public.  
* Keep the system lightweight, affordable, and easy to deploy/maintain without specialised hardware or a dedicated IT team.

**4\. Target Users**

| Role | Description | Account Creation |
| ----- | ----- | ----- |
| Member | A student/staff user who searches, borrows, and returns books. | Created by the Administrator |
| Administrator | Manages the book catalogue, member accounts, and borrowing activity. | Pre-configured / seeded at setup |

**5\. Scope**

**In Scope**

* Admin-provisioned member accounts (no public self-registration)  
* First-login password setup for new members  
* Searchable book catalogue (title, author, category)  
* Borrow and return functionality with due-date tracking  
* Overdue detection and flagging  
* Admin dashboard: add/edit/remove books, add/manage members, view/manage all transactions  
* Basic reporting (currently borrowed books, overdue books)

**Out of Scope**

* Public self-registration for members  
* E-book hosting/reading or file uploads of full book content  
* Payment gateway integration for fines  
* RFID or barcode hardware integration  
* Multi-branch/distributed library networks  
* Mobile native app (web-based/responsive only)

**6\. Functional Requirements**

**6.1 Authentication & User Management**

* FR1: Only an admin can create a new member account (name, Student/Staff ID, email, department/class — optional, temporary password).  
* FR2: New member accounts are flagged to require a password change on first login.  
* FR3: Members log in using their Student/Staff ID and password.  
* FR4: Passwords must be hashed and salted before storage (never stored in plain text).  
* FR5: The system distinguishes between "member" and "admin" roles, restricting admin routes to admin users only.  
* FR6: Members cannot create additional accounts or self-register.

**6.2 Book Catalogue**

* FR7: Members can search for books by title, author, or category.  
* FR8: Each book listing shows real-time availability status (available / borrowed).  
* FR9: Admins can add a new book (title, author, category, ISBN, total copies).  
* FR10: Admins can edit or remove existing book records.

**6.3 Borrowing and Returns**

* FR11: A logged-in member can borrow an available book, which automatically sets a due date (e.g., 14 days from borrow date).  
* FR12: A member cannot borrow a book with zero available copies.  
* FR13: A member can view their currently borrowed books and due dates.  
* FR14: A member (or admin) can mark a book as returned, which updates its availability.  
* FR15: The system automatically flags a transaction as "overdue" if the due date has passed without a return.

**6.4 Admin Dashboard**

* FR16: Admins can add new member accounts (Student/Staff ID, name, email, department/class).  
* FR17: Admins can view, edit, or deactivate existing member accounts.  
* FR18: Admins can view all active, returned, and overdue transactions.  
* FR19: Admins can view basic statistics (total books, total members, number of overdue items).

**7\. Non-Functional Requirements**

| Category | Requirement |
| ----- | ----- |
| Usability | Interface must be simple enough for users with minimal technical experience, informed by literature showing low digital literacy as a key adoption barrier. |
| Performance | Catalogue search should return results in under 2 seconds for a small-to-medium book collection (up to a few thousand records). |
| Security | Passwords hashed (not encrypted/reversible); session-based authentication; admin routes protected from unauthorised access; member accounts cannot self-elevate to admin. |
| Portability | Must run on a local machine or free/small-scale hosting without specialised infrastructure. |
| Maintainability | Codebase should be simple enough for a single developer (with AI coding assistance) to maintain and extend. |
| Cost | Built entirely with free, open-source tools (Python, Flask, SQLite). |

**8\. Data Model (High-Level)**

**Users**

* id, student\_staff\_id (unique, used as username), full\_name, email (optional), department\_class (optional), password\_hash, role (member/admin), must\_change\_password (boolean), date\_created

**Books**

* id, title, author, category, isbn, total\_copies, available\_copies

**Transactions**

* id, user\_id (FK), book\_id (FK), borrow\_date, due\_date, return\_date (nullable), status (borrowed/returned/overdue)

**9\. Key User Flows**

1. **Account Provisioning** → Admin adds a new member (Student/Staff ID, name, temporary password) → member receives their ID and temporary password.  
2. **First Login** → Member logs in with Student/Staff ID \+ temporary password → prompted to set a new password → redirected to catalogue.  
3. **Search & Borrow** → Member searches catalogue → selects available book → borrows it → due date generated → confirmation shown.  
4. **Return** → Member (or admin) marks a borrowed book as returned → availability updated → status changed to "returned."  
5. **Overdue Handling** → System checks due dates → automatically flags overdue transactions → visible to admin and to the member on their account.  
6. **Admin Management** → Admin logs in → adds/edits/removes books → adds/manages members → views transaction reports.

**10\. Technology Stack**

* **Backend:** Python, Flask  
* **Database:** SQLite  
* **Frontend:** HTML, CSS (Jinja templates rendered by Flask)  
* **Authentication:** Flask sessions \+ password hashing (Werkzeug security)  
* **Development Tooling:** Claude Code (AI-assisted development)  
* **Hosting (for demonstration):** Local machine or free-tier hosting platform

**11\. Assumptions and Constraints**

* This is a small-scale academic prototype, not a production system — no expectation of handling high concurrent traffic.  
* The developer is a single person using an AI coding assistant, favouring simplicity over exhaustive feature coverage.  
* No dedicated IT support is assumed post-deployment, so the system must be low-maintenance.  
* Internet/power reliability may be inconsistent (per literature review findings), so the system should function acceptably on modest infrastructure.  
* Member identity verification (confirming a Student/Staff ID is legitimate) happens outside the system — the admin is trusted to enter accurate records.

**12\. Success Criteria**

* An admin can create a new member account, and that member can log in with the provided credentials and is prompted to set a new password on first login.  
* A member can search the catalogue, borrow a book, and see it correctly reflected as unavailable to other users.  
* A borrowed book's due date is correctly calculated and displayed.  
* An overdue book is automatically and correctly flagged without manual intervention.  
* An admin can add a new book and see it immediately searchable in the catalogue.  
* A member cannot access admin-only routes (books management, member management, reports).  
* The system runs reliably on a local machine without requiring specialised hardware or paid infrastructure.

**13\. Future Enhancements (Out of Current Scope)**

* Email/SMS notifications for due-date reminders and account credential delivery  
* Fine calculation for overdue books  
* Book reservation queue for high-demand titles  
* AI-assisted semantic search (informed by literature on "Smart OPAC" systems)  
* Bulk member import (e.g., CSV upload of a class list)  
* Multi-branch support for larger institutions

