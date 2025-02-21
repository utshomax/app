import os
import boto3
from botocore.exceptions import ClientError
from typing import Union, BinaryIO
import logging

class S3Service:
    def __init__(self):
        # Initialize S3 client with credentials from environment variables
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('AWS_S3_BUCKET')

    def fetch_resume(self, file_path: str) -> Union[BinaryIO, None]:
        temp_file_path = None
        try:
            if not file_path:
                logging.error("Empty file path provided")
                return None

            # Create resumes directory if it doesn't exist
            resume_dir = os.path.join(os.getcwd(), "resumes", os.path.dirname(file_path))
            os.makedirs(resume_dir, exist_ok=True)

            # Create a temporary file to store the downloaded content
            temp_file_path = os.path.join(resume_dir, os.path.basename(file_path))
            
            # Check if file already exists locally
            if os.path.exists(temp_file_path):
                logging.info(f"File already exists locally: {temp_file_path}")
                return temp_file_path
            
            # Check if file exists in S3 before downloading
            try:
                self.s3_client.head_object(Bucket=self.bucket_name, Key=file_path)
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    logging.error(f"File not found in S3: {file_path}")
                    return None
                raise
           
            # Download the file from S3
            self.s3_client.download_file(
                self.bucket_name,
                file_path,
                temp_file_path
            )
            
            return temp_file_path
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                logging.error(f"S3 bucket not found: {self.bucket_name}")
            else:
                logging.error(f"Error accessing S3: {str(e)}")
            return None

        except Exception as e:
            logging.error(f"Unexpected error fetching file from S3: {str(e)}")
            # Cleanup temporary file if something went wrong
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    logging.warning(f"Cleaning up temporary file: {temp_file_path}")
                    os.remove(temp_file_path)
                except Exception as e:
                    logging.warning(f"Failed to cleanup temporary file {temp_file_path}: {str(e)}")
            return None
