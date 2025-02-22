from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from .resume import Experience

class ExperienceRelevance(BaseModel):
    experience_id: int = Field(
        description="ID of the relevent experience experience_from_resume ( strict )"
    )
    is_relevant: bool = Field(
        description="Indicates whether the experience is relevant to the job description"
    )

class CandidateEvaluation(BaseModel):
    # Badge di Feedback - minimo 5 richiesti
    feedback_badges: List[str] = Field(
        description="Lista dei badge di feedback che evidenziano le caratteristiche chiave"
    )

    # Punteggio di Corrispondenza su 100
    matching_score: float = Field(
        description="Punteggio complessivo di corrispondenza del candidato (0-100)"
    )

    # Punti di Forza - esattamente 3 punti
    strengths: List[str] = Field(
        description="Principali punti di forza del candidato (Max : 3)"
    )

    # Punti di Attenzione - massimo 3 punti
    caution_points: List[str] = Field(
        description="Punti di attenzione o aree di miglioramento (Max : 3)"
    )

    # Panoramica del Profilo del Candidato
    profile_overview: str = Field(
        description="Panoramica completa del profilo del candidato"
    )

    # Disponibilità e Preferenze
    location_preferences: List[str] = Field(
        default_factory=list,
        description="Località di lavoro preferite"
    )
    remote_work_preference: str = Field(
        description="Preferenze di lavoro remoto (es., 'Solo remoto', 'Ibrido', 'Solo in sede')"
    )

    # Valutazione della Rilevanza dell'Esperienza
    experience_relevance: List[ExperienceRelevance] = Field(
        description="Valutazione della rilevanza per ogni esperienza dal curriculum (Massimo 4)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "feedback_badges": [
                    "Esperto Tecnico",
                    "Team Player",
                    "Apprendimento Rapido",
                    "Problem Solver",
                    "Innovatore"
                ],
                "matching_score": 85.5,
                "strengths": [
                    "Solida preparazione tecnica",
                    "Eccellenti capacità comunicative",
                    "Comprovata esperienza di leadership"
                ],
                "caution_points": [
                    "Esperienza limitata in ambiente startup",
                    "Potrebbe necessitare di mentoring in tecnologie cloud"
                ],
                "profile_overview": "Ingegnere software esperto con più di 5 anni di esperienza in applicazioni aziendali",
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
                "location_preferences": ["Milano", "Roma", "Torino"],
                "remote_work_preference": "Ibrido"
            }
        }