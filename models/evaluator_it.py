from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from .resume import Experience

class ExperienceRelevance(BaseModel):
    experience: Experience
    is_relevant: bool = Field(
        description="Indica se l'esperienza è rilevante per la descrizione del lavoro"
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

    # Sezione Informazioni
    about: str = Field(
        description="Background personale e professionale dettagliato del candidato"
    )

    # Valutazione delle Competenze
    technical_skills: List[str] = Field(
        default_factory=list,
        description="Competenze tecniche e professionali"
    )
    soft_skills: List[str] = Field(
        default_factory=list,
        description="Competenze trasversali e capacità interpersonali"
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

    certifications: List[str] = Field(default_factory=list, description="Certificazioni e licenze professionali")


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
                        "experience": {
                            "company": "Google",
                            "title": "Senior Software Engineer",
                            "start_date": "2021-07",
                            "end_date": "Presente",
                            "description": "Ha guidato lo sviluppo di soluzioni cloud, gestito un team di 5 ingegneri",
                            "location": "Mountain View, CA, USA"
                        },
                        "is_relevant": True
                    },
                    {
                        "experience": {
                            "company": "Azienda B",
                            "title": "Senior Software Engineer",
                            "start_date": "2021-01-01",
                            "end_date": "2022-12-31",
                            "description": "Ha guidato lo sviluppo di nuove funzionalità e iniziative",
                            "location": "Mountain View, CA, USA"
                        },
                        "is_relevant": False
                    }
                ],
                "certifications": [
                    "Certificazione 1",
                    "Certificazione 2"
                ],
                "about": "Ingegnere software esperto con una solida preparazione in tecnologie cloud e leadership del team. Noto per fornire soluzioni di alta qualità e mentoring per sviluppatori junior.",
                "technical_skills": ["Python", "AWS", "Docker", "Kubernetes", "React"],
                "soft_skills": ["Leadership", "Comunicazione", "Problem Solving", "Collaborazione in Team"],
                "location_preferences": ["Area della Baia di San Francisco", "Seattle", "New York"],
                "remote_work_preference": "Ibrido"
            }
        }