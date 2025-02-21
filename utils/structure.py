import os
from typing import Dict, Any
from openai import OpenAI
from models.resume_it import ResumeData

class DataStructureService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.system_prompt = "Extract structured information from the provided text."

    def structure_data(self, content: str, model_class: Any, system_prompt: str = None) -> Dict[str, ResumeData]:
        """Extract structured information from unstructured text using OpenAI

        Args:
            content (str): The unstructured text content to parse
            model_class (Any): The Pydantic model class to use for structuring the data
            system_prompt (str, optional): Custom system prompt for the extraction.
                                         Defaults to a generic extraction prompt.

        Returns:
            Dict[str, Any]: Dictionary containing the original content and structured data
        """
        if system_prompt is not None:
            self.system_prompt = system_prompt

        # Use OpenAI to extract structured information
        completion = self.client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": content}
            ],
            response_format=model_class,
        )

        parsed_data = completion.choices[0].message.parsed

        return {
            'content': content,
            'parsed_data': parsed_data.model_dump()
        }

    def structure_resume_data(self, content: str) -> Dict[str, ResumeData]:
        """Legacy method for resume parsing, uses the generic structure_data method"""
        return self.structure_data(
            content=content,
            model_class=ResumeData,
            system_prompt="Extract structured information from the resume text."
        )
    
    def struture_resume_with_blended_jobby_data(self, content: str) -> Dict[str, Any]:
        """Blend resume data with jobby data for a comprehensive profile"""
        # Placeholder for blending logic
        return self.structure_data(
            content=content,
            model_class=ResumeData,
            system_prompt="""You are a resume parser.
            Ensure all relevant information is captured and structured accurately.
            - Remove any duplicates or unnecessary data.
            - Ensure all fields are accurately captured.
            - Blend resume data with jobby data ( About, Skills, Certifications ) for a comprehensive profile.
            - For About Section Add Detailed narrative of the candidate's background, including both personal and professional aspects.
            - Organize data into the given structured format.
            """
        )