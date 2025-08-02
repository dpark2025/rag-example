#!/usr/bin/env python3
"""Fix typing imports in Reflex app to use standard library instead of local imports."""

import os
import re

def fix_typing_imports_in_file(filepath):
    """Fix typing imports in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Pattern to fix typing imports
    patterns = [
        (r'from \.typing import (.+)', r'from typing import \1'),  # from .typing import -> from typing import
        (r'from \.\.typing import (.+)', r'from typing import \1'),  # from ..typing import -> from typing import
        (r'from \.\.\.typing import (.+)', r'from typing import \1'),  # from ...typing import -> from typing import
        (r'from .datetime import (.+)', r'from datetime import \1'),  # from .datetime import -> from datetime import
        (r'from \.\.datetime import (.+)', r'from datetime import \1'),  # from ..datetime import -> from datetime import
    ]
    
    original_content = content
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    # Only write if content changed
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed typing imports in: {filepath}")
        return True
    return False

def fix_all_typing_imports(directory):
    """Fix typing imports in all Python files in directory."""
    fixed_count = 0
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_typing_imports_in_file(filepath):
                    fixed_count += 1
    
    print(f"\nFixed typing imports in {fixed_count} files.")

if __name__ == "__main__":
    reflex_app_dir = "/Users/dpark/projects/github.com/rag-example/app/reflex_app/rag_reflex_app"
    print(f"Fixing typing imports in: {reflex_app_dir}")
    fix_all_typing_imports(reflex_app_dir)