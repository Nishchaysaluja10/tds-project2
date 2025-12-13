
def process_image_diff(before_url, after_url):
    """Compare two images and count differing pixels"""
    try:
        print(f"🖼️  Comparing images: {before_url} vs {after_url}")
        import requests
        from PIL import Image
        from io import BytesIO
        
        # Download images
        resp1 = requests.get(before_url, timeout=10)
        resp2 = requests.get(after_url, timeout=10)
        resp1.raise_for_status()
        resp2.raise_for_status()
        
        img1 = Image.open(BytesIO(resp1.content)).convert('RGB')
        img2 = Image.open(BytesIO(resp2.content)).convert('RGB')
        
        # Ensure same size
        if img1.size != img2.size:
            print(f"⚠️ Image sizes differ: {img1.size} vs {img2.size}")
            img2 = img2.resize(img1.size)
            
        # Compare pixels
        pixels1 = list(img1.getdata())
        pixels2 = list(img2.getdata())
        
        diff_count = 0
        for p1, p2 in zip(pixels1, pixels2):
            if p1 != p2:
                diff_count += 1
                
        print(f"✅ Found {diff_count} differing pixels")
        return diff_count
        
    except Exception as e:
        print(f"❌ Image diff error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
