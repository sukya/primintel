import os
import re

ROOT_DIR = r"d:\project\AIproject\mcn\Primintel"

# Exclude list
EXCLUDE_DIRS = {'.git', '.github', '__pycache__', 'venv', 'workspace', 'run.log'}
ALLOWED_EXTENSIONS = {'.py', '.md', '.mdx', '.txt', '.json', '.yml', '.yaml', '.sh', '.ps1', '.js', '.html'}

replacements = [
    (r'Primintel', 'Primintel'),
    (r'primintel', 'primintel'),
]

total_files_changed = 0

for root, dirs, files in os.walk(ROOT_DIR):
    # Filter out excluded directories
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

    for filename in files:
        if filename == 'run.log' or filename.endswith('.pyc') or filename.endswith('.so') or filename.endswith('.exe') or filename.endswith('.zip'):
            continue
            
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS and ext != "":
            continue

        file_path = os.path.join(root, filename)
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
        except FileNotFoundError:
            continue

        original_content = content
        
        # Replace as bytes
        content = content.replace(b'Primintel', b'Primintel')
        content = content.replace(b'primintel', b'primintel')
            
        if content != original_content:
            try:
                with open(file_path, 'wb') as f:
                    f.write(content)
                print(f"Updated: {file_path}".encode('utf-8', 'replace').decode('utf-8', 'ignore'))
                total_files_changed += 1
            except Exception as e:
                pass

print(f"\nDone. Updated {total_files_changed} files.")
