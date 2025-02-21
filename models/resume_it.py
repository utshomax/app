from typing import Literal, Optional, List
from pydantic import BaseModel, Field

class Education(BaseModel):
    institution: str = Field(..., description="Nome dell'istituto di istruzione")
    degree: str = Field(..., description="Titolo di studio o certificazione ottenuta")
    field_of_study: Optional[str] = Field(None, description="Campo di studio principale o specializzazione")
    start_date: Optional[str] = Field(None, description="Data di inizio degli studi (formato AAAA-MM)")
    end_date: Optional[str] = Field(None, description="Data di fine degli studi (formato AAAA-MM o 'Presente')")
    gpa: Optional[float] = Field(None, description="Media dei voti su scala 4.0")

    class Config:
        json_schema_extra = {
            "example": {
                "institution": "Università di Milano",
                "degree": "Laurea Magistrale",
                "field_of_study": "Informatica",
                "start_date": "2019-09",
                "end_date": "2021-06",
                "gpa": 3.8
            }
        }

class Experience(BaseModel):
    experience_id: int = Field(..., description="Identificatore univoco per l'esperienza lavorativa")
    company: str = Field(..., description="Nome dell'azienda o organizzazione")
    title: str = Field(..., description="Titolo o posizione lavorativa")
    start_date: str = Field(..., description="Data di inizio impiego (formato AAAA-MM)")
    end_date: Optional[str] = Field(None, description="Data di fine impiego (formato AAAA-MM o 'Presente')")
    description: Optional[str] = Field(None, description="Descrizione dettagliata dei ruoli, responsabilità e risultati")
    location: Optional[str] = Field(None, description="Località del lavoro (Città, Regione, Paese)")

    class Config:
        json_schema_extra = {
            "example": {
                "company": "TechItalia SpA",
                "title": "Senior Software Engineer",
                "start_date": "2021-07",
                "end_date": "Presente",
                "description": "Guidato lo sviluppo di soluzioni cloud, gestito un team di 5 ingegneri",
                "location": "Milano, Lombardia, Italia"
            }
        }

class ResumeData(BaseModel):
    name: str = Field(..., description="Nome completo del candidato")
    email: Optional[str] = Field(None, description="Indirizzo email professionale")
    phone: Optional[str] = Field(None, description="Numero di telefono")
    location: Optional[str] = Field(None, description="Località attuale (Città, Regione, Paese)")
    gender: Optional[Literal["M", "F", "0"]] = Field(None, description="Genere (M: Maschio, F: Femmina, 0: Altro)")
    summary: Optional[str] = Field(None, description="Sommario professionale o dichiarazione di obiettivi")
    skills: List[str] = Field(default_factory=list, description="Competenze tecniche e professionali")
    projects: List[str] = Field(default_factory=list, description="Progetti notevoli completati")
    achievements: List[str] = Field(default_factory=list, description="Risultati professionali e accademici")
    publications: List[str] = Field(default_factory=list, description="Pubblicazioni e articoli di ricerca")
    experience: List[Experience] = Field(default_factory=list, description="Esperienza professionale")
    education: List[Education] = Field(default_factory=list, description="Formazione accademica")
    languages: List[str] = Field(default_factory=list, description="Lingue conosciute con livello di competenza")
    certifications: List[str] = Field(default_factory=list, description="Certificazioni e licenze professionali")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Marco Rossi",
                "email": "marco.rossi@esempio.it",
                "phone": "+39 123 456 7890",
                "location": "Milano, Lombardia, Italia",
                "gender": "M",
                "summary": "Ingegnere software esperto con oltre 8 anni di esperienza nello sviluppo full-stack",
                "skills": ["Python", "JavaScript", "AWS", "Docker", "React"],
                "projects": ["Sviluppato architettura microservizi scalabile", "Implementato sistema di raccomandazione basato su ML"],
                "achievements": ["Depositato 2 brevetti", "Aumentato le prestazioni del sistema del 40%"],
                "publications": ["Machine Learning in Produzione: Best Practices"],
                "experience": [
                    {
                        "experience_id": 1,
                        "company": "TechItalia SpA",
                        "title": "Senior Software Engineer",
                        "start_date": "2021-07",
                        "end_date": "Presente",
                        "description": "Guidato lo sviluppo di soluzioni cloud",
                        "location": "Milano, Lombardia, Italia"
                    }
                ],
                "education": [
                    {
                        "institution": "Università di Milano",
                        "degree": "Laurea Magistrale",
                        "field_of_study": "Informatica",
                        "start_date": "2019-09",
                        "end_date": "2021-06",
                        "gpa": 3.8
                    }
                ],
                "languages": ["Italiano (Madrelingua)", "Inglese (Intermedio)"],
                "certifications": ["AWS Certified Solutions Architect", "Google Cloud Professional Engineer"]
            }
        }