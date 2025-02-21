from typing import Optional, List
from pydantic import BaseModel, EmailStr
from datetime import date, datetime


class UserProfile(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None  # Consider using an Enum for gender if possible
    email: EmailStr
    telephone: Optional[str] = None
    about: Optional[str] = None
    avatar: Optional[str] = None
    company_name: Optional[str] = None
    is_company: bool = False
    language: str = "it_IT"  # Default value
    created_at: datetime
    updated_at: Optional[datetime] = None
    premium: Optional[bool] = False
    timezone: str = "Europe/Rome"  # Default value
    rating_as_worker: Optional[float] = 3.0 # Default value
    rating_as_offerer: Optional[float] = 3.0 # Default value
    business_name: Optional[str] = None
    birth_nation: Optional[str] = None
    rating: Optional[float] = None # STORED GENERATED, but might be useful in the model
    # The following fields are not directly present in the schema, but are derived/related
    # and useful for data curation and selection
    skills: Optional[List[str]] = None  # Hard and Soft Skills
    location_preferences: Optional[List[str]] = None  # Could be a list of cities/regions
    availability: Optional[str] = None  # Days & Time
    certifications: Optional[List[str]] = None
    experience: Optional[str] = None # Description of experience.
    resume: Optional[str] = None
    personal_description: Optional[str] = None

#TODO: Just get the data from the resume and get the data from the database, then use the evaluation function to get the score