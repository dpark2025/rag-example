"""Main application layout."""

import reflex as rx
from ..components.sidebar.system_status import system_status_panel

def header_component() -> rx.Component:
    """Top header component."""
    return rx.hstack(
        rx.heading("Local RAG System", size="lg", color="gray.800"),
        rx.spacer(),
        rx.hstack(
            rx.text("v2.0 - Reflex", font_size="sm", color="gray.500"),
            spacing="4"
        ),
        width="100%",
        padding="4",
        border_bottom="1px solid",
        border_color="gray.200",
        bg="white"
    )

def sidebar_component() -> rx.Component:
    """Left sidebar component."""
    return rx.vstack(
        rx.heading("RAG Controls", size="md", color="gray.700", margin_bottom="4"),
        
        # Navigation links
        rx.vstack(
            rx.link(
                rx.hstack(
                    rx.icon("message-circle", size=16),
                    rx.text("Chat", font_size="sm"),
                    spacing="2"
                ),
                href="/",
                _hover={"bg": "gray.100"},
                padding="2",
                border_radius="md",
                width="100%"
            ),
            rx.link(
                rx.hstack(
                    rx.icon("file-text", size=16),
                    rx.text("Documents", font_size="sm"),
                    spacing="2"
                ),
                href="/documents",
                _hover={"bg": "gray.100"},
                padding="2",
                border_radius="md",
                width="100%"
            ),
            rx.link(
                rx.hstack(
                    rx.icon("settings", size=16),
                    rx.text("Settings", font_size="sm"),
                    spacing="2"
                ),
                href="/settings",
                _hover={"bg": "gray.100"},
                padding="2",
                border_radius="md",
                width="100%"
            ),
            spacing="2",
            width="100%",
            margin_bottom="6"
        ),
        
        # System status
        system_status_panel(),
        
        spacing="4",
        width="250px",
        height="100vh",
        padding="4",
        border_right="1px solid",
        border_color="gray.200",
        bg="gray.50",
        overflow_y="auto"
    )

def main_layout(page_content: rx.Component) -> rx.Component:
    """Main application layout with sidebar and header."""
    return rx.hstack(
        sidebar_component(),
        rx.vstack(
            header_component(),
            rx.box(
                page_content,
                width="100%",
                height="calc(100vh - 80px)",
                overflow="auto",
                padding="4"
            ),
            spacing="0",
            width="100%"
        ),
        height="100vh",
        spacing="0",
        width="100%"
    )