from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import pandas as pd
from io import StringIO, BytesIO
from urllib.parse import urljoin
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Your credentials
YOUR_EMAIL = os.getenv('YOUR_EMAIL')
YOUR_SECRET = os.getenv('YOUR_SECRET')
AIPIPE_API_KEY = os.getenv('AIPIPE_API_KEY')  # AIpipe.org API key

# Initialize OpenAI client with AIpipe.org endpoint
client = OpenAI(
    api_key=AIPIPE_API_KEY,
    base_url="https://aipipe.org/v1"  # AIpipe.org endpoint
)

# Submission endpoint - will be extracted from quiz page
SUBMIT_ENDPOINT = None  # Don't hardcode - extract from page


def scrape_quiz_page(url):
    """Fetch the quiz page and extract the question (handles JavaScript)"""
    try:
        print(f"Scraping: {url}")
        
        # Try with Playwright first (for JavaScript-rendered pages)
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                try:
                    browser = p.chromium.launch(headless=True)
                except Exception as e:
                    # Don't try to install during request - browsers should be installed by build.sh
                    # Just fall back to requests
                    print(f"⚠️ Playwright browser launch failed: {str(e)}")
                    print("⚠️ Falling back to requests library")
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    content = response.text
                else:
                    page = browser.new_page()
                    
                    # Navigate and wait for content
                    page.goto(url, wait_until='networkidle', timeout=30000)
                    
                    # Wait for result div
                    try:
                        page.wait_for_selector('#result', timeout=5000)
                    except:
                        print("⚠️ Timeout waiting for #result, continuing anyway")
                    
                    # Wait a bit for JavaScript
                    page.wait_for_timeout(2000)
                    
                    # Get rendered HTML
                    content = page.content()
                    browser.close()
                
        except ImportError:
            print("⚠️ Playwright not available, using requests")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            content = response.text
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Try to find result div
        result_div = soup.find('div', id='result')
        question_text = None
        
        if result_div:
            question_text = result_div.get_text(strip=True)
            if question_text:
                print(f"✅ Question found in #result: {question_text[:100]}...")
            else:
                # Result div is empty - likely JavaScript-rendered
                # Try to extract base64 content from script tags
                print("⚠️ #result div is empty, checking for base64 in scripts")
                import re
                import base64
                
                for script in soup.find_all('script'):
                    script_text = script.string
                    if script_text and 'atob' in script_text:
                        # Extract base64 content from atob() calls
                        matches = re.findall(r'atob\([`\'"]([A-Za-z0-9+/=\s]+)[`\'"]\)', script_text)
                        for match in matches:
                            try:
                                # Remove whitespace and decode
                                decoded = base64.b64decode(match.replace('\n', '').replace(' ', '')).decode('utf-8')
                                if len(decoded) > 20:
                                    question_text = decoded
                                    print(f"✅ Decoded base64 question: {question_text[:100]}...")
                                    break
                            except Exception as e:
                                print(f"⚠️ Failed to decode base64: {e}")
                        if question_text:
                            break
        
        if not question_text:
            # Try alternative selectors
            print("⚠️ No #result div, trying alternatives")
            for selector in ['#quiz', '#question', '.question', 'main', 'article']:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    if len(text) > 20:
                        question_text = text
                        print(f"✅ Question found in {selector}")
                        break
        
        # Last resort - get body text
        if not question_text or len(question_text) < 10:
            body = soup.find('body')
            if body:
                for script in body(['script', 'style', 'nav', 'footer']):
                    script.decompose()
                question_text = body.get_text(strip=True)
                print(f"⚠️ Using body text as question")
        
        if not question_text or len(question_text) < 10:
            print("❌ No meaningful content found")
            return None
        
        # Look for submit URL in the page
        global SUBMIT_ENDPOINT
        for text in soup.stripped_strings:
            if 'submit' in text.lower() and ('http://' in text or 'https://' in text):
                # Try to extract URL
                import re
                urls = re.findall(r'https?://[^\s<>"]+', text)
                if urls:
                    SUBMIT_ENDPOINT = urls[0]
                    print(f"📤 Submit endpoint found: {SUBMIT_ENDPOINT}")
                    break
        
        # Look for downloadable files
        files = {}
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            
            if (link.get('download') or 
                'download' in text.lower() or 
                any(href.endswith(ext) for ext in ['.csv', '.xlsx', '.xls', '.pdf', '.txt', '.json'])):
                
                if not href.startswith('http'):
                    href = urljoin(url, href)
                files[text or 'file'] = href
                print(f"📎 File found: {text} -> {href}")
        
        return {
            'question': question_text,
            'files': files
        }
        
    except Exception as e:
        print(f"❌ Scraping error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def download_file(url):
    """Download file and return content as string"""
    try:
        print(f"Downloading file: {url}")
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        # Check if it's a CSV file
        if url.endswith('.csv') or 'csv' in response.headers.get('content-type', '').lower():
            df = pd.read_csv(StringIO(response.text))
            print(f"✅ CSV loaded: {df.shape[0]} rows, {df.shape[1]} columns")
            return df.to_string()
        
        # Check if it's Excel
        elif url.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(BytesIO(response.content))
            print(f"✅ Excel loaded: {df.shape[0]} rows, {df.shape[1]} columns")
            return df.to_string()
        
        # PDF handling (basic)
        elif url.endswith('.pdf'):
            print(f"✅ PDF downloaded: {len(response.content)} bytes")
            return f"PDF file with {len(response.content)} bytes"
        
        else:
            print(f"✅ Text file loaded: {len(response.text)} characters")
            return response.text
            
    except Exception as e:
        print(f"❌ File download error: {str(e)}")
        return None


def solve_with_gpt(question, data_context=None):
    """Use GPT to solve the question"""
    try:
        # Build the prompt
        prompt = f"""You are solving a data analysis quiz question. 

Question: {question}
"""
        
        if data_context:
            # Limit context size to avoid token limits
            if len(data_context) > 8000:
                prompt += f"\n\nData provided (truncated):\n{data_context[:8000]}...\n"
            else:
                prompt += f"\n\nData provided:\n{data_context}\n"
        
        prompt += """
Important instructions:
- Provide ONLY the final answer
- If it's a number, give just the number (no units, no commas, no formatting)
- If it's a yes/no question, answer with just "yes" or "no" (or true/false)
- If it's a calculation, show only the result
- No explanations or reasoning
- Be precise and exact

Answer:"""

        print("🤖 Calling GPT...")
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise data analyst. Always provide exact, concise answers with no explanations."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content.strip()
        print(f"✅ GPT raw answer: {answer}")
        
        # Clean up the answer
        answer = answer.replace('Answer:', '').strip()
        answer = answer.replace('The answer is', '').strip()
        answer = answer.replace('The result is', '').strip()
        
        return parse_answer(answer)
            
    except Exception as e:
        print(f"❌ GPT error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def parse_answer(answer_text):
    """Parse answer to appropriate type (boolean, number, string)"""
    answer = answer_text.strip()
    
    # Try boolean
    if answer.lower() in ['true', 'yes']:
        return True
    if answer.lower() in ['false', 'no']:
        return False
    
    # Try number (remove commas first)
    try:
        clean = answer.replace(',', '')
        if '.' in clean:
            return float(clean)
        return int(clean)
    except ValueError:
        pass
    
    # Return as string
    return answer


def submit_answer(quiz_url, answer):
    """Submit the answer back to the evaluation system"""
    global SUBMIT_ENDPOINT
    
    # Use extracted submit endpoint or default
    submit_url = SUBMIT_ENDPOINT or "https://tds-llm-analysis.s-anand.net/submit"
    
    try:
        # CRITICAL: Use YOUR actual credentials, not template text
        payload = {
            "email": YOUR_EMAIL,  # Your actual email
            "secret": YOUR_SECRET,  # Your actual secret (NOT "your secret")
            "url": quiz_url,  # The actual quiz URL (NOT "this page's URL")
            "answer": answer  # Your computed answer
        }
        
        print(f"📤 Submitting to: {submit_url}")
        print(f"📤 Email: {YOUR_EMAIL}")
        print(f"📤 Secret: {'*' * len(YOUR_SECRET)}")  # Don't print actual secret
        print(f"📤 URL: {quiz_url}")
        print(f"📤 Answer: {answer} (type: {type(answer).__name__})")
        
        response = requests.post(submit_url, json=payload, timeout=30)
        
        # Parse response
        try:
            result = response.json()
        except:
            result = {"error": "Invalid JSON response", "text": response.text[:200]}
        
        print(f"📨 Status: {response.status_code}")
        print(f"📨 Response: {result}")
        
        return result
        
    except Exception as e:
        print(f"❌ Submission error: {str(e)}")
        return {"error": str(e), "correct": False}

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "running",
        "message": "LLM Quiz Solver API",
        "endpoints": {
            "/": "Health check",
            "/quiz": "POST - Solve quiz"
        },
        "aipipe_configured": AIPIPE_API_KEY is not None,
        "credentials_configured": YOUR_EMAIL is not None and YOUR_SECRET is not None
    })


@app.route('/quiz', methods=['POST'])
def handle_quiz():
    """Main endpoint that receives quiz tasks"""
    start_time = time.time()
    
    try:
        data = request.json
        
        # Validate JSON
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400
        
        print(f"\n{'='*60}")
        print(f"📥 NEW QUIZ REQUEST at {time.strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        # Verify secret
        if data.get('secret') != YOUR_SECRET:
            print("❌ Invalid secret!")
            return jsonify({"error": "Invalid secret"}), 403
        
        # Verify email
        if data.get('email') != YOUR_EMAIL:
            print("❌ Invalid email!")
            return jsonify({"error": "Invalid email"}), 403
        
        # Process quizzes in sequence
        current_url = data.get('url')
        quiz_count = 0
        max_quizzes = 20  # Safety limit
        
        while current_url and quiz_count < max_quizzes:
            quiz_count += 1
            elapsed = time.time() - start_time
            
            print(f"\n{'='*60}")
            print(f"📋 QUIZ {quiz_count} | Elapsed: {elapsed:.1f}s")
            print(f"{'='*60}")
            print(f"🔗 URL: {current_url}")
            
            # Check 3-minute timeout
            if elapsed > 170:  # 170 seconds = 2:50, leave buffer
                print("⚠️ Approaching 3-minute limit, stopping")
                break
            
            # Step 1: Scrape
            quiz_data = scrape_quiz_page(current_url)
            if not quiz_data:
                print("❌ Failed to scrape, moving on")
                break
            
            question = quiz_data['question']
            print(f"❓ Question: {question[:150]}...")
            
            # Step 2: Download files
            data_context = None
            if quiz_data['files']:
                for file_name, file_url in quiz_data['files'].items():
                    data_context = download_file(file_url)
                    if data_context:
                        break
            
            # Step 3: Solve
            answer = solve_with_gpt(question, data_context)
            if answer is None:
                print("❌ Failed to solve, moving on")
                break
            
            # Step 4: Submit
            result = submit_answer(current_url, answer)
            
            # Check result
            if result.get('correct'):
                print(f"✅ CORRECT!")
                if result.get('url'):
                    current_url = result['url']
                    print(f"➡️  Next quiz: {current_url}")
                else:
                    print(f"🎉 Quiz chain complete!")
                    break
            else:
                print(f"❌ INCORRECT: {result.get('reason', 'Unknown error')}")
                # Could retry here, but moving on for now
                if result.get('url'):
                    current_url = result['url']
                else:
                    break
        
        total_time = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"✅ SESSION COMPLETE")
        print(f"Quizzes attempted: {quiz_count}")
        print(f"Total time: {total_time:.1f}s")
        print(f"{'='*60}\n")
        
        return jsonify({
            "status": "complete",
            "quizzes_attempted": quiz_count,
            "total_time": total_time
        }), 200
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Starting LLM Quiz API with OpenAI")
    print("="*60)
    print(f"📧 Email: {YOUR_EMAIL}")
    print(f"🔑 Secret: {'✅ SET' if YOUR_SECRET else '❌ NOT SET'}")
    print(f"🤖 OpenAI Key: {'✅ SET' if OPENAI_API_KEY else '❌ NOT SET'}")
    print(f"🌐 Server: http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)