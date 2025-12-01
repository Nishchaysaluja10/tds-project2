from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
load_dotenv()

# Version tracking
API_VERSION = "v3.0-document-analyzer"

import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import pandas as pd
from io import StringIO, BytesIO
import json

app = Flask(__name__)

# Environment variables
AIPIPE_API_KEY = os.getenv('AIPIPE_API_KEY')

# Initialize OpenAI client
client = OpenAI(
    api_key=AIPIPE_API_KEY,
    base_url="https://aipipe.org/openai/v1"
)

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "running",
        "version": API_VERSION,
        "name": "AI Document Analyzer API",
        "endpoints": {
            "/": "Health check",
            "/analyze": "POST - Analyze document or data",
            "/ask": "POST - Ask questions about data"
        },
        "supported_formats": ["CSV", "JSON", "Text", "URL"],
        "ai_configured": AIPIPE_API_KEY is not None
    })


@app.route('/analyze', methods=['POST'])
def analyze_document():
    """
    Analyze any document or data
    
    Request body:
    {
        "data": "CSV data or text content",
        "type": "csv|json|text",
        "question": "What insights can you provide?" (optional)
    }
    
    OR
    
    {
        "url": "https://example.com/data.csv",
        "question": "Analyze this data" (optional)
    }
    """
    try:
        data = request.json
        
        # Get data from request
        if 'url' in data:
            # Download from URL
            response = requests.get(data['url'], timeout=10)
            content = response.text
            data_type = data.get('type', 'csv')
        elif 'data' in data:
            content = data['data']
            data_type = data.get('type', 'text')
        else:
            return jsonify({"error": "Please provide 'data' or 'url'"}), 400
        
        # Process based on type
        if data_type == 'csv':
            df = pd.read_csv(StringIO(content))
            data_summary = f"CSV Data ({len(df)} rows, {len(df.columns)} columns)\n\n"
            data_summary += f"Columns: {', '.join(df.columns)}\n\n"
            data_summary += f"First 5 rows:\n{df.head().to_string()}\n\n"
            data_summary += f"Statistics:\n{df.describe().to_string()}"
        elif data_type == 'json':
            json_data = json.loads(content)
            data_summary = f"JSON Data:\n{json.dumps(json_data, indent=2)}"
        else:
            data_summary = f"Text Content:\n{content[:2000]}"
        
        # Get question or use default
        question = data.get('question', 'Provide a comprehensive analysis of this data, including key insights, patterns, and notable findings.')
        
        # Ask GPT-4
        prompt = f"""Analyze the following data and answer the question.

Data:
{data_summary}

Question: {question}

Provide a clear, concise answer with specific insights from the data."""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a data analyst providing clear, actionable insights."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        answer = response.choices[0].message.content
        
        return jsonify({
            "status": "success",
            "data_type": data_type,
            "question": question,
            "answer": answer,
            "tokens_used": response.usage.total_tokens
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/ask', methods=['POST'])
def ask_question():
    """
    Ask a specific question about provided data
    
    Request body:
    {
        "data": "Your data here (CSV, JSON, or text)",
        "question": "What is the average value?",
        "type": "csv|json|text" (optional, defaults to text)
    }
    """
    try:
        data = request.json
        
        if 'data' not in data or 'question' not in data:
            return jsonify({"error": "Please provide both 'data' and 'question'"}), 400
        
        content = data['data']
        question = data['question']
        data_type = data.get('type', 'text')
        
        # Process data
        if data_type == 'csv':
            df = pd.read_csv(StringIO(content))
            context = f"CSV with {len(df)} rows:\n{df.to_string()}"
        elif data_type == 'json':
            context = f"JSON data:\n{json.dumps(json.loads(content), indent=2)}"
        else:
            context = content
        
        # Ask GPT-4
        prompt = f"""Answer the question based on the provided data.

Data:
{context[:3000]}

Question: {question}

Provide a direct, specific answer."""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions accurately based on provided data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        answer = response.choices[0].message.content
        
        return jsonify({
            "status": "success",
            "question": question,
            "answer": answer,
            "tokens_used": response.usage.total_tokens
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
