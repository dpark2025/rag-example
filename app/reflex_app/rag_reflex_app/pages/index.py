"""Main chat interface page."""

import reflex as rx
from ..layouts.main_layout import main_layout
from ..components.common.loading_spinner import loading_spinner
from ..components.chat.chat_interface import chat_interface
from ..state.app_state import AppState
from ..state.chat_state import ChatState

def index_page() -> rx.Component:
    """Main chat page with full RAG interface."""
    return main_layout(
        rx.cond(
            AppState.is_loading,
            loading_spinner("lg", "Loading chat interface..."),
            chat_interface()
        )
    )