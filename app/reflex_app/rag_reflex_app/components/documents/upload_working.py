"""Working document upload component."""

import reflex as rx
from ...state.document_state import DocumentState


def simple_upload() -> rx.Component:
    """Simple file upload component that works."""
    return rx.box(
        rx.button(
            rx.icon("upload", size=16),
            "Upload Documents",
            color_scheme="blue",
            size="3",
            on_click=DocumentState.toggle_upload_modal
        ),
        
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
                                    font_size="20px",
                                    font_weight="600",
                                    color="white"
                                ),
                                spacing="3",
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
                        
                        # Simple upload
                        rx.box(
                            rx.vstack(
                                rx.icon("cloud-upload", size=48, color="blue.400"),
                                rx.text(
                                    "Click to upload text files",
                                    font_size="18px",
                                    font_weight="600",
                                    color="white"
                                ),
                                rx.text(
                                    "Supports: .txt, .md files (max 10MB each)",
                                    font_size="12px",
                                    color="gray.400"
                                ),
                                rx.upload(
                                    rx.button(
                                        "Select Files",
                                        color_scheme="blue",
                                        size="3"
                                    ),
                                    id="file-upload",
                                    multiple=True,
                                    accept={
                                        "text/plain": [".txt"],
                                        "text/markdown": [".md"]
                                    },
                                    max_files=10,
                                    max_size=10 * 1024 * 1024,
                                    on_upload=DocumentState.handle_file_upload
                                ),
                                spacing="4",
                                align="center"
                            ),
                            border="2px dashed rgba(59, 130, 246, 0.3)",
                            background="rgba(59, 130, 246, 0.02)",
                            border_radius="12px",
                            padding="8",
                            width="100%",
                            min_height="250px",
                            display="flex",
                            align_items="center",
                            justify_content="center"
                        ),
                        
                        # Upload progress
                        rx.cond(
                            DocumentState.uploading_files.length() > 0,
                            rx.vstack(
                                rx.divider(color="rgba(255, 255, 255, 0.1)"),
                                rx.text(
                                    "Upload Progress",
                                    font_size="16px",
                                    font_weight="600",
                                    color="white"
                                ),
                                rx.vstack(
                                    rx.foreach(
                                        DocumentState.uploading_files,
                                        lambda progress: rx.text(
                                            f"{progress.filename}: {progress.status}",
                                            font_size="14px",
                                            color="gray.300"
                                        )
                                    ),
                                    spacing="2",
                                    width="100%"
                                ),
                                spacing="3",
                                width="100%"
                            )
                        ),
                        
                        # Actions
                        rx.hstack(
                            rx.button(
                                "Close",
                                on_click=DocumentState.toggle_upload_modal,
                                variant="soft",
                                color_scheme="gray",
                                size="3"
                            ),
                            width="100%",
                            justify="end"
                        ),
                        
                        spacing="6",
                        width="100%",
                        padding="6"
                    ),
                    position="fixed",
                    top="50%",
                    left="50%",
                    transform="translate(-50%, -50%)",
                    background="rgba(20, 25, 35, 0.98)",
                    border="1px solid rgba(255, 255, 255, 0.1)",
                    border_radius="16px",
                    box_shadow="0 20px 25px -5px rgba(0, 0, 0, 0.5)",
                    width="500px",
                    max_width="90vw",
                    max_height="80vh",
                    overflow_y="auto",
                    z_index="999"
                )
            )
        )
    )