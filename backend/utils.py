import os
from datetime import datetime
from typing import Optional



def create_upload_folder():
    """ create folder if it doesn't exist """
    upload_folder = os.getenv("UPLOAD_FOLDER", "uploads")

    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    return upload_folder


def is_allowed_file(filename: str) -> bool:
    """ checks is file extension is allowed """
    allowed_extensions = os.getenv("ALLOWED_EXTENSIONS", "csv").split(",")

    file_extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    return file_extension in allowed_extensions


def generate_unique_filename(original_filename: str) -> str:
    """ to avoid conflicts """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    filename, extension = original_filename.rsplit(".", 1) if "." in original_filename else (original_filename, "")

    unique_filename = f"{filename}_{timestamp}.{extension}" if extension else f"{filename}_{timestamp}"

    return unique_filename


def format_file_size(size_bytes: int) -> str:
    """ convert file size to human readable format """

    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.1f} TB"


def validate_file_size(file_size: int) -> tuple[bool, Optional[str]]:
    
    max_size = int(os.getenv("MAX_FILE_SIZE", "10485760")) # default 10MB

    if file_size > max_size:
        return False, f"File too large. Maximum size: {format_file_size(max_size)}"
    
    return True, None

