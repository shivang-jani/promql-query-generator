import os
from dotenv import load_dotenv

#Loads env vars from .env
load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPEN_AI_KEY")
    OPENAI_MODEL_NAME = os.getenv("OPEN_AI_MODEL_NAME","gpt-4.1-mini")
    PROMETHEUS_CONNECTOR_URL = os.getenv("PROMETHEUS_CONNECTOR_URL")