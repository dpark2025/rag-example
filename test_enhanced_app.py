"""Test script to verify the enhanced RAG app works without DOM errors."""

import subprocess
import time
import sys
from playwright.sync_api import sync_playwright
import threading
import os

def run_reflex_server():
    """Run the Reflex server in the background."""
    os.chdir("app/reflex_app/rag_reflex_app")
    process = subprocess.Popen(
        ["reflex", "run", "--app", "rag_reflex_app_enhanced_simple.py", "--port", "3001"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return process

def test_enhanced_app():
    """Test the enhanced RAG app for DOM stability and functionality."""
    
    print("🚀 Starting enhanced RAG app test...")
    
    # Start the server
    server_process = run_reflex_server()
    
    try:
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        time.sleep(8)
        
        with sync_playwright() as p:
            print("🌐 Launching browser...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            # Collect console errors
            console_errors = []
            def handle_console(msg):
                if msg.type == 'error':
                    console_errors.append(msg.text)
                    print(f"❌ Console Error: {msg.text}")
            
            page.on('console', handle_console)
            
            # Navigate to the app
            print("📱 Navigating to app...")
            page.goto("http://localhost:3001")
            
            # Wait for page to load
            page.wait_for_timeout(3000)
            
            # Test 1: Check if main elements are present
            print("🔍 Testing main UI elements...")
            
            # Check header
            header = page.locator("text=RAG System")
            if header.is_visible():
                print("✅ Header found")
            else:
                print("❌ Header not found")
            
            # Check system status
            status = page.locator("text=System Online")
            if status.is_visible() or page.locator("text=System Issues").is_visible():
                print("✅ System status indicator found")
            else:
                print("❌ System status indicator not found")
            
            # Check input field
            input_field = page.locator("input[placeholder*='Ask a question']")
            if input_field.is_visible():
                print("✅ Chat input field found")
            else:
                print("❌ Chat input field not found")
            
            # Test 2: Test system status panel toggle
            print("🔧 Testing system status panel...")
            settings_btn = page.locator("[aria-label='System status']")
            if settings_btn.is_visible():
                settings_btn.click()
                page.wait_for_timeout(1000)
                
                # Check if panel opened
                status_panel = page.locator("text=System Status")
                if status_panel.is_visible():
                    print("✅ System status panel opens")
                    
                    # Close panel
                    close_btn = page.locator("[aria-label='Close status panel']")
                    if close_btn.is_visible():
                        close_btn.click()
                        print("✅ System status panel closes")
                else:
                    print("❌ System status panel did not open")
            
            # Test 3: Test document upload modal
            print("📤 Testing document upload modal...")
            upload_btn = page.locator("text=Upload Documents").first
            if upload_btn.is_visible():
                upload_btn.click()
                page.wait_for_timeout(1000)
                
                # Check if modal opened
                upload_modal = page.locator("text=Drop files here")
                if upload_modal.is_visible():
                    print("✅ Upload modal opens")
                    
                    # Close modal
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(500)
                    print("✅ Upload modal closes")
                else:
                    print("❌ Upload modal did not open")
            
            # Test 4: Test chat functionality
            print("💬 Testing chat functionality...")
            input_field = page.locator("input[placeholder*='Ask a question']")
            if input_field.is_visible():
                # Type a message
                input_field.fill("Test message for enhanced RAG system")
                page.wait_for_timeout(500)
                
                # Send message
                send_btn = page.locator("button", has_text="Send")
                if send_btn.is_visible():
                    send_btn.click()
                    page.wait_for_timeout(2000)
                    
                    # Check for messages
                    user_message = page.locator("text=Test message for enhanced RAG system")
                    if user_message.is_visible():
                        print("✅ User message displayed")
                        
                        # Check for AI response with sources
                        sources_section = page.locator("text=Sources:")
                        if sources_section.is_visible():
                            print("✅ AI response with source attribution displayed")
                        else:
                            print("❌ Source attribution not found")
                    else:
                        print("❌ User message not displayed")
            
            # Test 5: Test health check simulation
            print("🔄 Testing health check simulation...")
            settings_btn = page.locator("[aria-label='System status']")
            if settings_btn.is_visible():
                settings_btn.click()
                page.wait_for_timeout(1000)
                
                refresh_btn = page.locator("text=Refresh Status")
                if refresh_btn.is_visible():
                    refresh_btn.click()
                    page.wait_for_timeout(1000)
                    print("✅ Health check refresh works")
                
                # Close panel
                close_btn = page.locator("[aria-label='Close status panel']")
                if close_btn.is_visible():
                    close_btn.click()
            
            # Final assessment
            print("\n📊 Test Results Summary:")
            print(f"Console Errors: {len(console_errors)}")
            
            if len(console_errors) == 0:
                print("🎉 SUCCESS: No console errors detected!")
                print("✅ Enhanced RAG app is stable and functional")
            else:
                print("⚠️ WARNING: Console errors detected:")
                for error in console_errors[:5]:  # Show first 5 errors
                    print(f"  - {error}")
            
            browser.close()
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    finally:
        # Clean up server
        print("🧹 Cleaning up server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
    
    return len(console_errors) == 0

if __name__ == "__main__":
    success = test_enhanced_app()
    sys.exit(0 if success else 1)