from typing import List, Dict, Any
from sqlalchemy.orm import Session
from utils.structure import DataStructureService
from utils.text_to_sql import TextToSQLConverter
from openai import OpenAI
from models.evaluator import CandidateEvaluation
from models.evaluator_it import CandidateEvaluation as CandidateEvalIt
import os
from sqlalchemy import text
from utils.system_prompts import english as system_english, italian as system_it
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
            system_prompt = system_it

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
                model_class= CandidateEvalIt,
                system_prompt=system_prompt,
            )

            return {
                'candidate_id': candidate.get('user_id'),
                'evaluation_result': evaluation_result["parsed_data"],
                'candidat_data': candidate
            }

        except Exception as e:
            return {'error': str(e)}
