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
        schema = []
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
            {"role": "system", "content": "You are a SQL expert. Convert the natural language query to a SQL query based on the provided schema.You MUST ONLY return the SQL query or False without any explanation. RETURN False if you are unable to generate the query or the query is invalid. FOR A VALID QUERY RETURN only the user_id. Add a limit of 50. Do not include any other information in the response."},
            {"role": "user", "content": f"### Postgres SQL tables, with their properties:\n{schema}\n ### Additional Information: \n{additional_context}\n ### {query}\n### SQL Query:"}
        ]
        
        # Generate SQL query using GPT-4
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0,
            max_tokens=500
        )
        
        sql_query = response.choices[0].message.content.strip()
        return sql_query

    def execute_query(self, query: str, table_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute the generated SQL query"""
        try:
            if not os.getenv('OPENAI_API_KEY'):
                raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
            additional_context = """
            experience, education, certification, skills should be queied in both jobby_* and normal columns.
            Pydantic Models for Data Structure:
                    class JobCategory:
                        count: int
                        category: str
                    class JobTitle:
                        count: int
                        title: str

                    class jobby_certificates: List[str]
                    class jobby_Jobs:
                        total: int
                        categories: List[JobCategory]
                        job_titles: List[JobTitle]
                        last_job_done: datetime"""
            sql = self.convert_to_sql(query, table_names, additional_context)
            logging.info(f"Generated SQL: {sql}")

            if sql == "False":
                raise ValueError("Unable to generate valid SQL query.")
            
            # Check if the SQL query is valid
            # allow only read only queries
            if not sql.startswith("SELECT"):
                raise ValueError("SQL query is not a SELECT statement.")

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