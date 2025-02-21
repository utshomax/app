from sqlalchemy import Column, Integer, String, JSON, DateTime, Date, Float, Boolean, Text, BigInteger
from datetime import datetime
from core.database import Base, PGBase

class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True, index=True)
    uuid = Column(String(255), nullable=False, index=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    date_of_birth = Column(Date)
    gender = Column(String(1))
    telephone = Column(String(45))
    about = Column(Text)
    company_name = Column(String(512))
    is_company = Column(Boolean, nullable=False, default=False)
    language = Column(String(5), nullable=False, default='it_IT')
    email = Column(String(255), nullable=False)
    premium = Column(Boolean, default=False)
    cf = Column(String(18))
    timezone = Column(String(128), default='Europe/Rome')
    rating_as_worker = Column(Float, default=3)
    rating_as_offerer = Column(Float, default=3)
    business_name = Column(String(1024))
    birth_province_id = Column(BigInteger)
    birth_nation = Column(String(255))
    parent_id = Column(BigInteger)
    rating = Column(Float(4, 2))

class CandidateResume(PGBase):
    __tablename__ = 'candidate_resumes'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)  # Reference to User.id in MySQL
    resume_path = Column(String(255), unique=True, index=True)

    #data from jobby for faster search
    has_jobby_data = Column(Boolean, default=False)
    jobby_name = Column(String(255))
    jobby_gender = Column(String(10), nullable=True)  # Male, Female, Others
    jobby_telephone = Column(String(45))
    jobby_email = Column(String(255))
    jobby_date_of_birth = Column(Date)
    jobby_location = Column(String(255))  # GPS or preferred cities
    jobby_availability = Column(String(255))  # e.g., "Monday Morning, Tuesday Evening"
    jobby_about = Column(Text)  # Professional about/objective
    jobby_skills = Column(JSON)  # List of skills
    jobby_language = Column(String(45))  # List of languages
    jobby_certifications = Column(JSON)  # List of certifications
    jobby_education = Column(JSON)  # List of education records with institution, degree, dates, etc.
    jobby_jobs = Column(JSON)  # List of jobs with company, title, dates, etc.
    jobby_rating = Column(Float(4, 2))
    jobby_premium = Column(Boolean, default=False)
    jobby_reviews = Column(JSON)

    # data from resume
    name = Column(String(255))
    gender = Column(String(10), nullable=True)  # Male, Female, Others
    phone = Column(String(45))
    email = Column(String(255))
    location = Column(String(255))  # GPS or preferred cities
    # availability = Column(String(255))  # e.g., "Monday Morning, Tuesday Evening"
    about = Column(Text)  # Professional about/objective

    # Skills and Languages
    skills = Column(JSON)  # List of skills
    languages = Column(JSON)  # List of languages
    certifications = Column(JSON)  # List of certifications

    # Education and Experience
    education = Column(JSON)  # List of education records with institution, degree, dates, etc.
    experience = Column(JSON)  # List of work experiences with company, title, dates, etc.
    projects = Column(JSON)  # Projects worked on

    # Additional Professional Information
    achievements = Column(JSON)  # List of professional achievements
    publications = Column(JSON)  # List of publications if any
    volunteer_work = Column(JSON)  # Volunteer experience
    professional_links = Column(JSON)  # LinkedIn, portfolio, etc.

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)