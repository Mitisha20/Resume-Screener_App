from flask import Blueprint, request, jsonify,current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from os import getenv

from app.services.pdf_extractor import extract_text_from_pdf
from app.services.skills import extract_skills_from_text
from app.models.db import get_db

from app.utils.responses import ok,created,fail
import logging

resumes_bp = Blueprint("resumes", __name__, url_prefix="/api/resumes")

log:logging.Logger = logging.getLogger("resume_backend")


MAX_FILE_MB = float(getenv("MAX_FILE_MB", "10"))

@resumes_bp.post("/upload")
@jwt_required()
def upload_resume():
    user_id = get_jwt_identity()
    # 1) file present?
    if "file" not in request.files:
       return fail("no file provided (use form-data field 'file')", 422)  

    file = request.files["file"]

    # 2) basic checks
    if file.filename == "":
        return fail("empty filename", 422) 
    if not file.filename.lower().endswith(".pdf"):
        return fail("only PDF files are allowed", 415)  

    # 3) size guard
    file_bytes = file.read()
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_MB:
       return fail(
            f"file too large (> {current_app.config['MAX_FILE_MB']} MB)", 413
        )

    # 4) extract text
    try:
        text = extract_text_from_pdf(file_bytes)  
    except Exception as e:
         log.exception("pdf_extract_error user=%s file=%s", user_id, file.filename) 
         return fail("failed to read pdf", 400, details=str(e))              

    if not text:
        return fail("no extractable text found in PDF", 400)

    # 5) extract skills from text
    skills = extract_skills_from_text(text)

    # 6) who uploaded + db handle
    user_id = get_jwt_identity()   
    db = get_db()                  

    # 7) persist
    doc = {
        "user_id": user_id,
        "filename": file.filename,
        "text": text,
        "skills_extracted": skills,
    }
    inserted = db["resumes"].insert_one(doc)

    log.info(
        "resume_upload user=%s file=%s chars=%d skills=%d",
        user_id, file.filename, len(text), len(skills)
    )
    return created(
        "resume uploaded",
        resume_id=str(inserted.inserted_id),
        filename=file.filename,
        chars=len(text),
        skills_extracted=skills
    )

@resumes_bp.get("/")
@jwt_required()
def list_resumes():
    
    user_id = get_jwt_identity()
    db = get_db()

    try:
        cursor = db["resumes"].find({"user_id": user_id}, {"text": 0})
    except Exception as e:
        log.exception("db_query_error user=%s collection=resumes", user_id)  
        return fail("could not fetch resumes", 500, details=str(e))    

    out = []
    for r in cursor:
        out.append({
            "id": str(r["_id"]),
            "filename": r.get("filename", ""),
            "skills_extracted": r.get("skills_extracted", []),
        })

    log.info("list_resumes user=%s count=%d", user_id, len(out))            

    
    return ok("fetched resumes", resumes=out)