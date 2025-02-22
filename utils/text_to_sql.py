from typing import Dict, Any, Optional, List
from openai import OpenAI
from sqlalchemy import text
from sqlalchemy.orm import Session
from core.database import PGBase
import logging
import os

class TextToSQLConverter:
    def __init__(self, db: Session):
        self.db = db
        # Initialize OpenAI client
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def get_table_schema(self, table_names: Optional[List[str]] = None) -> str:
        """Get database schema information for context"""
        schema = ["""CREATE TABLE candidate_resumes (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            resume_path VARCHAR(255) UNIQUE NOT NULL,

            -- Data from jobby for faster search
            has_jobby_data BOOLEAN DEFAULT FALSE,
            jobby_name VARCHAR(255),
            jobby_gender VARCHAR(10),
            jobby_telephone VARCHAR(45),
            jobby_email VARCHAR(255),
            jobby_date_of_birth DATE,
            jobby_location VARCHAR(255),
            jobby_availability VARCHAR(255),
            jobby_about TEXT,
            jobby_skills JSONB (ARRAY),
            jobby_language VARCHAR(45),
            jobby_certifications JSONB (ARRAY),
            jobby_education JSONB (ARRAY),
            jobby_jobs JSONB (Object of {total: int
                    categories: array of JobCategory({
                        count: int
                        category: str})
                    job_titles: array of JobTitle({
                        count: int
                        title: str})
                    last_job_done: datetime}),
            jobby_rating FLOAT(4,2),
            jobby_premium BOOLEAN DEFAULT FALSE,
            jobby_reviews JSONB (ARRAY),

            -- Data from resume
            name VARCHAR(255),
            gender VARCHAR(10),
            phone VARCHAR(45),
            email VARCHAR(255),
            location VARCHAR(255),
            about TEXT,

            -- Skills and Languages
            skills JSONB (ARRAY),
            languages JSONB (ARRAY),
            certifications JSONB (ARRAY),

            -- Education and Experience
            education JSONB,
            experience JSONB, # JSONB ARRAY of { company: str
                        title: str
                        start_date: datetime
                        end_date: datetime
                        description: str
                        location: str },
            projects JSONB,

            -- Additional Professional Information
            achievements JSONB,
            publications JSONB,
            volunteer_work JSONB,
            professional_links JSONB,

            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );

        -- Indexes
        CREATE INDEX idx_candidate_resumes_user_id ON candidate_resumes (user_id);
        CREATE INDEX idx_candidate_resumes_resume_path ON candidate_resumes (resume_path);
        CREATE INDEX idx_candidate_resumes_jobby_name ON candidate_resumes (jobby_name);
        CREATE INDEX idx_candidate_resumes_jobby_email ON candidate_resumes (jobby_email);
        CREATE INDEX idx_candidate_resumes_jobby_location ON candidate_resumes (jobby_location);"""]
        return '\n'.join(schema)
        logging.info(f"Table names: {table_names}")
        for table in PGBase.metadata.sorted_tables:
            # Filter tables if table_names is provided
            if table_names and table.name not in table_names:
                continue
            columns = [f"{col.name} {col.type}" for col in table.columns]
            schema.append(f"CREATE TABLE {table.name} ({', '.join(columns)})")
        return '\n'.join(schema)

    def convert_to_sql(self, query: str, table_names: Optional[List[str]] = None, additional_context: str="") -> str:
        """Convert natural language query to SQL"""
        schema = self.get_table_schema(table_names)

        messages = [
            {"role": "system", "content": "You are a PostGres SQL Fuzzy Search expert for finding suitable candidates for diffrent possitions. Analize the search text and Try to find users intent. Determine possible places to search for the information. Generate a postgres compatible SQL query based on the provided schema.You MUST ONLY return the SQL query or False without any explanation. RETURN False if you are unable to generate the query or the query is invalid. FOR A VALID QUERY RETURN only the user_id. Add a limit of 50. Do not include any other information in the response."},
            {"role": "user", "content": f"### Postgres SQL table with properties:\n{schema}\n ### Additional Information: \n{additional_context}\n ### {query}\n### SQL Query:"}
        ]

        # Generate SQL query using GPT-4
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0,
            max_tokens=500
        )

        # Parse and clean the SQL response
        sql_query = response.choices[0].message.content.strip()
        if sql_query.startswith('```sql'):
            # Remove SQL code block markers
            sql_query = sql_query.replace('```sql', '').replace('```', '')
        
        # Clean up any remaining newlines and extra spaces
        sql_query = ' '.join(sql_query.split())
        
        return sql_query.strip()

    def execute_query(self, query: str, table_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute the generated SQL query"""
        try:
            if not os.getenv('OPENAI_API_KEY'):
                raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
            additional_context = """
            experience, education, certification, skills should be queried in both jobby_* and normal columns.
            Try to do proximity search on skills, certifications, experience, education, language using ilike oparator.
            Use ILIKE operator for fuzzy search.
            You may decide to search in descriptions feilds or about coloumn as well.
            Exact match may not be available.
                Some examples:
                Question: Candidates who can cook
                Answer:
                    SELECT user_id
                    FROM candidate_resumes
                    WHERE EXISTS (
                        SELECT 1
                        FROM jsonb_array_elements_text(skills::JSONB) AS skill
                        WHERE skill ILIKE '%cook%'
                    )
                    OR EXISTS (
                        SELECT 1
                        FROM jsonb_array_elements_text(jobby_skills::JSONB) AS job_skill
                        WHERE job_skill ILIKE '%cook%'
                    )
                    LIMIT 50;
                Question: Candidates worked in RANDSTAD
                Answer:
                    SELECT user_id
                    FROM candidate_resumes
                    WHERE EXISTS (
                        SELECT 1
                        FROM jsonb_array_elements(experience::JSONB) AS experience_element
                        WHERE experience_element->>'company' ILIKE '%RANDSTAD%'
                    )
                    OR EXISTS (
                        SELECT 1
                        FROM jsonb_array_elements(jobby_jobs::JSONB -> 'categories') AS category_element
                        WHERE category_element->>'category' ILIKE '%RANDSTAD%'
                    )
                    LIMIT 50;"""
            sql = self.convert_to_sql(query, table_names, additional_context)
            logging.info(f"Generated SQL: {sql}")

            if sql == "False":
                raise ValueError("Unable to generate valid SQL query.")

            # Check if the SQL query is valid
            # allow only read only queries
            if not sql.startswith("SELECT"):
                raise ValueError("SQL query is not a SELECT statement.")


            logging.info(f"Sanitized SQL: {sql}")

            # Execute SQL query
            result = self.db.execute(text(sql))

            # Properly format results by fetching all rows and converting to dict
            rows = result.fetchall()
            if not rows:
                formatted_results = []
            else:
                # Get column names from the result
                columns = result.keys()
                # Convert each row to a dictionary with column names as keys and extract only user_id
                formatted_results = [{'user_id': dict(zip(columns, row))['user_id']} for row in rows]

            logging.info(f"Query Results: {formatted_results}")
            return {
                'sql': sql,
                'results': formatted_results
            }
        except Exception as e:
            return {
                'error': str(e),
                'sql': sql if 'sql' in locals() else None
            }

