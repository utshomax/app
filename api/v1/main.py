from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Generator

from core.database import get_db, get_pg_db
from logic.collect import collect_candidate_data
from services import ServiceManager, get_service_manager
from models.sql import CandidateResume
from logic.resume import get_resume_path, check_existing_resume, store_resume_data
import logging
import core.database
from services.evaluator import CandidateEvaluator

app = FastAPI(
    title="Jobby API",
    description="API for resume parsing and candidate evaluation",
    version="1.0.0"
)

@app.post("/resumes/parse")
async def parse_resume(
    candidate_id: int,
    service_manager: ServiceManager = Depends(get_service_manager),
    pg_db: Session = Depends(get_pg_db)
) -> Dict[str, Any]:
    try:
        # Get resume path
        path_result = get_resume_path(service_manager, candidate_id)
        if "error" in path_result:
            return path_result
        resume_path = path_result["resume_path"]
        
        # Check if resume exists
        existing_result = check_existing_resume(pg_db, resume_path)
        if existing_result["exists"]:
            return {"success": True, "message": "Resume already processed", "resume_id": existing_result["resume_id"], "data": existing_result["resume_data"]}
    
        # Get resume from S3
        logging.info(f"Fetching resume from path: {resume_path}")
        temp_resume_path = service_manager.s3.fetch_resume(resume_path)
        if not temp_resume_path:
            return {"success": False,"error": "Failed to fetch resume from storage"}

        # Process resume
        result = await service_manager.resume_parser.process_resume(temp_resume_path, candidate_id)
        if "error" in result:
            return result
        
        # Store resume data
        store_result =await store_resume_data(pg_db, candidate_id, resume_path, result)
        if "error" in store_result:
            return store_result
            
        result['resume_id'] = store_result["resume_id"]
        return {"success": True,"message": "Resume processed and stored successfully", "data": result}

    except Exception as e:
        if pg_db and hasattr(pg_db, 'is_active') and pg_db.is_active:
            pg_db.rollback()
        logging.error(f"Error processing resume for candidate {candidate_id}: {str(e)}")
        return {"success": False, "error": f"Failed to process resume: {str(e)}"}

@app.get("/candidates/search")
async def search_candidates(
    query: str,
    pg_db: Session = Depends(get_pg_db),
) -> Dict[str, Any]:
    """Search and evaluate candidates based on criteria"""
    return await CandidateEvaluator(pg_db).search_candidates(query)

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