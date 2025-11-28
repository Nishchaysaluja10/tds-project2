#!/usr/bin/env python3
"""
Test with sample_quiz.html hosted on GitHub raw URL.
This allows the deployed Render API to access the quiz.
"""

import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://llm-quiz-api.onrender.com/quiz"
YOUR_EMAIL = os.getenv('YOUR_EMAIL')
YOUR_SECRET = os.getenv('YOUR_SECRET')

# GitHub raw URL for sample_quiz.html
# Replace with your actual GitHub username and repo name
GITHUB_RAW_URL = "https://raw.githubusercontent.com/Nishchaysaluja10/tds-project2/main/sample_quiz.html"

def test_with_github_quiz():
    print("="*70)
    print("TESTING WITH SAMPLE QUIZ FROM GITHUB")
    print("="*70)
    print()
    
    if not YOUR_EMAIL or not YOUR_SECRET:
        print("❌ ERROR: Email or Secret not configured in .env file")
        return
    
    print("📋 Configuration:")
    print(f"   Email: {YOUR_EMAIL}")
    print(f"   Secret: {'✅ SET' if YOUR_SECRET else '❌ NOT SET'}")
    print(f"   API: {API_URL}")
    print(f"   Quiz URL: {GITHUB_RAW_URL}")
    print()
    
    # First, verify the quiz is accessible
    print("🔍 Verifying quiz is accessible from GitHub...")
    try:
        quiz_response = requests.get(GITHUB_RAW_URL, timeout=10)
        if quiz_response.status_code == 200:
            print(f"✅ Quiz accessible (HTTP {quiz_response.status_code})")
            print(f"   Content length: {len(quiz_response.text)} bytes")
        else:
            print(f"❌ Quiz not accessible (HTTP {quiz_response.status_code})")
            print("   Make sure you've pushed sample_quiz.html to GitHub")
            return
    except Exception as e:
        print(f"❌ Cannot access quiz: {e}")
        print("   Make sure you've pushed sample_quiz.html to GitHub")
        return
    
    print()
    
    # Test the API
    payload = {
        "email": YOUR_EMAIL,
        "secret": YOUR_SECRET,
        "url": GITHUB_RAW_URL
    }
    
    print("🧪 Testing API with GitHub-hosted quiz...")
    print(f"📤 Sending request to: {API_URL}")
    print(f"⏳ Waiting for response...\n")
    
    start_time = time.time()
    
    try:
        response = requests.post(API_URL, json=payload, timeout=60)
        elapsed = time.time() - start_time
        
        print(f"⏱️  Response received in {elapsed:.1f}s")
        print(f"📊 Status Code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            print("📄 Response:")
            print(json.dumps(result, indent=2))
            print()
            
            quizzes = result.get('quizzes_attempted', 0)
            total_time = result.get('total_time', 0)
            
            print("✅ TEST RESULTS:")
            print(f"   - Status: HTTP 200 ✅")
            print(f"   - Quizzes attempted: {quizzes}")
            print(f"   - Processing time: {total_time:.2f}s")
            
            if total_time < 180:
                print(f"   - Within 3-minute limit: ✅ ({total_time:.2f}s < 180s)")
            else:
                print(f"   - Exceeded 3-minute limit: ⚠️ ({total_time:.2f}s > 180s)")
            
            print()
            print("🔍 TO SEE WHAT WAS SCRAPED:")
            print("   Go to Render logs and look for:")
            print("   - '✅ Decoded base64 question: Q834. Download...'")
            print("   - '🤖 Calling GPT...'")
            print("   - '✅ GPT raw answer: ...'")
            print()
            
            if quizzes > 0:
                print("🎉 SUCCESS! Your API correctly handled the GitHub-hosted quiz!")
            else:
                print("⚠️  No quizzes attempted - check Render logs for details")
                
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print()
    print("="*70)

if __name__ == "__main__":
    test_with_github_quiz()
