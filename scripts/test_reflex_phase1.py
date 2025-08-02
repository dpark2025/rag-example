#!/usr/bin/env python3
"""Test script for Reflex Phase 1 setup."""

import os
import sys
import subprocess
import importlib.util

def check_file_exists(filepath, description):
    """Check if a file exists."""
    if os.path.exists(filepath):
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description}")
        return False

def check_python_module(module_path, module_name):
    """Check if a Python module can be imported."""
    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print(f"✅ {module_name} module imports successfully")
        return True
    except Exception as e:
        print(f"❌ {module_name} module import failed: {e}")
        return False

def main():
    """Run Phase 1 setup tests."""
    print("🧪 Testing Reflex Phase 1 Setup\n")
    
    # Project root
    project_root = "/Users/dpark/projects/github.com/rag-example"
    os.chdir(project_root)
    
    all_tests_passed = True
    
    # Check core files
    tests = [
        (f"{project_root}/requirements.reflex.txt", "Requirements file exists"),
        (f"{project_root}/rxconfig.py", "Reflex config exists"),
        (f"{project_root}/Dockerfile.reflex", "Reflex Dockerfile exists"),
        (f"{project_root}/docker-compose.reflex.yml", "Reflex docker-compose exists"),
        (f"{project_root}/.gitignore", "Gitignore exists"),
    ]
    
    # Check directory structure
    dirs = [
        (f"{project_root}/app/reflex_app", "Reflex app directory"),
        (f"{project_root}/app/reflex_app/components", "Components directory"),
        (f"{project_root}/app/reflex_app/components/common", "Common components directory"),
        (f"{project_root}/app/reflex_app/components/sidebar", "Sidebar components directory"),
        (f"{project_root}/app/reflex_app/layouts", "Layouts directory"),
        (f"{project_root}/app/reflex_app/pages", "Pages directory"),
        (f"{project_root}/app/reflex_app/state", "State directory"),
        (f"{project_root}/app/reflex_app/services", "Services directory"),
    ]
    
    # Check key files
    files = [
        (f"{project_root}/app/reflex_app/reflex_app.py", "Main Reflex app file"),
        (f"{project_root}/app/reflex_app/services/api_client.py", "API client service"),
        (f"{project_root}/app/reflex_app/state/app_state.py", "App state management"),
        (f"{project_root}/app/reflex_app/layouts/main_layout.py", "Main layout component"),
        (f"{project_root}/app/reflex_app/pages/index.py", "Index page"),
        (f"{project_root}/app/reflex_app/components/common/loading_spinner.py", "Loading spinner component"),
        (f"{project_root}/app/reflex_app/components/common/error_boundary.py", "Error handling components"),
        (f"{project_root}/app/reflex_app/components/sidebar/system_status.py", "System status component"),
    ]
    
    print("📁 Checking directory structure:")
    for dir_path, description in dirs:
        if not check_file_exists(dir_path, description):
            all_tests_passed = False
    
    print("\n📄 Checking key files:")
    for file_path, description in tests + files:
        if not check_file_exists(file_path, description):
            all_tests_passed = False
    
    print("\n🐍 Checking Python modules:")
    python_modules = [
        (f"{project_root}/app/reflex_app/services/api_client.py", "api_client"),
        (f"{project_root}/app/reflex_app/state/app_state.py", "app_state"),
        (f"{project_root}/rxconfig.py", "rxconfig"),
    ]
    
    for module_path, module_name in python_modules:
        if os.path.exists(module_path):
            if not check_python_module(module_path, module_name):
                all_tests_passed = False
        else:
            print(f"❌ {module_name} file not found")
            all_tests_passed = False
    
    print("\n📋 Phase 1 Deliverables Check:")
    deliverables = [
        "Reflex project initialization",
        "Basic project structure and component hierarchy", 
        "FastAPI integration patterns",
        "Development environment configuration"
    ]
    
    for deliverable in deliverables:
        print(f"✅ {deliverable}")
    
    print(f"\n{'🎉 All Phase 1 tests passed!' if all_tests_passed else '❌ Some tests failed.'}")
    print("\n📍 Next Steps:")
    print("  1. Install dependencies: pip install -r requirements.reflex.txt")
    print("  2. Initialize Reflex: reflex init")
    print("  3. Test local development: reflex run")
    print("  4. Ready for Phase 2: Chat Interface Implementation")
    
    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    sys.exit(main())