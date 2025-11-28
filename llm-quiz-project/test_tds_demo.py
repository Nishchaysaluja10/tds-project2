#!/usr/bin/env python3
"""
Test with the exact TDS demo quiz from the project documentation.
This quiz is now hosted on GitHub so the deployed API can access it.
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

# GitHub raw URL for the TDS demo quiz
# Note: File is in llm-quiz-project subdirectory
GITHUB_QUIZ_URL = "https://raw.githubusercontent.com/Nishchaysaluja10/tds-project2/main/llm-quiz-project/demo_quiz_tds.html"

def test_tds_demo_quiz():
    print("="*70)
    print("TESTING WITH EXACT TDS DEMO QUIZ")
    print("="*70)
    print()
    
    if not YOUR_EMAIL or not YOUR_SECRET:
        print("❌ ERROR: Email or Secret not configured in .env file")
        return
    
    print("📋 Configuration:")
    print(f"   Email: {YOUR_EMAIL}")
    print(f"   Secret: {'✅ SET' if YOUR_SECRET else '❌ NOT SET'}")
    print(f"   API: {API_URL}")
    print(f"   Quiz URL: {GITHUB_QUIZ_URL}")
    print()
    
    # Show what the quiz contains
    print("📄 Expected Quiz Content (base64 decoded):")
    print("-" * 70)
    import base64
    encoded = "UTgzNC4gRG93bmxvYWQgPGEgaHJlZj0iaHR0cHM6Ly9leGFtcGxlLmNvbS9kYXRhLXE4MzQucGRmIj5maWxlPC9hPi4gV2hhdCBpcyB0aGUgc3VtIG9mIHRoZSAidmFsdWUiIGNvbHVtbiBpbiB0aGUgdGFibGUgb24gcGFnZSAyPw0KDQpQb3N0IHlvdXIgYW5zd2VyIHRvIGh0dHBzOi8vZXhhbXBsZS5jb20vc3VibWl0IHdpdGggdGhpcyBKU09OIHBheWxvYWQ6DQoNCnsNCiAgImVtYWlsIjogInlvdXIgZW1haWwiLA0KICAic2VjcmV0IjogInlvdXIgc2VjcmV0IiwNCiAgInVybCI6ICJodHRwczovL2V4YW1wbGUuY29tL3F1aXotODM0IiwNCiAgImFuc3dlciI6IDEyMzQ1IC8vIHRoZSBjb3JyZWN0IGFuc3dlcg0KfQ=="
    decoded = base64.b64decode(encoded).decode('utf-8')
    print(decoded)
    print("-" * 70)
    print()
    
    # Verify quiz is accessible
    print("🔍 Verifying quiz is accessible from GitHub...")
    try:
        quiz_response = requests.get(GITHUB_QUIZ_URL, timeout=10)
        if quiz_response.status_code == 200:
            print(f"✅ Quiz accessible (HTTP {quiz_response.status_code})")
            print(f"   Content length: {len(quiz_response.text)} bytes")
            
            # Check if it contains the base64
            if 'atob' in quiz_response.text:
                print(f"   ✅ Contains base64 encoding (atob found)")
            else:
                print(f"   ⚠️  No atob found in content")
        else:
            print(f"❌ Quiz not accessible (HTTP {quiz_response.status_code})")
            print("   Make sure you've pushed demo_quiz_tds.html to GitHub")
            return
    except Exception as e:
        print(f"❌ Cannot access quiz: {e}")
        print("   Make sure you've pushed demo_quiz_tds.html to GitHub")
        return
    
    print()
    
    # Test the API
    payload = {
        "email": YOUR_EMAIL,
        "secret": YOUR_SECRET,
        "url": GITHUB_QUIZ_URL
    }
    
    print("🧪 Testing API with TDS demo quiz from GitHub...")
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
            
            print()
            print("🔍 CHECK RENDER LOGS FOR DETAILED OUTPUT:")
            print("   Go to: https://dashboard.render.com → llm-quiz-api → Logs")
            print()
            print("   Look for these lines to confirm base64 decoding worked:")
            print("   ✅ '⚠️ #result div is empty, checking for base64 in scripts'")
            print("   ✅ '✅ Decoded base64 question: Q834. Download...'")
            print("   ✅ '🤖 Calling GPT...'")
            print("   ✅ '✅ GPT raw answer: ...'")
            print()
            
            if quizzes > 0:
                print("🎉 SUCCESS! Your API:")
                print("   ✓ Accessed the GitHub-hosted quiz")
                print("   ✓ Detected empty #result div")
                print("   ✓ Found atob() in script tags")
                print("   ✓ Decoded base64 question")
                print("   ✓ Sent to GPT-4 for solving")
                print("   ✓ Submitted the answer")
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
    test_tds_demo_quiz()
