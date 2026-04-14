from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import os
from typing import Optional, List
from config import config


router = APIRouter(prefix="/api/charts", tags=["charts"])


@router.post("/bar")
async def prepare_bar_chart(
    filename: str,
    x_column: str,
    y_column: str,
    limit: Optional[int] = 20
):
    file_path = os.path.join(config.UPLOAD_FOLDER, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        df = pd.read_csv(file_path)
        
        # Validate columns
        if x_column not in df.columns or y_column not in df.columns:
            raise HTTPException(status_code=400, detail="Column not found")
        
        # Group by x_column and sum y_column
        chart_data = df.groupby(x_column)[y_column].sum().sort_values(ascending=False)
        
        if limit:
            chart_data = chart_data.head(limit)
        
        return JSONResponse(
            status_code=200,
            content={
                "chart_type": "bar",
                "x_axis": x_column,
                "y_axis": y_column,
                "data": {
                    "labels": chart_data.index.tolist(),
                    "values": chart_data.values.tolist()
                }
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/line")
async def prepare_line_chart(
    filename: str,
    x_column: str,
    y_columns: List[str]
):
    file_path = os.path.join(config.UPLOAD_FOLDER, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        df = pd.read_csv(file_path)
        
        # Validate columns
        if x_column not in df.columns:
            raise HTTPException(status_code=400, detail=f"Column '{x_column}' not found")
        
        for col in y_columns:
            if col not in df.columns:
                raise HTTPException(status_code=400, detail=f"Column '{col}' not found")
        
        # Prepare series data
        series = []
        for y_col in y_columns:
            series.append({
                "name": y_col,
                "data": df[y_col].tolist()
            })
        
        return JSONResponse(
            status_code=200,
            content={
                "chart_type": "line",
                "x_axis": x_column,
                "labels": df[x_column].tolist(),
                "series": series
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pie")
async def prepare_pie_chart(
    filename: str,
    column: str,
    top_n: Optional[int] = 10
):
    file_path = os.path.join(config.UPLOAD_FOLDER, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        df = pd.read_csv(file_path)
        
        if column not in df.columns:
            raise HTTPException(status_code=400, detail="Column not found")
        
        # Get value counts
        value_counts = df[column].value_counts()
        
        if top_n and len(value_counts) > top_n:
            # Keep top N, group rest as "Other"
            top_values = value_counts.head(top_n)
            other_sum = value_counts[top_n:].sum()
            
            if other_sum > 0:
                top_values["Other"] = other_sum
            
            value_counts = top_values
        
        return JSONResponse(
            status_code=200,
            content={
                "chart_type": "pie",
                "column": column,
                "data": {
                    "labels": value_counts.index.tolist(),
                    "values": value_counts.values.tolist()
                }
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scatter")
async def prepare_scatter_chart(
    filename: str,
    x_column: str,
    y_column: str,
    limit: Optional[int] = 500
):
    file_path = os.path.join(config.UPLOAD_FOLDER, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        df = pd.read_csv(file_path)
        
        if x_column not in df.columns or y_column not in df.columns:
            raise HTTPException(status_code=400, detail="Column not found")
        
        # Get data
        scatter_df = df[[x_column, y_column]].dropna()
        
        if limit:
            scatter_df = scatter_df.head(limit)
        
        return JSONResponse(
            status_code=200,
            content={
                "chart_type": "scatter",
                "x_axis": x_column,
                "y_axis": y_column,
                "data": {
                    "points": [
                        {"x": float(row[x_column]), "y": float(row[y_column])}
                        for _, row in scatter_df.iterrows()
                    ]
                }
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))