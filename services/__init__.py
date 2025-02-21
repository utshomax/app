from typing import Optional
from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db, get_pg_db
from .jobby import JobbyDBService
from .evaluator import CandidateEvaluator
from .resume_parser import ResumeParserService
from .s3 import S3Service

class ServiceManager:
    _instance = None
    _db: Optional[Session] = None
    _jobby_service: Optional[JobbyDBService] = None
    _evaluator_service: Optional[CandidateEvaluator] = None
    _resume_parser_service: Optional[ResumeParserService] = None
    _s3_service: Optional[S3Service] = None

    def __new__(cls, db: Session = None):
        if cls._instance is None:
            cls._instance = super(ServiceManager, cls).__new__(cls)
        if db is not None:
            # Ensure db is a Session object, not a generator
            if hasattr(db, '__next__'):
                try:
                    cls._db = next(db)
                except StopIteration:
                    # Handle the case where the generator is exhausted
                    cls._db = None
            else:
                cls._db = db
        return cls._instance

    @property
    def jobby(self) -> JobbyDBService:
        if self._jobby_service is None:
            self._jobby_service = JobbyDBService(self._db)
        return self._jobby_service

    @property
    def resume_parser(self) -> ResumeParserService:
        if self._resume_parser_service is None:
            self._resume_parser_service = ResumeParserService(self._db)
        return self._resume_parser_service

    @property
    def s3(self) -> S3Service:
        if self._s3_service is None:
            self._s3_service = S3Service()
        return self._s3_service

    def reset(self):
        """Reset all service instances"""
        self._jobby_service = None
        self._evaluator_service = None
        self._resume_parser_service = None
        self._s3_service = None
        self._db = None

# Initialize ServiceManager
def get_service_manager(db: Session = Depends(get_db)) -> ServiceManager:
    return ServiceManager(db)

# Create a dependency function that returns the ServiceManager instance
async def get_sm(db: Session = Depends(get_db)) -> ServiceManager:
    return get_service_manager(db)