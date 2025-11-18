import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

# Test 1: Health check
print("Test 1: Health Check")
print("="*50)
response = requests.get("http://localhost:5000/")
print(json.dumps(response.json(), indent=2))
print()

# Test 2: Quiz with demo URL
print("Test 2: Demo Quiz")
print("="*50)

payload = {
    "email": os.getenv('YOUR_EMAIL'),
    "secret": os.getenv('YOUR_SECRET'),
    "url": "https://tds-llm-analysis.s-anand.net/demo"
}

print(f"Sending request with:")
print(f"  Email: {payload['email']}")
print(f"  Secret: {'*' * len(payload['secret'])}")
print(f"  URL: {payload['url']}")
print()

response = requests.post(
    "http://localhost:5000/quiz",
    json=payload,
    timeout=60
)

print(f"Status Code: {response.status_code}")
print(f"Response:")
print(json.dumps(response.json(), indent=2))