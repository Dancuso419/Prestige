import functools
import secrets

from flask import flash, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password, password_hash):
    return check_password_hash(password_hash, password)


def generate_csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]


def csrf_field():
    return f'<input type="hidden" name="_csrf_token" value="{generate_csrf_token()}">'


def csrf_protect(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            token = request.form.get("_csrf_token", "")
            if not token or token != session.get("_csrf_token"):
                flash("Invalid request. Please try again.", "error")
                return redirect(request.path)
        return view(*args, **kwargs)
    return wrapper


def login_required(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


def admin_required(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session or session.get("role") != "admin":
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper
