"""
Keyboard shortcuts system for enhanced navigation and accessibility.
"""

import reflex as rx
from typing import Dict, List, Optional, Callable
from ..common.toast_notifications import ToastState

class KeyboardShortcutState(rx.State):
    """State for managing keyboard shortcuts and command palette."""
    
    # Command palette visibility
    show_command_palette: bool = False
    
    # Search term in command palette
    search_term: str = ""
    
    # Available commands
    commands: List[Dict] = [
        {
            "id": "search",
            "title": "Search Documents",
            "description": "Open document search",
            "shortcut": "Ctrl+K",
            "action": "open_search",
            "icon": "search"
        },
        {
            "id": "upload",
            "title": "Upload Document",
            "description": "Upload new document",
            "shortcut": "Ctrl+U",
            "action": "open_upload",
            "icon": "upload"
        },
        {
            "id": "chat",
            "title": "Focus Chat",
            "description": "Focus on chat input",
            "shortcut": "Ctrl+/",
            "action": "focus_chat",
            "icon": "message-circle"
        },
        {
            "id": "documents",
            "title": "Go to Documents",
            "description": "Navigate to documents page",
            "shortcut": "Ctrl+D",
            "action": "goto_documents",
            "icon": "file-text"
        },
        {
            "id": "settings",
            "title": "Open Settings",
            "description": "Open application settings",
            "shortcut": "Ctrl+,",
            "action": "open_settings",
            "icon": "settings"
        },
        {
            "id": "help",
            "title": "Show Help",
            "description": "Show keyboard shortcuts",
            "shortcut": "Ctrl+?",
            "action": "show_help",
            "icon": "circle-help"
        },
        {
            "id": "clear_chat",
            "title": "Clear Chat",
            "description": "Clear current chat history",
            "shortcut": "Ctrl+Shift+C",
            "action": "clear_chat",
            "icon": "trash-2"
        },
        {
            "id": "export_chat",
            "title": "Export Chat",
            "description": "Export chat conversation",
            "shortcut": "Ctrl+E",
            "action": "export_chat",
            "icon": "download"
        }
    ]
    
    # Help modal visibility
    show_help_modal: bool = False
    
    def toggle_command_palette(self):
        """Toggle command palette visibility."""
        self.show_command_palette = not self.show_command_palette
        if self.show_command_palette:
            self.search_term = ""
    
    def close_command_palette(self):
        """Close command palette."""
        self.show_command_palette = False
        self.search_term = ""
    
    def update_search_term(self, term: str):
        """Update search term for command filtering."""
        self.search_term = term.lower()
    
    def execute_command(self, command_id: str):
        """Execute a command by ID."""
        self.close_command_palette()
        
        # Handle different command actions
        if command_id == "search":
            self.open_search()
        elif command_id == "upload":
            self.open_upload()
        elif command_id == "focus_chat":
            self.focus_chat()
        elif command_id == "goto_documents":
            self.goto_documents()
        elif command_id == "open_settings":
            self.open_settings()
        elif command_id == "show_help":
            self.show_help()
        elif command_id == "clear_chat":
            self.clear_chat()
        elif command_id == "export_chat":
            self.export_chat()
    
    def open_search(self):
        """Open document search."""
        # This would integrate with document search functionality
        ToastState.toast_info("🔍 Document search opened")
    
    def open_upload(self):
        """Open upload modal."""
        # This would trigger the upload modal
        ToastState.toast_info("📁 Upload dialog opened")
    
    def focus_chat(self):
        """Focus on chat input."""
        # This would focus the chat input field
        ToastState.toast_info("💬 Chat input focused")
    
    def goto_documents(self):
        """Navigate to documents page."""
        return rx.redirect("/documents")
    
    def open_settings(self):
        """Open settings page."""
        return rx.redirect("/settings")
    
    def show_help(self):
        """Show help modal."""
        self.show_help_modal = True
    
    def close_help(self):
        """Close help modal."""
        self.show_help_modal = False
    
    def clear_chat(self):
        """Clear chat history."""
        # This would integrate with chat state
        ToastState.toast_success("🗑️ Chat history cleared")
    
    def export_chat(self):
        """Export chat conversation."""
        # This would trigger chat export
        ToastState.toast_info("💾 Chat exported")
    
    @rx.var
    def filtered_commands(self) -> List[Dict]:
        """Get filtered commands based on search term."""
        if not self.search_term:
            return self.commands
        
        return [
            cmd for cmd in self.commands
            if (self.search_term in cmd["title"].lower() or 
                self.search_term in cmd["description"].lower())
        ]


def command_palette_item(command: Dict) -> rx.Component:
    """Individual command item in the palette."""
    return rx.box(
        rx.hstack(
            # Icon
            rx.icon(str(command["icon"]), size=18, color="violet.400"),
            
            # Title and description
            rx.vstack(
                rx.text(
                    command["title"],
                    font_weight="500",
                    color="gray.100",
                    font_size="sm"
                ),
                rx.text(
                    command["description"],
                    color="gray.400",
                    font_size="xs"
                ),
                align="start",
                spacing="1",
                flex="1"
            ),
            
            # Keyboard shortcut
            rx.code(
                command["shortcut"],
                color="gray.300",
                bg="rgba(255, 255, 255, 0.1)",
                border="1px solid rgba(255, 255, 255, 0.2)",
                font_size="xs",
                padding="2px 4px",
                border_radius="sm"
            ),
            
            align="center",
            spacing="3",
            width="100%"
        ),
        
        on_click=lambda: KeyboardShortcutState.execute_command(command["id"]),
        padding="3",
        border_radius="lg",
        cursor="pointer",
        _hover={
            "bg": "rgba(139, 92, 246, 0.15)",
            "border_color": "rgba(139, 92, 246, 0.3)"
        },
        transition="all 0.2s ease",
        border="1px solid transparent"
    )


def command_palette() -> rx.Component:
    """Command palette modal with search and command execution."""
    return rx.cond(
        KeyboardShortcutState.show_command_palette,
        rx.box(
            # Backdrop
            rx.box(
                on_click=KeyboardShortcutState.close_command_palette,
                position="fixed",
                top="0",
                left="0",
                width="100vw",
                height="100vh",
                bg="rgba(0, 0, 0, 0.6)",
                backdrop_filter="blur(8px)",
                z_index="9997"
            ),
            
            # Command palette content
            rx.box(
                rx.vstack(
                    # Search input
                    rx.hstack(
                        rx.icon("search", size=18, color="violet.400"),
                        rx.input(
                            placeholder="Search commands...",
                            value=KeyboardShortcutState.search_term,
                            on_change=KeyboardShortcutState.update_search_term,
                            variant="soft",
                            font_size="lg",
                            color="gray.100",
                            _placeholder={"color": "gray.400"},
                            auto_focus=True,
                            flex="1"
                        ),
                        align="center",
                        spacing="3",
                        padding="4",
                        border_bottom="1px solid rgba(255, 255, 255, 0.1)"
                    ),
                    
                    # Commands list
                    rx.scroll_area(
                        rx.vstack(
                            rx.foreach(
                                KeyboardShortcutState.filtered_commands,
                                command_palette_item
                            ),
                            spacing="1",
                            padding="2",
                            width="100%"
                        ),
                        max_height="400px",
                        width="100%"
                    ),
                    
                    # Footer
                    rx.hstack(
                        rx.text(
                            "Use ↑↓ to navigate",
                            font_size="xs",
                            color="gray.500"
                        ),
                        rx.spacer(),
                        rx.hstack(
                            rx.code("Enter", font_size="xs", padding="1px 3px", border_radius="sm"),
                            rx.text("to select", font_size="xs", color="gray.500"),
                            rx.code("Esc", font_size="xs", padding="1px 3px", border_radius="sm"),
                            rx.text("to close", font_size="xs", color="gray.500"),
                            spacing="2",
                            align="center"
                        ),
                        width="100%",
                        align="center",
                        padding="3",
                        border_top="1px solid rgba(255, 255, 255, 0.1)"
                    ),
                    
                    spacing="0",
                    width="100%"
                ),
                
                position="fixed",
                top="20%",
                left="50%",
                transform="translateX(-50%)",
                width="600px",
                max_width="90vw",
                bg="rgba(15, 15, 35, 0.95)",
                backdrop_filter="blur(20px)",
                border="1px solid rgba(255, 255, 255, 0.1)",
                border_radius="xl",
                box_shadow="0 20px 60px rgba(0, 0, 0, 0.5)",
                z_index="9998",
                animation="slideInUp 0.3s ease-out"
            ),
            
            position="fixed",
            top="0",
            left="0",
            width="100vw",
            height="100vh",
            z_index="9997"
        ),
        rx.fragment()
    )


def help_modal() -> rx.Component:
    """Keyboard shortcuts help modal."""
    return rx.cond(
        KeyboardShortcutState.show_help_modal,
        rx.box(
            # Backdrop
            rx.box(
                on_click=KeyboardShortcutState.close_help,
                position="fixed",
                top="0",
                left="0",
                width="100vw",
                height="100vh",
                bg="rgba(0, 0, 0, 0.6)",
                backdrop_filter="blur(8px)",
                z_index="9996"
            ),
            
            # Help content
            rx.box(
                rx.vstack(
                    # Header
                    rx.hstack(
                        rx.hstack(
                            rx.icon("circle-help", size=24, color="violet.400"),
                            rx.heading("Keyboard Shortcuts", size="5", color="gray.100"),
                            spacing="3",
                            align="center"
                        ),
                        rx.spacer(),
                        rx.button(
                            rx.icon("x", size=18),
                            on_click=KeyboardShortcutState.close_help,
                            variant="ghost",
                            size="2",
                            color_scheme="gray"
                        ),
                        width="100%",
                        align="center",
                        margin_bottom="6"
                    ),
                    
                    # Shortcuts grid
                    rx.scroll_area(
                        rx.vstack(
                            rx.foreach(
                                KeyboardShortcutState.commands,
                                lambda cmd: rx.hstack(
                                    rx.hstack(
                                        rx.icon(str(cmd["icon"]), size=16, color="violet.400"),
                                        rx.vstack(
                                            rx.text(cmd["title"], font_weight="500", color="gray.100"),
                                            rx.text(cmd["description"], font_size="sm", color="gray.400"),
                                            align="start",
                                            spacing="1"
                                        ),
                                        spacing="3",
                                        align="center",
                                        flex="1"
                                    ),
                                    rx.code(
                                        cmd["shortcut"],
                                        color="gray.300",
                                        bg="rgba(255, 255, 255, 0.1)",
                                        border="1px solid rgba(255, 255, 255, 0.2)",
                                        padding="2px 4px",
                                        border_radius="sm"
                                    ),
                                    width="100%",
                                    align="center",
                                    padding="3",
                                    border_radius="lg",
                                    _hover={"bg": "rgba(255, 255, 255, 0.05)"}
                                )
                            ),
                            spacing="2",
                            width="100%"
                        ),
                        max_height="400px",
                        width="100%"
                    ),
                    
                    # Footer tip
                    rx.box(
                        rx.text(
                            "💡 Tip: Press Ctrl+K to open the command palette anytime",
                            font_size="sm",
                            color="gray.400",
                            text_align="center"
                        ),
                        padding="4",
                        bg="rgba(139, 92, 246, 0.1)",
                        border_radius="lg",
                        border="1px solid rgba(139, 92, 246, 0.2)",
                        width="100%"
                    ),
                    
                    spacing="4",
                    width="100%"
                ),
                
                position="fixed",
                top="50%",
                left="50%",
                transform="translate(-50%, -50%)",
                width="600px",
                max_width="90vw",
                max_height="80vh",
                bg="rgba(15, 15, 35, 0.95)",
                backdrop_filter="blur(20px)",
                border="1px solid rgba(255, 255, 255, 0.1)",
                border_radius="xl",
                box_shadow="0 20px 60px rgba(0, 0, 0, 0.5)",
                padding="6",
                z_index="9997"
            ),
            
            position="fixed",
            top="0",
            left="0",
            width="100vw",
            height="100vh",
            z_index="9996"
        ),
        rx.fragment()
    )


def keyboard_handler() -> rx.Component:
    """Global keyboard event handler."""
    return rx.script(
        """
        document.addEventListener('keydown', function(e) {
            // Command palette - Ctrl+K
            if (e.ctrlKey && e.key === 'k') {
                e.preventDefault();
                // Trigger command palette toggle
                window.dispatchEvent(new CustomEvent('toggle-command-palette'));
            }
            
            // Upload - Ctrl+U
            if (e.ctrlKey && e.key === 'u') {
                e.preventDefault();
                window.dispatchEvent(new CustomEvent('open-upload'));
            }
            
            // Focus chat - Ctrl+/
            if (e.ctrlKey && e.key === '/') {
                e.preventDefault();
                const chatInput = document.querySelector('input[placeholder*="message"], textarea[placeholder*="message"]');
                if (chatInput) chatInput.focus();
            }
            
            // Documents - Ctrl+D
            if (e.ctrlKey && e.key === 'd') {
                e.preventDefault();
                window.location.href = '/documents';
            }
            
            // Settings - Ctrl+,
            if (e.ctrlKey && e.key === ',') {
                e.preventDefault();
                window.location.href = '/settings';
            }
            
            // Help - Ctrl+?
            if (e.ctrlKey && e.shiftKey && e.key === '?') {
                e.preventDefault();
                window.dispatchEvent(new CustomEvent('show-help'));
            }
            
            // Clear chat - Ctrl+Shift+C
            if (e.ctrlKey && e.shiftKey && e.key === 'C') {
                e.preventDefault();
                window.dispatchEvent(new CustomEvent('clear-chat'));
            }
            
            // Export chat - Ctrl+E
            if (e.ctrlKey && e.key === 'e') {
                e.preventDefault();
                window.dispatchEvent(new CustomEvent('export-chat'));
            }
            
            // Close modals with Escape
            if (e.key === 'Escape') {
                window.dispatchEvent(new CustomEvent('close-modals'));
            }
        });
        
        // Listen for custom events
        window.addEventListener('toggle-command-palette', () => {
            // This would trigger the Reflex state update
        });
        
        window.addEventListener('close-modals', () => {
            // This would close any open modals
        });
        """
    )


def shortcut_indicator(shortcut: str, description: str) -> rx.Component:
    """Small shortcut indicator for UI elements."""
    return rx.tooltip(
        rx.hstack(
            rx.code(
                shortcut,
                font_size="xs",
                padding="1px 3px",
                border_radius="sm",
                color="gray.400",
                bg="rgba(255, 255, 255, 0.05)",
                border="1px solid rgba(255, 255, 255, 0.1)"
            ),
            spacing="1"
        ),
        content=description,
        delay_duration=500
    )


# Animation styles for keyboard interactions
def keyboard_animation_styles() -> rx.Component:
    """CSS animations for keyboard interactions."""
    return rx.html(
        """
        <style>
        @keyframes slideInUp {
            from {
                opacity: 0;
                transform: translateX(-50%) translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateX(-50%) translateY(0);
            }
        }
        
        @keyframes keyPress {
            0% { transform: scale(1); }
            50% { transform: scale(0.95); }
            100% { transform: scale(1); }
        }
        
        .key-press {
            animation: keyPress 0.15s ease-out;
        }
        
        kbd {
            transition: all 0.2s ease;
        }
        
        kbd:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        }
        </style>
        """,
        tag="head"
    )