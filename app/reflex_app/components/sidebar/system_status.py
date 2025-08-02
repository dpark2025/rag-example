"""System status sidebar component."""

import reflex as rx
from ...state.app_state import AppState

def system_status_panel() -> rx.Component:
    """Display system health status."""
    return rx.vstack(
        rx.heading("System Status", size="md", color="gray.700"),
        
        # Health indicators
        rx.vstack(
            # LLM Status
            rx.hstack(
                rx.circle(
                    size="8px",
                    bg=rx.cond(
                        AppState.health_status.get("llm", {}).get("healthy", False),
                        "green.500",
                        "red.500"
                    )
                ),
                rx.text("LLM Server", font_size="sm"),
                rx.spacer(),
                rx.text(
                    rx.cond(
                        AppState.health_status.get("llm", {}).get("healthy", False),
                        "Online",
                        "Offline"
                    ),
                    font_size="xs",
                    color="gray.600"
                ),
                width="100%",
                align="center"
            ),
            
            # Vector DB Status
            rx.hstack(
                rx.circle(
                    size="8px",
                    bg=rx.cond(
                        AppState.health_status.get("vector_db", {}).get("healthy", False),
                        "green.500",
                        "red.500"
                    )
                ),
                rx.text("Vector DB", font_size="sm"),
                rx.spacer(),
                rx.text(
                    rx.cond(
                        AppState.health_status.get("vector_db", {}).get("healthy", False),
                        "Online",
                        "Offline"
                    ),
                    font_size="xs",
                    color="gray.600"
                ),
                width="100%",
                align="center"
            ),
            
            # Embeddings Status
            rx.hstack(
                rx.circle(
                    size="8px",
                    bg=rx.cond(
                        AppState.health_status.get("embeddings", {}).get("healthy", False),
                        "green.500",
                        "red.500"
                    )
                ),
                rx.text("Embeddings", font_size="sm"),
                rx.spacer(),
                rx.text(
                    rx.cond(
                        AppState.health_status.get("embeddings", {}).get("healthy", False),
                        "Online",
                        "Offline"
                    ),
                    font_size="xs",
                    color="gray.600"
                ),
                width="100%",
                align="center"
            ),
            
            spacing="3",
            width="100%"
        ),
        
        # Refresh button
        rx.button(
            rx.cond(
                AppState.is_checking_health,
                rx.spinner(size="sm"),
                "Refresh Status"
            ),
            on_click=AppState.check_health,
            size="sm",
            variant="outline",
            width="100%",
            disabled=AppState.is_checking_health
        ),
        
        spacing="4",
        padding="4",
        border="1px solid",
        border_color="gray.200",
        border_radius="md",
        width="100%"
    )