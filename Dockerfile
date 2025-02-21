# Use Python 3.9 as the base image
FROM python:3.9-slim-buster

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
  && apt-get -y install libpq-dev gcc \
  && pip install psycopg2

# Copy the entire project first
COPY . .

# Install Python dependencies
RUN pip install poetry && \
  poetry config virtualenvs.create false && \
  poetry install

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["poetry", "run", "python", "main.py"]