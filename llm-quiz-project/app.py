from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
load_dotenv()

# Version tracking for deployment verification
API_VERSION = "v4.0-reevaluation"

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
# AIpipe proxies OpenAI requests through /openai/* path
client = OpenAI(
    api_key=AIPIPE_API_KEY,
    base_url="https://aipipe.org/openai/v1"  # AIpipe.org OpenAI proxy endpoint
)

# Submission endpoint - will be extracted from quiz page
SUBMIT_ENDPOINT = None  # Don't hardcode - extract from page


def scrape_quiz_page(url):
    """Fetch the quiz page and extract the question using requests library"""
    try:
        print(f"Scraping: {url}")
        
        # Use requests library directly (Playwright browsers don't install on Render)
        # This avoids 30-second timeout trying to launch Playwright for each quiz
        print("📡 Using requests library (Playwright disabled for speed)")
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
            for selector in ['#quiz', '#question', '.question', 'main', 'article', 'body']:
                elem = soup.select_one(selector)
                if elem:
                    # Remove scripts, styles, nav, footer
                    for tag in elem(['script', 'style', 'nav', 'footer']):
                        tag.decompose()
                    text = elem.get_text(strip=True)
                    if text:  # Accept ANY non-empty text
                        question_text = text
                        print(f"✅ Question found in {selector}: {len(text)} chars")
                        break
        
        # FINAL FALLBACK: If no specific tags found, extract from root
        if not question_text:
            print("⚠️ No standard tags found, extracting from root HTML")
            # Remove unwanted tags globally
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            # Get text directly from soup
            text = soup.get_text(separator='\n', strip=True)
            if text:
                question_text = text
                print(f"✅ Question extracted from root: {len(text)} chars")
        
        # Only return None if we truly have no content at all
        if not question_text:
            print("❌ No content found")
            return None
        
        print(f"✅ Extracted content ({len(question_text)} chars) [v4.0-fixed]")
        
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


def analyze_image_with_gpt(image_url, question):
    """Analyze an image using GPT-4 Vision"""
    try:
        print(f"🖼️  Analyzing image with GPT-4 Vision: {image_url}")
        
        # Download image
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # Encode to base64
        import base64
        base64_image = base64.b64encode(response.content).decode('utf-8')
        
        # Determine image type
        if image_url.endswith('.png'):
            mime_type = 'image/png'
        elif image_url.endswith(('.jpg', '.jpeg')):
            mime_type = 'image/jpeg'
        elif image_url.endswith('.gif'):
            mime_type = 'image/gif'
        else:
            mime_type = 'image/png'  # default
        
        # Call GPT-4 Vision
        vision_prompt = f"""Analyze this image and answer the question.

Question: {question}

Provide ONLY the final answer. Be precise and exact.

For color questions:
- Return the hex code in lowercase format: #rrggbb
- For "dominant color" or "most frequent color", analyze the pixel colors

Answer:"""
        
        response = client.chat.completions.create(
            model="gpt-4o",  # GPT-4o has vision capabilities
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": vision_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content.strip()
        print(f"✅ GPT-4 Vision answer: {answer}")
        
        # Clean up answer
        answer = answer.replace('Answer:', '').strip()
        answer = answer.replace('The answer is', '').strip()
        
        return answer
        
    except Exception as e:
        print(f"❌ Image analysis error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def download_file(url):
    """Download a file and process it based on type"""
    print(f"Downloading file: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Check if it's an image file
        if url.endswith(('.png', '.jpg', '.jpeg', '.gif')) or 'image' in response.headers.get('content-type', '').lower():
            print(f"🖼️  Image file detected: {url}")
            # Return URL for later processing with vision
            return f"IMAGE:{url}"
        
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
        
        # Check if it's a SQLite database
        elif url.endswith('.db') or url.endswith('.sqlite'):
            import sqlite3
            import tempfile
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
                tmp.write(response.content)
                tmp_path = tmp.name
            
            # Connect and extract data
            conn = sqlite3.connect(tmp_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            result = f"SQLite Database with {len(tables)} tables:\n\n"
            
            # Extract data from each table
            for table in tables:
                table_name = table[0]
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                result += f"\n=== Table: {table_name} ({df.shape[0]} rows, {df.shape[1]} columns) ===\n"
                result += df.to_string() + "\n"
            
            conn.close()
            os.unlink(tmp_path)  # Clean up temp file
            
            print(f"✅ SQLite DB loaded: {len(tables)} tables")
            return result
        
        # Check if it's a ZIP file
        elif url.endswith('.zip'):
            import zipfile
            import tempfile
            
            result = "ZIP Archive Contents:\n\n"
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
                tmp.write(response.content)
                tmp_path = tmp.name
            
            with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                result += f"Files in archive: {', '.join(file_list)}\n\n"
                
                # Extract and process each file
                for filename in file_list:
                    file_data = zip_ref.read(filename)
                    
                    # Try to process based on file extension
                    if filename.endswith('.csv'):
                        df = pd.read_csv(BytesIO(file_data))
                        result += f"\n=== {filename} ({df.shape[0]} rows, {df.shape[1]} columns) ===\n"
                        result += df.to_string() + "\n"
                    elif filename.endswith(('.xlsx', '.xls')):
                        df = pd.read_excel(BytesIO(file_data))
                        result += f"\n=== {filename} ({df.shape[0]} rows, {df.shape[1]} columns) ===\n"
                        result += df.to_string() + "\n"
                    elif filename.endswith('.txt') or filename.endswith('.json'):
                        result += f"\n=== {filename} ===\n"
                        result += file_data.decode('utf-8', errors='ignore') + "\n"
                    else:
                        result += f"\n=== {filename} ({len(file_data)} bytes) ===\n"
            
            os.unlink(tmp_path)  # Clean up temp file
            print(f"✅ ZIP loaded: {len(file_list)} files")
            return result
        
        # PDF handling (basic)
        elif url.endswith('.pdf'):
            print(f"✅ PDF downloaded: {len(response.content)} bytes")
            return f"PDF file with {len(response.content)} bytes"
        
        else:
            print(f"✅ Text file loaded: {len(response.text)} characters")
            return response.text
            
    except Exception as e:
        print(f"❌ File download error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def solve_with_gpt(question, data_context=None, quiz_url=None):
    """Use GPT to solve the question with enhanced context"""
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
        
        # Add context hints based on question type
        prompt += "\n"
        
        # URL/Command context
        if any(keyword in question.lower() for keyword in ["http get", "curl", "command string", "uv http"]):
            prompt += "IMPORTANT: When constructing URLs, use ABSOLUTE URLs starting with https://tds-llm-analysis.s-anand.net (not relative paths).\n"
        
        # JSON formatting context
        if "json" in question.lower():
            if "normalize" in question.lower() or "snake_case" in question.lower():
                prompt += "IMPORTANT: Return ONLY valid JSON array. Convert ALL column names to snake_case (lowercase with underscores). Sort data as specified. No markdown code blocks.\n"
            else:
                prompt += "IMPORTANT: Return ONLY valid JSON. No markdown code blocks, no backticks, no explanations.\n"
        
        # Email length context for personalized quizzes
        if "email" in question.lower() and ("length" in question.lower() or "mod" in question.lower()):
            email = YOUR_EMAIL
            prompt += f"Your email address: {email}\n"
            prompt += f"Email length: {len(email)}\n"
            prompt += "Show calculation: count the items first, then add (email_length mod 2).\n"
        
        # Color/hex code context
        if "color" in question.lower() or "hex" in question.lower() or "heatmap" in question.lower():
            prompt += "IMPORTANT: Return color as lowercase hex code (#rrggbb format).\n"
        
        prompt += """
Important instructions:
- Provide ONLY the final answer
- If it's a number, give just the number (no units, no commas, no formatting)
- If it's a command, provide ONLY the command string (no explanations)
- If it's JSON, provide ONLY the JSON (no markdown, no backticks)
- If it's a yes/no question, answer with just "yes" or "no"
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
            max_tokens=1000
        )
        
        answer = response.choices[0].message.content.strip()
        print(f"✅ GPT raw answer: {answer}")
        
        # Clean up the answer
        answer = answer.replace('Answer:', '').strip()
        answer = answer.replace('The answer is', '').strip()
        answer = answer.replace('The result is', '').strip()
        
        # Remove markdown code blocks
        import re
        answer = re.sub(r'```\w*\n?', '', answer).strip()
        answer = re.sub(r'```$', '', answer).strip()
        
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
        "version": API_VERSION,
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
            image_url = None
            if quiz_data['files']:
                for file_name, file_url in quiz_data['files'].items():
                    file_data = download_file(file_url)
                    if file_data:
                        # Check if it's an image
                        if isinstance(file_data, str) and file_data.startswith('IMAGE:'):
                            image_url = file_data[6:]  # Remove 'IMAGE:' prefix
                            print(f"🖼️  Image file will be analyzed with Vision API")
                        else:
                            data_context = file_data
                        break
            
            # Step 3: Solve
            if image_url:
                # Use Vision API for images
                answer = analyze_image_with_gpt(image_url, question)
            else:
                # Use regular GPT for text
                answer = solve_with_gpt(question, data_context, quiz_url=current_url)
            
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