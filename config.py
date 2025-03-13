# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Google Cloud project and location
PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "cjnyasg-customer360")
LOCATION = os.getenv("GOOGLE_REGION", "us-central1")

# Model ID for Gemini 2.0 Flash
MODEL_ID = "gemini-2.0-flash-001"
