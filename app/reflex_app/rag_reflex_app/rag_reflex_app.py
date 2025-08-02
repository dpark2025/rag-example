"""Main Reflex RAG Application."""

import reflex as rx
from .pages.index import index_page
from .state.app_state import AppState
from .state.chat_state import ChatState

# Modern dark glass morphism theme (2025 trend)
theme = rx.theme(
    appearance="dark",  # Dark mode base
    has_background=True,
    accent_color="violet",  # Modern accent
    gray_color="mauve",    # Warmer grays
    scaling="100%",
)

# 2025 Glass Morphism Dark Theme
style = {
    "font_family": "Inter, system-ui, -apple-system, sans-serif",
    # Dark gradient background with depth
    "background": """
        linear-gradient(135deg, 
            #0f0f23 0%,
            #1a1a2e 25%,
            #16213e 50%,
            #0f3460 75%,
            #0e2954 100%
        )
    """,
    "min_height": "100vh",
    "position": "relative",
    # Add some subtle noise texture
    "&::before": {
        "content": '""',
        "position": "absolute",
        "top": "0",
        "left": "0",
        "right": "0",
        "bottom": "0",
        "background": """
            radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.15) 0%, transparent 50%),
            radial-gradient(circle at 40% 40%, rgba(120, 219, 255, 0.1) 0%, transparent 50%)
        """,
        "pointer_events": "none",
    }
}

# Create the Reflex app
app = rx.App(
    style=style,
    theme=theme,
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
                rx.heading("Document Management", size="3", color="gray.700"),
                rx.text(
                    "Phase 3: Document management will be implemented here",
                    font_size="18px",
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
                rx.heading("System Settings", size="3", color="gray.700"),
                rx.text(
                    "Phase 5: Settings panel will be implemented here",
                    font_size="18px",
                    color="gray.500",
                    text_align="center"
                ),
                spacing="4",
                align="center"
            ),
            height="400px"
        )
    )