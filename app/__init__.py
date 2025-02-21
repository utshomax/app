from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from api.v1.main import app as app_v1

app = FastAPI(
    title="Jobby API",
    description="API for Jobby",
    version="1.0.0",
)

# Mount API v1 routes
app.mount("/api/v1", app_v1)