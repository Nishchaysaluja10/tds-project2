
import sqlite3
import openai
from dotenv import load_dotenv
import os

load_dotenv()
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def process_sqlite_quiz(sql_file_content, question):
    """
    1. Create in-memory DB.
    2. Execute sql_file_content (schema + data).
    3. Ask GPT to generate SELECT query for 'question'.
    4. Execute query and return result.
    """
    try:
        # 1. Setup DB
        conn = sqlite3.connect(':memory:')
        cur = conn.cursor()
        
        # 2. Seed DB
        cur.executescript(sql_file_content)
        conn.commit()
        
        # Inspection (Optional: Get table schema to help GPT)
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cur.fetchall()
        schema_info = ""
        for t in tables:
            table_name = t[0]
            cur.execute(f"PRAGMA table_info({table_name})")
            cols = cur.fetchall()
            col_names = [c[1] for c in cols]
            schema_info += f"Table {table_name}: {', '.join(col_names)}\n"
            
        print(f"🗄️ Database Schema:\n{schema_info}")
        
        # 3. GPT generate SQL
        prompt = f"""
You are a SQLite expert. Given the database schema:
{schema_info}

Write a single valid SQL query to answer this question:
"{question}"

Return ONLY the SQL query. Do not wrap in markdown or quotes.
EXAMPLE:
Question: Count users > 18
SQL: SELECT COUNT(*) FROM users WHERE age > 18;
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        
        sql_query = response.choices[0].message.content.strip()
        # Clean markdown if present
        sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
        
        print(f"🤖 Generated SQL: {sql_query}")
        
        # 4. Execute
        cur.execute(sql_query)
        result = cur.fetchone()[0]
        
        print(f"✅ SQL Result: {result}")
        return result
        
    except Exception as e:
        print(f"❌ SQLite Processing Error: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()
