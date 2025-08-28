from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from pymongo import MongoClient

# --- centralized Config import (loads .env inside) ---
from app.config import Config

import logging

# --- App + CORS ---
app = Flask(__name__)
CORS(app)

# --- Apply config
app.config.from_object(Config)  

# --- Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("resume_backend")

# --- JWT setup 
jwt = JWTManager(app)  

# --- Mongo connection 
mongo_uri = app.config["MONGO_URI"]             
client = MongoClient(mongo_uri)
db_name = mongo_uri.rsplit("/", 1)[-1] or "resume_screener"
app.config["MONGO_DB"] = client[db_name]


try:
    from app.models.db import ensure_indexes
    ensure_indexes()
except Exception as e:
    logger.warning("Index setup skipped or failed: %s", e)

# --- Health + home routes 
@app.get("/api/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.get("/")
def home():
    return "Backend is running", 200

# --- Blueprints
from app.routes.auth import auth_bp
from app.routes.resumes import resumes_bp
from app.routes.jobs import jobs_bp
from app.routes.match import match_bp  

app.register_blueprint(auth_bp)
app.register_blueprint(resumes_bp)
app.register_blueprint(jobs_bp)
app.register_blueprint(match_bp)       

if __name__ == "__main__":
    print(app.url_map)
    app.run(host="127.0.0.1", port=app.config["PORT"], debug=True)  