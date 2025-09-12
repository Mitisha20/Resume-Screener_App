from flask import Blueprint, request, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from passlib.hash import bcrypt
from datetime import timedelta
from app.models.db import users_col
from app.utils.responses import ok, created, fail
import logging
import os

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
log: logging.Logger = logging.getLogger("resume_backend")

# ---- small helper ----
def _payload():
    return request.get_json(silent=True) or {}

# ------------------ REGISTER ------------------
@auth_bp.post("/register")
def register():
    data = _payload()
    username = (data.get("username") or "").strip().lower()
    password = (data.get("password") or "").strip()  # trim to avoid trailing-space trap

    if not username:
        return fail("username is required", 422)
    if not password:
        return fail("password is required", 422)
    if len(password) < 8:
        return fail("password must be at least 8 characters", 422)

    if users_col().find_one({"username": username}):
        return fail("username already exists", 409)

    try:
        users_col().insert_one({
            "username": username,
            "password_hash": bcrypt.hash(password)
        })
    except Exception as e:
        log.exception("db_insert_error collection=users username=%s", username)
        return fail("could not register user", 500, details=str(e))

    log.info("user_registered username=%s", username)
    return created("registered", username=username)

# ------------------ LOGIN ------------------
@auth_bp.post("/login")
def login():
    data = _payload()
    username = (data.get("username") or "").strip().lower()
    password = (data.get("password") or "").strip()  # trim here too

    if not username or not password:
        return fail("username and password are required", 422)

    user = users_col().find_one({"username": username})
    if not user:
        log.info("login_no_user username=%s", username)
        return fail("invalid credentials", 401)

    try:
        ok_hash = bcrypt.verify(password, user.get("password_hash", ""))
    except Exception:
        log.exception("bcrypt_verify_error username=%s", username)
        return fail("server error verifying password", 500)

    if not ok_hash:
        log.info("login_bad_password username=%s", username)
        return fail("invalid credentials", 401)

    token = create_access_token(identity=str(user["_id"]), expires_delta=timedelta(hours=8))
    log.info("user_login_success username=%s", username)
    return ok("login successful", access_token=token)

# ------------------ ME ------------------
@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    log.info("user_me_checked user_id=%s", user_id)
    return ok("fetched user", user_id=user_id)

# ------------------ DEV HELPERS (REMOVE IN PROD) ------------------
DEV_TOOLS = os.getenv("DEV_AUTH_TOOLS", "1") == "1"

if DEV_TOOLS:
    @auth_bp.get("/dev/user/<username>")
    def dev_get_user(username: str):
        """Inspect a user doc (mask hash). Dev only."""
        u = users_col().find_one({"username": username.strip().lower()})
        if not u:
            return fail("not found", 404)
        masked = (u.get("password_hash") or "")[:12] + "..." if u.get("password_hash") else None
        return ok("user", username=u.get("username"), has_hash=bool(u.get("password_hash")), hash_preview=masked)

    @auth_bp.post("/dev/reset_password")
    def dev_reset_password():
        """Reset a user's password to a known value. Dev only."""
        data = _payload()
        username = (data.get("username") or "").strip().lower()
        new_pw = (data.get("new_password") or "").strip()
        if not username or len(new_pw) < 8:
            return fail("username and new_password required (>=8 chars)", 422)
        users_col().update_one({"username": username}, {"$set": {"password_hash": bcrypt.hash(new_pw)}})
        return ok("password reset", username=username)
