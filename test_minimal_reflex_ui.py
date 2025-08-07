#!/usr/bin/env python3
"""Comprehensive test for the minimal Reflex UI using Playwright."""

import asyncio
from playwright.async_api import async_playwright, Page, expect
import time
from pathlib import Path

async def test_reflex_ui():
    """Test all functionality of the minimal Reflex UI."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        page = await browser.new_page()
        
        try:
            print("🔍 Starting comprehensive UI testing...")
            
            # Test 1: Page loads without errors
            print("\n1. Testing page load...")
            response = await page.goto("http://localhost:3000/", wait_until="networkidle")
            assert response.status == 200, f"Page failed to load with status {response.status}"
            
            # Wait for the page to be fully rendered
            await page.wait_for_selector('h1:has-text("🤖 RAG System")', timeout=10000)
            print("✅ Page loaded successfully with correct title")
            
            # Take initial screenshot
            await page.screenshot(path="screenshots/01_initial_load.png")
            print("📸 Screenshot saved: 01_initial_load.png")
            
            # Test 2: Chat interface functionality
            print("\n2. Testing chat interface...")
            
            # Check initial state - should show welcome message
            welcome_box = page.locator('text=Welcome to RAG System')
            await expect(welcome_box).to_be_visible()
            print("✅ Welcome message is visible")
            
            # Test chat input and send
            chat_input = page.locator('input[placeholder="Type your message..."]')
            send_button = page.locator('button:has-text("Send")')
            
            await expect(chat_input).to_be_visible()
            await expect(send_button).to_be_visible()
            print("✅ Chat input and send button are visible")
            
            # Send a test message
            test_message = "Hello, can you help me find information about documents?"
            await chat_input.fill(test_message)
            await send_button.click()
            
            # Wait for messages to appear
            await page.wait_for_selector('text=Hello, can you help me find information about documents?', timeout=5000)
            user_message = page.locator('text=Hello, can you help me find information about documents?')
            await expect(user_message).to_be_visible()
            print("✅ User message appears in chat")
            
            # Check for AI response
            await page.wait_for_selector('text=I understand you asked:', timeout=5000)
            ai_response = page.locator('text=I understand you asked:')
            await expect(ai_response).to_be_visible()
            print("✅ AI response appears in chat")
            
            # Check for sources indicator
            sources_indicator = page.locator('text=Sources available')
            await expect(sources_indicator).to_be_visible()
            print("✅ Sources indicator is visible")
            
            await page.screenshot(path="screenshots/02_chat_interaction.png")
            print("📸 Screenshot saved: 02_chat_interaction.png")
            
            # Test 3: System Status Panel
            print("\n3. Testing system status panel...")
            
            system_status_button = page.locator('button:has-text("System Status")')
            await expect(system_status_button).to_be_visible()
            print("✅ System Status button is visible")
            
            # Click to expand system panel
            await system_status_button.click()
            
            # Wait for panel to expand
            await page.wait_for_selector('text=Service Health', timeout=3000)
            service_health = page.locator('text=Service Health')
            await expect(service_health).to_be_visible()
            print("✅ System status panel expanded")
            
            # Check health indicators
            llm_service = page.locator('text=LLM Service')
            vector_db = page.locator('text=Vector DB')
            embeddings = page.locator('text=Embeddings')
            
            await expect(llm_service).to_be_visible()
            await expect(vector_db).to_be_visible()
            await expect(embeddings).to_be_visible()
            print("✅ All service health indicators are visible")
            
            # Test refresh functionality
            refresh_button = page.locator('button:has-text("Refresh")')
            await expect(refresh_button).to_be_visible()
            await refresh_button.click()
            print("✅ Health refresh button works")
            
            await page.screenshot(path="screenshots/03_system_status_panel.png")
            print("📸 Screenshot saved: 03_system_status_panel.png")
            
            # Test 4: Document Upload Modal
            print("\n4. Testing document upload modal...")
            
            upload_button = page.locator('button:has-text("Upload")')
            await expect(upload_button).to_be_visible()
            print("✅ Upload button is visible")
            
            # Click to open modal
            await upload_button.click()
            
            # Wait for modal to appear
            await page.wait_for_selector('text=Upload Documents', timeout=3000)
            modal_title = page.locator('text=Upload Documents')
            await expect(modal_title).to_be_visible()
            print("✅ Upload modal opened successfully")
            
            # Check modal elements
            drag_drop_area = page.locator('text=Drag and drop files here')
            supported_formats = page.locator('text=Supported: PDF, TXT, MD, HTML')
            cancel_button = page.locator('button:has-text("Cancel")')
            upload_files_button = page.locator('button:has-text("Upload Files")')
            close_button = page.locator('button svg') # X icon
            
            await expect(drag_drop_area).to_be_visible()
            await expect(supported_formats).to_be_visible()
            await expect(cancel_button).to_be_visible()
            await expect(upload_files_button).to_be_visible()
            print("✅ All modal elements are visible")
            
            await page.screenshot(path="screenshots/04_upload_modal.png")
            print("📸 Screenshot saved: 04_upload_modal.png")
            
            # Test closing modal with Cancel button
            await cancel_button.click()
            
            # Wait for modal to disappear
            await page.wait_for_selector('text=Upload Documents', state='hidden', timeout=3000)
            await expect(modal_title).to_be_hidden()
            print("✅ Modal closes with Cancel button")
            
            # Test 5: Additional UI elements
            print("\n5. Testing additional UI elements...")
            
            # Check document count display
            doc_count = page.locator('text=3 documents')
            await expect(doc_count).to_be_visible()
            print("✅ Document count is displayed")
            
            # Check system ready status
            system_ready = page.locator('text=✅ System Ready')
            await expect(system_ready).to_be_visible()
            print("✅ System ready status is displayed")
            
            # Test opening and closing upload modal with X button
            await upload_button.click()
            await page.wait_for_selector('text=Upload Documents', timeout=3000)
            
            # Find and click the X button (close icon)
            close_x_button = page.locator('button svg[class*="icon"]').first()
            await close_x_button.click()
            
            await page.wait_for_selector('text=Upload Documents', state='hidden', timeout=3000)
            print("✅ Modal closes with X button")
            
            # Test 6: Responsive design check
            print("\n6. Testing responsive design...")
            
            # Test mobile viewport
            await page.set_viewport_size({"width": 375, "height": 667})
            await page.wait_for_timeout(1000)  # Wait for layout to adjust
            
            # Check if elements are still visible and accessible
            await expect(system_status_button).to_be_visible()
            await expect(chat_input).to_be_visible()
            await expect(send_button).to_be_visible()
            
            await page.screenshot(path="screenshots/05_mobile_view.png")
            print("📸 Screenshot saved: 05_mobile_view.png")
            print("✅ Mobile responsiveness verified")
            
            # Test 7: Final comprehensive screenshot
            print("\n7. Taking final comprehensive screenshot...")
            
            # Reset to desktop view
            await page.set_viewport_size({"width": 1280, "height": 720})
            await page.wait_for_timeout(500)
            
            await page.screenshot(path="screenshots/06_final_overview.png", full_page=True)
            print("📸 Screenshot saved: 06_final_overview.png (full page)")
            
            print("\n🎉 All tests completed successfully!")
            print("📊 Test Summary:")
            print("  ✅ Page loads without errors")
            print("  ✅ Chat interface is functional")
            print("  ✅ System status panel works")
            print("  ✅ Document upload modal works") 
            print("  ✅ All UI elements are properly rendered")
            print("  ✅ Responsive design works")
            print("  📸 6 screenshots saved to screenshots/ directory")
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            # Take error screenshot
            await page.screenshot(path="screenshots/error_state.png")
            print("📸 Error screenshot saved")
            raise
            
        finally:
            await browser.close()

async def setup_screenshots_dir():
    """Create screenshots directory if it doesn't exist."""
    Path("screenshots").mkdir(exist_ok=True)

if __name__ == "__main__":
    print("🚀 Starting Reflex UI Testing with Playwright")
    asyncio.run(setup_screenshots_dir())
    asyncio.run(test_reflex_ui())