from flask import current_app
from pymongo import ASCENDING


def get_db():
   
    return current_app.config["MONGO_DB"]


def users_col():
    
    return get_db()["users"]


def ensure_indexes():
   
    db = get_db()

    # unique usernames for auth
    db.users.create_index(
        [("username", ASCENDING)],
        unique=True,
        name="uniq_username",
    )
def scans_col():
    return get_db()["scans"]

    db.scans.create_index([("user_id",1),("created_at",-1)], name="idx_scans_user_created")

   
    