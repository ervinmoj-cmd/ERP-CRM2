
import os

file_path = 'app.py'

print(f"Fixing encoding for {file_path}...")

try:
    with open(file_path, 'rb') as f:
        content = f.read()
        
    print(f"Original size: {len(content)} bytes")
    
    # Remove null bytes which are typical of UTF-16 being interpreted as something else or just PowerShell artifacts
    cleaned_content = content.replace(b'\x00', b'')
    
    # Try to decode to ensure it's valid text now
    text_content = cleaned_content.decode('utf-8', errors='ignore')
    
    print(f"Cleaned size: {len(cleaned_content)} bytes")
    
    # Write back as proper utf-8
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text_content)
        
    print("File saved successfully.")
    
except Exception as e:
    print(f"Error fixing file: {e}")
