from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class JobCategory(BaseModel):
    count: int
    category: str

class JobTitle(BaseModel):
    count: int
    title: str

class Jobs(BaseModel):
    total: int
    categories: List[JobCategory]
    job_titles: List[JobTitle]
    last_job_done: datetime

class BasicInfo(BaseModel):
    updated_at: datetime
    date_of_birth: datetime
    first_name: str
    last_name: str
    email: str
    telephone: Optional[str] = None
    gender: str
    language: str
    about: Optional[str] = None
    rating_as_worker: float
    premium: int

class CandidateData(BaseModel):
    certifications: List[str]
    jobs: Jobs
    basic_info: BasicInfo