"""Chat utility functions and enhancements."""

import reflex as rx
from typing import Dict, Any

def auto_scroll_script() -> rx.Component:
    """JavaScript to auto-scroll chat to bottom."""
    return rx.script("""
        function scrollChatToBottom() {
            const chatContainer = document.getElementById('chat-messages-container');
            if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        }
        
        // Auto-scroll when new messages are added
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    setTimeout(scrollChatToBottom, 100);
                }
            });
        });
        
        // Start observing when DOM is ready
        document.addEventListener('DOMContentLoaded', function() {
            const chatContainer = document.getElementById('chat-messages-container');
            if (chatContainer) {
                observer.observe(chatContainer, { childList: true, subtree: true });
            }
        });
    """)

def enhanced_textarea() -> rx.Component:
    """Enhanced textarea with better UX."""
    return rx.script("""
        document.addEventListener('DOMContentLoaded', function() {
            // Auto-resize textarea
            function autoResize(textarea) {
                textarea.style.height = 'auto';
                textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
            }
            
            // Find textarea and add auto-resize
            const textareas = document.querySelectorAll('textarea');
            textareas.forEach(function(textarea) {
                textarea.addEventListener('input', function() {
                    autoResize(this);
                });
                
                // Handle Shift+Enter for new line, Enter for send
                textarea.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        // Trigger send message
                        const sendButton = document.querySelector('button[data-send="true"]');
                        if (sendButton && !sendButton.disabled) {
                            sendButton.click();
                        }
                    }
                });
            });
        });
    """)

def format_response_time(seconds: float) -> str:
    """Format response time for display."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    else:
        return f"{seconds:.2f}s"

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(' ', 1)[0] + "..."

def get_source_preview(source: Dict[str, Any]) -> str:
    """Get a preview of source content."""
    content = source.get("content", "")
    if not content:
        return "No preview available"
    
    # Clean and truncate content
    preview = content.replace('\n', ' ').strip()
    return truncate_text(preview, 200)