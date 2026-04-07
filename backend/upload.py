from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import os
from config import config
from utils import (
    create_upload_folder,
    is_allowed_file,
    generate_unique_filename,
    validate_file_size
)


router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):

    if not is_allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(config.ALLOWED_EXTENSIONS)}"
        )

    file_content = await file.read()
    file_size = len(file_content)

    is_valid, error_message = validate_file_size(file_size)

    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
    upload_folder = create_upload_folder()

    unique_filename = generate_unique_filename(file.filename)
    file_path = os.path.join(upload_folder, unique_filename)

    try:
        with open(file_path, "wb") as f:
            f.write(file_content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )
    
    try:
        df = pd.read_csv(file_path)
    
    except pd.errors.EmptyDataError:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="CSV file is empty")
    
    except pd.errors.ParserError as e:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")
    
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to parse csv: {str(e)}")
    

    try:
        metadata = {
            "filename": unique_filename,
            "original_filename": file.filename,
            "size_bytes": file_size,
            "size_readable": f"{file_size / 1024 / 1024:.2f} MB",
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.to_list(),
            "column_types": df.dtypes.astype(str).to_dict(),
            "preview": df.head(5).to_dict(orient="records"),
            "file_path": file_path

        }
        return JSONResponse(
            status_code=200,
            content = {
                "message": "File Uploaded Successfully",
                "data": metadata
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract metadata: {str(e)}"
        )
    
