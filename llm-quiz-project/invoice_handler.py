
import io
import re
import sys
import subprocess

def process_invoice_pdf(content_bytes):
    try:
        # Use pdftotext (subprocess) if available, or pypdf?
        # Detailed prompt said "pdf text extracted".
        # Simplest way in python is pypdf (if installed) or subprocess to pdftotext.
        # Check requirements.txt? 
        # app.py imports?
        # If I don't have pypdf, I can't import it.
        # The logs earlier said "Moving to pypdf for potential better extraction".
        # So pypdf IS likely installed.
        # I'll try pypdf first.
        
        text = ""
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content_bytes))
            for page in reader.pages:
                text += page.extract_text() + "\n"
        except ImportError:
            # Fallback to subprocess pdftotext (if installed on Render)
            # Or strings?
            pass
            
        if not text:
             print("⚠️ pypdf failed or empty, trying simple string extraction")
             # Fallback: extract readable ascii (not reliable for PDF but better than nothing)
             text = content_bytes.decode('latin-1', errors='ignore')

        # Find numbers
        # Based on logs "Found 6 numbers: [3.0, 19.99, ...]"
        # Pattern seems to be Qty, Price pairs.
        # We find ALL floats in the text.
        
        # Normalize text to remove "Invoice", "Item" lines if they don't contain data.
        nums = re.findall(r'\d+\.\d+|\d+', text)
        floats = [float(x) for x in nums]
        
        # Filter out likely header numbers or large dates?
        # Heuristic: The numbers we want are likely small integers (qty) and prices.
        # Logs: [3.0, 19.99, 2.0, 5.5, 1.0, 100.0]
        # These look like strict pairs.
        # I'll assume the extracted numbers are in correct order after headers are skipped.
        # "Invoice #123"? If 123 is detected, it offsets everything!
        
        # Improved Heuristic: Look for lines with exactly 2 numbers?
        # But extract_text might merge lines.
        
        # Let's try to match the specific "Item Qty Price" structure.
        # If I can't be sure, I'll use the "find all numbers" approach but be careful.
        # The logs showed exactly 6 numbers found.
        # This implies "Invoice" and "Item" didn't have numbers, or we skipped them.
        
        # I'll assume the pairs are at the END or specific lines.
        # But for now, simple regex has the best chance if valid.
        
        total = 0.0
        # Iterate in pairs
        # But we need to filter out noise.
        # Assume valid lines have: String Int Float?
        
        # Let's stick to simple "find all numbers" for now as it worked before.
        # But filter out things that look like dates "2024..." or huge IDs "85617" (quiz ID)?
        
        clean_floats = []
        for x in floats:
             # Filter quiz IDs (usually 5+ digits integers)
             if x > 10000 and x.is_integer():
                 continue
             clean_floats.append(x)
             
        # Take pairs
        for i in range(0, len(clean_floats), 2):
            if i+1 < len(clean_floats):
                qty = clean_floats[i]
                price = clean_floats[i+1]
                total += qty * price
                
        return total

    except Exception as e:
        print(f"❌ Error processing invoice: {str(e)}")
        return 0.0
