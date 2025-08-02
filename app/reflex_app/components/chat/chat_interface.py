"""Main chat interface component."""

import reflex as rx
from ...state.chat_state import ChatState
from .message_component import message_component, typing_indicator
from .input_form import chat_input_form, quick_prompts
from .chat_utils import auto_scroll_script, enhanced_textarea

def chat_header() -> rx.Component:
    """Chat interface header with stats."""
    return rx.hstack(
        rx.hstack(
            rx.icon("message-circle", size=20, color="blue.500"),
            rx.heading("RAG Chat", size="md", color="gray.700"),
            spacing="2",
            align="center"
        ),
        rx.spacer(),
        rx.hstack(
            rx.cond(
                ChatState.total_messages > 0,
                rx.badge(
                    f"{ChatState.total_messages} messages",
                    color_scheme="blue",
                    variant="outline"
                ),
                rx.fragment()
            ),
            rx.cond(
                ChatState.has_messages,
                rx.button(
                    rx.icon("download", size=14),
                    "Export",
                    size="sm",
                    variant="outline",
                    color_scheme="gray"
                ),
                rx.fragment()
            ),
            spacing="2"
        ),
        width="100%",
        padding="4",
        border_bottom="1px solid",
        border_color="gray.200",
        bg="white"
    )

def empty_chat_state() -> rx.Component:
    """Display when there are no messages."""
    return rx.center(
        rx.vstack(
            rx.icon("message-circle", size=64, color="blue.500"),
            rx.heading("Welcome to RAG Chat", size="lg", color="gray.700"),
            rx.text(
                "Ask questions about your documents and get intelligent answers with source attribution.",
                font_size="md",
                color="gray.500",
                text_align="center",
                max_width="400px"
            ),
            rx.vstack(
                rx.text("Features:", font_weight="bold", color="gray.600"),
                rx.vstack(
                    rx.text("• Semantic search across your documents", font_size="sm", color="gray.600"),
                    rx.text("• Source attribution for transparency", font_size="sm", color="gray.600"),
                    rx.text("• Adjustable similarity thresholds", font_size="sm", color="gray.600"),
                    rx.text("• Real-time response metrics", font_size="sm", color="gray.600"),
                    align="start",
                    spacing="1"
                ),
                spacing="2",
                align="start"
            ),
            spacing="4",
            align="center",
            padding="8"
        ),
        height="100%"
    )

def message_list() -> rx.Component:
    """Display list of chat messages."""
    return rx.scroll_area(
        rx.vstack(
            # Messages
            rx.foreach(
                ChatState.messages,
                message_component
            ),
            
            # Typing indicator
            rx.cond(
                ChatState.is_typing,
                typing_indicator(),
                rx.fragment()
            ),
            
            spacing="0",
            padding="4",
            width="100%"
        ),
        height="100%",
        width="100%",
        id="chat-messages-container"
    )

def chat_interface() -> rx.Component:
    """Complete chat interface with all components."""
    return rx.vstack(
        # Header
        chat_header(),
        
        # Main chat area
        rx.box(
            rx.cond(
                ChatState.has_messages,
                message_list(),
                empty_chat_state()
            ),
            height="calc(100vh - 300px)",
            width="100%",
            overflow="hidden"
        ),
        
        # Quick prompts (only show when no messages)
        quick_prompts(),
        
        # Input form
        chat_input_form(),
        
        # JavaScript enhancements
        auto_scroll_script(),
        enhanced_textarea(),
        
        spacing="0",
        width="100%",
        height="100%"
    )