from typing import Literal, Optional, List
from pydantic import BaseModel, Field

class Education(BaseModel):
    institution: str = Field(..., description="Name of the educational institution")
    degree: str = Field(..., description="Degree or certification obtained")
    field_of_study: Optional[str] = Field(None, description="Major field of study or specialization")
    start_date: Optional[str] = Field(None, description="Start date of education (YYYY-MM format)")
    end_date: Optional[str] = Field(None, description="End date of education (YYYY-MM format or 'Present')")
    gpa: Optional[float] = Field(None, description="Grade Point Average on a 4.0 scale")

    class Config:
        json_schema_extra = {
            "example": {
                "institution": "Stanford University",
                "degree": "Master of Science",
                "field_of_study": "Computer Science",
                "start_date": "2019-09",
                "end_date": "2021-06",
                "gpa": 3.8
            }
        }

class Experience(BaseModel):
    expeience_id: int = Field(..., description="Unique identifier for the experience entry")
    company: str = Field(..., description="Name of the company or organization")
    title: str = Field(..., description="Job title or position held")
    start_date: str = Field(..., description="Start date of employment (YYYY-MM format)")
    end_date: Optional[str] = Field(None, description="End date of employment (YYYY-MM format or 'Present')")
    description: Optional[str] = Field(None, description="Detailed description of roles, responsibilities, and achievements")
    location: Optional[str] = Field(None, description="Location of the job (City, State, Country)")

    class Config:
        json_schema_extra = {
            "example": {
                "expeience_id": 1,
                "company": "Google",
                "title": "Senior Software Engineer",
                "start_date": "2021-07",
                "end_date": "Present",
                "description": "Led development of cloud-based solutions, managed team of 5 engineers",
                "location": "Mountain View, CA, USA"
            }
        }

class ResumeData(BaseModel):
    name: str = Field(..., description="Full name of the candidate")
    email: Optional[str] = Field(None, description="Professional email address")
    phone: Optional[str] = Field(None, description="Contact phone number")
    location: Optional[str] = Field(None, description="Current location (City, State, Country)")
    gender: Optional[Literal["M", "F", "0"]] = Field(None, description="Gender (M: Male, F: Female, 0: Other)")
    about: Optional[str] = Field(None, description="Detailed personal and professional background of the candidate")
    skills: List[str] = Field(default_factory=list, description="Technical and Soft skills")
    projects: List[str] = Field(default_factory=list, description="Notable projects completed")
    achievements: List[str] = Field(default_factory=list, description="Personal, professional and academic achievements")
    publications: List[str] = Field(default_factory=list, description="Published works and research papers")
    experience: List[Experience] = Field(default_factory=list, description="Professional & Industry work experience")
    education: List[Education] = Field(default_factory=list, description="Educational background")
    languages: List[str] = Field(default_factory=list, description="Languages known with proficiency")
    certifications: List[str] = Field(default_factory=list, description="certifications and licenses")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1-123-456-7890",
                "location": "San Francisco, CA, USA",
                "gender": "M",
                "about": "Experienced software engineer with 8+ years in full-stack development",
                "skills": ["Python", "JavaScript", "AWS", "Docker", "React"],
                "projects": ["Built scalable microservices architecture", "Developed ML-powered recommendation system"],
                "achievements": ["Filed 2 patents", "Increased system performance by 40%"],
                "publications": ["Machine Learning in Production: Best Practices"],
                "experience": [
                    {   "expeience_id": 1,
                        "company": "Google",
                        "title": "Senior Software Engineer",
                        "start_date": "2021-07",
                        "end_date": "Present",
                        "description": "Led development of cloud-based solutions",
                        "location": "Mountain View, CA, USA"
                    }
                ],
                "education": [
                    {
                        "institution": "Stanford University",
                        "degree": "Master of Science",
                        "field_of_study": "Computer Science",
                        "start_date": "2019-09",
                        "end_date": "2021-06",
                        "gpa": 3.8
                    }
                ],
                "languages": ["English (Native)", "Spanish (Intermediate)"],
                "certifications": ["AWS Certified Solutions Architect", "Google Cloud Professional Engineer"]
            }
        }