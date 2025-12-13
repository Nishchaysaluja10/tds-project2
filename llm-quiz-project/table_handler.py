
import pandas as pd
import openai
import json
import re
from dotenv import load_dotenv
import os

def process_table_quiz(html_content, question):
    """
    Extracts table from HTML.
    Uses GPT to determine which column to aggregate and how (SUM/COUNT/MEAN).
    Performs aggregation using Pandas.
    """
    client = openai.OpenAI(
        api_key=os.environ.get("AIPIPE_API_KEY"),
        base_url="https://aipipe.org/openai/v1"
    )

    try:
        # Use lxml flavor if installed, else default
        try:
            tables = pd.read_html(html_content)
        except Exception as e:
            print(f"⚠️ Pandas read_html failed: {e}")
            return None
            
        if not tables:
            print("❌ No tables found in HTML")
            return None
            
        df = tables[0]
        print(f"📋 Table Found: {df.shape} - Columns: {list(df.columns)}")
        
        # Ask GPT for instruction
        prompt = f"""
You are a Data Analyst.
I have a DataFrame with columns: {list(df.columns)}
The user asks: "{question}"

Identify:
1. The Column Name to operate on (must match one of the columns exactly or closely).
2. The Operation (SUM, MEAN, COUNT, MIN, MAX).

Return JSON ONLY:
{{
  "column": "ColumnName",
  "operation": "SUM"
}}
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = response.choices[0].message.content.strip()
        # content clean
        content = re.sub(r'```json\n?', '', content)
        content = re.sub(r'```', '', content).strip()
        
        cmd = json.loads(content)
        col_name = cmd.get('column')
        op = cmd.get('operation', 'SUM').upper()
        
        print(f"🤖 GPT Instruction: Op={op}, Col={col_name}")
        
        # Process
        # Fuzzy match column if not exact
        if col_name not in df.columns:
            # Simple fuzzy
            match = None
            for c in df.columns:
                if col_name.lower() in c.lower() or c.lower() in col_name.lower():
                    match = c
                    break
            if match:
                col_name = match
                
        if col_name not in df.columns:
            print(f"❌ Column '{col_name}' not found.")
            return None
            
        series = df[col_name]
        
        # Clean currency/strings
        # Remove '$', ',', etc.
        if series.dtype == object:
            series = series.astype(str).str.replace(r'[$,]', '', regex=True)
            series = pd.to_numeric(series, errors='coerce')
            
        if op == 'SUM':
            result = series.sum()
        elif op == 'MEAN':
            result = series.mean()
        elif op == 'COUNT':
            result = series.count()
        elif op == 'MAX':
            result = series.max()
        elif op == 'MIN':
            result = series.min()
        else:
            result = 0
            
        # Round if 'round' in question? Question Q6 said "Round to 2 decimal places"
        # Since API might want float or string?
        # User logs: "Answer: 272.0" (failed). Correct "273".
        # If result is integer-like (X.0), return int?
        
        print(f"✅ Table Result raw: {result}")
        return result
        
    except Exception as e:
        print(f"❌ Table Handler Error: {e}")
        return None
