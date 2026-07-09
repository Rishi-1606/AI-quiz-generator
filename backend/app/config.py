import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./quiz_generator.db")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
