import os

from dotenv import load_dotenv
from flask import (Flask, flash, redirect, render_template, request,
                   session, url_for)

import auth
import db

# Load .env so `python app.py` works, not just `flask run`.
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

if not app.secret_key:
    raise RuntimeError("SESSION_SECRET environment variable is not set.")

# Prepare the database at import time so it also runs under gunicorn (the
# __main__ block below only runs with `python app.py`). All three are idempotent.
db.init_db()
db.migrate()
db.seed_admin()


@app.context_processor
def inject_template_helpers():
    return {"csrf_field": auth.csrf_field}


@app.context_processor
def inject_admin_badges():
    # Admin sidebar badges: pending return requests (needs confirmation) and
    # overdue count. get_overdue_count() also reclassifies overdue on load.
    if session.get("role") == "admin":
        return {
            "pending_returns_badge": db.get_pending_returns_count(),
            "overdue_badge": db.get_overdue_count(),
        }
    return {"pending_returns_badge": 0, "overdue_badge": 0}


# ---------------------------------------------------------------------------
# Authentication routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
@auth.csrf_protect
def login():
    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        password = request.form.get("password", "")

        user = db.get_user_by_student_id(student_id)
        if user is None or not auth.verify_password(password, user["password_hash"]):
            flash("Invalid login credentials.", "error")
            return render_template("auth/login.html")

        session["user_id"] = user["id"]
        session["role"] = user["role"]
        session["full_name"] = user["full_name"]
        session["student_id"] = user["student_staff_id"]
        session["is_super_admin"] = bool(user["is_super_admin"]) if "is_super_admin" in user.keys() else False

        if user["must_change_password"]:
            return redirect(url_for("change_password"))

        return _redirect_home(user["role"])

    return render_template("auth/login.html")


@app.route("/change-password", methods=["GET", "POST"])
@auth.login_required
@auth.csrf_protect
def change_password():
    user = db.get_user_by_id(session["user_id"])

    if request.method == "POST":
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(new_password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("auth/change_password.html")

        if new_password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("auth/change_password.html")

        db.update_user_password(user["id"], auth.hash_password(new_password))
        db.clear_must_change_password(user["id"])
        flash("Password changed successfully. You are now logged in.", "success")

        if user["role"] == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("catalogue"))

    return render_template("auth/change_password.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Member routes
# ---------------------------------------------------------------------------

@app.route("/catalogue", methods=["GET"])
@auth.login_required
def catalogue():
    query = request.args.get("q", "").strip()
    if query:
        books = db.search_books(query)
    else:
        books = db.get_all_books()

    return render_template("member/catalogue.html", books=books, query=query)


@app.route("/borrow/<int:book_id>", methods=["POST"])
@auth.login_required
@auth.csrf_protect
def borrow_book(book_id):
    book = db.get_book_by_id(book_id)
    if book is None:
        flash("Book not found.", "error")
        return redirect(url_for("catalogue"))

    if book["available_copies"] <= 0:
        flash("No copies of this book are currently available.", "error")
        return redirect(url_for("catalogue"))

    db.borrow_book(session["user_id"], book_id)
    flash(f"You have borrowed \"{book['title']}\".", "success")
    return redirect(url_for("my_loans"))


@app.route("/return/<int:transaction_id>", methods=["POST"])
@auth.login_required
@auth.csrf_protect
def request_return(transaction_id):
    # A member's return is a *request*: the admin must confirm the physical book
    # was handed back before it counts as returned and the copy is freed.
    txn = db.get_transaction_by_id(transaction_id)
    if txn is None or txn["user_id"] != session["user_id"]:
        flash("Transaction not found.", "error")
        return redirect(url_for("my_loans"))

    if txn["return_date"] is not None:
        flash("This book has already been returned.", "error")
        return redirect(url_for("my_loans"))

    if txn["return_requested"]:
        flash("You have already requested to return this book.", "error")
        return redirect(url_for("my_loans"))

    db.request_return(transaction_id)
    flash("Return requested. An admin will confirm once you hand the book in.", "success")
    return redirect(url_for("my_loans"))


@app.route("/return/<int:transaction_id>/cancel", methods=["POST"])
@auth.login_required
@auth.csrf_protect
def cancel_return(transaction_id):
    txn = db.get_transaction_by_id(transaction_id)
    if txn is None or txn["user_id"] != session["user_id"]:
        flash("Transaction not found.", "error")
        return redirect(url_for("my_loans"))

    if not txn["return_requested"] or txn["return_date"] is not None:
        flash("There is no pending return request to cancel.", "error")
        return redirect(url_for("my_loans"))

    db.cancel_return_request(transaction_id)
    flash("Return request cancelled.", "success")
    return redirect(url_for("my_loans"))


@app.route("/my-loans")
@auth.login_required
def my_loans():
    # Re-classify overdue transactions on page load
    db.mark_overdue_transactions()
    transactions = db.get_user_transactions(session["user_id"])
    return render_template("member/my_loans.html", transactions=transactions)


# ---------------------------------------------------------------------------
# Admin routes
# ---------------------------------------------------------------------------

@app.route("/admin")
@auth.admin_required
def admin_dashboard():
    db.mark_overdue_transactions()
    stats = db.get_admin_stats()
    return render_template("admin/dashboard.html", stats=stats)


@app.route("/admin/books", methods=["GET", "POST"])
@auth.admin_required
@auth.csrf_protect
def manage_books():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "add":
            title = request.form.get("title", "").strip()
            author = request.form.get("author", "").strip()
            category = request.form.get("category", "").strip()
            isbn = request.form.get("isbn", "").strip()
            try:
                total_copies = int(request.form.get("total_copies", "0"))
            except ValueError:
                total_copies = 0

            if not title or not author:
                flash("Title and author are required.", "error")
            elif total_copies <= 0:
                flash("Total copies must be at least 1.", "error")
            else:
                db.add_book(title, author, category, isbn, total_copies)
                flash(f"Book \"{title}\" added successfully.", "success")

        elif action == "edit":
            book_id = int(request.form.get("book_id"))
            title = request.form.get("title", "").strip()
            author = request.form.get("author", "").strip()
            category = request.form.get("category", "").strip()
            isbn = request.form.get("isbn", "").strip()
            try:
                total_copies = int(request.form.get("total_copies", "0"))
            except ValueError:
                total_copies = 0

            if not title or not author:
                flash("Title and author are required.", "error")
            else:
                db.update_book(book_id, title, author, category, isbn, total_copies)
                flash(f"Book \"{title}\" updated successfully.", "success")

        elif action == "remove":
            book_id = int(request.form.get("book_id"))
            book = db.get_book_by_id(book_id)
            if book:
                db.remove_book(book_id)
                flash(f"Book \"{book['title']}\" removed.", "success")

        return redirect(url_for("manage_books"))

    books = db.get_all_books()
    return render_template("admin/manage_books.html", books=books)


@app.route("/admin/members", methods=["GET", "POST"])
@auth.admin_required
@auth.csrf_protect
def manage_members():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "add":
            student_id = request.form.get("student_id", "").strip()
            full_name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip()
            department_class = request.form.get("department_class", "").strip()
            temp_password = request.form.get("temp_password", "").strip()

            if not student_id or not full_name or not temp_password:
                flash("Student/Staff ID, full name, and temporary password are required.", "error")
            elif len(temp_password) < 6:
                flash("Temporary password must be at least 6 characters.", "error")
            else:
                db.add_member(student_id, full_name, email, department_class, temp_password)
                flash(f"Member \"{full_name}\" added successfully.", "success")

            return redirect(url_for("manage_members"))

        elif action == "edit":
            member_id = int(request.form.get("member_id"))
            student_id = request.form.get("student_id", "").strip()
            full_name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip()
            department_class = request.form.get("department_class", "").strip()

            if not student_id or not full_name:
                flash("Student/Staff ID and full name are required.", "error")
            else:
                db.update_member(member_id, student_id, full_name, email, department_class)
                flash(f"Member \"{full_name}\" updated successfully.", "success")

            return redirect(url_for("manage_members"))

        elif action == "reset_password":
            member_id = int(request.form.get("member_id"))
            temp_password = request.form.get("temp_password", "").strip()
            if len(temp_password) < 6:
                flash("Temporary password must be at least 6 characters.", "error")
            else:
                db.reset_member_password(member_id, temp_password)
                flash("Password reset. The member must set a new password on next login.", "success")
            return redirect(url_for("manage_members"))

        elif action == "toggle_active":
            member_id = int(request.form.get("member_id"))
            db.toggle_member_active(member_id)
            flash("Member status toggled.", "success")
            return redirect(url_for("manage_members"))

    members = db.get_all_members()
    return render_template("admin/manage_members.html", members=members)


@app.route("/account", methods=["GET", "POST"])
@auth.admin_required
@auth.csrf_protect
def account():
    user = db.get_user_by_id(session["user_id"])
    # Trust the database record (not just the session) for super-admin gating.
    is_super = bool(user["is_super_admin"]) if "is_super_admin" in user.keys() else False

    if request.method == "POST":
        action = request.form.get("action")

        if action == "profile":
            full_name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip()
            if not full_name:
                flash("Full name is required.", "error")
            else:
                db.update_user_profile(user["id"], full_name, email)
                session["full_name"] = full_name
                flash("Profile updated.", "success")

        elif action == "password":
            current_password = request.form.get("current_password", "")
            new_password = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")
            if not auth.verify_password(current_password, user["password_hash"]):
                flash("Your current password is incorrect.", "error")
            elif len(new_password) < 6:
                flash("New password must be at least 6 characters.", "error")
            elif new_password != confirm_password:
                flash("New passwords do not match.", "error")
            else:
                db.update_user_password(user["id"], auth.hash_password(new_password))
                flash("Password changed successfully.", "success")

        elif action == "settings" and is_super:
            try:
                days = int(request.form.get("loan_period_days", ""))
            except ValueError:
                days = 0
            if days < 1 or days > 365:
                flash("Loan period must be between 1 and 365 days.", "error")
            else:
                db.set_setting("loan_period_days", days)
                flash("Library settings updated.", "success")

        elif action == "add_admin" and is_super:
            student_id = request.form.get("student_id", "").strip()
            full_name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip()
            temp_password = request.form.get("temp_password", "").strip()
            if not student_id or not full_name or not temp_password:
                flash("Staff/Student ID, full name, and temporary password are required.", "error")
            elif len(temp_password) < 6:
                flash("Temporary password must be at least 6 characters.", "error")
            elif not db.add_admin(student_id, full_name, email, temp_password):
                flash("That Staff/Student ID is already in use.", "error")
            else:
                flash(f"Administrator \"{full_name}\" created.", "success")

        elif action == "reset_admin" and is_super:
            admin_id = int(request.form.get("admin_id"))
            temp_password = request.form.get("temp_password", "").strip()
            if admin_id == user["id"]:
                flash("Use the Security panel to change your own password.", "error")
            elif len(temp_password) < 6:
                flash("Temporary password must be at least 6 characters.", "error")
            else:
                db.reset_admin_password(admin_id, temp_password)
                flash("Administrator password reset. They must set a new one on next login.", "success")

        elif action == "remove_admin" and is_super:
            admin_id = int(request.form.get("admin_id"))
            if admin_id == user["id"]:
                flash("You cannot remove your own account.", "error")
            else:
                db.remove_admin(admin_id)
                flash("Administrator removed.", "success")

        return redirect(url_for("account"))

    admins = db.get_all_admins() if is_super else None
    return render_template(
        "admin/account.html",
        user=user,
        is_super=is_super,
        loan_period=db.get_loan_period(),
        admins=admins,
    )


@app.route("/admin/transactions")
@auth.admin_required
def view_transactions():
    db.mark_overdue_transactions()
    status_filter = request.args.get("status", "").strip()
    transactions = db.get_all_transactions(status_filter if status_filter else None)
    return render_template("admin/transactions.html", transactions=transactions, status_filter=status_filter)


@app.route("/admin/return/<int:transaction_id>", methods=["POST"])
@auth.admin_required
@auth.csrf_protect
def admin_return_book(transaction_id):
    txn = db.get_transaction_by_id(transaction_id)
    if txn is None:
        flash("Transaction not found.", "error")
        return redirect(url_for("view_transactions"))

    if txn["status"] not in ("borrowed", "overdue"):
        flash("This book has already been returned.", "error")
        return redirect(url_for("view_transactions"))

    db.return_book(transaction_id)
    flash("Book marked as returned.", "success")
    return redirect(url_for("view_transactions"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _redirect_home(role):
    if role == "admin":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("catalogue"))


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(500)
def internal_error(e):
    return render_template("error.html", message="An unexpected error occurred."), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
