from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import config
from upload import router as upload_router
from analysis import router as analysis_router
from charts import router as charts_router


app = FastAPI(
    title="Alys API",
    description="AI-powered Data Analyst Dashboard - Backend API",
)



app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(upload_router)
app.include_router(analysis_router)
app.include_router(charts_router)


@app.get("/")
def home():
    return {
        "message": "Alys API is running",
        "status": "Active"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Alys Backend"
    }