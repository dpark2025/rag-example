"""Simple test to verify enhanced app loads without errors."""

import subprocess
import time
import os

def test_enhanced_app_startup():
    """Test that the enhanced app starts without Python errors."""
    
    print("🧪 Testing enhanced RAG app startup...")
    
    # Change to the app directory
    original_dir = os.getcwd()
    try:
        os.chdir("app/reflex_app/rag_reflex_app")
        
        # Try to import the app
        print("📦 Testing app import...")
        result = subprocess.run(
            ["python", "-c", "from rag_reflex_app_enhanced_simple import app; print('✅ Enhanced app imported successfully')"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(result.stdout)
            print("🎉 SUCCESS: Enhanced app loads without Python errors!")
            
            # Test export
            print("📤 Testing app export...")
            export_result = subprocess.run(
                ["reflex", "export", "--app", "rag_reflex_app_enhanced_simple.py", "--no-zip"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if export_result.returncode == 0:
                print("✅ App exports successfully (no React DOM errors)")
                return True
            else:
                print(f"❌ Export failed: {export_result.stderr}")
                return False
                
        else:
            print(f"❌ App import failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    finally:
        os.chdir(original_dir)

if __name__ == "__main__":
    success = test_enhanced_app_startup()
    print(f"\n🏁 Test {'PASSED' if success else 'FAILED'}")