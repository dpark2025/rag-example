"""Chat message display components."""

import reflex as rx
from typing import Dict, Any, List
from ...state.chat_state import ChatMessage

def format_timestamp(timestamp) -> str:
    """Format timestamp for display."""
    return timestamp.strftime("%H:%M:%S")

def source_badge(source: Dict[str, Any]) -> rx.Component:
    """Display a source attribution badge."""
    return rx.badge(
        rx.hstack(
            rx.icon("file-text", size=12),
            rx.text(
                source.get("title", "Unknown Source")[:30] + "..." 
                if len(source.get("title", "")) > 30 
                else source.get("title", "Unknown Source"),
                font_size="xs"
            ),
            rx.text(
                f"{source.get('similarity', 0):.2f}",
                font_size="xs",
                color="gray.500"
            ),
            spacing="1",
            align="center"
        ),
        variant="outline",
        color_scheme="blue",
        size="sm"
    )

def sources_panel(sources: List[Dict[str, Any]]) -> rx.Component:
    """Display sources used in the response."""
    if not sources:
        return rx.fragment()
    
    return rx.vstack(
        rx.text("Sources:", font_size="sm", font_weight="bold", color="gray.600"),
        rx.wrap(
            *[source_badge(source) for source in sources[:5]],  # Limit to 5 sources
            spacing="2"
        ),
        spacing="2",
        width="100%",
        padding="3",
        bg="gray.50",
        border_radius="md",
        border="1px solid",
        border_color="gray.200"
    )

def metrics_panel(metrics: Dict[str, Any]) -> rx.Component:
    """Display response metrics."""
    if not metrics:
        return rx.fragment()
    
    return rx.hstack(
        rx.text(
            f"⚡ {metrics.get('response_time', 0):.2f}s",
            font_size="xs",
            color="gray.500"
        ),
        rx.text(
            f"📄 {metrics.get('chunks_used', 0)} chunks",
            font_size="xs", 
            color="gray.500"
        ),
        spacing="4"
    )

def user_message(message: ChatMessage) -> rx.Component:
    """Display a user message."""
    return rx.hstack(
        rx.spacer(),
        rx.vstack(
            rx.hstack(
                rx.text("You", font_weight="bold", font_size="sm", color="blue.600"),
                rx.text(format_timestamp(message.timestamp), font_size="xs", color="gray.500"),
                spacing="2",
                align="center",
                justify="end"
            ),
            rx.box(
                rx.text(message.content, white_space="pre-wrap"),
                padding="3",
                bg="blue.500",
                color="white",
                border_radius="lg",
                max_width="400px",
                word_break="break-word"
            ),
            align="end",
            spacing="1"
        ),
        width="100%",
        margin_bottom="4"
    )

def assistant_message(message: ChatMessage) -> rx.Component:
    """Display an assistant message with sources and metrics."""
    return rx.hstack(
        rx.vstack(
            rx.hstack(
                rx.avatar(
                    fallback="AI",
                    size="sm",
                    bg="green.500",
                    color="white"
                ),
                rx.text("RAG Assistant", font_weight="bold", font_size="sm", color="green.600"),
                rx.text(format_timestamp(message.timestamp), font_size="xs", color="gray.500"),
                spacing="2",
                align="center"
            ),
            rx.box(
                rx.text(message.content, white_space="pre-wrap"),
                padding="3",
                bg="gray.100",
                border_radius="lg",
                max_width="500px",
                word_break="break-word"
            ),
            # Sources panel
            rx.cond(
                message.sources and len(message.sources) > 0,
                sources_panel(message.sources),
                rx.fragment()
            ),
            # Metrics panel
            rx.cond(
                message.metrics,
                metrics_panel(message.metrics),
                rx.fragment()
            ),
            align="start",
            spacing="2"
        ),
        rx.spacer(),
        width="100%",
        margin_bottom="4"
    )

def message_component(message: ChatMessage) -> rx.Component:
    """Render a message based on its role."""
    return rx.cond(
        message.role == "user",
        user_message(message),
        assistant_message(message)
    )

def typing_indicator() -> rx.Component:
    """Show typing indicator when assistant is responding."""
    return rx.hstack(
        rx.avatar(
            fallback="AI",
            size="sm",
            bg="green.500",
            color="white"
        ),
        rx.hstack(
            rx.text("RAG Assistant is thinking", font_size="sm", color="gray.600"),
            rx.spinner(size="sm", color="green.500"),
            spacing="2",
            align="center"
        ),
        spacing="3",
        margin_bottom="4",
        padding="2"
    )