import requests
import json
import time

print("="*70)
print("TESTING YOUR DEPLOYED API")
print("="*70)

# Test with the official demo endpoint
payload = {
    "email": "24f2003882@ds.study.iitm.ac.in",
    "secret": "messi10",
    "url": "https://tds-llm-analysis.s-anand.net/demo"
}

print(f"\n📍 Your API: https://llm-quiz-api.onrender.com/quiz")
print(f"📍 Testing with: {payload['url']}")
print(f"\n⏳ Sending request (may take 10-30 seconds)...\n")

start = time.time()

try:
    response = requests.post(
        "https://llm-quiz-api.onrender.com/quiz",
        json=payload,
        timeout=180  # 3 minutes
    )
    
    elapsed = time.time() - start
    
    print(f"⏱️  Time taken: {elapsed:.1f}s")
    print(f"📊 Status Code: {response.status_code}")
    print(f"\n📄 Response:")
    print("-"*70)
    
    try:
        result = response.json()
        print(json.dumps(result, indent=2))
    except:
        print(response.text)
    
    print("-"*70)
    
    # Interpret results
    if response.status_code == 200:
        print("\n✅ SUCCESS - Your API is working!")
        if 'quizzes_attempted' in result:
            print(f"   Quizzes solved: {result.get('quizzes_attempted', 0)}")
    elif response.status_code == 403:
        print("\n❌ FAILED - Secret mismatch (check environment variables)")
    elif response.status_code == 400:
        print("\n❌ FAILED - Error in processing (check logs)")
    else:
        print(f"\n⚠️  Unexpected status code: {response.status_code}")
    
except requests.Timeout:
    print("\n⏰ TIMEOUT - Request took longer than 3 minutes")
    print("   This might mean:")
    print("   - Server is processing but too slow")
    print("   - Infinite loop in code")
    print("   - Check Render logs for details")
    
except requests.ConnectionError:
    print("\n❌ CONNECTION ERROR - Cannot reach your API")
    print("   Check if your API is deployed and running on Render")
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")

print("\n" + "="*70)
print("\n💡 TIP: Check Render logs for detailed execution trace")
print("   Go to: https://dashboard.render.com → Your Service → Logs")
print("="*70)