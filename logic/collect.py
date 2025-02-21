from services import ServiceManager, get_service_manager
from services.jobby import JobbyDBService
import logging
from  models.candidate import CandidateData



async def collect_jobby_data(sm: ServiceManager, candidate_id: int):
    import asyncio
    from functools import partial
    from core.database import SessionLocal

    async def run_sync(func, *args):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args)

    async def get_certifications():
        db = SessionLocal()
        try:
            jobby_service = JobbyDBService(db)
            jobby_certifications = await run_sync(jobby_service.get_candidate_certifications, candidate_id)
            logging.info(f"Jobby certifications: {jobby_certifications}")
            return jobby_certifications
        finally:
            db.close()

    async def get_jobs():
        db = SessionLocal()
        try:
            jobby_service = JobbyDBService(db)
            jobby_jobs = await run_sync(jobby_service.get_candidate_jobs_done, candidate_id)
            logging.info(f"Jobby jobs: {jobby_jobs}")
            return jobby_jobs
        finally:
            db.close()
    async def get_skills():
        db = SessionLocal()
        try:
            jobby_service = JobbyDBService(db)
            jobby_skills = await run_sync(jobby_service.get_candidate_skills, candidate_id)
            logging.info(f"Jobby skills: {jobby_skills}")
            return jobby_skills
        finally:
            db.close()

    async def get_education():
        db = SessionLocal()
        try:
            jobby_service = JobbyDBService(db)
            jobby_education = await run_sync(jobby_service.get_candidate_education, candidate_id)
            logging.info(f"Jobby education: {jobby_education}")
            return jobby_education
        finally:
            db.close()

    async def get_basic_info():
        db = SessionLocal()
        try:
            jobby_service = JobbyDBService(db)
            jobby_basic_info = await run_sync(jobby_service.get_candidate_basic_info, candidate_id)
            logging.info(f"Jobby basic info: {jobby_basic_info}")
            return jobby_basic_info
        finally:
            db.close()

    certifications, jobs , basic_info = await asyncio.gather(
        get_certifications(),
        get_jobs(),
        get_basic_info(),
    )

    return {
        "certifications": certifications,
        "jobs": jobs,
        "basic_info": basic_info,
    }


async def collect_candidate_data(sm: ServiceManager, candidate_id: int) -> CandidateData:
    logging.info("Collecting data")
    return await collect_jobby_data(sm, candidate_id)