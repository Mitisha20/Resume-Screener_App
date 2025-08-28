from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from app.models.db import get_db
from app.utils.responses import ok, fail
import logging

match_bp = Blueprint("match", __name__, url_prefix="/api/match")
log: logging.Logger = logging.getLogger("resume_backend")

def compute_match(job_skills, resume_skills):
    js, rs = set(s.lower() for s in job_skills or []), set(s.lower() for s in resume_skills or [])
    if not js: return 0.0, [], []
    overlap = sorted(js & rs)
    missing = sorted(js - rs)
    return round(len(overlap) / max(1, len(js)), 3), overlap, missing

@match_bp.post("/run")
@jwt_required()
def run_match_for_job():
    user_id = get_jwt_identity()
    job_id = (request.args.get("job_id") or "").strip()
    if not ObjectId.is_valid(job_id):
        return fail("valid job_id required", 422)

    db = get_db()
    job = db["jobs"].find_one({"_id": ObjectId(job_id)})
    if not job:
        return fail("job not found", 404)

    resumes = list(db["resumes"].find({"user_id": user_id}))
    results = []
    for r in resumes:
        score, matched, missing = compute_match(job.get("skills_extracted", []), r.get("skills_extracted", []))
        doc = {
            "job_id": str(job["_id"]),
            "resume_id": str(r["_id"]),
            "score": score,
            "matched_skills": matched,
            "missing_skills": missing,
        }
        db["matches"].update_one({"job_id": doc["job_id"], "resume_id": doc["resume_id"]}, {"$set": doc}, upsert=True)
        results.append({**doc, "filename": r.get("filename", "")})

    results.sort(key=lambda x: x["score"], reverse=True)
    log.info("match_run user=%s job_id=%s resumes=%d", user_id, job_id, len(results))
    return ok("match results", job_id=str(job["_id"]), results=results)

@match_bp.get("/job/<job_id>")
@jwt_required()
def list_matches_for_job(job_id):
    if not ObjectId.is_valid(job_id):
        return fail("invalid job_id", 422)
    db = get_db()
    items = list(db["matches"].find({"job_id": job_id}))
    items.sort(key=lambda x: x.get("score", 0), reverse=True)
    out = []
    for m in items:
        res = db["resumes"].find_one({"_id": ObjectId(m["resume_id"])}, {"filename": 1})
        out.append({
            "resume_id": m["resume_id"],
            "filename": (res or {}).get("filename", ""),
            "score": m.get("score", 0),
            "matched_skills": m.get("matched_skills", []),
            "missing_skills": m.get("missing_skills", []),
        })
    return ok("fetched matches", matches=out)
