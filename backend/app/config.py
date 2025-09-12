import os
from dotenv import load_dotenv


load_dotenv()  

class Config:
    
    # server
    PORT = int(os.getenv("PORT", "5050"))
    
    # auth
    JWT_SECRET_KEY = os.getenv("JWT_SECRET", "dev_change_me")
    
    # database
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/resume_screener")
    
    # upload limits
    MAX_FILE_MB = float(os.getenv("MAX_FILE_MB", "10"))
    
    # semantic scoring feature flag
    USE_SEMANTIC = os.getenv("USE_SEMANTIC", "1") == "1"
    
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN".rstrip("/"))

