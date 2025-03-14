import asyncio
from fastapi import FastAPI, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Generator, Optional
from pydantic import BaseModel

from core.database import get_db, get_pg_db
from logic.collect import collect_candidate_data
from services import ServiceManager, get_service_manager
from models.sql import CandidateResume
from logic.resume import check_existing_resume, get_resume_path, store_resume_data, get_resume_result,blend_data
import logging
import core.database
from services.evaluator import CandidateEvaluator
from utils.structure import DataStructureService

app = FastAPI(
    title="Jobby API",
    description="""API for resume parsing and candidate evaluation.
    
    The search endpoint (/candidates/search) accepts a POST request with a JSON body containing:
    - query: Required search query string
    - location: Optional list of locations to filter by
    - experience_level: Optional list of experience levels (e.g., "1-3 years")
    - soft_skills: Optional list of soft skills to filter by
    - hard_skills: Optional list of hard skills to filter by
    - languages: Optional list of languages to filter by
    - certifications: Optional list of certifications to filter by
    """,
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    query: str
    location: Optional[List[str]] = None
    experience_level: Optional[List[str]] = None
    soft_skills: Optional[List[str]] = None
    hard_skills: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    certifications: Optional[List[str]] = None

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "jobby-api",
        "version": app.version
    }

@app.post("/resumes/parse/")
async def parse_resume(
    candidate_id: int,
    blend: bool = False,
    service_manager: ServiceManager = Depends(get_service_manager),
    pg_db: Session = Depends(get_pg_db)
) -> Dict[str, Any]:
    try:
        path_result = get_resume_path(service_manager, candidate_id)
        if "error" in path_result:
            return path_result
        resume_path = path_result["resume_path"]

        # Check if resume exists
        existing_result = check_existing_resume(pg_db, resume_path)
        if existing_result["exists"] and existing_result["blended"] == blend:
            return existing_result

        # Process resume and collect candidate data concurrently
        tasks = [
            get_resume_result(service_manager, resume_path, candidate_id, structured=not blend),
            collect_candidate_data(service_manager, candidate_id)
        ]
        resume_result, candidate_data = await asyncio.gather(*tasks)

        if not resume_result:
            return {"error": "Failed to process resume"}
        data_to_store = resume_result[0]
        if blend:
            structureService = DataStructureService()
            content = blend_data(data_to_store, candidate_data)
            structured_data = structureService.struture_resume_with_blended_jobby_data(content)
            store_result = await store_resume_data(pg_db, candidate_id, candidate_data, resume_path, {"data" : structured_data["parsed_data"]}, blended=blend)
            return store_result["data"]
        # Store resume data
        store_result = await store_resume_data(pg_db, candidate_id, candidate_data, resume_path, resume_result[0], blended=blend)
        return store_result["data"]

    except Exception as e:
        if pg_db and hasattr(pg_db, 'is_active') and pg_db.is_active:
            pg_db.rollback()
        logging.error(f"Error processing resume for candidate {candidate_id}: {str(e)}")
        return {"success": False, "error": f"Failed to process resume: {str(e)}"}

@app.post("/candidates/search")
async def search_candidates(
    request: SearchRequest,
    pg_db: Session = Depends(get_pg_db),
) -> Dict[str, Any]:
    """
    Search and evaluate candidates based on criteria with optional filters.
    
    Request body:
    - **query**: Natural language search query (e.g., "Find Java developers")
    - **location**: List of locations to filter by (e.g., ["New York", "San Francisco"])
    - **experience_level**: List of experience levels (e.g., ["1-3 years", "3-5 years"])
    - **soft_skills**: List of soft skills to filter by (e.g., ["communication", "teamwork"])
    - **hard_skills**: List of hard skills to filter by (e.g., ["Java", "Python"])
    - **languages**: List of languages to filter by (e.g., ["English", "Spanish"])
    - **certifications**: List of certifications to filter by (e.g., ["AWS", "PMP"])
    
    The search combines both semantic search (via the query parameter) and direct database filtering.
    Results will include candidates that match both the semantic search and the applied filters.
    
    Example request:
    ```json
    {
        "query": "Find experienced software developers",
        "location": ["Milan", "Rome"],
        "experience_level": ["3-5 years", "5+ years"],
        "hard_skills": ["Python", "JavaScript"],
        "languages": ["English", "Italian"],
        "certifications": ["AWS"]
    }
    ```
    """
    return await CandidateEvaluator(pg_db).search_candidates(
        request.query, 
        location=request.location,
        experience_level=request.experience_level,
        soft_skills=request.soft_skills,
        hard_skills=request.hard_skills,
        languages=request.languages,
        certifications=request.certifications
    )

@app.post("/candidates/evaluate")
async def evaluate_candidate(
    request: Dict[str, Any],
    pg_db: Session = Depends(get_pg_db),
) -> Dict[str, Any]:
    """Evaluate a candidate based on their resume data"""
    candidate_ids = request.get("candidate_ids", [])
    compare_with = request.get("compare_with", "")
    return await CandidateEvaluator(pg_db).evaluate_candidate_list(candidate_ids, compare_with)


@app.get("/collect_data/{candidate_id}")
async def collect_data(
    candidate_id: int,
    service_manager: ServiceManager = Depends(get_service_manager)
) -> Dict[str, Any]:
    """Collect data for a candidate"""
    data =await collect_candidate_data(service_manager, candidate_id)
    return {"success" : True, "message": "Data collected successfully", "data" : data}