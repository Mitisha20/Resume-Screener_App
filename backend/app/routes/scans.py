from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.db import scans_col
from app.utils.responses import ok, created, fail
from datetime import datetime
from bson import ObjectId

scans_bp = Blueprint("scans", __name__, url_prefix="/api/scans")

@scans_bp.post("/")
@jwt_required()
def save_scan():
    data = request.get_json(silent=True) or {}
    resume_text = (data.get("resume_text") or "")[:10000]
    jd_text = (data.get("jd_text") or "")[:10000]
    result = data.get("result") or {}

    if not resume_text or not jd_text or not isinstance(result, dict):
        return fail("resume_text, jd_text and result are required", 422)

    uid = get_jwt_identity()
    try:
        doc = {
            "user_id": ObjectId(uid),
            "created_at": datetime.utcnow(),
            "resume_text": resume_text,
            "jd_text": jd_text,
            "result": result,
        }
        ins = scans_col().insert_one(doc)
        return created("saved", id=str(ins.inserted_id))
    except Exception as e:
        return fail("could not save scan", 500, details=str(e))

@scans_bp.get("/")
@jwt_required()
def list_scans():
    uid = get_jwt_identity()
    try:
        limit = max(1, min(int(request.args.get("limit", 20)), 100))
    except:
        limit = 20
    try:
        cur = (scans_col()
               .find({"user_id": ObjectId(uid)})
               .sort("created_at", -1)
               .limit(limit))
        items = []
        for d in cur:
            items.append({
                "id": str(d["_id"]),
                "created_at": d.get("created_at").isoformat() + "Z",
                "score": float(d.get("result", {}).get("score", 0)),
                "matched": len(d.get("result", {}).get("matched_skills", [])),
                "missing": len(d.get("result", {}).get("missing_skills", [])),
                "resume_preview": (d.get("resume_text", "")[:120] + "...") if d.get("resume_text") else "",
                "jd_preview": (d.get("jd_text", "")[:120] + "...") if d.get("jd_text") else "",
                "resume_text": d.get("resume_text", ""),
                "jd_text": d.get("jd_text", ""),
                "result": d.get("result", {}),
            })
        return ok("fetched", items=items)
    except Exception as e:
        return fail("could not list scans", 500, details=str(e))
