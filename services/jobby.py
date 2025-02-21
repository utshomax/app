from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import json

class JobbyDBService:
    def __init__(self, db: Session):
        self.db = db


    def get_resume_paths_by_dom_data_id(self, user_id: int) -> List[Dict]:
        """Retrieve resume paths using dom_user_data_id

        Args:
            dom_data_id (int): The dom_user_data_id to fetch resume paths for

        Returns:
            List[Dict]: List of dictionaries containing candidate_id and resume_path
        """
        query = text("""
           SELECT
                users_has_dom_user_data.users_id as candidate_id,
                users_has_dom_user_data.value as resume_path
            FROM
                jobby_users.users_has_dom_user_data
            WHERE
                users_has_dom_user_data.dom_user_data_id = 25 AND
 				        users_has_dom_user_data.users_id = :id;
        """)
        logging.info(f"Query: {user_id}")
        result = self.db.execute(query, {"id": user_id})
        results = [dict(zip(result.keys(), row)) for row in result]
        return results if results else None

    def get_candidate_certifications(self, user_id: int) -> List[Dict]:
        """Retrieve certifications for a candidate

        Args:
            user_id (int): The user ID to fetch certifications for

        Returns:
            List[Dict]: List of dictionaries containing candidate_id and certification
        """
        query = text("""
            SELECT
                jobby_users.dom_certifications.label as certification
            FROM
                jobby_users.users_has_dom_user_data
            INNER JOIN
                jobby_users.dom_certifications ON jobby_users.users_has_dom_user_data.value = jobby_users.dom_certifications.id
            WHERE
                jobby_users.users_has_dom_user_data.dom_user_data_id = 5 AND
                jobby_users.users_has_dom_user_data.users_id = :id;
        """)
        logging.info(f"Fetching certifications for user: {user_id}")
        result = self.db.execute(query, {"id": user_id})
        results = [row[0] for row in result]
        return results if results else None

    def get_job_details(self, job_id: int) -> Dict:
        """Retrieve job details from the ads table

        Args:
            job_id (int): The job ID to fetch details for

        Returns:
            Dict: Dictionary containing job title, description, and salary range
        """
        query = text("""
            SELECT
                jobby_jobs.ads.title as job_title,
                jobby_jobs.ads.description as job_description,
                jobby_jobs.ads.contract_range as job_salary_range
            FROM
                jobby_jobs.ads
            WHERE
                jobby_jobs.ads.id = :id;
        """)
        result = self.db.execute(query, {"id": job_id})
        row = result.fetchone()
        return dict(zip(result.keys(), row)) if row else None



    def get_candidate_jobs_done(self, user_id: int) -> List[Dict]:
        """Retrieve jobs done for a candidate with statistics

        Args:
            user_id (int): The user ID to fetch jobs done for

        Returns:
            List[Dict]: List containing job statistics with category breakdown, last job date, and grouped job roles
        """
        query = text("""
            SELECT JSON_OBJECT(
                'total', total_jobs,
                'categories', categories_json,
                'job_titles', job_titles_json,
                'last_job_done', last_job_date
            ) as result
            FROM (
                SELECT 
                    COUNT(DISTINCT jobs.id) as total_jobs,
                    MAX(jobs.jobstart_at) as last_job_date,
                    (
                        SELECT JSON_ARRAYAGG(
                            JSON_OBJECT(
                                'category', category,
                                'count', job_count
                            )
                        )
                        FROM (
                            SELECT 
                                job_macro_category_translations.label as category,
                                COUNT(DISTINCT jobs.id) as job_count
                            FROM jobby_jobs.jobs jobs
                            INNER JOIN jobby_jobs.applications apps
                                ON apps.jobs_id = jobs.id
                                AND apps.dom_application_status_id IN (2,6)
                            INNER JOIN jobby_jobs.job_micro_categories micro
                                ON jobs.job_micro_categories_id = micro.id
                            INNER JOIN jobby_jobs.job_macro_categories macro
                                ON macro.id = micro.job_macro_categories_id
                            INNER JOIN jobby_jobs.job_macro_category_translations
                                ON job_macro_category_translations.job_macro_categories_id = macro.id
                            WHERE apps.users_id = :id
                            GROUP BY job_macro_category_translations.label
                        ) category_stats
                    ) as categories_json,
                    (
                        SELECT JSON_ARRAYAGG(
                            JSON_OBJECT(
                                'title', title,
                                'count', job_count
                            )
                        )
                        FROM (
                            SELECT 
                                jobs.title,
                                COUNT(*) as job_count
                            FROM jobby_jobs.jobs jobs
                            INNER JOIN jobby_jobs.applications apps
                                ON apps.jobs_id = jobs.id
                                AND apps.dom_application_status_id IN (2,6)
                            WHERE apps.users_id = :id
                            GROUP BY jobs.title
                        ) title_stats
                    ) as job_titles_json
                FROM jobby_jobs.jobs jobs
                INNER JOIN jobby_jobs.applications apps
                    ON apps.jobs_id = jobs.id
                    AND apps.dom_application_status_id IN (2,6)
                WHERE apps.users_id = :id
            ) stats;
        """)
        logging.info(f"Fetching jobs done for user: {user_id}")
        result = self.db.execute(query, {"id": user_id})
        row = result.fetchone()
        return json.loads(row.result) if row and row.result else None



    def get_candidate_basic_info(self, user_id: int) -> Dict:
      """Retrieve basic information for a candidate

      Args:
          user_id (int): The user ID to fetch basic information for

      Returns:
          Dict: Dictionary containing basic information for the candidate
      """

      #TODO: add localtion
      query = text("""
          SELECT
              users.updated_at,
              users.date_of_birth,
              users.first_name,
              users.last_name,
              users.email,
              users.telephone,
              users.gender,
              users.language,
              users.about,
              users.rating_as_worker,
              users.premium
          FROM jobby_users.users users
          WHERE users.id = :id
      """)
      logging.info(f"Fetching basic information for user: {user_id}")
      result = self.db.execute(query, {"id": user_id})
      row = result.fetchone()
      return dict(zip(result.keys(), row)) if row else None