from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
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



@router.get("/files")
async def list_uploaded_files():
    upload_folder = config.UPLOAD_FOLDER

    if not os.path.exists(upload_folder):
        return JSONResponse(
            status_code=200,
            content={"files": [], "total": 0}
        )
    
    files = []
    for filename in os.listdir(upload_folder):
        if filename.endswith('.csv'):
            filepath = os.path.join(upload_folder, filename)
            file_stat = os.stat(filepath)

            parts = filename.rsplit('_', 2)
            if len(parts) == 3:
                original_name = parts[0] + '.csv'
            else:
                original_name = filename
            
            files.append({
                "filename": filename,
                "original_name": original_name,
                "size_bytes": file_stat.st_size,
                "size_readable": f"{file_stat.st_size / 1024:.2f} KB",
                "uploaded_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            })
    
    files.sort(key=lambda x: x['uploaded_at'], reverse=True)

    return JSONResponse(
        status_code=200,
        content={
            "files": files,
            "total": len(files)
        }
    )


@router.delete("/files/{filename}")
async def delete_file(filename: str):
    file_path = os.path.join(config.UPLOAD_FOLDER, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"File '{filename}' not found"
        )
    
    if not filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="Can only delete CSV files"
        )
    
    try:
        os.remove(file_path)
        return JSONResponse(
            status_code=200,
            content={
                "message": "File deleted successfully",
                "filename": filename
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete file: {str(e)}"
        )



@router.get("/files/{filename}/info")
async def get_file_info(filename: str):
    file_path = os.path.join(config.UPLOAD_FOLDER, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"File '{filename}' not found"
        )
    
    try:
        # Get file stats
        file_stat = os.stat(file_path)
        
        # Load CSV to get structure info
        df = pd.read_csv(file_path)
        
        return JSONResponse(
            status_code=200,
            content={
                "filename": filename,
                "size_bytes": file_stat.st_size,
                "size_readable": f"{file_stat.st_size / 1024:.2f} KB",
                "uploaded_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "column_types": df.dtypes.astype(str).to_dict(),
                "memory_usage": f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get file info: {str(e)}"
        )


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):

    if not is_allowed_file(file.filename or ""):
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

    unique_filename = generate_unique_filename(file.filename or "")
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
    
