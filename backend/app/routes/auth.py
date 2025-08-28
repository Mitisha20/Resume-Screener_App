from flask import Blueprint, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from passlib.hash import bcrypt
from datetime import timedelta
from app.models.db import users_col
from app.utils.responses import ok, created, fail   
import logging                                    

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
log: logging.Logger = logging.getLogger("resume_backend") 

@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""

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


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""

    if not username or not password:
        return fail("username and password are required", 422)  

    user = users_col().find_one({"username": username})
    if not user or not bcrypt.verify(password, user["password_hash"]):
        return fail("invalid credentials", 401)                  
    token = create_access_token(identity=str(user["_id"]), expires_delta=timedelta(hours=8))
    log.info("user_login_success username=%s", username)         
    return ok("login successful", access_token=token)            

@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    log.info("user_me_checked user_id=%s", user_id)              
    return ok("fetched user", user_id=user_id)                 
