# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Your credentials
YOUR_EMAIL = os.getenv('YOUR_EMAIL')
YOUR_SECRET = os.getenv('YOUR_SECRET')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# This will be the actual submission endpoint from the evaluation
# Based on the pattern, it should be:
SUBMIT_ENDPOINT = "https://tds-llm-analysis.s-anand.net/submit"