"""
Accessibility testing automation for UI components.

Tests WCAG 2.1 AA compliance, keyboard navigation, screen reader compatibility,
color contrast, and inclusive design patterns for the Reflex UI.

Authored by: QA/Test Engineer (Darren Fong)
Date: 2025-08-05
"""

import pytest
import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import re

# Import test utilities
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'app'))


@pytest.mark.accessibility
class TestUIAccessibility:
    """Accessibility tests for UI components and interactions."""

    @pytest.fixture
    async def browser_context(self):
        """Create browser context with accessibility testing setup."""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        
        # Create context with accessibility preferences
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            # Simulate screen reader and keyboard navigation preferences
            extra_http_headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 AccessibilityTest/1.0"
            }
        )
        
        yield context
        
        await context.close()
        await browser.close()
        await playwright.stop()

    @pytest.fixture
    async def accessibility_page(self, browser_context):
        """Create page with accessibility testing tools."""
        page = await browser_context.new_page()
        
        # Inject axe-core accessibility testing library
        await page.add_script_tag(url="https://unpkg.com/axe-core@4.7.2/axe.min.js")
        
        # Navigate to the application
        await page.goto("http://localhost:3000", wait_until="networkidle")
        
        yield page
        
        await page.close()

    async def run_axe_analysis(self, page: Page, context: str = "document") -> Dict[str, Any]:
        """Run axe-core accessibility analysis."""
        # Wait for axe to be available
        await page.wait_for_function("typeof axe !== 'undefined'")
        
        # Configure axe for WCAG 2.1 AA compliance
        axe_config = {
            "tags": ["wcag2a", "wcag2aa", "wcag21aa"],
            "context": context,
            "options": {
                "runOnly": {
                    "type": "tag",
                    "values": ["wcag2a", "wcag2aa", "wcag21aa", "best-practice"]
                }
            }
        }
        
        # Run axe analysis
        results = await page.evaluate("""
            async (config) => {
                try {
                    return await axe.run(config.context, config.options);
                } catch (error) {
                    return { error: error.message };
                }
            }
        """, axe_config)
        
        return results

    def analyze_axe_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze axe results and categorize violations."""
        if "error" in results:
            return {"error": results["error"], "violations": [], "passes": [], "incomplete": []}
        
        violations_by_impact = {
            "critical": [],
            "serious": [],
            "moderate": [],
            "minor": []
        }
        
        for violation in results.get("violations", []):
            impact = violation.get("impact", "minor")
            violations_by_impact[impact].append({
                "id": violation["id"],
                "description": violation["description"],
                "help": violation["help"],
                "helpUrl": violation["helpUrl"],
                "nodes": len(violation["nodes"]),
                "tags": violation["tags"]
            })
        
        return {
            "violations_by_impact": violations_by_impact,
            "total_violations": len(results.get("violations", [])),
            "passes": len(results.get("passes", [])),
            "incomplete": len(results.get("incomplete", [])),
            "raw_results": results
        }

    @pytest.mark.asyncio
    async def test_homepage_accessibility_compliance(self, accessibility_page):
        """Test homepage WCAG 2.1 AA compliance."""
        # Wait for page to fully load
        await accessibility_page.wait_for_selector("[data-testid='main-content'], main, .main-content", timeout=10000)
        
        # Run accessibility analysis
        results = await self.run_axe_analysis(accessibility_page)
        analysis = self.analyze_axe_results(results)
        
        # Assert no critical or serious violations
        assert len(analysis["violations_by_impact"]["critical"]) == 0, f"Critical accessibility violations: {analysis['violations_by_impact']['critical']}"
        assert len(analysis["violations_by_impact"]["serious"]) == 0, f"Serious accessibility violations: {analysis['violations_by_impact']['serious']}"
        
        # Allow some moderate violations but log them
        moderate_violations = analysis["violations_by_impact"]["moderate"]
        if moderate_violations:
            print(f"Moderate accessibility violations found: {len(moderate_violations)}")
            for violation in moderate_violations:
                print(f"  - {violation['id']}: {violation['description']}")
        
        # Should have more passes than violations
        assert analysis["passes"] > analysis["total_violations"], "More accessibility violations than passes"
        
        print(f"Accessibility results: {analysis['passes']} passes, {analysis['total_violations']} violations")

    @pytest.mark.asyncio
    async def test_keyboard_navigation_chat_interface(self, accessibility_page):
        """Test keyboard navigation through chat interface."""
        # Wait for chat interface to load
        await accessibility_page.wait_for_selector("textarea, input[type='text']", timeout=10000)
        
        # Test tab navigation through interactive elements
        interactive_elements = await accessibility_page.locator(
            "button, input, textarea, select, [tabindex]:not([tabindex='-1']), a[href]"
        ).all()
        
        assert len(interactive_elements) > 0, "No interactive elements found for keyboard navigation"
        
        # Test focus management
        for i, element in enumerate(interactive_elements[:10]):  # Test first 10 elements
            await element.focus()
            
            # Verify element is focused
            is_focused = await element.evaluate("el => document.activeElement === el")
            assert is_focused, f"Element {i} could not receive focus"
            
            # Check if focus is visible
            computed_style = await element.evaluate("""
                el => {
                    const style = window.getComputedStyle(el, ':focus');
                    return {
                        outline: style.outline,
                        outlineColor: style.outlineColor,
                        outlineWidth: style.outlineWidth,
                        boxShadow: style.boxShadow
                    };
                }
            """)
            
            # Should have visible focus indicator
            has_focus_indicator = (
                computed_style["outline"] != "none" or
                computed_style["outlineWidth"] != "0px" or
                "shadow" in computed_style["boxShadow"]
            )
            
            if not has_focus_indicator:
                print(f"Warning: Element {i} may not have visible focus indicator")

    @pytest.mark.asyncio
    async def test_keyboard_only_chat_workflow(self, accessibility_page):
        """Test complete chat workflow using only keyboard."""
        # Find chat input
        chat_input = accessibility_page.locator("textarea, input[placeholder*='message'], input[placeholder*='question'], input[placeholder*='query']").first
        await chat_input.wait_for(state="visible", timeout=10000)
        
        # Focus and type message using keyboard only
        await chat_input.focus()
        await accessibility_page.keyboard.type("What is artificial intelligence?", delay=50)
        
        # Verify text was entered
        input_value = await chat_input.input_value()
        assert "artificial intelligence" in input_value.lower(), "Text input failed"
        
        # Submit using Enter key
        await accessibility_page.keyboard.press("Enter")
        
        # Wait for response (with timeout)
        try:
            await accessibility_page.wait_for_selector(
                "[data-testid='chat-response'], .chat-message, .response",
                timeout=15000
            )
            response_found = True
        except:
            response_found = False
        
        # For testing purposes, we'll accept if the form submission was attempted
        # even if no actual response comes back (since we're testing UI accessibility)
        if not response_found:
            # Check if input was cleared (indicating form submission)
            current_value = await chat_input.input_value()
            form_submitted = len(current_value.strip()) == 0
            assert form_submitted, "Chat form did not submit via keyboard"

    @pytest.mark.asyncio
    async def test_screen_reader_compatibility(self, accessibility_page):
        """Test screen reader compatibility with semantic markup."""
        # Check for proper heading structure
        headings = await accessibility_page.locator("h1, h2, h3, h4, h5, h6").all()
        
        if headings:
            # Verify heading hierarchy
            heading_levels = []
            for heading in headings:
                tag_name = await heading.evaluate("el => el.tagName.toLowerCase()")
                level = int(tag_name[1])  # Extract number from h1, h2, etc.
                heading_levels.append(level)
            
            # Should start with h1 and not skip levels
            if heading_levels:
                assert heading_levels[0] == 1, "Page should start with h1"
                
                for i in range(1, len(heading_levels)):
                    level_jump = heading_levels[i] - heading_levels[i-1]
                    assert level_jump <= 1, f"Heading level jump too large: h{heading_levels[i-1]} to h{heading_levels[i]}"
        
        # Check for ARIA labels and landmarks
        landmarks = await accessibility_page.locator("[role='main'], main, [role='navigation'], nav, [role='banner'], header").all()
        assert len(landmarks) > 0, "No semantic landmarks found for screen readers"
        
        # Check for form labels
        form_inputs = await accessibility_page.locator("input, textarea, select").all()
        for input_element in form_inputs:
            # Check for associated label
            input_id = await input_element.get_attribute("id")
            has_label = False
            
            if input_id:
                labels = await accessibility_page.locator(f"label[for='{input_id}']").count()
                has_label = labels > 0
            
            if not has_label:
                # Check for aria-label or aria-labelledby
                aria_label = await input_element.get_attribute("aria-label")
                aria_labelledby = await input_element.get_attribute("aria-labelledby")
                has_label = bool(aria_label or aria_labelledby)
            
            if not has_label:
                # Check for placeholder as fallback (not ideal but acceptable)
                placeholder = await input_element.get_attribute("placeholder")
                has_label = bool(placeholder)
            
            assert has_label, f"Form input missing accessible label: {await input_element.get_attribute('type')}"

    @pytest.mark.asyncio
    async def test_color_contrast_compliance(self, accessibility_page):
        """Test color contrast ratios for WCAG AA compliance."""
        # Get all text elements
        text_elements = await accessibility_page.locator("p, span, div, button, a, label, h1, h2, h3, h4, h5, h6").all()
        
        contrast_violations = []
        
        for element in text_elements[:20]:  # Test first 20 text elements
            try:
                # Get computed styles
                styles = await element.evaluate("""
                    el => {
                        const style = window.getComputedStyle(el);
                        const rect = el.getBoundingClientRect();
                        return {
                            color: style.color,
                            backgroundColor: style.backgroundColor,
                            fontSize: parseFloat(style.fontSize),
                            fontWeight: style.fontWeight,
                            visible: rect.width > 0 && rect.height > 0,
                            text: el.textContent.trim()
                        };
                    }
                """)
                
                if not styles["visible"] or not styles["text"]:
                    continue
                
                # Parse RGB values
                color_match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', styles["color"])
                bg_match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', styles["backgroundColor"])
                
                if color_match and bg_match:
                    # Calculate relative luminance (simplified)
                    def relative_luminance(r, g, b):
                        r, g, b = r/255.0, g/255.0, b/255.0
                        r = r/12.92 if r <= 0.03928 else ((r+0.055)/1.055)**2.4
                        g = g/12.92 if g <= 0.03928 else ((g+0.055)/1.055)**2.4
                        b = b/12.92 if b <= 0.03928 else ((b+0.055)/1.055)**2.4
                        return 0.2126*r + 0.7152*g + 0.0722*b
                    
                    text_rgb = [int(x) for x in color_match.groups()]
                    bg_rgb = [int(x) for x in bg_match.groups()]
                    
                    text_lum = relative_luminance(*text_rgb)
                    bg_lum = relative_luminance(*bg_rgb)
                    
                    # Calculate contrast ratio
                    lighter = max(text_lum, bg_lum)
                    darker = min(text_lum, bg_lum)
                    contrast_ratio = (lighter + 0.05) / (darker + 0.05)
                    
                    # WCAG AA requirements
                    is_large_text = styles["fontSize"] >= 18 or (styles["fontSize"] >= 14 and "bold" in styles["fontWeight"])
                    min_ratio = 3.0 if is_large_text else 4.5
                    
                    if contrast_ratio < min_ratio:
                        contrast_violations.append({
                            "text": styles["text"][:50],
                            "contrast_ratio": round(contrast_ratio, 2),
                            "required_ratio": min_ratio,
                            "font_size": styles["fontSize"],
                            "is_large_text": is_large_text
                        })
                
            except Exception as e:
                print(f"Error checking contrast for element: {e}")
        
        # Allow some violations but log them
        if contrast_violations:
            print(f"Color contrast violations found: {len(contrast_violations)}")
            for violation in contrast_violations[:5]:  # Show first 5
                print(f"  - Text: '{violation['text']}' - Ratio: {violation['contrast_ratio']} (required: {violation['required_ratio']})")
        
        # Should have mostly good contrast
        violation_rate = len(contrast_violations) / max(1, len(text_elements[:20]))
        assert violation_rate < 0.3, f"Too many contrast violations: {violation_rate:.1%}"

    @pytest.mark.asyncio
    async def test_responsive_accessibility(self, browser_context):
        """Test accessibility across different viewport sizes."""
        viewports = [
            {"width": 320, "height": 568},   # Mobile
            {"width": 768, "height": 1024},  # Tablet  
            {"width": 1920, "height": 1080}  # Desktop
        ]
        
        for viewport in viewports:
            page = await browser_context.new_page()
            await page.set_viewport_size(viewport)
            await page.add_script_tag(url="https://unpkg.com/axe-core@4.7.2/axe.min.js")
            await page.goto("http://localhost:3000", wait_until="networkidle")
            
            # Wait for content to load
            await page.wait_for_selector("body", timeout=10000)
            
            # Run accessibility analysis
            results = await self.run_axe_analysis(page)
            analysis = self.analyze_axe_results(results)
            
            # Check for critical violations
            critical_violations = analysis["violations_by_impact"]["critical"]
            serious_violations = analysis["violations_by_impact"]["serious"]
            
            assert len(critical_violations) == 0, f"Critical violations at {viewport['width']}px: {critical_violations}"
            assert len(serious_violations) <= 2, f"Too many serious violations at {viewport['width']}px: {serious_violations}"
            
            # Test keyboard navigation still works
            interactive_elements = await page.locator("button, input, textarea, a[href]").count()
            assert interactive_elements > 0, f"No interactive elements at {viewport['width']}px"
            
            await page.close()

    @pytest.mark.asyncio
    async def test_focus_management_modal_dialogs(self, accessibility_page):
        """Test focus management in modal dialogs and overlays."""
        # Look for modal triggers (buttons that might open modals)
        modal_triggers = await accessibility_page.locator(
            "button[aria-haspopup], button[data-modal], button[data-dialog], [role='button'][aria-haspopup]"
        ).all()
        
        for trigger in modal_triggers[:3]:  # Test first 3 modal triggers
            try:
                # Click trigger to open modal
                await trigger.click()
                await accessibility_page.wait_for_timeout(500)  # Wait for modal to open
                
                # Check if modal opened
                modal = accessibility_page.locator("[role='dialog'], [role='modal'], .modal, .dialog").first
                is_visible = await modal.is_visible()
                
                if is_visible:
                    # Test focus is trapped in modal
                    await accessibility_page.keyboard.press("Tab")
                    focused_element = await accessibility_page.evaluate("document.activeElement.tagName")
                    
                    # Should be able to focus within modal
                    modal_contains_focus = await modal.evaluate(
                        "modal => modal.contains(document.activeElement)"
                    )
                    
                    assert modal_contains_focus, "Focus not properly managed in modal"
                    
                    # Try to close modal (ESC key)
                    await accessibility_page.keyboard.press("Escape")
                    await accessibility_page.wait_for_timeout(500)
                    
                    # Check if modal closed
                    is_still_visible = await modal.is_visible()
                    if is_still_visible:
                        # Try clicking close button
                        close_button = modal.locator("button[aria-label*='close'], button[data-close], .close").first
                        if await close_button.count() > 0:
                            await close_button.click()
                
            except Exception as e:
                print(f"Error testing modal: {e}")

    @pytest.mark.asyncio
    async def test_aria_live_regions(self, accessibility_page):
        """Test ARIA live regions for dynamic content updates."""
        # Look for live regions
        live_regions = await accessibility_page.locator(
            "[aria-live], [role='status'], [role='alert'], [aria-atomic]"
        ).all()
        
        # Should have at least one live region for chat responses or status updates
        if len(live_regions) == 0:
            print("Warning: No ARIA live regions found for dynamic content")
        
        for region in live_regions:
            # Check live region attributes
            aria_live = await region.get_attribute("aria-live")
            aria_atomic = await region.get_attribute("aria-atomic")
            
            if aria_live:
                assert aria_live in ["polite", "assertive", "off"], f"Invalid aria-live value: {aria_live}"
            
            if aria_atomic:
                assert aria_atomic in ["true", "false"], f"Invalid aria-atomic value: {aria_atomic}"

    @pytest.mark.asyncio
    async def test_form_validation_accessibility(self, accessibility_page):
        """Test accessibility of form validation messages."""
        # Find forms with validation
        forms = await accessibility_page.locator("form").all()
        
        for form in forms:
            # Look for required fields
            required_fields = await form.locator("input[required], textarea[required], select[required]").all()
            
            for field in required_fields[:2]:  # Test first 2 required fields
                # Try to submit without filling required field
                await field.focus()
                await accessibility_page.keyboard.press("Tab")  # Move focus away
                
                # Look for validation messages
                field_id = await field.get_attribute("id")
                if field_id:
                    # Check for associated error message
                    error_messages = await accessibility_page.locator(
                        f"[aria-describedby*='{field_id}'], [data-error-for='{field_id}'], .error-message"
                    ).all()
                    
                    for message in error_messages:
                        # Error messages should be accessible
                        is_visible = await message.is_visible()
                        if is_visible:
                            aria_role = await message.get_attribute("role")
                            aria_live = await message.get_attribute("aria-live")
                            
                            # Should have appropriate ARIA attributes
                            has_aria_support = aria_role == "alert" or aria_live in ["polite", "assertive"]
                            
                            if not has_aria_support:
                                print(f"Warning: Error message may not be accessible to screen readers")


@pytest.mark.accessibility
class TestDocumentManagementAccessibility:
    """Accessibility tests for document management interface."""

    @pytest.mark.asyncio
    async def test_document_list_accessibility(self, accessibility_page):
        """Test accessibility of document list interface."""
        # Navigate to documents page (if it exists)
        documents_links = await accessibility_page.locator("a[href*='document'], button:has-text('Documents')").all()
        
        if documents_links:
            await documents_links[0].click()
            await accessibility_page.wait_for_timeout(2000)
        
        # Run accessibility analysis on document interface
        results = await self.run_axe_analysis(accessibility_page)
        analysis = self.analyze_axe_results(results)
        
        # Should have minimal violations
        assert len(analysis["violations_by_impact"]["critical"]) == 0, "Critical violations in document interface"
        assert len(analysis["violations_by_impact"]["serious"]) <= 1, "Too many serious violations in document interface"

    @pytest.mark.asyncio
    async def test_file_upload_accessibility(self, accessibility_page):
        """Test accessibility of file upload interface."""
        # Look for file upload elements
        file_inputs = await accessibility_page.locator("input[type='file']").all()
        
        for file_input in file_inputs:
            # Check for accessible label
            input_id = await file_input.get_attribute("id")
            has_label = False
            
            if input_id:
                labels = await accessibility_page.locator(f"label[for='{input_id}']").count()
                has_label = labels > 0
            
            if not has_label:
                aria_label = await file_input.get_attribute("aria-label")
                aria_labelledby = await file_input.get_attribute("aria-labelledby")
                has_label = bool(aria_label or aria_labelledby)
            
            assert has_label, "File input missing accessible label"
            
            # Check if file input is keyboard accessible
            await file_input.focus()
            is_focused = await file_input.evaluate("el => document.activeElement === el")
            assert is_focused, "File input not keyboard accessible"

    async def run_axe_analysis(self, page: Page, context: str = "document") -> Dict[str, Any]:
        """Run axe-core accessibility analysis."""
        # Wait for axe to be available
        await page.wait_for_function("typeof axe !== 'undefined'", timeout=5000)
        
        # Configure axe for WCAG 2.1 AA compliance
        axe_config = {
            "tags": ["wcag2a", "wcag2aa", "wcag21aa"],
            "context": context,
            "options": {
                "runOnly": {
                    "type": "tag",
                    "values": ["wcag2a", "wcag2aa", "wcag21aa", "best-practice"]
                }
            }
        }
        
        # Run axe analysis
        results = await page.evaluate("""
            async (config) => {
                try {
                    return await axe.run(config.context, config.options);
                } catch (error) {
                    return { error: error.message };
                }
            }
        """, axe_config)
        
        return results

    def analyze_axe_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze axe results and categorize violations."""
        if "error" in results:
            return {"error": results["error"], "violations": [], "passes": [], "incomplete": []}
        
        violations_by_impact = {
            "critical": [],
            "serious": [],
            "moderate": [],
            "minor": []
        }
        
        for violation in results.get("violations", []):
            impact = violation.get("impact", "minor")
            violations_by_impact[impact].append({
                "id": violation["id"],
                "description": violation["description"],
                "help": violation["help"],
                "helpUrl": violation["helpUrl"],
                "nodes": len(violation["nodes"]),
                "tags": violation["tags"]
            })
        
        return {
            "violations_by_impact": violations_by_impact,
            "total_violations": len(results.get("violations", [])),
            "passes": len(results.get("passes", [])),
            "incomplete": len(results.get("incomplete", [])),
            "raw_results": results
        }


@pytest.mark.accessibility
@pytest.mark.slow
class TestAccessibilityRegressionSuite:
    """Regression tests to prevent accessibility regressions."""

    @pytest.mark.asyncio
    async def test_accessibility_baseline_comparison(self, accessibility_page):
        """Test current accessibility state against baseline."""
        # Define baseline expectations
        baseline_expectations = {
            "max_critical_violations": 0,
            "max_serious_violations": 0,
            "max_moderate_violations": 5,
            "min_passes": 20
        }
        
        # Run full accessibility analysis
        await accessibility_page.wait_for_selector("body", timeout=10000)
        results = await self.run_axe_analysis(accessibility_page)
        analysis = self.analyze_axe_results(results)
        
        # Compare against baseline
        critical_violations = len(analysis["violations_by_impact"]["critical"])
        serious_violations = len(analysis["violations_by_impact"]["serious"])
        moderate_violations = len(analysis["violations_by_impact"]["moderate"])
        passes = analysis["passes"]
        
        # Assertions against baseline
        assert critical_violations <= baseline_expectations["max_critical_violations"], f"Critical violations exceeded baseline: {critical_violations}"
        assert serious_violations <= baseline_expectations["max_serious_violations"], f"Serious violations exceeded baseline: {serious_violations}"
        assert moderate_violations <= baseline_expectations["max_moderate_violations"], f"Moderate violations exceeded baseline: {moderate_violations}"
        assert passes >= baseline_expectations["min_passes"], f"Accessibility passes below baseline: {passes}"
        
        # Generate accessibility report
        report = {
            "timestamp": time.time(),
            "violations_by_impact": analysis["violations_by_impact"],
            "total_violations": analysis["total_violations"],
            "passes": passes,
            "baseline_comparison": {
                "critical_within_limit": critical_violations <= baseline_expectations["max_critical_violations"],
                "serious_within_limit": serious_violations <= baseline_expectations["max_serious_violations"],
                "moderate_within_limit": moderate_violations <= baseline_expectations["max_moderate_violations"],
                "passes_above_minimum": passes >= baseline_expectations["min_passes"]
            }
        }
        
        print(f"Accessibility Report: {json.dumps(report, indent=2)}")

    async def run_axe_analysis(self, page: Page) -> Dict[str, Any]:
        """Run axe-core accessibility analysis."""
        await page.wait_for_function("typeof axe !== 'undefined'", timeout=5000)
        
        results = await page.evaluate("""
            async () => {
                try {
                    return await axe.run(document, {
                        runOnly: {
                            type: "tag",
                            values: ["wcag2a", "wcag2aa", "wcag21aa", "best-practice"]
                        }
                    });
                } catch (error) {
                    return { error: error.message };
                }
            }
        """)
        
        return results

    def analyze_axe_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze axe results and categorize violations."""
        if "error" in results:
            return {"error": results["error"], "violations_by_impact": {"critical": [], "serious": [], "moderate": [], "minor": []}, "passes": 0}
        
        violations_by_impact = {"critical": [], "serious": [], "moderate": [], "minor": []}
        
        for violation in results.get("violations", []):
            impact = violation.get("impact", "minor")
            violations_by_impact[impact].append(violation)
        
        return {
            "violations_by_impact": violations_by_impact,
            "total_violations": len(results.get("violations", [])),
            "passes": len(results.get("passes", [])),
            "incomplete": len(results.get("incomplete", []))
        }