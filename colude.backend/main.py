import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Ensure root in path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Load environment variables
load_dotenv(dotenv_path=ROOT_DIR / ".env")

from matcher import calculate_match
from ai_engine.inference import predict_skills, predict_match
from llm_analyzer import analyse_resume

app = FastAPI(
    title="Resumind PyTorch Neural API",
    version="2.0.0",
    description="REST API backend for Resumind Resume Intelligence powered by PyTorch"
)

API_KEY = os.getenv("APP_API_KEY", "")


class ResumeRequest(BaseModel):
    resume_text: str = Field(min_length=15, description="Full text extracted from candidate resume")
    job_description: str = Field(min_length=10, description="Target job description")


@app.get("/")
def home():
    return {
        "application": "Resumind AI",
        "engine": "Custom PyTorch Neural Models",
        "status": "active"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "engine": "PyTorch Neural Architecture (SkillNet & MatchNet)",
        "models_loaded": True
    }


@app.post("/analyze")
def analyze_resume_endpoint(
    request: ResumeRequest,
    authorization: str = Header(default="")
):
    if API_KEY and authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    try:
        # 1. Deterministic match
        match_data = calculate_match(request.resume_text, request.job_description)

        # 2. Neural Skill Predictions
        skill_predictions = predict_skills(request.resume_text)

        # 3. Neural Match Score
        neural_score = predict_match(request.resume_text, request.job_description)

        # 4. Executive synthesis
        synthesis = analyse_resume(request.resume_text, request.job_description)

        return {
            "success": True,
            "overall_match_score": match_data.get("match_score", neural_score),
            "ats_compatibility_score": match_data.get("ats_score", 75),
            "neural_match_score": neural_score,
            "matched_skills": match_data.get("matched_skills", []),
            "missing_skills": match_data.get("missing_skills", []),
            "recommendations": match_data.get("recommendations", []),
            "neural_skill_predictions": skill_predictions[:10],
            "executive_analysis": synthesis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis pipeline error: {str(e)}")
