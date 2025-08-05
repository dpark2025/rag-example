#!/usr/bin/env python3
"""Fix Reflex component size parameters to use valid values."""

import os
import re

def fix_component_sizes_in_file(filepath):
    """Fix component size parameters in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Define size mappings for different components
    patterns = [
        # Button sizes: 1, 2, 3, 4
        (r'rx\.button\([^)]*size="sm"', lambda m: m.group(0).replace('size="sm"', 'size="2"')),
        (r'rx\.button\([^)]*size="md"', lambda m: m.group(0).replace('size="md"', 'size="3"')),
        (r'rx\.button\([^)]*size="lg"', lambda m: m.group(0).replace('size="lg"', 'size="4"')),
        
        # Heading sizes: 1-9
        (r'rx\.heading\([^)]*size="xs"', lambda m: m.group(0).replace('size="xs"', 'size="8"')),
        (r'rx\.heading\([^)]*size="sm"', lambda m: m.group(0).replace('size="sm"', 'size="7"')),
        (r'rx\.heading\([^)]*size="md"', lambda m: m.group(0).replace('size="md"', 'size="5"')),
        (r'rx\.heading\([^)]*size="lg"', lambda m: m.group(0).replace('size="lg"', 'size="4"')),
        (r'rx\.heading\([^)]*size="xl"', lambda m: m.group(0).replace('size="xl"', 'size="3"')),
        
        # Spinner sizes: 1, 2, 3
        (r'rx\.spinner\([^)]*size="sm"', lambda m: m.group(0).replace('size="sm"', 'size="1"')),
        (r'rx\.spinner\([^)]*size="md"', lambda m: m.group(0).replace('size="md"', 'size="2"')),
        (r'rx\.spinner\([^)]*size="lg"', lambda m: m.group(0).replace('size="lg"', 'size="3"')),
        
        # Avatar sizes: 1-9 (similar to heading)
        (r'rx\.avatar\([^)]*size="xs"', lambda m: m.group(0).replace('size="xs"', 'size="8"')),
        (r'rx\.avatar\([^)]*size="sm"', lambda m: m.group(0).replace('size="sm"', 'size="7"')),
        (r'rx\.avatar\([^)]*size="md"', lambda m: m.group(0).replace('size="md"', 'size="5"')),
        (r'rx\.avatar\([^)]*size="lg"', lambda m: m.group(0).replace('size="lg"', 'size="4"')),
        (r'rx\.avatar\([^)]*size="xl"', lambda m: m.group(0).replace('size="xl"', 'size="3"')),
        
        # Badge sizes: 1, 2, 3
        (r'rx\.badge\([^)]*size="sm"', lambda m: m.group(0).replace('size="sm"', 'size="2"')),
        (r'rx\.badge\([^)]*size="md"', lambda m: m.group(0).replace('size="md"', 'size="2"')),
        (r'rx\.badge\([^)]*size="lg"', lambda m: m.group(0).replace('size="lg"', 'size="3"')),
        
        # Text sizes - common size strings to remove if they're invalid
        (r'font_size="xs"', 'font_size="12px"'),
        (r'font_size="sm"', 'font_size="14px"'),
        (r'font_size="md"', 'font_size="16px"'),
        (r'font_size="lg"', 'font_size="18px"'),
        (r'font_size="xl"', 'font_size="20px"'),
    ]
    
    original_content = content
    for pattern, replacement in patterns:
        if callable(replacement):
            # For complex replacements using lambda functions
            matches = list(re.finditer(pattern, content))
            for match in reversed(matches):  # Process in reverse to maintain positions
                old_text = match.group(0)
                new_text = replacement(match)
                content = content[:match.start()] + new_text + content[match.end():]
        else:
            # For simple string replacements
            content = re.sub(pattern, replacement, content)
    
    # Only write if content changed
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed component sizes in: {filepath}")
        return True
    return False

def fix_all_component_sizes(directory):
    """Fix component sizes in all Python files in directory."""
    fixed_count = 0
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_component_sizes_in_file(filepath):
                    fixed_count += 1
    
    print(f"\nFixed component sizes in {fixed_count} files.")

if __name__ == "__main__":
    reflex_app_dir = "/Users/dpark/projects/github.com/rag-example/app/reflex_app/rag_reflex_app"
    print(f"Fixing component sizes in: {reflex_app_dir}")
    fix_all_component_sizes(reflex_app_dir)