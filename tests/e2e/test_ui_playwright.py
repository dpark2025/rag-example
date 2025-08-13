#!/usr/bin/env python3
"""
End-to-end UI tests using Playwright.
Consolidated from multiple test files.
"""

import asyncio
from playwright.async_api import async_playwright, Page, expect
import time
from pathlib import Path

async def test_reflex_ui():
    """Test all functionality of the Reflex UI."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, slow_mo=100)
        page = await browser.new_page()
        
        try:
            print("🔍 Starting UI testing...")
            
            # Test 1: Page loads without errors
            print("\n1. Testing page load...")
            response = await page.goto("http://localhost:3000/", wait_until="networkidle")
            assert response.status == 200, f"Page failed to load with status {response.status}"
            
            # Wait for the page to be fully rendered
            await page.wait_for_selector('h1:has-text("🤖 RAG System")', timeout=10000)
            print("✅ Page loaded successfully")
            
            # Test 2: Chat interface
            print("\n2. Testing chat interface...")
            chat_input = await page.wait_for_selector('textarea[placeholder="Type your message..."]')
            await chat_input.fill("Hello, this is a test message")
            
            send_button = await page.wait_for_selector('button:has-text("Send")')
            await send_button.click()
            
            # Wait for response
            await page.wait_for_selector('.message-content', timeout=10000)
            print("✅ Chat interface working")
            
            # Test 3: Document upload
            print("\n3. Testing document upload...")
            upload_button = await page.wait_for_selector('button:has-text("Documents")')
            await upload_button.click()
            
            # Wait for modal
            await page.wait_for_selector('.upload-modal', timeout=5000)
            print("✅ Document modal opens")
            
            # Test 4: Settings
            print("\n4. Testing settings...")
            settings_button = await page.wait_for_selector('button:has-text("Settings")')
            await settings_button.click()
            
            await page.wait_for_selector('.settings-modal', timeout=5000)
            print("✅ Settings modal works")
            
            # Test 5: Health status
            print("\n5. Testing health status...")
            health_indicator = await page.wait_for_selector('.health-status')
            health_text = await health_indicator.inner_text()
            assert "Healthy" in health_text or "Ready" in health_text
            print("✅ Health status displayed")
            
            print("\n✨ All UI tests passed!")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            await page.screenshot(path="test_failure.png")
            raise
        finally:
            await browser.close()

async def test_enhanced_features():
    """Test enhanced UI features."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            print("🔍 Testing enhanced features...")
            
            await page.goto("http://localhost:3000/")
            
            # Test conversation history
            print("\n1. Testing conversation history...")
            chat_input = await page.wait_for_selector('textarea')
            
            # Send multiple messages
            for i in range(3):
                await chat_input.fill(f"Test message {i+1}")
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(1000)
            
            # Check message count
            messages = await page.query_selector_all('.message-content')
            assert len(messages) >= 3, "Conversation history not maintained"
            print("✅ Conversation history working")
            
            # Test session uploads
            print("\n2. Testing session upload tracking...")
            doc_button = await page.wait_for_selector('button:has-text("Documents")')
            doc_text = await doc_button.inner_text()
            assert "0" in doc_text or "No" in doc_text.lower()
            print("✅ Session upload tracking working")
            
            print("\n✨ Enhanced features working!")
            
        except Exception as e:
            print(f"❌ Enhanced test failed: {e}")
            raise
        finally:
            await browser.close()

if __name__ == "__main__":
    print("=" * 50)
    print("RAG System UI Test Suite")
    print("=" * 50)
    
    # Run basic tests
    asyncio.run(test_reflex_ui())
    
    # Run enhanced tests
    asyncio.run(test_enhanced_features())
    
    print("\n" + "=" * 50)
    print("✅ All tests completed successfully!")
    print("=" * 50)