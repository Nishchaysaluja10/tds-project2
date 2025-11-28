#!/usr/bin/env python3
"""
Comprehensive test based on TDS project requirements.
Tests all the requirements from the project specification.
"""

import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://llm-quiz-api.onrender.com/quiz"
HEALTH_URL = "https://llm-quiz-api.onrender.com/"
DEMO_QUIZ_URL = "https://tds-llm-analysis.s-anand.net/demo"

YOUR_EMAIL = os.getenv('YOUR_EMAIL')
YOUR_SECRET = os.getenv('YOUR_SECRET')

def test_requirement_1_health_check():
    """Test: API is accessible"""
    print("\n" + "="*70)
    print("TEST 1: Health Check (API Accessibility)")
    print("="*70)
    
    try:
        response = requests.get(HEALTH_URL, timeout=10)
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Response: {json.dumps(response.json(), indent=2)}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_requirement_2_secret_validation():
    """Test: Secret validation (HTTP 403 for wrong secret)"""
    print("\n" + "="*70)
    print("TEST 2: Secret Validation (Requirement: HTTP 403 for invalid)")
    print("="*70)
    
    payload = {
        "email": YOUR_EMAIL,
        "secret": "wrong_secret",
        "url": DEMO_QUIZ_URL
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=30)
        if response.status_code == 403:
            print(f"✅ PASSED: Got HTTP 403 for invalid secret")
            return True
        else:
            print(f"❌ FAILED: Expected 403, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_requirement_3_invalid_json():
    """Test: Invalid JSON handling (HTTP 400)"""
    print("\n" + "="*70)
    print("TEST 3: Invalid JSON Handling (Requirement: HTTP 400)")
    print("="*70)
    
    try:
        response = requests.post(
            API_URL, 
            data="invalid json", 
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        if response.status_code == 400:
            print(f"✅ PASSED: Got HTTP 400 for invalid JSON")
            return True
        else:
            print(f"❌ FAILED: Expected 400, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_requirement_4_quiz_solving():
    """Test: Complete quiz solving flow"""
    print("\n" + "="*70)
    print("TEST 4: Quiz Solving (Full Flow)")
    print("="*70)
    print("Requirements:")
    print("  - Scrape JavaScript-rendered quiz page")
    print("  - Extract question from base64-encoded content")
    print("  - Solve with GPT-4")
    print("  - Submit answer within 3 minutes")
    print("="*70)
    
    payload = {
        "email": YOUR_EMAIL,
        "secret": YOUR_SECRET,
        "url": DEMO_QUIZ_URL
    }
    
    print(f"\n📤 Sending request to: {API_URL}")
    print(f"📋 Quiz URL: {DEMO_QUIZ_URL}")
    print(f"⏳ Waiting for response (max 60s)...\n")
    
    start_time = time.time()
    
    try:
        response = requests.post(API_URL, json=payload, timeout=60)
        elapsed = time.time() - start_time
        
        print(f"⏱️  Response received in {elapsed:.1f}s")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📄 Response: {json.dumps(result, indent=2)}")
            
            quizzes = result.get('quizzes_attempted', 0)
            total_time = result.get('total_time', 0)
            
            print(f"\n✅ PASSED:")
            print(f"   - HTTP 200 response")
            print(f"   - Quizzes attempted: {quizzes}")
            print(f"   - Processing time: {total_time:.2f}s")
            
            if total_time < 180:  # 3 minutes
                print(f"   - ✅ Within 3-minute requirement ({total_time:.2f}s < 180s)")
            else:
                print(f"   - ⚠️  Exceeded 3-minute limit ({total_time:.2f}s > 180s)")
            
            return quizzes > 0
        else:
            print(f"❌ FAILED: Got HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ FAILED: Request timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_requirement_5_response_format():
    """Test: Response format is valid JSON"""
    print("\n" + "="*70)
    print("TEST 5: Response Format (Valid JSON)")
    print("="*70)
    
    payload = {
        "email": YOUR_EMAIL,
        "secret": YOUR_SECRET,
        "url": DEMO_QUIZ_URL
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=60)
        
        # Try to parse JSON
        result = response.json()
        print(f"✅ PASSED: Response is valid JSON")
        print(f"   Keys: {list(result.keys())}")
        return True
    except json.JSONDecodeError:
        print(f"❌ FAILED: Response is not valid JSON")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("TDS PROJECT REQUIREMENTS VERIFICATION")
    print("="*70)
    print(f"API URL: {API_URL}")
    print(f"Email: {YOUR_EMAIL}")
    print(f"Secret: {'✅ SET' if YOUR_SECRET else '❌ NOT SET'}")
    
    if not YOUR_EMAIL or not YOUR_SECRET:
        print("\n❌ ERROR: Email or Secret not configured in .env file")
        return
    
    results = []
    
    # Run all tests
    results.append(("Health Check", test_requirement_1_health_check()))
    results.append(("Secret Validation", test_requirement_2_secret_validation()))
    results.append(("Invalid JSON Handling", test_requirement_3_invalid_json()))
    results.append(("Quiz Solving Flow", test_requirement_4_quiz_solving()))
    results.append(("Response Format", test_requirement_5_response_format()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Your API is ready for evaluation!")
        print("\n⚠️  IMPORTANT REMINDERS:")
        print("   1. Evaluation window: Sat 29 Nov 2025, 3:00-4:00 PM IST")
        print("   2. Ensure your Render service is running during evaluation")
        print("   3. Check that environment variables are set in Render dashboard")
        print("   4. Monitor Render logs during evaluation for debugging")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix before evaluation.")
    
    print("="*70)

if __name__ == "__main__":
    main()
