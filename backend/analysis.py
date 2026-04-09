import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
from typing import Optional, List
from config import config



router = APIRouter(prefix="/api", tags=["Analysis"])



# HELPER Functions
def get_basic_info(df: pd.DataFrame) -> dict:
    return {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "column_names": df.columns.to_list(),
        "memory_usage": f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB"
    }


def get_summary_stats(df: pd.DataFrame) -> dict:
    
    numeric_df = df.select_dtypes(include=['number'])

    if numeric_df is None:
        return {"message": "No numeric columns found"}
    
    stats = numeric_df.describe().to_dict()

    for col in stats:
        for stat in stats[col]:
            stats[col][stat] = round(stats[col][stat], 2)

    return stats


def get_missing_data(df: pd.DataFrame) -> dict:
    
    missing = df.isnull().sum()
    total_rows = len(df)

    missing_info = {}

    for col, count in missing.items():
        if count > 0:
            percentage = (count / total_rows) * 100
            missing_info[col] = {
                "count": int(count),
                "percentage": round(percentage, 2)
            }
    
    if not missing_info:
        return {"message": "No missing values found.!"}
    
    return missing_info


def get_column_info(df: pd.DataFrame) -> dict:
    
    column_info = {}

    for col in df.columns:
        unique_count = df[col].nunique()

        dtype = str(df[col].dtype)

        sample_values = df[col].dropna().unique()[:3].tolist()

        column_info[col] = {
            "data_type": dtype,
            "unique_values": int(unique_count),
            "sample_values": sample_values
        }

    return column_info



@router.get("/analyze/{filename}")
async def analyze_csv(filename: str):
    
    file_path = os.path.join(config.UPLOAD_FOLDER, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File: {filename} not found.!")
    
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

    try:
        analysis_result = {
            "basic_info": get_basic_info(df),
            "summary_stats": get_summary_stats(df),
            "missing_data": get_missing_data(df),
            "column_info": get_column_info(df)
        }
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Analysis Complete",
                "filename": filename,
                "data": analysis_result
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis Failed: {str(e)}"
        )
    


@router.post("/analyze/group")
async def group_analysis(
    filename: str,
    group_column: str,
    agg_column: str,
    operation: str = "sum"
):
    
    file_path = os.path.join(config.UPLOAD_FOLDER, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"File {filename} not found"
        )
    
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")
    
    if group_column not in df.columns:
        raise HTTPException(status_code=404, detail=f"Columns {group_column} not found in csv")
    if agg_column not in df.columns:
        raise HTTPException(status_code=404, detail=f"Columns {agg_column} not found in csv")

    try:
        grouped = df.groupby(group_column)[agg_column]

        if operation == "sum":
            result = grouped.sum()
        elif operation == "mean":
            result = grouped.mean()
        elif operation == "count":
            result = grouped.count()
        elif operation == "min":
            result = grouped.min()
        elif operation == "max":
            result = grouped.max()
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid Operation. Use -> sum, mean, count, min & max only."
            )
        
        result = result.sort_values(ascending=False)

        return JSONResponse(
            status_code=200,
            content={
                "message": "Group Analysis Complete",
                "operation": f"{operation} of {agg_column} grouped by {group_column}",
                "results": result.to_dict()
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Grouped analysis failed: {str(e)}")
    


@router.post("/analyze/filter")
async def filter_data(
    filename: str,
    column: str,
    operator: str,
    value: str,
    limit: Optional[int] = 100
):
    
    file_path = os.path.join(config.UPLOAD_FOLDER, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File: {filename}, not found.!")
    
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Read error: {str(e)}")
    
    if column not in df.columns:
        raise HTTPException(status_code=404, detail=f"Column: {column} not found.!")
    
    try:
        try:
            value_numeric = float(value)
            is_numeric = True

        except ValueError:
            value_numeric = value
            is_numeric = False
        
        if operator == "eq":
            filtered = df[df[column] == value_numeric]
        elif operator == "gt" and is_numeric:
            filtered = df[df[column] > value_numeric]
        elif operator == "lt" and is_numeric:
            filtered = df[df[column] < value_numeric]
        elif operator == "gte":
            filtered = df[df[column] >= value_numeric]
        elif operator == "lte":
            filtered = df[df[column] <= value_numeric]
        elif operator == "contains":
            filtered = df[df[column].astype(str).str.contains(str(value), case=False)]
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid Operator. Use: eq, gt, lt, gte, lte & contains.!"
            )
        
        filtered = filtered.head(limit or 10)

        return JSONResponse(
            status_code=200,
            content={
                "message": "Filter Applied.!",
                "filter": f"{column} {operator} {value}",
                "total_matches": len(filtered),
                "showing": min(len(filtered), limit or 10),
                "data": filtered.to_dict(orient="records") 
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Filter failed: {str(e)}"
        )    
