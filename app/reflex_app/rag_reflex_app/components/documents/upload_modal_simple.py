"""Simplified upload modal component for document uploads."""

import reflex as rx
from ...state.document_state import DocumentState


def upload_button() -> rx.Component:
    """Simple upload button that toggles modal."""
    return rx.button(
        rx.icon("upload", size=16),
        "Upload Documents", 
        color_scheme="blue",
        size="3",
        on_click=DocumentState.toggle_upload_modal
    )


def upload_modal() -> rx.Component:
    """Simplified document upload modal."""
    return rx.box(
        # Upload button
        upload_button(),
        
        # Modal overlay
        rx.cond(
            DocumentState.show_upload_modal,
            rx.box(
                # Backdrop
                rx.box(
                    position="fixed",
                    top="0",
                    left="0",
                    right="0",
                    bottom="0",
                    background="rgba(0, 0, 0, 0.7)",
                    z_index="998",
                    on_click=DocumentState.toggle_upload_modal
                ),
                
                # Modal content
                rx.box(
                    rx.vstack(
                        # Header
                        rx.hstack(
                            rx.hstack(
                                rx.icon("upload", size=20, color="blue.400"),
                                rx.text(
                                    "Upload Documents",
                                    font_size="18px",
                                    font_weight="600"
                                ),
                                spacing="2",
                                align="center"
                            ),
                            rx.button(
                                rx.icon("x", size=16),
                                on_click=DocumentState.toggle_upload_modal,
                                variant="ghost",
                                color_scheme="gray",
                                size="2"
                            ),
                            width="100%",
                            justify="between",
                            align="center"
                        ),
                        
                        rx.divider(color="rgba(255, 255, 255, 0.1)"),
                        
                        # Upload area
                        rx.box(
                            rx.vstack(
                                rx.icon("cloud-upload", size=48, color="blue.400"),
                                rx.text(
                                    "Drag and drop files here",
                                    font_size="16px",
                                    font_weight="500"
                                ),
                                rx.text(
                                    "or click to browse",
                                    font_size="14px",
                                    color="gray.400"
                                ),
                                rx.button(
                                    "Select Files (Coming Soon)",
                                    color_scheme="blue",
                                    size="3",
                                    disabled=True
                                ),
                                spacing="3",
                                align="center"
                            ),
                            width="100%",
                            padding="8"
                        ),
                        
                        # Status messages
                        rx.cond(
                            DocumentState.upload_status != "",
                            rx.text(
                                DocumentState.upload_status,
                                color="green.400",
                                font_size="14px"
                            )
                        ),
                        
                        spacing="4",
                        width="100%",
                        padding="6"
                    ),
                    position="fixed",
                    top="50%",
                    left="50%",
                    transform="translate(-50%, -50%)",
                    background="rgba(20, 25, 35, 0.95)",
                    border="1px solid rgba(255, 255, 255, 0.1)",
                    border_radius="12px",
                    box_shadow="0 20px 25px -5px rgba(0, 0, 0, 0.5)",
                    width="500px",
                    max_width="90vw",
                    z_index="999"
                )
            )
        )
    )