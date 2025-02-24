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
            jobby_jobs JSONB (Object of {total: int
                    categories: array of JobCategory the user has worked on({
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
            --- Associated search tags
            tags:  JSONB ( Array of Strings )

            -- Skills and Languages
            skills JSONB (ARRAY of strings),
            languages JSONB (ARRAY of strings),
            certifications JSONB (ARRAY of strings),

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
        );"""]
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
            {"role": "system", "content": """You are a PostGres SQL Fuzzy Search expert for finding suitable candidates for diffrent possitions.
             Analize the search text and Try to find users intent.
             Determine possible places to search for the information.
             Tags columns contains relevent tags for a candidate.
             Generate a postgres compatible SQL query based on the provided schema.
            Guidelines for Searching Inside a JSONB Object in PostgreSQL
            1. Understanding JSONB Structure
            Check if the data is a simple key-value pair, an array of values, or an array of objects.
            Inspect the structure before querying to avoid incorrect assumptions.
            2. Choosing the Right Operator Based on Use Case
            Use Case	Operator	When to Use
            Check if a key exists	?	When you only need to know if a key is present in the JSONB object.
            Check if multiple keys exist	?&	When checking if all given keys exist in the JSONB object.
            Check if at least one key exists	`?	`
            Extract a value by key	->	When retrieving a JSONB object or array (not text).
            Extract a value as text	->>	When retrieving a value as text for filtering or comparison.
            Search inside a JSONB array of values	jsonb_array_elements_text()	When dealing with arrays of plain text values.
            Search inside a JSONB array of objects	jsonb_array_elements()	When dealing with arrays containing JSON objects.
            Check if JSONB contains a value	@>	When checking if a JSONB object/array contains another JSON structure.
            Search for partial matches	ILIKE	When performing case-insensitive text searches within JSONB values.
            3. Searching Inside JSONB Arrays
            Use jsonb_array_elements_text() when searching inside an array of text values.
            Use jsonb_array_elements() when searching inside an array of JSON objects.
            Always extract specific fields before applying conditions.
            4. Searching Inside JSONB Objects
            Use -> when extracting JSONB sub-objects.
            Use ->> when extracting values as text for filtering.
            Use @> for checking if a JSONB object contains a specific key-value pair.

            You MUST ONLY return the SQL query or False without any explanation.
             RETURN False if you are unable to generate the query or the query is invalid.
             Try to do proximity search on skills, certifications, experience, education, language using ilike oparator.
             FOR A VALID QUERY RETURN only the user_id. Add a limit of 50.
             ALLWAYS use COALESCE when extracting values from JSONB fields.
             DO NOT include any other information in the response.
             """},
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

