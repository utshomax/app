from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from .resume import Experience

class ExperienceRelevance(BaseModel):
    experience: Experience
    is_relevant: bool = Field(
        description="Indicates whether the experience is relevant to the job description"
    )

class CandidateEvaluation(BaseModel):
    # Feedback Badges - minimum 5 required
    feedback_badges: List[str] = Field(
        description="List of feedback badges highlighting key characteristics"
    )

    # Matching Score out of 100
    matching_score: float = Field(
        description="Overall matching score of the candidate (0-100)"
    )

    # Strengths - exactly 3 points
    strengths: List[str] = Field(
        description="Main strengths of the candidate (Max : 3)"
    )

    # Points to Be Careful Of - maximum 3 points
    caution_points: List[str] = Field(
        description="Points of caution or areas for improvement (Max : 3)"
    )

    # Overview of Candidate Profile
    profile_overview: str = Field(
        description="Comprehensive overview of the candidate's profile"
    )

    # About Section
    about: str = Field(
        description="Detailed personal and professional background of the candidate"
    )

    # Skills Assessment
    technical_skills: List[str] = Field(
        default_factory=list,
        description="Technical skills and proficiencies"
    )
    soft_skills: List[str] = Field(
        default_factory=list,
        description="Soft skills and interpersonal abilities"
    )

    # Availability and Preferences
    location_preferences: List[str] = Field(
        default_factory=list,
        description="Preferred work locations"
    )
    remote_work_preference: str = Field(
        description="Remote work preferences (e.g., 'Remote only', 'Hybrid', 'On-site only')"
    )

    # Experience Relevance Assessment
    experience_relevance: List[ExperienceRelevance] = Field(
        description="Assessment of relevance for each experience_from_resume (Maximum 4)"
    )

    certifications: List[str] = Field(default_factory=list, description="Professional certifications and licenses")


    class Config:
        json_schema_extra = {
            "example": {
                "feedback_badges": [
                    "Technical Expert",
                    "Team Player",
                    "Fast Learner",
                    "Problem Solver",
                    "Innovation Driver"
                ],
                "matching_score": 85.5,
                "strengths": [
                    "Strong technical background",
                    "Excellent communication skills",
                    "Proven leadership experience"
                ],
                "caution_points": [
                    "Limited experience in startup environment",
                    "May need mentoring in cloud technologies"
                ],
                "profile_overview": "Experienced software engineer with 5+ years in enterprise applications",
                "experience_relevance": [
                    {
                        "experience": {
                            "company": "Google",
                            "title": "Senior Software Engineer",
                            "start_date": "2021-07",
                            "end_date": "Present",
                            "description": "Led development of cloud-based solutions, managed team of 5 engineers",
                            "location": "Mountain View, CA, USA"
                        },
                        "is_relevant": True
                    },
                    {
                        "experience": {
                            "company": "Company B",
                            "position": "Senior Software Engineer",
                            "start_date": "2021-01-01",
                            "end_date": "2022-12-31",
                            "description": "Led development of new features and initiatives",
                            "location": "Mountain View, CA, USA"
                        },
                        "is_relevant": False
                    }
                ],
                "certifications": [
                    "Certification 1",
                    "Certification 2"
                ],
                "about": "Experienced software engineer with a strong background in cloud technologies and team leadership. Known for delivering high-quality solutions and mentoring junior developers.",
                "technical_skills": ["Python", "AWS", "Docker", "Kubernetes", "React"],
                "soft_skills": ["Leadership", "Communication", "Problem Solving", "Team Collaboration"],
                "location_preferences": ["San Francisco Bay Area", "Seattle", "New York"],
                "remote_work_preference": "Hybrid"
            }
        }