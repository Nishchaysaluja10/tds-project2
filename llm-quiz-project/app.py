from config import YOUR_EMAIL, YOUR_SECRET, OPENAI_API_KEY, SUBMIT_ENDPOINT
from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import pandas as pd
from io import StringIO, BytesIO
from urllib.parse import urljoin

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Your credentials
YOUR_EMAIL = os.getenv('YOUR_EMAIL')
YOUR_SECRET = os.getenv('YOUR_SECRET')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Submission endpoint (you'll get this from project instructions)
SUBMIT_ENDPOINT = "https://example.com/submit"  # TODO: UPDATE THIS


def scrape_quiz_page(url):
    """Fetch the quiz page and extract the question (handles JavaScript)"""
    try:
        print(f"Scraping: {url}")
        
        # Use Playwright for JavaScript rendering
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Navigate and wait for content
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for result div to appear
            try:
                page.wait_for_selector('#result', timeout=5000)
            except:
                print("Warning: #result div not found immediately")
            
            # Wait a bit more for JavaScript to execute
            page.wait_for_timeout(2000)
            
            # Get the rendered HTML
            content = page.content()
            browser.close()
        
        # Now parse with BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract question from #result div
        result_div = soup.find('div', id='result')
        
        if not result_div:
            print("❌ No #result div found")
            return None
        
        question_text = result_div.get_text(strip=True)
        print(f"✅ Question found: {question_text[:150]}...")
        
        # Look for downloadable files
        files = {}
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            
            if (link.get('download') or 
                'download' in text.lower() or 
                any(href.endswith(ext) for ext in ['.csv', '.xlsx', '.xls', '.pdf', '.txt', '.json'])):
                
                if not href.startswith('http'):
                    from urllib.parse import urljoin
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
        response = requests.get(url, timeout=10)
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
            prompt += f"\n\nData provided:\n{data_context}\n"
        
        prompt += """
Important instructions:
- Provide ONLY the final answer
- If it's a number, give just the number (no units, no commas, no formatting)
- If it's a calculation, show only the result
- No explanations or reasoning
- Be precise and exact

Answer:"""

        print("🤖 Calling GPT...")
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",  # Change to "gpt-3.5-turbo" for testing to save money
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
            temperature=0,  # More deterministic
            max_tokens=500
        )
        
        answer = response.choices[0].message.content.strip()
        print(f"✅ GPT raw answer: {answer}")
        
        # Clean up the answer
        answer = answer.replace('Answer:', '').strip()
        answer = answer.replace('The answer is', '').strip()
        answer = answer.replace(',', '')  # Remove commas from numbers
        
        # Try to convert to number if possible
        try:
            if '.' in answer:
                return float(answer)
            return int(answer)
        except ValueError:
            # Return as string if not a number
            return answer
            
    except Exception as e:
        print(f"❌ GPT error: {str(e)}")
        return None


def submit_answer(quiz_url, answer):
    """Submit the answer back to the evaluation system"""
    try:
        payload = {
            "email": YOUR_EMAIL,
            "secret": YOUR_SECRET,
            "url": quiz_url,
            "answer": answer
        }
        
        print(f"📤 Submitting answer: {answer}")
        
        response = requests.post(SUBMIT_ENDPOINT, json=payload, timeout=30)
        result = response.json()
        
        print(f"📨 Submission result: {result}")
        return result
        
    except Exception as e:
        print(f"❌ Submission error: {str(e)}")
        return {"error": str(e)}


@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "running",
        "message": "LLM Quiz API with OpenAI 🚀",
        "email_configured": YOUR_EMAIL is not None,
        "secret_configured": YOUR_SECRET is not None,
        "openai_configured": OPENAI_API_KEY is not None
    })


@app.route('/quiz', methods=['POST'])
def handle_quiz():
    """Main endpoint that receives quiz tasks"""
    try:
        data = request.json
        print(f"\n{'='*60}")
        print(f"📥 NEW QUIZ REQUEST")
        print(f"{'='*60}")
        
        # Verify secret
        if data.get('secret') != YOUR_SECRET:
            print("❌ Invalid secret!")
            return jsonify({"error": "Invalid secret"}), 403
        
        # Verify email
        if data.get('email') != YOUR_EMAIL:
            print("❌ Invalid email!")
            return jsonify({"error": "Invalid email"}), 403
        
        quiz_url = data.get('url')
        print(f"🔗 Quiz URL: {quiz_url}")
        
        # Step 1: Scrape the quiz page
        print("\n📋 Step 1: Scraping quiz page...")
        quiz_data = scrape_quiz_page(quiz_url)
        if not quiz_data:
            return jsonify({"error": "Failed to scrape quiz page"}), 400
        
        question = quiz_data['question']
        
        # Step 2: Download files if any
        data_context = None
        if quiz_data['files']:
            print(f"\n📂 Step 2: Processing files...")
            for file_name, file_url in quiz_data['files'].items():
                data_context = download_file(file_url)
                if data_context:
                    break  # Use first file for now
        else:
            print("\n📂 Step 2: No files to download")
        
        # Step 3: Solve with GPT
        print(f"\n🧠 Step 3: Solving with GPT...")
        answer = solve_with_gpt(question, data_context)
        if answer is None:
            return jsonify({"error": "Failed to solve with GPT"}), 400
        
        # Step 4: Submit answer
        print(f"\n📤 Step 4: Submitting answer...")
        result = submit_answer(quiz_url, answer)
        
        print(f"\n{'='*60}")
        print(f"✅ QUIZ COMPLETE")
        print(f"Question: {question[:100]}...")
        print(f"Answer: {answer}")
        print(f"Result: {result}")
        print(f"{'='*60}\n")
        
        return jsonify({
            "status": "complete",
            "question": question,
            "answer": answer,
            "result": result
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