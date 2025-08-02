"""Main Reflex RAG Application."""

import reflex as rx
from .pages.index import index_page
from .state.app_state import AppState
from .state.chat_state import ChatState

# App styling
style = {
    "font_family": "Inter, system-ui, sans-serif",
    "background_color": "white",
}

# Create the Reflex app
app = rx.App(
    style=style,
    head_components=[
        rx.script(src="https://unpkg.com/react@18/umd/react.development.js"),
        rx.script(src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"),
    ],
)

# Add pages
app.add_page(
    index_page,
    route="/",
    title="RAG System - Chat",
    on_load=AppState.on_load
)

# Placeholder pages for Phase 2+
@rx.page(route="/documents", title="RAG System - Documents")
def documents_page():
    from .layouts.main_layout import main_layout
    return main_layout(
        rx.center(
            rx.vstack(
                rx.icon("file-text", size=64, color="blue.500"),
                rx.heading("Document Management", size="xl", color="gray.700"),
                rx.text(
                    "Phase 3: Document management will be implemented here",
                    font_size="lg",
                    color="gray.500",
                    text_align="center"
                ),
                spacing="4",
                align="center"
            ),
            height="400px"
        )
    )

@rx.page(route="/settings", title="RAG System - Settings")
def settings_page():
    from .layouts.main_layout import main_layout
    return main_layout(
        rx.center(
            rx.vstack(
                rx.icon("settings", size=64, color="blue.500"),
                rx.heading("System Settings", size="xl", color="gray.700"),
                rx.text(
                    "Phase 5: Settings panel will be implemented here",
                    font_size="lg",
                    color="gray.500",
                    text_align="center"
                ),
                spacing="4",
                align="center"
            ),
            height="400px"
        )
    )