#!/usr/bin/env python3
"""Fix relative imports in Reflex app to use absolute imports."""

import os
import re

def fix_imports_in_file(filepath):
    """Fix relative imports in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Pattern to add relative imports (dot notation) for intra-package imports
    patterns = [
        (r'from ([a-zA-Z_][a-zA-Z0-9_]*) import', r'from .\1 import'),  # from module import -> from .module import
    ]
    
    original_content = content
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    # Only write if content changed
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed imports in: {filepath}")
        return True
    return False

def fix_all_imports(directory):
    """Fix imports in all Python files in directory."""
    fixed_count = 0
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') and file != 'fix_imports.py':
                filepath = os.path.join(root, file)
                if fix_imports_in_file(filepath):
                    fixed_count += 1
    
    print(f"\nFixed imports in {fixed_count} files.")

if __name__ == "__main__":
    reflex_app_dir = "/Users/dpark/projects/github.com/rag-example/app/reflex_app/rag_reflex_app"
    print(f"Fixing imports in: {reflex_app_dir}")
    fix_all_imports(reflex_app_dir)