"""Main chat interface page."""

import reflex as rx
from ..layouts.main_layout import main_layout
from ..components.common.loading_spinner import loading_spinner
from ..state.app_state import AppState

def chat_placeholder() -> rx.Component:
    """Placeholder for chat interface during Phase 1."""
    return rx.center(
        rx.vstack(
            rx.icon("message-circle", size=64, color="blue.500"),
            rx.heading("RAG Chat Interface", size="xl", color="gray.700"),
            rx.text(
                "Phase 2: Chat interface will be implemented here",
                font_size="lg",
                color="gray.500",
                text_align="center"
            ),
            rx.text(
                "✅ Phase 1 Complete: Foundation setup with Reflex",
                font_size="md",
                color="green.600",
                text_align="center"
            ),
            spacing="4",
            align="center"
        ),
        height="400px"
    )

def index_page() -> rx.Component:
    """Main chat page."""
    return main_layout(
        rx.cond(
            AppState.is_loading,
            loading_spinner("lg", "Loading chat interface..."),
            chat_placeholder()
        )
    )