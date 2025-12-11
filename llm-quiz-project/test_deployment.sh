#!/bin/bash

echo "🔍 Testing LLM Quiz API Deployment"
echo "=================================="
echo ""

# Test 1: Health Check
echo "Test 1: Health Check"
echo "-------------------"
response=$(curl -s https://llm-quiz-api.onrender.com/)
echo "$response" | python3 -m json.tool
version=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('version', 'NOT FOUND'))")
echo ""
echo "Version: $version"
echo ""

if [ "$version" == "v2.1-fixed-scraping" ]; then
    echo "✅ Correct version deployed!"
else
    echo "❌ Wrong version! Expected v2.1-fixed-scraping, got: $version"
    exit 1
fi

echo ""
echo "Test 2: Demo Quiz"
echo "----------------"
curl -X POST https://llm-quiz-api.onrender.com/quiz \
  -H "Content-Type: application/json" \
  -d '{
    "email": "24f2003882@ds.study.iitm.ac.in",
    "secret": "messi10",
    "url": "https://tds-llm-analysis.s-anand.net/demo"
  }' | python3 -m json.tool

echo ""
echo "=================================="
echo "✅ All tests complete!"
