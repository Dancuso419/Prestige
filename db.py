import os
import sqlite3

import auth

# DATABASE_URL lets the host (e.g. Render persistent disk) point the DB
# somewhere durable; falls back to a file next to the code for local dev.
DATABASE_PATH = os.environ.get(
    "DATABASE_PATH", os.path.join(os.path.dirname(__file__), "library.db")
)

LOAN_PERIOD_DAYS = 14  # Fallback loan period if the setting is missing/invalid


def get_connection():
    """Return a new database connection with row_factory set."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create tables if they do not already exist."""
    # Ensure the DB's parent directory exists (e.g. a mounted disk path).
    parent = os.path.dirname(DATABASE_PATH)
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_staff_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT DEFAULT '',
            department_class TEXT DEFAULT '',
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('member', 'admin')),
            must_change_password INTEGER NOT NULL DEFAULT 1,
            is_active INTEGER NOT NULL DEFAULT 1,
            is_super_admin INTEGER NOT NULL DEFAULT 0,
            date_created TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT DEFAULT '',
            isbn TEXT DEFAULT '',
            total_copies INTEGER NOT NULL DEFAULT 1,
            available_copies INTEGER NOT NULL DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            borrow_date TEXT NOT NULL DEFAULT (date('now', 'localtime')),
            due_date TEXT NOT NULL,
            return_date TEXT,
            status TEXT NOT NULL DEFAULT 'borrowed'
                CHECK(status IN ('borrowed', 'returned', 'overdue')),
            return_requested INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    """)

    conn.commit()
    conn.close()


def migrate():
    """Add missing columns to existing tables (for dev upgrades)."""
    conn = get_connection()
    cursor = conn.cursor()

    # Add columns missing on databases created before these features existed.
    cols = [row[1] for row in cursor.execute("PRAGMA table_info(users)").fetchall()]
    if "is_active" not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")
    if "is_super_admin" not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN is_super_admin INTEGER NOT NULL DEFAULT 0")

    # Pending return-request flag on transactions (member asks, admin confirms).
    txn_cols = [row[1] for row in cursor.execute("PRAGMA table_info(transactions)").fetchall()]
    if "return_requested" not in txn_cols:
        cursor.execute("ALTER TABLE transactions ADD COLUMN return_requested INTEGER NOT NULL DEFAULT 0")

    # Key/value settings table for configurable options (e.g. loan period).
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
    )
    cursor.execute(
        "INSERT OR IGNORE INTO settings (key, value) VALUES ('loan_period_days', '14')"
    )

    # Ensure exactly one super admin exists; on upgrade, promote the earliest admin.
    if cursor.execute("SELECT id FROM users WHERE is_super_admin = 1").fetchone() is None:
        first_admin = cursor.execute(
            "SELECT id FROM users WHERE role = 'admin' ORDER BY id ASC LIMIT 1"
        ).fetchone()
        if first_admin:
            cursor.execute(
                "UPDATE users SET is_super_admin = 1 WHERE id = ?", (first_admin[0],)
            )

    conn.commit()
    conn.close()


def seed_admin():
    """Create the default admin account if no admin exists."""
    conn = get_connection()
    cursor = conn.cursor()

    existing = cursor.execute(
        "SELECT id FROM users WHERE role = 'admin'"
    ).fetchone()

    if existing is None:
        admin_id = os.environ.get("ADMIN_ID", "admin")
        admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
        password_hash = auth.hash_password(admin_password)

        cursor.execute(
            "INSERT INTO users (student_staff_id, full_name, password_hash, role, must_change_password, is_super_admin) "
            "VALUES (?, ?, ?, 'admin', 0, 1)",
            (admin_id, "Administrator", password_hash),
        )
        conn.commit()

    conn.close()


# ---------------------------------------------------------------------------
# User queries
# ---------------------------------------------------------------------------

def get_user_by_student_id(student_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE student_staff_id = ?", (student_id,)
    ).fetchone()
    conn.close()
    return row


def get_user_by_id(user_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return row


def update_user_password(user_id, password_hash):
    conn = get_connection()
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (password_hash, user_id),
    )
    conn.commit()
    conn.close()


def clear_must_change_password(user_id):
    conn = get_connection()
    conn.execute(
        "UPDATE users SET must_change_password = 0 WHERE id = ?", (user_id,)
    )
    conn.commit()
    conn.close()


def update_user_profile(user_id, full_name, email):
    """Update the signed-in user's own display name and email."""
    conn = get_connection()
    conn.execute(
        "UPDATE users SET full_name = ?, email = ? WHERE id = ?",
        (full_name, email, user_id),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Admin account queries (super-admin managed)
# ---------------------------------------------------------------------------

def get_all_admins():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM users WHERE role = 'admin' "
        "ORDER BY is_super_admin DESC, date_created ASC"
    ).fetchall()
    conn.close()
    return rows


def add_admin(student_id, full_name, email, temp_password):
    """Create a new (non-super) admin. Returns False if the ID already exists."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (student_staff_id, full_name, email, password_hash, role, must_change_password, is_super_admin) "
            "VALUES (?, ?, ?, ?, 'admin', 1, 0)",
            (student_id, full_name, email, auth.hash_password(temp_password)),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def remove_admin(admin_id):
    """Delete an admin account. Super admins are protected and never removed."""
    conn = get_connection()
    conn.execute(
        "DELETE FROM users WHERE id = ? AND role = 'admin' AND is_super_admin = 0",
        (admin_id,),
    )
    conn.commit()
    conn.close()


def reset_admin_password(admin_id, temp_password):
    """Super admin resets another admin's password. Super admins are protected;
    the reset forces the target admin to set a new password on next login."""
    conn = get_connection()
    conn.execute(
        "UPDATE users SET password_hash = ?, must_change_password = 1 "
        "WHERE id = ? AND role = 'admin' AND is_super_admin = 0",
        (auth.hash_password(temp_password), admin_id),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def get_setting(key, default=None):
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    conn = get_connection()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, str(value)),
    )
    conn.commit()
    conn.close()


def get_loan_period():
    try:
        return int(get_setting("loan_period_days", LOAN_PERIOD_DAYS))
    except (TypeError, ValueError):
        return LOAN_PERIOD_DAYS


def add_member(student_id, full_name, email, department_class, temp_password):
    conn = get_connection()
    password_hash = auth.hash_password(temp_password)
    conn.execute(
        "INSERT INTO users (student_staff_id, full_name, email, department_class, password_hash, role, must_change_password) "
        "VALUES (?, ?, ?, ?, ?, 'member', 1)",
        (student_id, full_name, email, department_class, password_hash),
    )
    conn.commit()
    conn.close()


def get_all_members():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM users WHERE role = 'member' ORDER BY date_created DESC"
    ).fetchall()
    conn.close()
    return rows


def update_member(member_id, student_id, full_name, email, department_class):
    conn = get_connection()
    conn.execute(
        "UPDATE users SET student_staff_id=?, full_name=?, email=?, department_class=? WHERE id=? AND role='member'",
        (student_id, full_name, email, department_class, member_id),
    )
    conn.commit()
    conn.close()


def reset_member_password(member_id, temp_password):
    """Admin resets a member's password to a new temporary one, forcing the
    member to set their own password on next login (must_change_password = 1)."""
    conn = get_connection()
    conn.execute(
        "UPDATE users SET password_hash = ?, must_change_password = 1 "
        "WHERE id = ? AND role = 'member'",
        (auth.hash_password(temp_password), member_id),
    )
    conn.commit()
    conn.close()


def toggle_member_active(member_id):
    conn = get_connection()
    member = conn.execute(
        "SELECT is_active FROM users WHERE id=? AND role='member'", (member_id,)
    ).fetchone()
    if member:
        new_status = 0 if member["is_active"] else 1
        conn.execute(
            "UPDATE users SET is_active=? WHERE id=? AND role='member'",
            (new_status, member_id),
        )
        conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Book queries
# ---------------------------------------------------------------------------

def get_all_books():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM books ORDER BY title ASC"
    ).fetchall()
    conn.close()
    return rows


def get_book_by_id(book_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM books WHERE id = ?", (book_id,)
    ).fetchone()
    conn.close()
    return row


def search_books(query):
    conn = get_connection()
    like = f"%{query}%"
    rows = conn.execute(
        "SELECT * FROM books WHERE title LIKE ? OR author LIKE ? OR category LIKE ? "
        "ORDER BY title ASC",
        (like, like, like),
    ).fetchall()
    conn.close()
    return rows


def add_book(title, author, category, isbn, total_copies):
    conn = get_connection()
    conn.execute(
        "INSERT INTO books (title, author, category, isbn, total_copies, available_copies) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (title, author, category, isbn, total_copies, total_copies),
    )
    conn.commit()
    conn.close()


def update_book(book_id, title, author, category, isbn, total_copies):
    conn = get_connection()
    book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()

    if book:
        borrowed = book["total_copies"] - book["available_copies"]
        new_available = max(0, total_copies - borrowed)

        conn.execute(
            "UPDATE books SET title=?, author=?, category=?, isbn=?, total_copies=?, available_copies=? "
            "WHERE id=?",
            (title, author, category, isbn, total_copies, new_available, book_id),
        )
        conn.commit()

    conn.close()


def remove_book(book_id):
    conn = get_connection()
    conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Transaction queries
# ---------------------------------------------------------------------------

def borrow_book(user_id, book_id):
    conn = get_connection()
    cursor = conn.cursor()

    # Calculate due date from the configured loan period. The modifier value is
    # parameterized; days is an int from get_loan_period(), so it is safe.
    days = get_loan_period()
    cursor.execute("SELECT date('now', 'localtime', ?)", (f"+{days} days",))
    due_date = cursor.fetchone()[0]

    cursor.execute(
        "INSERT INTO transactions (user_id, book_id, due_date, status) "
        "VALUES (?, ?, ?, 'borrowed')",
        (user_id, book_id, due_date),
    )

    cursor.execute(
        "UPDATE books SET available_copies = available_copies - 1 WHERE id = ?",
        (book_id,),
    )

    conn.commit()
    conn.close()


def request_return(transaction_id):
    """Member asks to return a book. Flags the loan as awaiting admin
    confirmation; availability is NOT restored until the admin confirms."""
    conn = get_connection()
    conn.execute(
        "UPDATE transactions SET return_requested = 1 "
        "WHERE id = ? AND return_date IS NULL",
        (transaction_id,),
    )
    conn.commit()
    conn.close()


def cancel_return_request(transaction_id):
    """Member withdraws a pending return request (before admin confirms)."""
    conn = get_connection()
    conn.execute(
        "UPDATE transactions SET return_requested = 0 "
        "WHERE id = ? AND return_date IS NULL",
        (transaction_id,),
    )
    conn.commit()
    conn.close()


def return_book(transaction_id):
    """Complete a return: restore availability, set return date, clear any
    pending request. Used by admin confirmation and admin direct return."""
    conn = get_connection()
    conn.execute(
        "UPDATE transactions SET return_date = date('now', 'localtime'), "
        "status = 'returned', return_requested = 0 "
        "WHERE id = ?",
        (transaction_id,),
    )

    # Restore available copies
    txn = conn.execute(
        "SELECT book_id FROM transactions WHERE id = ?", (transaction_id,)
    ).fetchone()
    if txn:
        conn.execute(
            "UPDATE books SET available_copies = available_copies + 1 WHERE id = ?",
            (txn["book_id"],),
        )

    conn.commit()
    conn.close()


def get_pending_returns_count():
    """Number of loans a member has asked to return, awaiting admin confirm."""
    conn = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE return_requested = 1 AND return_date IS NULL"
    ).fetchone()[0]
    conn.close()
    return count


def get_transaction_by_id(transaction_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM transactions WHERE id = ?", (transaction_id,)
    ).fetchone()
    conn.close()
    return row


def get_user_transactions(user_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT t.*, b.title AS book_title, b.author AS book_author "
        "FROM transactions t JOIN books b ON t.book_id = b.id "
        "WHERE t.user_id = ? "
        "ORDER BY t.borrow_date DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def get_all_transactions(status_filter=None):
    conn = get_connection()
    base = (
        "SELECT t.*, b.title AS book_title, b.author AS book_author, "
        "u.full_name AS member_name, u.student_staff_id "
        "FROM transactions t "
        "JOIN books b ON t.book_id = b.id "
        "JOIN users u ON t.user_id = u.id "
    )
    if status_filter == "requested":
        # Loans a member has asked to return, not yet confirmed by an admin.
        rows = conn.execute(
            base + "WHERE t.return_requested = 1 AND t.return_date IS NULL "
            "ORDER BY t.borrow_date DESC"
        ).fetchall()
    elif status_filter:
        rows = conn.execute(
            base + "WHERE t.status = ? ORDER BY t.borrow_date DESC",
            (status_filter,),
        ).fetchall()
    else:
        rows = conn.execute(base + "ORDER BY t.borrow_date DESC").fetchall()
    conn.close()
    return rows


def mark_overdue_transactions():
    """Re-classify borrowed transactions past their due date as overdue."""
    conn = get_connection()
    conn.execute(
        "UPDATE transactions SET status = 'overdue' "
        "WHERE status = 'borrowed' AND due_date < date('now', 'localtime') "
        "AND return_date IS NULL"
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Stats / reporting
# ---------------------------------------------------------------------------

def get_overdue_count():
    """Re-classify overdue items and return the current overdue count.
    Used by the sidebar badge, so it runs on every admin page load."""
    conn = get_connection()
    conn.execute(
        "UPDATE transactions SET status = 'overdue' "
        "WHERE status = 'borrowed' AND due_date < date('now', 'localtime') "
        "AND return_date IS NULL"
    )
    conn.commit()
    count = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE status = 'overdue'"
    ).fetchone()[0]
    conn.close()
    return count


def get_admin_stats():
    conn = get_connection()

    total_books = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    total_members = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role = 'member'"
    ).fetchone()[0]

    # Ensure overdue re-check before counting
    conn.execute(
        "UPDATE transactions SET status = 'overdue' "
        "WHERE status = 'borrowed' AND due_date < date('now', 'localtime') "
        "AND return_date IS NULL"
    )
    conn.commit()

    overdue_count = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE status = 'overdue'"
    ).fetchone()[0]

    borrowed_count = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE status = 'borrowed'"
    ).fetchone()[0]

    pending_returns = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE return_requested = 1 AND return_date IS NULL"
    ).fetchone()[0]

    conn.close()
    return {
        "total_books": total_books,
        "total_members": total_members,
        "overdue_count": overdue_count,
        "borrowed_count": borrowed_count,
        "pending_returns": pending_returns,
    }
