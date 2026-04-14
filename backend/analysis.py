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


@router.post("analyze/top")
async def get_top_records(
    filename: str,
    column: str,
    n: int = 10,
    ascending: bool = False
):
    file_path = os.path.join(config.UPLOAD_FOLDER, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        df = pd.read_csv(file_path)
        
        if column not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Column '{column}' not found"
            )
        
        # Sort and get top N
        sorted_df = df.sort_values(by=column, ascending=ascending).head(n)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": f"Top {n} records by {column}",
                "total_returned": len(sorted_df),
                "sorted_by": column,
                "order": "ascending" if ascending else "descending",
                "data": sorted_df.to_dict(orient="records")
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get top records: {str(e)}"
        )



@router.post("/analyze/correlation")
async def get_correlation(filename: str):
    file_path = os.path.join(config.UPLOAD_FOLDER, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        df = pd.read_csv(file_path)
        
        # Get only numeric columns
        numeric_df = df.select_dtypes(include=['number'])
        
        if numeric_df.empty:
            return JSONResponse(
                status_code=200,
                content={"message": "No numeric columns found for correlation"}
            )
        
        # Calculate correlation
        correlation = numeric_df.corr()
        
        # Round for readability
        correlation = correlation.round(3)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Correlation matrix calculated",
                "columns": correlation.columns.tolist(),
                "correlation_matrix": correlation.to_dict()
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Correlation calculation failed: {str(e)}"
        )



@router.post("/analyze/aggregate")
async def aggregate_data(
    filename: str,
    columns: List[str],
    operations: List[str]
):
    file_path = os.path.join(config.UPLOAD_FOLDER, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        df = pd.read_csv(file_path)
        
        results = {}
        
        for column in columns:
            if column not in df.columns:
                continue
            
            column_results = {}
            
            for operation in operations:
                if operation == "sum":
                    column_results["sum"] = float(df[column].sum())
                elif operation == "mean":
                    column_results["mean"] = float(df[column].mean())
                elif operation == "min":
                    column_results["min"] = float(df[column].min())
                elif operation == "max":
                    column_results["max"] = float(df[column].max())
                elif operation == "count":
                    column_results["count"] = int(df[column].count())
                elif operation == "median":
                    column_results["median"] = float(df[column].median())
                elif operation == "std":
                    column_results["std"] = float(df[column].std())
            
            results[column] = column_results
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Aggregation complete",
                "results": results
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Aggregation failed: {str(e)}"
        )



@router.post("/analyze/value-counts")
async def get_value_counts(
    filename: str,
    column: str,
    top_n: Optional[int] = None
):
    file_path = os.path.join(config.UPLOAD_FOLDER, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        df = pd.read_csv(file_path)
        
        if column not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Column '{column}' not found"
            )
        
        # Get value counts
        value_counts = df[column].value_counts()
        
        if top_n:
            value_counts = value_counts.head(top_n)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": f"Value counts for {column}",
                "column": column,
                "total_unique": int(df[column].nunique()),
                "counts": value_counts.to_dict(),
                "showing": len(value_counts)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Value counts failed: {str(e)}"
        )