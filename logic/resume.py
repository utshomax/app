from typing import Dict, Any
from sqlalchemy.orm import Session
import logging

from services import ServiceManager, get_service_manager
from models.sql import CandidateResume
from .collect import collect_candidate_data


def get_resume_path(service_manager: ServiceManager, candidate_id: int) -> Dict[str, Any]:
    """Get resume path for a candidate"""
    resume_info = service_manager.jobby.get_resume_paths_by_dom_data_id(candidate_id)
    if not resume_info:
        logging.error(f"No resume path found for candidate {candidate_id}")
        return {"error": "Resume path not found for the candidate"}

    resume_path = resume_info[0].get('resume_path') if resume_info else None
    if not resume_path:
        return {"error": "Resume path not found in the data"}
    
    return {"success": True, "resume_path": resume_path}

def check_existing_resume(pg_db: Session, resume_path: str) -> Dict[str, Any]:
    """Check if resume already exists in PostgreSQL"""
    existing_resume = pg_db.query(CandidateResume).filter(CandidateResume.resume_path == resume_path).first()
    if existing_resume:
        logging.info(f"Resume already processed for path: {resume_path}")
        return make_candidate_profile_response(existing_resume)
    return {"exists": False}

async def store_resume_data(pg_db: Session,candidate_id, resume_path: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """Store resume data in PostgreSQL"""
    try:
        sm: ServiceManager = get_service_manager()
        candidate_data = await collect_candidate_data(sm, candidate_id)
        logging.info(f"Storing resume data for path: {resume_path}", extra={"candidate": candidate_data})
        if not candidate_data:
            return {"error": "Candidate basic info not found"}
        # Create a new CandidateResume object
        new_resume = CandidateResume(
            has_jobby_data=True,
            jobby_name=candidate_data.get('basic_info', {}).get('first_name', '') + ' ' + candidate_data.get('basic_info', {}).get('last_name', ''),
            jobby_gender=candidate_data.get('basic_info', {}).get('gender'),
            jobby_telephone=candidate_data.get('basic_info', {}).get('telephone'),
            jobby_email=candidate_data.get('basic_info', {}).get('email'),
            jobby_date_of_birth=candidate_data.get('basic_info', {}).get('date_of_birth'),
            jobby_about=candidate_data.get('basic_info', {}).get('about'),
            jobby_rating=candidate_data.get('basic_info', {}).get('rating_as_worker'),
            jobby_premium=candidate_data.get('basic_info', {}).get('premium'),
            jobby_jobs=candidate_data.get('jobs'),
            jobby_language=candidate_data.get('basic_info', {}).get('language'),
            jobby_certifications=candidate_data.get('certifications'),
            name=result['data'].get('name'),
            email=result['data'].get('email'),
            phone=result['data'].get('phone'),
            location=result['data'].get('location'),
            gender=result['data'].get('gender'),
            resume_path=resume_path,
            user_id=candidate_id,
            summary=result['data'].get('summary'),
            skills=result['data'].get('skills'),
            languages=result['data'].get('languages'),
            certifications=result['data'].get('certifications'),
            education=result['data'].get('education'),
            experience=result['data'].get('experience'),
            projects=result['data'].get('projects'),
            achievements=result['data'].get('achievements'),
            publications=result['data'].get('publications'),
            volunteer_work=result['data'].get('volunteer_work'),
            professional_links=result['data'].get('professional_links')
        )
        
        pg_db.add(new_resume)
        pg_db.commit()
        pg_db.refresh(new_resume)
        
        return {"success": True, "resume_id": new_resume.id}
    except Exception as e:
        logging.error(f"Error storing resume data: {str(e)}")
        return {"error": f"Failed to store resume data: {str(e)}"}
    
def make_candidate_profile_response(existing_resume) -> Dict[str, Any]:
    resume_data = {
      "success": True,
      "message": "Resume processed successfully",
      "candidate_id": existing_resume.user_id,
      "data": {
          "name": existing_resume.name,
          "email": existing_resume.email,
          "phone": existing_resume.phone,
          "location": existing_resume.location,
          "gender": existing_resume.gender,
          "summary": existing_resume.summary,
          "skills": existing_resume.skills,
          "languages": existing_resume.languages,
          "certifications": existing_resume.certifications,
          "education": existing_resume.education,
          "experience": existing_resume.experience,
          "projects": existing_resume.projects,
          "achievements": existing_resume.achievements,
          "publications": existing_resume.publications,
          "volunteer_work": existing_resume.volunteer_work,
          "professional_links": existing_resume.professional_links,
          "jobby" : {
            "gender": existing_resume.jobby_gender,
            "telephone": existing_resume.jobby_telephone,
            "email": existing_resume.jobby_email,
            "about": existing_resume.jobby_about,
            "rating": existing_resume.jobby_rating,
            "premium": existing_resume.jobby_premium,
            "jobs": existing_resume.jobby_jobs,
            "certifications": existing_resume.jobby_certifications
            #add localtion, availibility, 
          }
      }
    }
    return {"exists": True, "resume_id": existing_resume.id, "resume_data": resume_data}