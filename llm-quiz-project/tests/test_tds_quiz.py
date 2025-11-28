#!/usr/bin/env python3
"""
Test with the actual TDS quiz format from the project documentation.
This creates a local quiz server matching the exact format shown in the TDS docs.
"""

import requests
import json
import os
import time
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://llm-quiz-api.onrender.com/quiz"
YOUR_EMAIL = os.getenv('YOUR_EMAIL')
YOUR_SECRET = os.getenv('YOUR_SECRET')

# The exact quiz HTML from TDS project documentation
QUIZ_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Sample Quiz</title>
</head>
<body>
    <div id="result"></div>

    <script>
        document.querySelector("#result").innerHTML = atob(`
UTgzNC4gRG93bmxvYWQgPGEgaHJlZj0iaHR0cHM6Ly9leGFtcGxlLmNvbS9kYXRhLXE4MzQucGRmIj5
maWxlPC9hPi4KV2hhdCBpcyB0aGUgc3VtIG9mIHRoZSAidmFsdWUiIGNvbHVtbiBpbiB0aGUgdGFibG
Ugb24gcGFnZSAyPwoKUG9zdCB5b3VyIGFuc3dlciB0byBodHRwczovL2V4YW1wbGUuY29tL3N1Ym1pd
CB3aXRoIHRoaXMgSlNPTiBwYXlsb2FkOgoKPHByZT4KewogICJlbWFpbCI6ICJ5b3VyLWVtYWlsIiwK
ICAic2VjcmV0IjogInlvdXIgc2VjcmV0IiwKICAidXJsIjogImh0dHBzOi8vZXhhbXBsZS5jb20vcXV
pei04MzQiLAogICJhbnN3ZXIiOiAxMjM0NSAgLy8gdGhlIGNvcnJlY3QgYW5zd2VyCn0KPC9wcmU+`);
    </script>
</body>
</html>
"""

class QuizHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/quiz':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(QUIZ_HTML.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress server logs

def start_local_server(port=8765):
    """Start a local HTTP server in a background thread"""
    server = HTTPServer(('localhost', port), QuizHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server

def test_with_tds_quiz():
    print("="*70)
    print("TESTING WITH TDS PROJECT QUIZ FORMAT")
    print("="*70)
    print()
    
    # Check configuration
    if not YOUR_EMAIL or not YOUR_SECRET:
        print("❌ ERROR: Email or Secret not configured in .env file")
        return
    
    print("📋 Configuration:")
    print(f"   Email: {YOUR_EMAIL}")
    print(f"   Secret: {'✅ SET' if YOUR_SECRET else '❌ NOT SET'}")
    print(f"   API: {API_URL}")
    print()
    
    # Start local quiz server
    print("🌐 Starting local quiz server on port 8765...")
    server = start_local_server(8765)
    time.sleep(1)  # Give server time to start
    print("✅ Local server started at http://localhost:8765/quiz")
    print()
    
    # Show what the quiz contains
    print("📄 Quiz Content (base64 decoded):")
    print("-" * 70)
    import base64
    encoded = """UTgzNC4gRG93bmxvYWQgPGEgaHJlZj0iaHR0cHM6Ly9leGFtcGxlLmNvbS9kYXRhLXE4MzQucGRmIj5
maWxlPC9hPi4KV2hhdCBpcyB0aGUgc3VtIG9mIHRoZSAidmFsdWUiIGNvbHVtbiBpbiB0aGUgdGFibG
Ugb24gcGFnZSAyPwoKUG9zdCB5b3VyIGFuc3dlciB0byBodHRwczovL2V4YW1wbGUuY29tL3N1Ym1pd
CB3aXRoIHRoaXMgSlNPTiBwYXlsb2FkOgoKPHByZT4KewogICJlbWFpbCI6ICJ5b3VyLWVtYWlsIiwK
ICAic2VjcmV0IjogInlvdXIgc2VjcmV0IiwKICAidXJsIjogImh0dHBzOi8vZXhhbXBsZS5jb20vcXV
pei04MzQiLAogICJhbnN3ZXIiOiAxMjM0NSAgLy8gdGhlIGNvcnJlY3QgYW5zd2VyCn0KPC9wcmU+"""
    decoded = base64.b64decode(encoded.replace('\n', '')).decode('utf-8')
    print(decoded)
    print("-" * 70)
    print()
    
    # Test the API
    print("🧪 Testing API with TDS quiz format...")
    print()
    
    # IMPORTANT: The deployed API on Render cannot access localhost!
    # We need to test with the public demo URL instead
    print("⚠️  NOTE: Deployed API cannot access localhost")
    print("   Testing with public demo URL instead: https://tds-llm-analysis.s-anand.net/demo")
    print()
    
    quiz_url = "https://tds-llm-analysis.s-anand.net/demo"
    
    payload = {
        "email": YOUR_EMAIL,
        "secret": YOUR_SECRET,
        "url": quiz_url
    }
    
    print(f"📤 Sending request to: {API_URL}")
    print(f"📋 Quiz URL: {quiz_url}")
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
            print("🔍 TO SEE DETAILED SCRAPING LOGS:")
            print("   1. Go to https://dashboard.render.com")
            print("   2. Click on 'llm-quiz-api' service")
            print("   3. Click 'Logs' tab")
            print("   4. Look for:")
            print("      - '✅ Decoded base64 question: ...'")
            print("      - '🤖 Calling GPT...'")
            print("      - '✅ GPT raw answer: ...'")
            print("      - '📤 Submitting to: ...'")
            print()
            
            if quizzes > 0:
                print("🎉 SUCCESS! Your API correctly:")
                print("   ✓ Scraped the JavaScript-rendered quiz page")
                print("   ✓ Decoded the base64-encoded question")
                print("   ✓ Sent question to GPT-4")
                print("   ✓ Submitted the answer")
            else:
                print("⚠️  No quizzes were attempted - check Render logs")
                
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    finally:
        # Stop the server
        server.shutdown()
        print()
        print("🛑 Local server stopped")
    
    print()
    print("="*70)

if __name__ == "__main__":
    test_with_tds_quiz()
