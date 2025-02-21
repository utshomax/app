from typing import List, Dict, Any
from sqlalchemy.orm import Session
from utils.structure import DataStructureService
from utils.text_to_sql import TextToSQLConverter
from openai import OpenAI
from models.evaluator import CandidateEvaluation
import os
from sqlalchemy import text
import logging

class CandidateEvaluator:
    def __init__(self, db: Session):
        self.db = db
        self.text_to_sql = TextToSQLConverter(db)
        self.table_names = ['candidate_resumes']
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.structure = DataStructureService()

    def get_candidates(self, candidate_ids: List):
        all_candidates = self.db.execute(text(f"SELECT * FROM candidate_resumes WHERE user_id IN ({','.join([str(id) for id in candidate_ids])})"))

        # Format the data
        rows = all_candidates.fetchall()
        if not rows:
            return []

        # Get column names and convert rows to dictionaries
        columns = all_candidates.keys()
        candidates_data = [dict(zip(columns, row)) for row in rows]
        return candidates_data
    async def search_candidates(self, search_query: str) -> Dict[str, Any]:
        """Search and evaluate candidates based on the search query with optimized performance"""
        try:
            # Convert natural language query to SQL
            sql_result = self.text_to_sql.execute_query(search_query, self.table_names)
            if 'error' in sql_result:
                return sql_result

            # Get candidates from database
            results = sql_result['results']
            if not results:
                return {
                    'sql': sql_result['sql'],
                    'candidates': [],
                }
            candidate_ids = [str(candidate['user_id']) for candidate in results]
            candidates = self.get_candidates(candidate_ids)
            # Optimize database query with batch processing

            return {
                 'sql': sql_result['sql'],
                 'candidates': candidates,
            }

        except Exception as e:
            logging.error(f"Error in search_candidates: {str(e)}")
            return {'error': str(e)}

    async def evaluate_candidate_list(self, candidate_ids:List, compare_with:str):
          import asyncio
          from concurrent.futures import ThreadPoolExecutor

          candidates_data = self.get_candidates(candidate_ids)
          async def evaluate_candidates_parallel():
              with ThreadPoolExecutor() as executor:
                  loop = asyncio.get_event_loop()
                  evaluation_tasks = [
                      loop.run_in_executor(executor, self.evaluate_candidate, candidate, compare_with)
                      for candidate in candidates_data
                  ]
                  return await asyncio.gather(*evaluation_tasks)

          # Execute parallel evaluations
          evaluations = await evaluate_candidates_parallel()
          logging.info(f"Evaluations completed for {len(evaluations)} candidates")

          return {
              'compare_with' : compare_with,
              'candidates': candidates_data,
              'evaluations': evaluations
          }
    
  

    
    def evaluate_candidate(self, candidate: Dict, compare_with: str) -> Dict:
        """Evaluate a single candidate using weighted criteria
        Args:
            candidate (Dict): Candidate data from database
            compare_with (str): Search text or requirements to compare against
        Returns:
            Dict: Structured and evaluated candidate data with scores
        """
        logging.info(f"Evaluating candidate: {candidate['user_id']}")
        try:
            # Prepare data for merging
            about_text = []
            if candidate.get('jobby_about'):
                about_text.append(candidate['jobby_about'])
            if candidate.get('summary'):
                about_text.append(candidate['summary'])

            # Merge skills
            skills = set()
            if candidate.get('jobby_skills'):
                skills.update(candidate['jobby_skills'])
            if candidate.get('skills'):
                skills.update(candidate['skills'])

            # Merge certifications
            certifications = set()
            if candidate.get('jobby_certifications'):
                certifications.update(candidate['jobby_certifications'])
            if candidate.get('certifications'):
                certifications.update(candidate['certifications'])

            # Prepare comprehensive candidate data
            candidate_data = {
                'profile_completion': {
                    'has_jobby_data': candidate.get('has_jobby_data', False),
                    'basic_info_complete': all([
                        candidate.get('jobby_name'),
                        candidate.get('jobby_email'),
                        candidate.get('jobby_telephone'),
                        candidate.get('jobby_gender')
                    ])
                },
                'experience_skills': {
                    'about': ' '.join(about_text),
                    'skills': list(skills),
                    'experience_from_resume': candidate.get('experience', []),
                    'jobby_jobs': candidate.get('jobby_jobs', {})
                },
                'location_availability': {
                    'location': candidate.get('jobby_location') or candidate.get('location'),
                    'availability': candidate.get('jobby_availability'),
                    'remote_work_possible': True  # Default to True, can be determined by job type
                },
                'performance': {
                    'rating': candidate.get('jobby_rating', 0.0),
                    'reviews': candidate.get('jobby_reviews', []),
                    'premium': candidate.get('jobby_premium', False)
                },
                'certifications_credentials': {
                    'certifications': list(certifications),
                    'languages': candidate.get('languages', []),
                    'education': candidate.get('education', [])
                }
            }

            # Use OpenAI to analyze and structure the data with scoring
            system_prompt = """You are an expert recruitment analyst. Evaluate the candidate data against the requirements using this scoring matrix:
                    - Profile Completeness & Verification (10%)
                        * Profile Completion Score (5%)
                        * Verification Status (5%)
                    - Experience & Skills (30%)
                        * Relevant Work Experience (15%)
                        * Experience in Jobby vs External (5%)
                        * Hard Skills Match (10%)
                    - Location & Availability (20%)
                        * Location Proximity (10%)
                        * Availability Match (5%)
                        * Remote Work Feasibility (5%)
                    - Performance & Engagement (15%)
                        * Profile Rating (5%)
                        * Reviews & Feedback (5%)
                        * Platform Activity (5%)
                    - Certifications & Credentials (10%)
                        * Relevant Certifications (5%)
                        * Language Proficiency (3%)
                        * Internal Badges (2%)
                    Analise and Return the following information in JSON format:
                    feedback_badges: Key characteristics of the candidate, requiring at least 5 badges to provide a well-rounded assessment of their professional profile.
                    matching_score: A quantitative measure (0-100) indicating the overall fit of the candidate for the position.
                    strengths: Top 3 distinctive qualities or capabilities that make the candidate stand out.
                    caution_points: Up to 3 areas where the candidate may need improvement or additional support.
                    profile_overview: A concise summary of the candidate's professional background and current status.
                    about: Detailed narrative of the candidate's background, including both personal and professional aspects.
                    technical_skills: List of specific technical competencies and tools the candidate is proficient in.
                    soft_skills: List of interpersonal and non-technical abilities that contribute to workplace effectiveness.
                    location_preferences: Geographic locations where the candidate is willing to work.
                    remote_work_preference: Candidate's preferred working arrangement (Remote/Hybrid/On-site).
                    experience_relevance: Assessment of each work experience's relevance to the position (output - maximum 4).
                    certifications: Professional qualifications and certifications that validate the candidate's expertise.
                 """

            content = f"Requirements: {compare_with}\n\nCandidate Data: {candidate_data}"

            # response = self.client.beta.completions.parse(
            #     model="gpt-4",
            #     messages=messages,
            #     temperature=0,
            #     max_tokens=1000
            # )

            # evaluation_result = response.choices[0].message.content

            evaluation_result = self.structure.structure_data(
                content = content,
                model_class= CandidateEvaluation,
                system_prompt=system_prompt,
            )

            return {
                'candidate_id': candidate.get('user_id'),
                'evaluation_result': evaluation_result["parsed_data"],
                'candidat_data': candidate
            }

        except Exception as e:
            return {'error': str(e)}
        