"""System status sidebar component."""

import reflex as rx
from ...state.app_state import AppState

def system_status_panel() -> rx.Component:
    """Display system health status with glass morphism."""
    return rx.vstack(
        rx.heading("System Status", size="5", color="gray.100"),
        
        # Health indicators
        rx.vstack(
            # LLM Status
            rx.hstack(
                rx.box(
                    width="10px",
                    height="10px",
                    border_radius="50%",
                    bg=rx.cond(
                        AppState.llm_healthy,
                        "#10b981",  # Emerald green
                        "#f87171"   # Rose red
                    ),
                    box_shadow=rx.cond(
                        AppState.llm_healthy,
                        "0 0 12px rgba(16, 185, 129, 0.6)",
                        "0 0 12px rgba(248, 113, 113, 0.6)"
                    ),
                    margin_right="10px"
                ),
                rx.text("LLM Server", font_size="14px", color="gray.200"),
                rx.spacer(),
                rx.text(
                    AppState.llm_status_text,
                    font_size="12px",
                    color="gray.300",
                    font_weight="500"
                ),
                width="100%",
                align="center"
            ),
            
            # Vector DB Status
            rx.hstack(
                rx.box(
                    width="10px",
                    height="10px",
                    border_radius="50%",
                    bg=rx.cond(
                        AppState.vector_db_healthy,
                        "#10b981",  # Emerald green
                        "#f87171"   # Rose red
                    ),
                    box_shadow=rx.cond(
                        AppState.vector_db_healthy,
                        "0 0 12px rgba(16, 185, 129, 0.6)",
                        "0 0 12px rgba(248, 113, 113, 0.6)"
                    ),
                    margin_right="10px"
                ),
                rx.text("Vector DB", font_size="14px", color="gray.200"),
                rx.spacer(),
                rx.text(
                    AppState.vector_db_status_text,
                    font_size="12px",
                    color="gray.300",
                    font_weight="500"
                ),
                width="100%",
                align="center"
            ),
            
            # Embeddings Status
            rx.hstack(
                rx.box(
                    width="10px",
                    height="10px",
                    border_radius="50%",
                    bg=rx.cond(
                        AppState.embeddings_healthy,
                        "#10b981",  # Emerald green
                        "#f87171"   # Rose red
                    ),
                    box_shadow=rx.cond(
                        AppState.embeddings_healthy,
                        "0 0 12px rgba(16, 185, 129, 0.6)",
                        "0 0 12px rgba(248, 113, 113, 0.6)"
                    ),
                    margin_right="10px"
                ),
                rx.text("Embeddings", font_size="14px", color="gray.200"),
                rx.spacer(),
                rx.text(
                    AppState.embeddings_status_text,
                    font_size="12px",
                    color="gray.300",
                    font_weight="500"
                ),
                width="100%",
                align="center"
            ),
            
            spacing="4",
            width="100%"
        ),
        
        # Refresh button
        rx.button(
            rx.cond(
                AppState.is_checking_health,
                rx.spinner(size="2"),
                "Refresh Status"
            ),
            on_click=AppState.check_health,
            size="2",
            variant="outline",
            width="100%",
            disabled=AppState.is_checking_health,
            color_scheme="violet",
            _hover={"bg": "rgba(139, 92, 246, 0.15)"},
            border_color="rgba(255, 255, 255, 0.1)"
        ),
        
        spacing="5",
        padding="5",
        border="1px solid",
        border_color="rgba(255, 255, 255, 0.08)",
        border_radius="xl",
        width="100%",
        # Glass morphism status panel
        bg="rgba(255, 255, 255, 0.04)",
        backdrop_filter="blur(15px)",
        box_shadow="inset 0 1px 0 rgba(255, 255, 255, 0.1)"
    )