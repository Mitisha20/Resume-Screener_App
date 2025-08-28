from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.db import get_db
from app.services.skills import extract_skills_from_text
from app.utils.responses import ok, created, fail  
import logging                                     

jobs_bp = Blueprint("jobs", __name__, url_prefix="/api/jobs")
log: logging.Logger = logging.getLogger("resume_backend")   


@jobs_bp.post("/")
@jwt_required()
def create_job():
    
    user_id = get_jwt_identity()
    db = get_db()

    
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()

    if not title:
        return fail("title is required", 422) 
    if len(description) < 20:
        return fail("description too short (min 20 chars)", 422) 
    if len(title) > 120:
        return fail("title too long (max 120 chars)", 422)  

    
    skills = extract_skills_from_text(description)

    
    doc = {
        "user_id": user_id,
        "title": title,
        "description": description,
        "skills_extracted": skills,
    }
    try:
        inserted = db["jobs"].insert_one(doc)
    except Exception as e:
        log.exception("db_insert_error collection=jobs user=%s title=%s", user_id, title)  
        return fail("could not create job", 500, details=str(e))

    
    log.info(
        "job_create user=%s job_id=%s title=%s skills=%d",
        user_id, str(inserted.inserted_id), title, len(skills)
    )

    
    return created(
        "job created",
        job_id=str(inserted.inserted_id),
        title=title,
        skills_extracted=skills
    )
