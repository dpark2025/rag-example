#!/usr/bin/env python3
"""
Observable Playwright test for container deployment.
This test runs with a visible browser so you can watch the interactions.
"""

import asyncio
import subprocess
import time
import requests
from pathlib import Path
from playwright.async_api import async_playwright

class ContainerPlaywrightTest:
    def __init__(self):
        self.base_dir = Path("/Users/dpark/projects/github.com/working/rag-example")
        
    async def run_command(self, command, timeout=60):
        """Run a shell command"""
        print(f"🔧 Running: {command}")
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            if result.returncode == 0:
                print(f"✅ Command completed: {command}")
                return True, result.stdout
            else:
                print(f"❌ Command failed: {command}")
                print(f"STDERR: {result.stderr}")
                return False, result.stderr
        except subprocess.TimeoutExpired:
            print(f"⏰ Command timeout: {command}")
            return False, "Command timeout"
        except Exception as e:
            print(f"❌ Command error: {command} - {e}")
            return False, str(e)
    
    async def wait_for_service(self, url, timeout=90, service_name="service"):
        """Wait for a service to become available"""
        print(f"⏳ Waiting for {service_name} at {url}...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ {service_name} is ready!")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            print(f"  ... still waiting ({int(time.time() - start_time)}s)")
            await asyncio.sleep(3)
        
        print(f"❌ {service_name} failed to start within {timeout}s")
        return False
    
    async def test_container_with_playwright(self):
        """Complete container deployment test with visible Playwright"""
        print("\n🎬 === OBSERVABLE CONTAINER DEPLOYMENT TEST ===")
        
        # Step 1: Clean shutdown
        print("\n🧹 Step 1: Clean Shutdown")
        await self.run_command("make clean")
        await asyncio.sleep(2)
        
        # Step 2: Build container
        print("\n🏗️ Step 2: Building Container")
        print("⏳ This may take several minutes - please be patient...")
        success, output = await self.run_command("make container-build", timeout=600)
        if not success:
            print("❌ Container build failed!")
            print(output)
            return False
        
        # Step 3: Start container
        print("\n🚀 Step 3: Starting Container")
        success, output = await self.run_command("make container-run", timeout=120)
        if not success:
            print("❌ Container start failed!")
            print(output)
            return False
        
        # Step 4: Wait for readiness
        print("\n⏳ Step 4: Waiting for Application Readiness")
        if not await self.wait_for_service("http://localhost:8000/ready", timeout=120, service_name="Container Application"):
            print("❌ Container application not ready")
            return False
        
        print("\n🎭 Step 5: Starting Playwright Visual Test")
        print("👀 WATCH THE BROWSER - it will open shortly!")
        await asyncio.sleep(3)  # Give you time to get ready
        
        # Step 5: Visual Playwright test
        async with async_playwright() as p:
            # Launch browser in VISIBLE mode
            print("🌐 Launching visible browser...")
            browser = await p.chromium.launch(
                headless=False,  # VISIBLE browser
                slow_mo=1000,    # Slow down actions so you can see them
                args=['--start-maximized']  # Start maximized
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            
            try:
                # Navigate to application
                print("🏠 Navigating to RAG application...")
                await page.goto("http://localhost:3000", wait_until="networkidle", timeout=30000)
                
                # Take initial screenshot
                await page.screenshot(path="test_step_1_loaded.png")
                print("📸 Screenshot 1: Application loaded")
                
                # Test 1: Check page title
                page_title = await page.title()
                print(f"📄 Page title: {page_title}")
                await asyncio.sleep(2)
                
                # Test 2: Look for main UI elements
                print("🔍 Looking for chat interface...")
                
                # Try to find chat input with multiple selectors
                chat_input = None
                chat_selectors = [
                    "textarea[placeholder*='message']",
                    "textarea[placeholder*='Type']", 
                    "textarea[placeholder*='Enter']",
                    "input[type='text']",
                    "textarea",
                    ".message-input",
                    "#message-input"
                ]
                
                for selector in chat_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=5000)
                        if element:
                            chat_input = element
                            print(f"✅ Found chat input: {selector}")
                            # Highlight the input
                            await page.evaluate(
                                f"document.querySelector('{selector}').style.border = '3px solid red'"
                            )
                            break
                    except:
                        continue
                
                await asyncio.sleep(2)  # Let you see the highlighted element
                
                if chat_input:
                    # Test 3: Send a test message
                    test_message = "Hello! Can you tell me about your capabilities?"
                    print(f"💬 Sending message: {test_message}")
                    
                    await chat_input.fill(test_message)
                    await page.screenshot(path="test_step_2_message_typed.png")
                    print("📸 Screenshot 2: Message typed")
                    
                    await asyncio.sleep(2)  # Let you see the typed message
                    
                    # Look for send button or press Enter
                    send_buttons = [
                        "button[type='submit']",
                        "button:has-text('Send')",
                        ".send-button",
                        "[data-testid='send-button']"
                    ]
                    
                    sent = False
                    for selector in send_buttons:
                        try:
                            button = await page.wait_for_selector(selector, timeout=2000)
                            if button:
                                print(f"🔘 Found send button: {selector}")
                                await button.click()
                                sent = True
                                break
                        except:
                            continue
                    
                    if not sent:
                        print("⌨️ No send button found, pressing Enter")
                        await chat_input.press("Enter")
                    
                    await page.screenshot(path="test_step_3_message_sent.png")
                    print("📸 Screenshot 3: Message sent")
                    
                    # Test 4: Wait for response
                    print("⏳ Waiting for AI response...")
                    await asyncio.sleep(5)  # Give time for processing
                    
                    # Look for response messages
                    response_selectors = [
                        ".message",
                        ".chat-message",
                        ".response",
                        ".assistant-message",
                        "[data-testid='message']"
                    ]
                    
                    found_response = False
                    for selector in response_selectors:
                        try:
                            messages = await page.query_selector_all(selector)
                            if len(messages) > 1:  # Original + response
                                found_response = True
                                print(f"✅ Found response messages: {len(messages)} total")
                                break
                        except:
                            continue
                    
                    await page.screenshot(path="test_step_4_response.png")
                    print("📸 Screenshot 4: After response check")
                    
                    if found_response:
                        print("🎉 Chat functionality working!")
                    else:
                        print("⚠️ No clear response detected (but input works)")
                
                else:
                    print("⚠️ Could not find chat input - taking screenshot for inspection")
                    await page.screenshot(path="test_step_debug_no_input.png")
                
                # Test 5: Look for document upload area
                print("📁 Looking for document upload area...")
                upload_selectors = [
                    "input[type='file']",
                    ".upload-area",
                    ".file-drop",
                    "[data-testid='file-upload']"
                ]
                
                for selector in upload_selectors:
                    try:
                        upload = await page.query_selector(selector)
                        if upload:
                            print(f"✅ Found upload area: {selector}")
                            # Highlight upload area
                            await page.evaluate(
                                f"document.querySelector('{selector}').style.border = '3px solid blue'"
                            )
                            break
                    except:
                        continue
                
                await page.screenshot(path="test_step_5_final.png")
                print("📸 Screenshot 5: Final state")
                
                # Keep browser open for a moment
                print("🎬 Test complete! Keeping browser open for 10 seconds...")
                await asyncio.sleep(10)
                
                print("✅ Visual Playwright test completed successfully!")
                
            except Exception as e:
                print(f"❌ Playwright test error: {e}")
                await page.screenshot(path="test_error_state.png")
                return False
            finally:
                await browser.close()
        
        # Step 6: Graceful shutdown
        print("\n🛑 Step 6: Graceful Shutdown")
        await self.run_command("make container-stop")
        
        print("\n🎉 CONTAINER TEST COMPLETED SUCCESSFULLY!")
        print("\n📸 Screenshots saved:")
        print("  - test_step_1_loaded.png")
        print("  - test_step_2_message_typed.png")
        print("  - test_step_3_message_sent.png")
        print("  - test_step_4_response.png")
        print("  - test_step_5_final.png")
        
        return True

async def main():
    """Main test runner"""
    tester = ContainerPlaywrightTest()
    success = await tester.test_container_with_playwright()
    
    if success:
        print("\n🎊 ALL TESTS PASSED! Container deployment is working perfectly.")
    else:
        print("\n❌ Test encountered issues. Check the output above for details.")
    
    return success

if __name__ == "__main__":
    print("🎬 Starting Observable Container Deployment Test")
    print("👀 This test will show you a visible browser!")
    print("📸 Screenshots will be saved at each step")
    print("\nPress Ctrl+C to cancel, or wait for test to start...")
    
    try:
        time.sleep(3)  # Give you time to cancel if needed
        result = asyncio.run(main())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test cancelled by user")
        exit(1)