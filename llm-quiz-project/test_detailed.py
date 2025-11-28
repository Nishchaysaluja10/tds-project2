#!/usr/bin/env python3
"""
Detailed test script to verify the quiz API is working correctly.
Shows the complete flow: scraping → GPT solving → submission
"""

import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_URL = "https://llm-quiz-api.onrender.com/quiz"
QUIZ_URL = "https://tds-llm-analysis.s-anand.net/demo"

YOUR_EMAIL = os.getenv('YOUR_EMAIL')
YOUR_SECRET = os.getenv('YOUR_SECRET')

def test_detailed():
    print("=" * 70)
    print("DETAILED QUIZ API TEST")
    print("=" * 70)
    print()
    
    # Check credentials
    print("1️⃣  Checking Configuration")
    print("-" * 70)
    print(f"   API URL: {API_URL}")
    print(f"   Quiz URL: {QUIZ_URL}")
    print(f"   Email: {YOUR_EMAIL}")
    print(f"   Secret: {'✅ SET' if YOUR_SECRET else '❌ NOT SET'}")
    print()
    
    if not YOUR_EMAIL or not YOUR_SECRET:
        print("❌ ERROR: Email or Secret not configured in .env file")
        return
    
    # Test health endpoint first
    print("2️⃣  Testing Health Endpoint")
    print("-" * 70)
    try:
        health_url = API_URL.replace('/quiz', '/')
        response = requests.get(health_url, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=6)}")
        print()
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        print()
    
    # Test quiz endpoint
    print("3️⃣  Testing Quiz Endpoint")
    print("-" * 70)
    
    payload = {
        "email": YOUR_EMAIL,
        "secret": YOUR_SECRET,
        "url": QUIZ_URL
    }
    
    print(f"   Sending request to: {API_URL}")
    print(f"   Payload: {json.dumps(payload, indent=6)}")
    print()
    print("   ⏳ Waiting for response (this may take 10-30 seconds)...")
    print()
    
    start_time = time.time()
    
    try:
        response = requests.post(API_URL, json=payload, timeout=60)
        elapsed = time.time() - start_time
        
        print(f"   ✅ Response received in {elapsed:.1f}s")
        print(f"   Status Code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            print("   📊 Response Data:")
            print(f"      {json.dumps(result, indent=6)}")
            print()
            
            # Interpret results
            print("4️⃣  Results Analysis")
            print("-" * 70)
            
            quizzes = result.get('quizzes_attempted', 0)
            total_time = result.get('total_time', 0)
            
            print(f"   ✅ Quizzes Attempted: {quizzes}")
            print(f"   ⏱️  Total Processing Time: {total_time:.2f}s")
            print()
            
            if quizzes > 0:
                print("   🎉 SUCCESS! The API is working correctly:")
                print("      ✓ Scraped the quiz page")
                print("      ✓ Extracted the question")
                print("      ✓ Called GPT-4 to solve it")
                print("      ✓ Submitted the answer")
                print()
                print("   💡 To see detailed logs (question, answer, etc.):")
                print("      1. Go to https://dashboard.render.com")
                print("      2. Select your service 'llm-quiz-api'")
                print("      3. Click 'Logs' tab")
                print("      4. Look for the quiz processing details")
            else:
                print("   ⚠️  No quizzes were attempted")
                print("      Check Render logs for error details")
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("   ❌ Request timed out after 60 seconds")
        print("      The API might be processing but taking too long")
        print("      Check Render logs for details")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    print("=" * 70)

if __name__ == "__main__":
    test_detailed()
