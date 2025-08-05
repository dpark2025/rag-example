"""Enhanced main chat interface component with animations and UX polish."""

import reflex as rx
from ...state.chat_state import ChatState
from .message_component import message_component, typing_indicator
from .input_form import chat_input_form, quick_prompts
from .chat_utils import auto_scroll_script, enhanced_textarea
from ..common.animations import fade_in, slide_in_from_up, staggered_fade_in, hover_lift
from ..common.loading_spinner import (
    skeleton_chat_history, skeleton_chat_message, loading_overlay
)
from ..common.toast_notifications import ToastState
from ..common.responsive_design import ResponsiveState

def chat_header() -> rx.Component:
    """Enhanced chat interface header with animations and responsive design."""
    return fade_in(
        rx.hstack(
            # Chat title and icon
            hover_lift(
                rx.hstack(
                    rx.icon("message-circle", size=20, color="violet.400"),
                    rx.heading(
                        rx.cond(
                            ResponsiveState.is_mobile,
                            "Chat",
                            "RAG Chat"
                        ),
                        size=rx.cond(ResponsiveState.is_mobile, "4", "5"),
                        color="gray.100"
                    ),
                    spacing="3",
                    align="center"
                ),
                lift_amount="2px"
            ),
            
            rx.spacer(),
            
            # Header actions
            rx.hstack(
                # Message count badge
                rx.cond(
                    ChatState.total_messages > 0,
                    fade_in(
                        rx.badge(
                            ChatState.total_messages_display,
                            color_scheme="violet",
                            variant="outline",
                            font_size="xs"
                        ),
                        delay="0.2s"
                    ),
                    rx.fragment()
                ),
                
                # Action buttons
                rx.cond(
                    ChatState.has_messages,
                    rx.hstack(
                        # Clear chat button
                        hover_lift(
                            rx.button(
                                rx.icon("trash-2", size=14),
                                rx.cond(
                                    ResponsiveState.is_mobile,
                                    rx.fragment(),
                                    rx.text("Clear", font_size="sm")
                                ),
                                size="2",
                                variant="outline",
                                color_scheme="red",
                                spacing="2",
                                on_click=lambda: ToastState.toast_info("Chat cleared"),
                                aria_label="Clear chat history"
                            ),
                            lift_amount="2px"
                        ),
                        
                        # Export button  
                        hover_lift(
                            rx.button(
                                rx.icon("download", size=14),
                                rx.cond(
                                    ResponsiveState.is_mobile,
                                    rx.fragment(),
                                    rx.text("Export", font_size="sm")
                                ),
                                size="2",
                                variant="outline",
                                color_scheme="blue",
                                spacing="2",
                                on_click=lambda: ToastState.toast_success("Chat exported successfully"),
                                aria_label="Export chat history"
                            ),
                            lift_amount="2px"
                        ),
                        
                        spacing="2"
                    ),
                    rx.fragment()
                ),
                
                spacing="3",
                align="center"
            ),
            
            width="100%",
            padding="4",
            align="center"
        ),
        
        # Enhanced styling
        border_bottom="1px solid rgba(255, 255, 255, 0.1)",
        bg="rgba(255, 255, 255, 0.02)",
        backdrop_filter="blur(10px)",
        position="sticky",
        top="0",
        z_index="10"
    )

def empty_chat_state() -> rx.Component:
    """Enhanced empty state with animations and onboarding."""
    return rx.center(
        staggered_fade_in([
            # Welcome icon
            rx.box(
                rx.icon("message-circle", size=72, color="violet.400"),
                animation="pulse 3s ease-in-out infinite"
            ),
            
            # Welcome heading
            rx.heading(
                "Welcome to RAG Chat",
                size=rx.cond(ResponsiveState.is_mobile, "3", "4"),
                color="gray.100",
                text_align="center"
            ),
            
            # Description
            rx.text(
                rx.cond(
                    ResponsiveState.is_mobile,
                    "Ask questions about your documents and get intelligent answers.",
                    "Ask questions about your documents and get intelligent answers with source attribution."
                ),
                font_size=rx.cond(ResponsiveState.is_mobile, "14px", "16px"),
                color="gray.300",
                text_align="center",
                max_width=rx.cond(ResponsiveState.is_mobile, "300px", "400px"),
                line_height="1.5"
            ),
            
            # Feature highlights
            rx.vstack(
                rx.text(
                    "✨ Key Features:",
                    font_weight="600",
                    color="violet.300",
                    font_size="sm"
                ),
                rx.vstack(
                    rx.hstack(
                        rx.icon("search", size=16, color="violet.400"),
                        rx.text("Semantic search across documents", font_size="sm", color="gray.300"),
                        spacing="2",
                        align="center"
                    ),
                    rx.hstack(
                        rx.icon("link", size=16, color="violet.400"),
                        rx.text("Source attribution for transparency", font_size="sm", color="gray.300"),
                        spacing="2",
                        align="center"
                    ),
                    rx.hstack(
                        rx.icon("zap", size=16, color="violet.400"),
                        rx.text("Real-time response metrics", font_size="sm", color="gray.300"),
                        spacing="2",
                        align="center"
                    ),
                    rx.hstack(
                        rx.icon("shield", size=16, color="violet.400"),
                        rx.text("Local processing for privacy", font_size="sm", color="gray.300"),
                        spacing="2",
                        align="center"
                    ),
                    align="start",
                    spacing="2"
                ),
                spacing="3",
                align="center",
                padding="4",
                bg="rgba(139, 92, 246, 0.1)",
                border="1px solid rgba(139, 92, 246, 0.2)",
                border_radius="xl",
                max_width="400px"
            ),
            
            # Quick start hint
            rx.box(
                rx.text(
                    rx.cond(
                        ResponsiveState.is_mobile,
                        "💡 Tap the input below to get started",
                        "💡 Type your question below or press Ctrl+/ to focus the input"
                    ),
                    font_size="xs",
                    color="gray.400",
                    text_align="center",
                    font_style="italic"
                ),
                margin_top="4"
            )
        ]),
        
        height="100%",
        padding="8"
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