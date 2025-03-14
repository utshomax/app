from typing import List, Dict, Any, Optional
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
    async def search_candidates(self, search_query: str, 
                               location: Optional[List[str]] = None,
                               experience_level: Optional[List[str]] = None,
                               soft_skills: Optional[List[str]] = None,
                               hard_skills: Optional[List[str]] = None,
                               languages: Optional[List[str]] = None,
                               certifications: Optional[List[str]] = None) -> Dict[str, Any]:
        """Search and evaluate candidates based on the search query with optimized performance and filters"""
        try:
            # Convert natural language query to SQL
            sql_result = self.text_to_sql.execute_query(search_query, self.table_names)

            llm_results = []
            if 'error' not in sql_result:
                llm_results = sql_result['results']
            # Get candidates from database using LLM-generated query
            if not llm_results:
                llm_candidate_ids = []
            else:
                llm_candidate_ids = [candidate['user_id'] for candidate in llm_results]
            
            # Apply direct database filters
            filtered_candidate_ids = self.apply_filters(
                location=location,
                experience_level=experience_level,
                soft_skills=soft_skills,
                hard_skills=hard_skills,
                languages=languages,
                certifications=certifications
            )
            
            # Merge results from LLM query and direct filters
            if llm_candidate_ids and filtered_candidate_ids:
                # Intersection of both result sets if both have results
                final_candidate_ids = list(set(llm_candidate_ids).intersection(set(filtered_candidate_ids)))
            elif filtered_candidate_ids:
                # Use only filter results if LLM returned nothing
                final_candidate_ids = filtered_candidate_ids
            else:
                # Use only LLM results if no filters applied or filters returned nothing
                final_candidate_ids = llm_candidate_ids
            
            if not final_candidate_ids:
                return {
                    'sql': sql_result.get('sql', ''),
                    'candidates': [],
                }
            
            # Get full candidate data
            candidates = self.get_candidates(final_candidate_ids)
            
            return {
                'sql': sql_result.get('sql', ''),
                'candidates': candidates,
            }
            
        except Exception as e:
            logging.error(f"Error in search_candidates: {str(e)}")
            return {'error': str(e)}
    
    def apply_filters(self, 
                     location: Optional[List[str]] = None,
                     experience_level: Optional[List[str]] = None,
                     soft_skills: Optional[List[str]] = None,
                     hard_skills: Optional[List[str]] = None,
                     languages: Optional[List[str]] = None,
                     certifications: Optional[List[str]] = None) -> List[int]:
        """Apply direct database filters to candidate data"""
        if not any([location, experience_level, soft_skills, hard_skills, languages, certifications]):
            return []  # No filters applied
        
        query = "SELECT user_id FROM candidate_resumes WHERE 1=1"
        params = {}
        
        # Location filter
        if location and len(location) > 0:
            location_conditions = []
            for i, loc in enumerate(location):
                param_name = f"location_{i}"
                location_conditions.append(f"location ILIKE :{param_name}")
                params[param_name] = f"%{loc}%"
            
            if location_conditions:
                query += f" AND ({' OR '.join(location_conditions)})"
        
        # Experience level filter (assuming it's stored in the experience JSON field)
        if experience_level and len(experience_level) > 0:
            query += """ AND EXISTS (
                SELECT 1 FROM jsonb_array_elements(experience::jsonb) AS exp
                WHERE """
            
            exp_conditions = []
            for i, level in enumerate(experience_level):
                param_name = f"exp_level_{i}"
                exp_conditions.append(f"exp->>'duration' ILIKE :{param_name}")
                params[param_name] = f"%{level}%"
            
            query += f"{' OR '.join(exp_conditions)})"
        
        # Skills filters (assuming skills are stored in the skills JSON field)
        if soft_skills and len(soft_skills) > 0:
            soft_skill_conditions = []
            for i, skill in enumerate(soft_skills):
                param_name = f"soft_skill_{i}"
                soft_skill_conditions.append(f"skill ILIKE :{param_name}")
                params[param_name] = f"%{skill}%"
            
            if soft_skill_conditions:
                query += f""" AND EXISTS (
                    SELECT 1 FROM jsonb_array_elements_text(skills::jsonb) AS skill
                    WHERE {' OR '.join(soft_skill_conditions)}
                )"""
        
        if hard_skills and len(hard_skills) > 0:
            hard_skill_conditions = []
            for i, skill in enumerate(hard_skills):
                param_name = f"hard_skill_{i}"
                hard_skill_conditions.append(f"skill ILIKE :{param_name}")
                params[param_name] = f"%{skill}%"
            
            if hard_skill_conditions:
                query += f""" AND EXISTS (
                    SELECT 1 FROM jsonb_array_elements_text(skills::jsonb) AS skill
                    WHERE {' OR '.join(hard_skill_conditions)}
                )"""
        
        # Languages filter
        if languages and len(languages) > 0:
            lang_conditions = []
            for i, lang in enumerate(languages):
                param_name = f"language_{i}"
                lang_conditions.append(f"lang_item->>'language' ILIKE :{param_name}")
                params[param_name] = f"%{lang}%"
            
            if lang_conditions:
                query += f""" AND EXISTS (
                    SELECT 1 FROM jsonb_array_elements(languages::jsonb) AS lang_item
                    WHERE {' OR '.join(lang_conditions)}
                )"""
        
        # Certifications filter
        if certifications and len(certifications) > 0:
            cert_conditions = []
            for i, cert in enumerate(certifications):
                param_name = f"cert_{i}"
                cert_conditions.append(f"cert_item->>'name' ILIKE :{param_name}")
                params[param_name] = f"%{cert}%"
            
            if cert_conditions:
                query += f""" AND EXISTS (
                    SELECT 1 FROM jsonb_array_elements(certifications::jsonb) AS cert_item
                    WHERE {' OR '.join(cert_conditions)}
                )"""
        
        try:
            logging.info(f"Filter query: {query}")
            logging.info(f"Filter params: {params}")
            result = self.db.execute(text(query), params)
            rows = result.fetchall()
            return [row[0] for row in rows]  # Extract user_ids
        except Exception as e:
            logging.error(f"Error applying filters: {str(e)}")
            return []

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
                    'about': candidate.get('about', ''),
                    'skills': candidate.get('skills', []),
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
                    'certifications': candidate.get('certifications', []),
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
                'result': evaluation_result["parsed_data"],
                'candidate' : candidate,
            }

        except Exception as e:
            return {'error': str(e)}
