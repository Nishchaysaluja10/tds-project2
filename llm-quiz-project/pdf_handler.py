
import io
import openai
from pypdf import PdfReader
from dotenv import load_dotenv
import os

def process_pdf_quiz(pdf_bytes, question):
    """
    Extract text from PDF and use GPT to answer the question.
    """
    client = openai.OpenAI(
        api_key=os.environ.get("AIPIPE_API_KEY"),
        base_url="https://aipipe.org/openai/v1"
    )
    
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
            
        print(f"📄 Extracted PDF text length: {len(text)}")
        
        # Specific Logic for Q19 (Q2 Summary)
        if "Q2 Summary" in question or "Q2 Summary" in text:
            import re
            # Pattern: "Q2 Summary: Total Operating Expenses: $8,126.49"
            # Flexible pattern: Q2 Summary ... $<number>
            match = re.search(r"Q2 Summary.*?\$([\d,]+\.\d{2})", text)
            if match:
                val_str = match.group(1).replace(',', '')
                print(f"✅ Regex found Q2 Summary: {val_str}")
                return float(val_str)
        
        # Truncate if too long (simple heuristic)
        if len(text) > 20000:
             text = text[:20000] + "...(truncated)"
             
        prompt = f"""
Use the following text extracted from a PDF to answer the question.
If the answer is a number, return only the number (e.g., 9876.54).
Format clearly.

Text:
{text}

Question:
{question}
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        
        answer = response.choices[0].message.content.strip()
        print(f"🤖 PDF Answer: {answer}")
        
        # Post-process cleanup (remove quotes, etc)
        # Assuming parse_answer in app.py does the heavy lifting
        return answer
        
    except Exception as e:
        print(f"❌ PDF Processing Error: {e}")
        return None
