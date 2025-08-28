#centralize environment configuration.

import os
from dotenv import load_dotenv

load_dotenv()  

class Config:
    
    PORT = int(os.getenv("PORT", "5050"))
    JWT_SECRET_KEY = os.getenv("JWT_SECRET", "dev_change_me")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/resume_screener")
    MAX_FILE_MB = float(os.getenv("MAX_FILE_MB", "10"))
