"""Main application layout."""

import reflex as rx
from ..components.sidebar.system_status import system_status_panel

def header_component() -> rx.Component:
    """Top header component with glass morphism."""
    return rx.hstack(
        rx.heading("Local RAG System", size="4", color="gray.100"),
        rx.spacer(),
        rx.hstack(
            rx.text("v2.0 - Reflex", font_size="14px", color="gray.400"),
            spacing="4"
        ),
        width="100%",
        padding="4",
        border_bottom="1px solid",
        border_color="rgba(255, 255, 255, 0.1)",
        # Glass morphism effect
        bg="rgba(255, 255, 255, 0.05)",
        backdrop_filter="blur(20px)",
        box_shadow="0 8px 32px rgba(0, 0, 0, 0.3)",
        border="1px solid rgba(255, 255, 255, 0.08)"
    )

def sidebar_component() -> rx.Component:
    """Left sidebar component with glass morphism."""
    return rx.vstack(
        rx.heading("RAG Controls", size="5", color="gray.100", margin_bottom="4"),
        
        # Navigation links
        rx.vstack(
            rx.link(
                rx.hstack(
                    rx.icon("message-circle", size=16, color="violet.400"),
                    rx.text("Chat", font_size="14px", color="gray.200"),
                    spacing="2"
                ),
                href="/",
                _hover={"bg": "rgba(139, 92, 246, 0.15)", "border_color": "rgba(139, 92, 246, 0.3)"},
                padding="3",
                border_radius="xl",
                width="100%",
                transition="all 0.3s ease",
                border="1px solid rgba(255, 255, 255, 0.05)"
            ),
            rx.link(
                rx.hstack(
                    rx.icon("file-text", size=16, color="violet.400"),
                    rx.text("Documents", font_size="14px", color="gray.200"),
                    spacing="2"
                ),
                href="/documents",
                _hover={"bg": "rgba(139, 92, 246, 0.15)", "border_color": "rgba(139, 92, 246, 0.3)"},
                padding="3",
                border_radius="xl",
                width="100%",
                transition="all 0.3s ease",
                border="1px solid rgba(255, 255, 255, 0.05)"
            ),
            rx.link(
                rx.hstack(
                    rx.icon("settings", size=16, color="violet.400"),
                    rx.text("Settings", font_size="14px", color="gray.200"),
                    spacing="2"
                ),
                href="/settings",
                _hover={"bg": "rgba(139, 92, 246, 0.15)", "border_color": "rgba(139, 92, 246, 0.3)"},
                padding="3",
                border_radius="xl",
                width="100%",
                transition="all 0.3s ease",
                border="1px solid rgba(255, 255, 255, 0.05)"
            ),
            spacing="3",
            width="100%",
            margin_bottom="6"
        ),
        
        # System status
        system_status_panel(),
        
        spacing="4",
        width="280px",
        height="100vh",
        padding="4",
        border_right="1px solid",
        border_color="rgba(255, 255, 255, 0.08)",
        # Glass morphism sidebar
        bg="rgba(255, 255, 255, 0.03)",
        backdrop_filter="blur(20px)",
        box_shadow="inset 0 1px 0 rgba(255, 255, 255, 0.1)",
        overflow_y="auto"
    )

def main_layout(page_content: rx.Component) -> rx.Component:
    """Main application layout with glass morphism."""
    return rx.hstack(
        sidebar_component(),
        rx.vstack(
            header_component(),
            rx.box(
                page_content,
                width="100%",
                height="calc(100vh - 80px)",
                overflow="auto",
                padding="6",
                # Glass morphism main content
                bg="rgba(255, 255, 255, 0.06)",
                backdrop_filter="blur(25px)",
                border_radius="2xl",
                margin="4",
                border="1px solid rgba(255, 255, 255, 0.1)",
                box_shadow="""
                    0 8px 32px rgba(0, 0, 0, 0.4),
                    inset 0 1px 0 rgba(255, 255, 255, 0.15)
                """
            ),
            spacing="0",
            width="100%"
        ),
        height="100vh",
        spacing="0",
        width="100%"
    )