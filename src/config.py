import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///../instance/condofix.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get("FLASK_DEBUG") == "1"
    MAX_IMAGE_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
