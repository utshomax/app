from typing import Dict, Any
from sqlalchemy.orm import Session
import logging

from services import ServiceManager, get_service_manager
from models.sql import CandidateResume
from .collect import collect_candidate_data
from sqlalchemy.dialects.postgresql import insert


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

def sanitize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize data by removing NUL characters from string values

    Args:
        data (Dict[str, Any]): Data dictionary to sanitize

    Returns:
        Dict[str, Any]: Sanitized data dictionary
    """
    if not isinstance(data, dict):
        return data

    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            # Replace NUL characters with empty string
            sanitized[key] = value.replace('\x00', '')
        elif isinstance(value, dict):
            sanitized[key] = sanitize_data(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_data(item) if isinstance(item, dict) else 
                             item.replace('\x00', '') if isinstance(item, str) else item 
                             for item in value]
        else:
            sanitized[key] = value
    return sanitized

async def store_resume_data(pg_db: Session, candidate_id, candidate_data, resume_path: str, result: Dict[str, Any], blended: bool=False) -> Dict[str, Any]:
    """Store resume data in PostgreSQL"""
    try:
        logging.info(f"Storing resume data for path: {resume_path}")
        if not candidate_data:
            return {"error": "Candidate basic info not found"}

        # Prepare data for insert/update
        data = {
            'has_jobby_data': blended,
            'jobby_name': candidate_data.get('basic_info', {}).get('first_name', '') + ' ' + candidate_data.get('basic_info', {}).get('last_name', ''),
            'jobby_gender': candidate_data.get('basic_info', {}).get('gender'),
            'jobby_telephone': candidate_data.get('basic_info', {}).get('telephone'),
            'jobby_email': candidate_data.get('basic_info', {}).get('email'),
            'jobby_date_of_birth': candidate_data.get('basic_info', {}).get('date_of_birth'),
            'jobby_about': candidate_data.get('basic_info', {}).get('about'),
            'jobby_rating': candidate_data.get('basic_info', {}).get('rating_as_worker'),
            'jobby_premium': candidate_data.get('basic_info', {}).get('premium'),
            'jobby_jobs': candidate_data.get('jobs'),
            'jobby_language': candidate_data.get('basic_info', {}).get('language'),
            'jobby_certifications': candidate_data.get('certifications'),
            'resume_path': resume_path,
            'user_id': candidate_id,
            **result.get('data', {})
        }

        # Sanitize data before storing
        sanitized_data = sanitize_data(data)

        stmt = insert(CandidateResume).values(**sanitized_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=['resume_path'],
            set_={col.name: stmt.excluded[col.name] for col in CandidateResume.__table__.columns if col.name != 'id'}
        )

        pg_db.execute(stmt)
        pg_db.commit()

        return {"success": True}

    except Exception as e:
        logging.error(f"Error storing resume data: {str(e)}")
        raise e
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
          "about": existing_resume.about,
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
    return {"exists": True, "resume_id": existing_resume.id, "data": resume_data}


async def get_resume_result(service_manager: ServiceManager, resume_path:str, candidate_id: int, structured: bool=True) -> Dict[str, Any]:
    # Get resume from S3
    logging.info(f"Fetching resume from path: {resume_path}")
    temp_resume_path = service_manager.s3.fetch_resume(resume_path)
    if not temp_resume_path:
        return None
    # Process resume

    if not structured:
       content = service_manager.resume_parser.parse_file(temp_resume_path)
       return [{"content": content}]
    parsed_result = await service_manager.resume_parser.process_resume(temp_resume_path, candidate_id)
    return [parsed_result]


def blend_data(resume_data: Dict[str, Any], candidate_data: Dict[str, Any]):
    """Blend resume data with candidate data"""
    jobby_certifications=candidate_data.get('certifications'),
    jobby_language=candidate_data.get('basic_info', {}).get('language'),
    jobby_about=candidate_data.get('basic_info', {}).get('about'),

               # Prepare data for merging
    data_to_send = f"Jobby Data: \nAbout {jobby_about} \n Certifications {jobby_certifications} \n Language {jobby_language}"
    resume_content = f"Resume Data: \n{resume_data.get('content', '')}"

    return data_to_send + resume_content