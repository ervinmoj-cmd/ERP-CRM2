
import os

files_to_check = ['app.py', 'database.py']

for file_path in files_to_check:
    if os.path.exists(file_path):
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            null_count = content.count(b'\x00')
            print(f"File: {file_path}")
            print(f"  Size: {len(content)} bytes")
            print(f"  Null bytes found: {null_count}")
            
            if null_count > 0:
                print("  CRITICAL: Null bytes detected!")
                # Attempt to fix
                cleaned = content.replace(b'\x00', b'')
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned.decode('utf-8', errors='ignore'))
                print("  Attempted auto-fix (removed null bytes).")
            else:
                print("  File seems clean of null bytes.")
                
        except Exception as e:
            print(f"Error checking {file_path}: {e}")
