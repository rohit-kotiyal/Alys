import os
from dotenv import load_dotenv


load_dotenv()


class Config:

    # CORS = Cross-Origin Resource Sharing
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    
    # File Configuration
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", 10485760))
    ALLOWED_EXTENSIONS: list = os.getenv("ALLOWED_EXTENSIONS", "csv").split(",")


config = Config()