# backend/app/app.py
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
from app.routes.scan import scan_bp
from app.config import Config
import logging
from app.routes.scans import scans_bp

# --- App ---
app = Flask(__name__)

# --- Apply config FIRST (so CORS can read FRONTEND_ORIGIN) ---
app.config.from_object(Config)

# --- CORS (dev localhost + optional prod origin) ---
allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
frontend_origin = app.config.get("FRONTEND_ORIGIN")
if frontend_origin:
    allowed_origins.append(frontend_origin)

CORS(
    app,
    resources={r"/api/*": {"origins": allowed_origins}},
    supports_credentials=False,  # using Bearer tokens, not cookies
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type", "Authorization"],
)

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
