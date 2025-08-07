"""
In-app help and documentation system.
"""

import reflex as rx
from typing import Dict, Any, List, Optional
from enum import Enum


class HelpCategory(Enum):
    """Help content categories."""
    GETTING_STARTED = "getting_started"
    UPLOADING_DOCUMENTS = "uploading_documents"
    ASKING_QUESTIONS = "asking_questions"
    DOCUMENT_MANAGEMENT = "document_management"
    SETTINGS = "settings"
    TROUBLESHOOTING = "troubleshooting"
    KEYBOARD_SHORTCUTS = "keyboard_shortcuts"
    ACCESSIBILITY = "accessibility"


class HelpState(rx.State):
    """State for managing help system."""
    
    # Help visibility
    show_help_panel: bool = False
    show_help_modal: bool = False
    help_panel_pinned: bool = False
    
    # Navigation
    current_category: str = HelpCategory.GETTING_STARTED.value
    search_query: str = ""
    search_results: List[Dict[str, Any]] = []
    
    # User preferences
    show_tooltips: bool = True
    show_contextual_help: bool = True
    completed_tutorials: List[str] = []
    
    # Help content
    help_content: Dict[str, Dict[str, Any]] = {
        HelpCategory.GETTING_STARTED.value: {
            "title": "Getting Started",
            "icon": "play-circle",
            "sections": [
                {
                    "title": "Welcome to RAG System",
                    "content": "Your local RAG (Retrieval-Augmented Generation) system allows you to chat with your documents using AI, completely offline and privately.",
                    "steps": [
                        "Upload your documents (PDF, TXT, etc.)",
                        "Ask questions about your documents",
                        "Get AI-powered responses with source citations",
                        "Explore advanced features as needed"
                    ]
                },
                {
                    "title": "Key Features",
                    "content": "Understanding what makes this system powerful:",
                    "features": [
                        "🔒 Complete Privacy - Everything runs locally",
                        "📄 Multiple Formats - PDF, TXT, and more",
                        "🤖 AI-Powered - Intelligent document understanding",
                        "⚡ Fast Search - Instant retrieval from your documents",
                        "📊 Source Attribution - See exactly where answers come from"
                    ]
                }
            ]
        },
        HelpCategory.UPLOADING_DOCUMENTS.value: {
            "title": "Document Upload",
            "icon": "upload",
            "sections": [
                {
                    "title": "Supported Formats",
                    "content": "The system supports various document formats:",
                    "formats": [
                        {"type": "PDF", "description": "Portable Document Format files"},
                        {"type": "TXT", "description": "Plain text files"},
                        {"type": "MD", "description": "Markdown files"},
                        {"type": "DOC/DOCX", "description": "Microsoft Word documents (coming soon)"}
                    ]
                },
                {
                    "title": "Upload Methods",
                    "content": "Multiple ways to add documents:",
                    "methods": [
                        "Drag and drop files directly onto the interface",
                        "Use the 'Upload Document' button",
                        "Bulk upload multiple files at once",
                        "Copy and paste text content directly"
                    ]
                },
                {
                    "title": "Best Practices",
                    "content": "Tips for optimal document processing:",
                    "tips": [
                        "Ensure PDFs have selectable text (not scanned images)",
                        "Use descriptive filenames for easier management",
                        "Break large documents into chapters if needed",
                        "Avoid uploading duplicate content"
                    ]
                }
            ]
        },
        HelpCategory.ASKING_QUESTIONS.value: {
            "title": "Asking Questions",
            "icon": "message-circle",
            "sections": [
                {
                    "title": "Question Types",
                    "content": "The system can handle various question types:",
                    "types": [
                        {"type": "Factual", "example": "What is the main conclusion of the research?"},
                        {"type": "Summary", "example": "Summarize the key points from chapter 3"},
                        {"type": "Comparison", "example": "How do these two approaches differ?"},
                        {"type": "Analysis", "example": "What are the implications of these findings?"}
                    ]
                },
                {
                    "title": "Tips for Better Results",
                    "content": "How to get the most accurate responses:",
                    "tips": [
                        "Be specific in your questions",
                        "Reference particular sections or topics when relevant",
                        "Ask follow-up questions for clarification",
                        "Use the chat history to build context"
                    ]
                }
            ]
        },
        HelpCategory.DOCUMENT_MANAGEMENT.value: {
            "title": "Document Management",
            "icon": "file-text",
            "sections": [
                {
                    "title": "Viewing Documents",
                    "content": "Access and manage your uploaded documents:",
                    "actions": [
                        "View document list and metadata",
                        "Preview document content",
                        "Check processing status",
                        "Remove unwanted documents"
                    ]
                },
                {
                    "title": "Organization",
                    "content": "Keep your documents organized:",
                    "features": [
                        "Sort by upload date, name, or size",
                        "Search through document names",
                        "Group related documents",
                        "Monitor storage usage"
                    ]
                }
            ]
        },
        HelpCategory.SETTINGS.value: {
            "title": "Settings & Configuration",
            "icon": "settings",
            "sections": [
                {
                    "title": "Chat Settings",
                    "content": "Customize your chat experience:",
                    "options": [
                        {"setting": "Max Chunks", "description": "Number of document chunks to consider"},
                        {"setting": "Similarity Threshold", "description": "Minimum relevance score for chunk inclusion"},
                        {"setting": "Response Length", "description": "Preferred answer length"}
                    ]
                },
                {
                    "title": "System Settings",
                    "content": "Configure system behavior:",
                    "options": [
                        {"setting": "Performance Mode", "description": "Balance speed vs. accuracy"},
                        {"setting": "Privacy Settings", "description": "Data retention and logging options"},
                        {"setting": "Accessibility", "description": "Screen reader and visual options"}
                    ]
                }
            ]
        },
        HelpCategory.TROUBLESHOOTING.value: {
            "title": "Troubleshooting",
            "icon": "circle-help",
            "sections": [
                {
                    "title": "Common Issues",
                    "content": "Solutions to frequent problems:",
                    "issues": [
                        {
                            "problem": "Document upload fails",
                            "solutions": [
                                "Check file size (max 50MB per file)",
                                "Ensure file format is supported",
                                "Try refreshing the page",
                                "Check your internet connection"
                            ]
                        },
                        {
                            "problem": "Slow response times",
                            "solutions": [
                                "Reduce max chunks in settings",
                                "Clear browser cache",
                                "Check system resources",
                                "Restart the application"
                            ]
                        }
                    ]
                },
                {
                    "title": "Error Messages",
                    "content": "Understanding common error messages:",
                    "errors": [
                        {"code": "NETWORK_ERROR", "meaning": "Connection issue", "action": "Check connectivity"},
                        {"code": "FILE_TOO_LARGE", "meaning": "File exceeds size limit", "action": "Split or compress file"},
                        {"code": "PROCESSING_FAILED", "meaning": "Document processing error", "action": "Try different format"}
                    ]
                }
            ]
        },
        HelpCategory.KEYBOARD_SHORTCUTS.value: {
            "title": "Keyboard Shortcuts",
            "icon": "keyboard",
            "sections": [
                {
                    "title": "Global Shortcuts",
                    "content": "Keyboard shortcuts available throughout the app:",
                    "shortcuts": [
                        {"keys": "Ctrl + /", "action": "Show/hide this help panel"},
                        {"keys": "Ctrl + U", "action": "Upload new document"},
                        {"keys": "Ctrl + K", "action": "Focus search/chat input"},
                        {"keys": "Escape", "action": "Close modal or panel"}
                    ]
                },
                {
                    "title": "Chat Shortcuts",
                    "content": "Shortcuts for the chat interface:",
                    "shortcuts": [
                        {"keys": "Enter", "action": "Send message"},
                        {"keys": "Shift + Enter", "action": "New line in message"},
                        {"keys": "Ctrl + L", "action": "Clear chat history"},
                        {"keys": "↑/↓", "action": "Navigate message history"}
                    ]
                }
            ]
        },
        HelpCategory.ACCESSIBILITY.value: {
            "title": "Accessibility",
            "icon": "accessibility",
            "sections": [
                {
                    "title": "Screen Reader Support",
                    "content": "Using the system with screen readers:",
                    "features": [
                        "Full ARIA label support",
                        "Semantic HTML structure",
                        "Live region announcements",
                        "Skip navigation links"
                    ]
                },
                {
                    "title": "Visual Accessibility",
                    "content": "Options for visual accessibility:",
                    "options": [
                        "High contrast mode",
                        "Adjustable font sizes",
                        "Color blind friendly themes",
                        "Reduced motion options"
                    ]
                }
            ]
        }
    }
    
    def toggle_help_panel(self):
        """Toggle help panel visibility."""
        self.show_help_panel = not self.show_help_panel
    
    def toggle_help_modal(self):
        """Toggle help modal."""
        self.show_help_modal = not self.show_help_modal
    
    def pin_help_panel(self):
        """Pin/unpin help panel."""
        self.help_panel_pinned = not self.help_panel_pinned
    
    def set_category(self, category: str):
        """Set the current help category."""
        self.current_category = category
    
    def search_help(self, query: str):
        """Search through help content."""
        self.search_query = query.lower()
        self.search_results = []
        
        if not query.strip():
            return
        
        for category_id, category_data in self.help_content.items():
            for section in category_data.get("sections", []):
                # Search in title and content
                if (query in section.get("title", "").lower() or 
                    query in section.get("content", "").lower()):
                    self.search_results.append({
                        "category": category_id,
                        "category_title": category_data["title"],
                        "section_title": section["title"],
                        "content": section["content"][:200] + "..." if len(section["content"]) > 200 else section["content"]
                    })
    
    def clear_search(self):
        """Clear search results."""
        self.search_query = ""
        self.search_results = []
    
    def toggle_tooltips(self):
        """Toggle tooltip visibility."""
        self.show_tooltips = not self.show_tooltips
    
    def toggle_contextual_help(self):
        """Toggle contextual help."""
        self.show_contextual_help = not self.show_contextual_help
    
    def mark_tutorial_completed(self, tutorial_id: str):
        """Mark a tutorial as completed."""
        if tutorial_id not in self.completed_tutorials:
            self.completed_tutorials.append(tutorial_id)


def help_search_box() -> rx.Component:
    """Help search input."""
    return rx.hstack(
        rx.input(
            placeholder="Search help...",
            value=HelpState.search_query,
            on_change=HelpState.search_help,
            size="sm",
            width="100%"
        ),
        rx.cond(
            HelpState.search_query != "",
            rx.icon_button(
                rx.icon("x", size=16),
                on_click=HelpState.clear_search,
                size="sm",
                variant="ghost"
            )
        ),
        width="100%",
        spacing="0.5rem"
    )


def help_category_nav() -> rx.Component:
    """Help category navigation."""
    return rx.vstack(
        rx.foreach(
            HelpState.help_content.items(),
            lambda item: rx.button(
                rx.hstack(
                    rx.icon(item[1]["icon"], size=16),
                    rx.text(item[1]["title"], font_size="sm"),
                    spacing="0.5rem",
                    align_items="center"
                ),
                on_click=lambda category=item[0]: HelpState.set_category(category),
                variant=rx.cond(
                    HelpState.current_category == item[0],
                    "solid",
                    "ghost"
                ),
                color_scheme="blue",
                size="sm",
                width="100%",
                justify_content="flex-start"
            )
        ),
        spacing="0.25rem",
        width="100%"
    )


def help_content_section(section: Dict[str, Any]) -> rx.Component:
    """Render a help content section."""
    return rx.vstack(
        rx.heading(
            section["title"],
            size="md",
            margin_bottom="0.5rem"
        ),
        rx.text(
            section["content"],
            color="gray.700",
            line_height="1.6",
            margin_bottom="1rem"
        ),
        
        # Steps (if present)
        rx.cond(
            "steps" in section,
            rx.vstack(
                rx.text("Steps:", font_weight="semibold", margin_bottom="0.5rem"),
                rx.foreach(
                    section.get("steps", []),
                    lambda step, index: rx.hstack(
                        rx.box(
                            rx.text(str(index + 1), font_size="sm", color="white"),
                            background_color="blue.500",
                            border_radius="full",
                            width="24px",
                            height="24px",
                            display="flex",
                            align_items="center",
                            justify_content="center"
                        ),
                        rx.text(step, flex="1"),
                        align_items="flex-start",
                        spacing="0.5rem",
                        margin_bottom="0.5rem"
                    )
                ),
                spacing="0.25rem",
                width="100%",
                margin_bottom="1rem"
            )
        ),
        
        # Features (if present)
        rx.cond(
            "features" in section,
            rx.vstack(
                rx.foreach(
                    section.get("features", []),
                    lambda feature: rx.text(feature, margin_bottom="0.25rem")
                ),
                spacing="0.25rem",
                width="100%",
                margin_bottom="1rem"
            )
        ),
        
        # Shortcuts (if present)
        rx.cond(
            "shortcuts" in section,
            rx.vstack(
                rx.foreach(
                    section.get("shortcuts", []),
                    lambda shortcut: rx.hstack(
                        rx.box(
                            rx.text(
                                shortcut["keys"],
                                font_family="monospace",
                                font_size="sm",
                                color="blue.600"
                            ),
                            background_color="gray.100",
                            border="1px solid",
                            border_color="gray.300",
                            border_radius="md",
                            padding="0.25rem 0.5rem"
                        ),
                        rx.text(shortcut["action"], flex="1"),
                        justify_content="space-between",
                        align_items="center",
                        width="100%",
                        margin_bottom="0.5rem"
                    )
                ),
                spacing="0.25rem",
                width="100%",
                margin_bottom="1rem"
            )
        ),
        
        spacing="0.5rem",
        width="100%",
        align_items="flex-start"
    )


def help_content_display() -> rx.Component:
    """Display help content for current category."""
    return rx.cond(
        len(HelpState.search_results) > 0,
        # Search results
        rx.vstack(
            rx.heading("Search Results", size="lg", margin_bottom="1rem"),
            rx.foreach(
                HelpState.search_results,
                lambda result: rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.text(
                                result["category_title"],
                                font_size="sm",
                                color="blue.600",
                                font_weight="semibold"
                            ),
                            rx.text("•", color="gray.400"),
                            rx.text(
                                result["section_title"],
                                font_size="sm",
                                color="gray.600"
                            ),
                            spacing="0.5rem"
                        ),
                        rx.text(
                            result["content"],
                            font_size="sm",
                            color="gray.700"
                        ),
                        align_items="flex-start",
                        spacing="0.25rem",
                        width="100%"
                    ),
                    padding="1rem",
                    border="1px solid",
                    border_color="gray.200",
                    border_radius="md",
                    margin_bottom="0.5rem",
                    cursor="pointer",
                    on_click=lambda category=result["category"]: HelpState.set_category(category),
                    _hover={"background_color": "gray.50"}
                )
            ),
            spacing="0.5rem",
            width="100%"
        ),
        # Category content
        rx.vstack(
            rx.heading(
                HelpState.help_content[HelpState.current_category]["title"],
                size="lg",
                margin_bottom="1rem"
            ),
            rx.foreach(
                HelpState.help_content[HelpState.current_category]["sections"],
                help_content_section
            ),
            spacing="2rem",
            width="100%",
            align_items="flex-start"
        )
    )


def help_panel() -> rx.Component:
    """Main help panel component."""
    return rx.cond(
        HelpState.show_help_panel,
        rx.box(
            rx.vstack(
                # Header
                rx.hstack(
                    rx.text(
                        "Help & Documentation",
                        font_size="lg",
                        font_weight="bold"
                    ),
                    rx.spacer(),
                    rx.icon_button(
                        rx.icon(
                            rx.cond(
                                HelpState.help_panel_pinned,
                                "pin",
                                "pin-off"
                            ),
                            size=16
                        ),
                        on_click=HelpState.pin_help_panel,
                        size="sm",
                        variant="ghost",
                        aria_label="Pin help panel"
                    ),
                    rx.icon_button(
                        rx.icon("x", size=16),
                        on_click=HelpState.toggle_help_panel,
                        size="sm",
                        variant="ghost",
                        aria_label="Close help panel"
                    ),
                    width="100%",
                    align_items="center"
                ),
                
                # Search
                help_search_box(),
                
                rx.divider(),
                
                # Content area
                rx.hstack(
                    # Navigation
                    rx.box(
                        help_category_nav(),
                        width="200px",
                        flex_shrink="0"
                    ),
                    
                    rx.divider(orientation="vertical", height="400px"),
                    
                    # Content
                    rx.box(
                        help_content_display(),
                        flex="1",
                        overflow_y="auto",
                        max_height="400px",
                        padding_left="1rem"
                    ),
                    
                    width="100%",
                    align_items="flex-start",
                    spacing="1rem"
                ),
                
                spacing="1rem",
                width="100%"
            ),
            position="fixed",
            top="50%",
            right="2rem",
            transform="translateY(-50%)",
            width="800px",
            max_height="600px",
            background_color="white",
            border="1px solid",
            border_color="gray.200",
            border_radius="lg",
            box_shadow="lg",
            padding="1.5rem",
            z_index="1000"
        )
    )


def help_button() -> rx.Component:
    """Help button to open help panel."""
    return rx.button(
        rx.icon("circle-help", size=16),
        "Help",
        on_click=HelpState.toggle_help_panel,
        variant="ghost",
        size="sm",
        color_scheme="blue"
    )


def contextual_help(content: str, position: str = "top") -> rx.Component:
    """Show contextual help tooltip."""
    return rx.cond(
        HelpState.show_contextual_help,
        rx.tooltip(
            content,
            placement=position
        )
    )


def quick_help_shortcuts() -> rx.Component:
    """Quick access to common help topics."""
    return rx.hstack(
        rx.button(
            "Getting Started",
            on_click=lambda: [HelpState.set_category("getting_started"), HelpState.toggle_help_panel()],
            size="sm",
            variant="outline"
        ),
        rx.button(
            "Keyboard Shortcuts",
            on_click=lambda: [HelpState.set_category("keyboard_shortcuts"), HelpState.toggle_help_panel()],
            size="sm",
            variant="outline"
        ),
        rx.button(
            "Troubleshooting",
            on_click=lambda: [HelpState.set_category("troubleshooting"), HelpState.toggle_help_panel()],
            size="sm",
            variant="outline"
        ),
        spacing="0.5rem",
        align_items="center"
    )