from flask import current_app

def get_db():
    return current_app.config["MONGO_DB"]

def users_col():
    return get_db()["users"]

def ensure_indexes():
    db = get_db()
    
    db.users.create_index([("username",1)],unique=True,name="uniq_username")
    
    db.matches.create_index(
    [("job_id",1),("resume_id",1)],
    unique=True,
    name="uniq_job_resume"
    )
    
    db.resumes.create_index([("user_id",1)],name="idx_resumes_user")
    
    db.jobs.create_index(
    [("title","text"),("description","text")],
    name="text_jobs_title_description",
    weights={"title":5,"description":1}
    )