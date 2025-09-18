# backend/app/app.py
from flask import Flask, jsonify
from flask import request, make_response
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
from app.routes.scan import scan_bp
from app.config import Config
import logging
from app.routes.scans import scans_bp
import os

# --- App ---
app = Flask(__name__)

# --- Apply config FIRST (so CORS can read FRONTEND_ORIGIN) ---
app.config.from_object(Config)


def _norm_origin(o: str | None) -> str | None:
    if not o:
        return None
    return o.strip().rstrip("/")


origins_csv = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173"
)

_allowed = []
for part in origins_csv.split(","):
    n = _norm_origin(part)
    if n:
        _allowed.append(n)
allowed_origins = set(_allowed)

CORS(
    app,
    resources={r"/api/*": {"origins": list(allowed_origins)}},
    supports_credentials=False,  # using Bearer tokens, not cookies
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Authorization"],
)


@app.after_request
def _add_cors_headers(resp):
    try:
        origin = _norm_origin(request.headers.get("Origin"))
        if request.path.startswith("/api/") and origin in allowed_origins:
            resp.headers["Access-Control-Allow-Origin"] = origin
            # Tells caches that responses vary by Origin (prevents caching bugs)
            resp.headers["Vary"] = "Origin"
            resp.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
            resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    finally:
        return resp

# NEW: explicit preflight responder so OPTIONS never 404s
@app.route("/api/<path:_subpath>", methods=["OPTIONS"])
def _cors_preflight(_subpath):
    return make_response(("", 204))


# --- Logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("resume_backend")

# --- JWT setup ---
jwt = JWTManager(app)

# --- Mongo connection ---
mongo_uri = app.config["MONGO_URI"]
client = MongoClient(mongo_uri)

# Prefer explicit name from config; otherwise parse from URI and strip any query part
db_name = app.config.get("MONGO_DB_NAME")
if not db_name:
    tail = mongo_uri.rsplit("/", 1)[-1]
    db_name = (tail.split("?", 1)[0]) or "resume_screener"

app.config["MONGO_DB"] = client[db_name]

# --- Ensure indexes (inside app context) ---
try:
    from app.models.db import ensure_indexes
    with app.app_context():
        ensure_indexes()
except Exception as e:
    logger.warning("Index setup skipped or failed: %s", e)

# --- Health + home routes ---
@app.get("/api/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.get("/")
def home():
    return "Backend is running", 200

# --- Blueprints ---
from app.routes.auth import auth_bp
app.register_blueprint(auth_bp)
app.register_blueprint(scan_bp)
app.register_blueprint(scans_bp)

if __name__ == "__main__":
    print(app.url_map)
    app.run(host="127.0.0.1", port=app.config["PORT"], debug=True)
