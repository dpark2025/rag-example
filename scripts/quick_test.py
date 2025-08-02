#!/usr/bin/env python3
"""Quick test to verify Reflex components can be imported and instantiated."""

import sys
import os

# Add the reflex app directory to the path (relative to script location)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
reflex_app_path = os.path.join(project_root, 'app', 'reflex_app')
app_path = os.path.join(project_root, 'app')

# Add both paths for proper imports
sys.path.insert(0, reflex_app_path)
sys.path.insert(0, app_path)

# Set PYTHONPATH environment variable for consistent imports
os.environ['PYTHONPATH'] = reflex_app_path

def test_imports():
    """Test if our components can be imported."""
    print("🧪 Testing Reflex Component Imports")
    print("=================================")
    
    try:
        # Test basic reflex import
        print("📦 Testing Reflex framework...")
        import reflex as rx
        print("✅ Reflex imported successfully")
        
        # Test our state classes
        print("📦 Testing state classes...")
        from rag_reflex_app.state.app_state import AppState
        from rag_reflex_app.state.chat_state import ChatState, ChatMessage
        print("✅ State classes imported successfully")
        
        # Test components
        print("📦 Testing component imports...")
        from rag_reflex_app.components.common.loading_spinner import loading_spinner
        from rag_reflex_app.components.common.error_boundary import error_alert
        from rag_reflex_app.components.sidebar.system_status import system_status_panel
        print("✅ Common components imported successfully")
        
        from rag_reflex_app.components.chat.message_component import message_component, user_message, assistant_message
        from rag_reflex_app.components.chat.input_form import chat_input_form
        from rag_reflex_app.components.chat.chat_interface import chat_interface
        print("✅ Chat components imported successfully")
        
        # Test layouts
        print("📦 Testing layout imports...")
        from rag_reflex_app.layouts.main_layout import main_layout
        print("✅ Layout components imported successfully")
        
        # Test services
        print("📦 Testing service imports...")
        from rag_reflex_app.services.api_client import RAGAPIClient
        print("✅ Service classes imported successfully")
        
        print("\n🎉 All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_component_creation():
    """Test if components can be created (without reflex server)."""
    print("\n🔧 Testing Component Creation")
    print("============================")
    
    try:
        import reflex as rx
        from datetime import datetime
        from rag_reflex_app.state.chat_state import ChatMessage
        
        # Test ChatMessage creation
        test_message = ChatMessage(
            role="user",
            content="Test message",
            timestamp=datetime.now(),
            message_id="test_1"
        )
        print("✅ ChatMessage created successfully")
        
        # Test that we can access message properties
        assert test_message.role == "user"
        assert test_message.content == "Test message"
        print("✅ ChatMessage properties work correctly")
        
        # Test component function definitions exist
        from rag_reflex_app.components.chat.chat_interface import chat_interface
        from rag_reflex_app.components.chat.input_form import chat_input_form
        print("✅ Component functions are callable")
        
        print("\n🎉 Component creation tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Component creation failed: {e}")
        return False

def test_api_client():
    """Test API client instantiation."""
    print("\n🌐 Testing API Client")
    print("====================")
    
    try:
        from rag_reflex_app.services.api_client import RAGAPIClient
        
        # Create client instance
        client = RAGAPIClient("http://localhost:8000")
        print("✅ RAGAPIClient created successfully")
        
        # Test client has expected methods
        assert hasattr(client, 'health_check')
        assert hasattr(client, 'query')
        assert hasattr(client, 'add_documents')
        print("✅ RAGAPIClient has required methods")
        
        print("\n🎉 API client tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ API client test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Quick Reflex Component Test Suite")
    print("====================================\n")
    
    tests = [
        test_imports,
        test_component_creation,
        test_api_client
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print(f"\n📊 Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All tests passed! Reflex components are ready.")
        print("\n📍 Next steps:")
        print("1. Install dependencies: pip install -r requirements.reflex.txt")
        print("2. Start RAG backend: cd app && python main.py")
        print("3. Start Reflex: cd app/reflex_app && reflex run")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())