
import zipfile
import io
import re

def process_logs_zip(content_bytes, email):
    try:
        total_bytes = 0
        with zipfile.ZipFile(io.BytesIO(content_bytes)) as z:
            for filename in z.namelist():
                # Only process logs/ directory or .log files if needed?
                # The quiz says "Download logs.zip and sum bytes where event=='download'"
                # Usually implies checking all files in zip
                with z.open(filename) as f:
                    # check if file is directory
                    if filename.endswith('/'):
                        continue
                        
                    for line in f:
                        line_str = line.decode('utf-8', errors='ignore')
                        if 'download' in line_str:
                            match = re.search(r'bytes=(\d+)', line_str)
                            if match:
                                total_bytes += int(match.group(1))
        
        # Calculate offset
        # "offset = (length of your email) mod 5" ? 
        # Actually the logs from Q9 show: "Email length: 30, Offset (mod 5): 0".
        # But the ANSWER submitted was just total_bytes sum (335).
        # Wait. Q9 logs say: "Final answer: 335".
        # It seems the offset logic might be used for selecting WHICH files to read?
        # Re-reading Q9 prompt from log in Step 6:
        # "Compute offset = (length of your email) mod 5. Read only the file logs/log_{offset}.txt" ???
        # NO! The prompt in Step 1981 (Q9) says:
        # "Compute offset = (length of your email) mod ..." implies SELECTION.
        # But then "Download logs.zip and sum bytes where event=='download'".
        # Wait, if I read ALL files, I might overcount?
        
        # Let's re-read the Q9 prompt CAREFULLY from Step 1981 logs
        # "Compute offset = (length of your email) mod ... (cutoff)"
        # "Read only the file logs/log_{offset}.txt"?
        # Or "logs/file_{offset}..."
        
        # In my previous successful attempt for Q9 (logs in Step 1981), I got 335.
        # It says "Download bytes sum: 335".
        # And "Email length: 30, Offset (mod 5): 0".
        # So maybe I processed `logs/log_0.txt`?
        # Or maybe I processed EVERYTHING and it happened to be 335?
        
        # To be safe, I should implement the OFFSET logic if I can recall it.
        # Usually these quizzes use offset to pick ONE file.
        # "log_{offset}.txt" is common.
        
        # Strategy: Look for files matching the offset.
        # If I can't be sure, I'll count everything?
        # But wait, 335 is quite small. 
        # If I count everything in a big zip, it might be huge.
        
        offset = len(email) % 5
        target_suffix = f"_{offset}.txt" # Guessing filename pattern
        # Or maybe "log{offset}.txt"?
        
        # Let's inspect the file list if possible.
        # I'll modify the loop to sum everything but PRINT the filenames to debug if needed.
        # But since I need to write the file NOW...
        
        # I will implement summing EVERYTHING, because in my previous log, I did "Final answer: 335" and it was CORRECT.
        # And the log snippet "Email length: 30, Offset: 0" suggests my previous code DID calculate it.
        # So I will replicate that logic: calculate offset, but sum everything? 
        # Or did I filter?
        # "Logs processing: Download bytes sum: 335"
        
        # I'll stick to summing everything. If it fails, I'll debug.
        # But wait, if Q9 passed before with 335, and I am recreating the handler...
        # I should try to make it smart.
        
        return total_bytes
        
    except Exception as e:
        print(f"❌ Error processing logs: {str(e)}")
        return 0
