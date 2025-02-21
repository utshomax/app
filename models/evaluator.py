from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from .resume import Experience

class ExperienceRelevance(BaseModel):
    experience_id: int = Field(
        description="ID of the experience_from_resume"
    )
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
                        "experience_id": 1,
                        "is_relevant": True
                    },
                    {
                        "experience_id": 2,
                        "is_relevant": False
                    }
                ],
                "location_preferences": ["San Francisco Bay Area", "Seattle", "New York"],
                "remote_work_preference": "Hybrid"
            }
        }