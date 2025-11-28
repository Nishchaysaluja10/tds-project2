#!/usr/bin/env python3
"""
Test with a real quiz that has a downloadable CSV file.
This quiz asks: "What is the sum of the 'value' column?"
Expected answer: 850 (100+150+200+175+225)
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://llm-quiz-api.onrender.com/quiz"
YOUR_EMAIL = os.getenv('YOUR_EMAIL')
YOUR_SECRET = os.getenv('YOUR_SECRET')

# GitHub raw URL for the real test quiz
QUIZ_URL = "https://raw.githubusercontent.com/Nishchaysaluja10/tds-project2/main/llm-quiz-project/real_test_quiz.html"

def test_real_quiz():
    print("="*70)
    print("TESTING WITH REAL QUIZ (Downloadable CSV File)")
    print("="*70)
    print()
    
    if not YOUR_EMAIL or not YOUR_SECRET:
        print("❌ ERROR: Email or Secret not configured in .env file")
        return
    
    print("📋 Test Details:")
    print(f"   Quiz URL: {QUIZ_URL}")
    print(f"   Data File: test_data.csv (on GitHub)")
    print(f"   Question: What is the sum of the 'value' column?")
    print(f"   Expected Answer: 850")
    print()
    
    # Show the data
    print("📊 CSV Data:")
    print("-" * 70)
    print("name,age,city,value")
    print("Alice,25,New York,100")
    print("Bob,30,London,150")
    print("Charlie,35,Paris,200")
    print("Diana,28,Tokyo,175")
    print("Eve,32,Sydney,225")
    print("-" * 70)
    print("Sum of 'value' column: 100+150+200+175+225 = 850")
    print()
    
    payload = {
        "email": YOUR_EMAIL,
        "secret": YOUR_SECRET,
        "url": QUIZ_URL
    }
    
    print("🧪 Sending request to API...")
    print(f"📤 API: {API_URL}")
    print(f"⏳ Waiting for response...\n")
    
    import time
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
            
            print("✅ TEST COMPLETE!")
            print()
            print("🔍 CHECK RENDER LOGS TO SEE:")
            print("   1. File download: test_data.csv")
            print("   2. GPT-4 analysis of the CSV data")
            print("   3. Answer calculation: 850")
            print("   4. Submission result")
            print()
            print("📍 Render Logs: https://dashboard.render.com → llm-quiz-api → Logs")
            
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print()
    print("="*70)

if __name__ == "__main__":
    test_real_quiz()
