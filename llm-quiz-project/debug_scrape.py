import requests
from bs4 import BeautifulSoup

url = "https://tds-llm-analysis.s-anand.net/demo"

print(f"Fetching: {url}")
print("="*60)

try:
    response = requests.get(url, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Content Type: {response.headers.get('content-type')}")
    print(f"Content Length: {len(response.content)} bytes")
    print()
    
    # Save the HTML to a file so we can inspect it
    with open('demo_page.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("✅ Saved HTML to demo_page.html")
    print()
    
    # Parse it
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Look for div with id="result"
    result_div = soup.find('div', id='result')
    print(f"Found div#result: {result_div is not None}")
    
    if result_div:
        print(f"Content: {result_div.get_text(strip=True)}")
    else:
        # Let's see what's actually in the page
        print("\nAll div elements found:")
        for div in soup.find_all('div')[:5]:  # First 5 divs
            div_id = div.get('id', 'no-id')
            div_class = div.get('class', 'no-class')
            print(f"  - ID: {div_id}, Class: {div_class}")
        
        print("\nAll script tags found:")
        scripts = soup.find_all('script')
        print(f"  Found {len(scripts)} script tags")
        
        # Check if it's a JavaScript-rendered page
        if len(scripts) > 0:
            print("\n⚠️  This might be a JavaScript-rendered page!")
            print("  The content might be loaded dynamically.")
    
    print("\n" + "="*60)
    print("First 500 characters of HTML:")
    print("="*60)
    print(response.text[:500])
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()