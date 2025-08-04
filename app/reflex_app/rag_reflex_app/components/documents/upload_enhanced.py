"""Enhanced document upload component with drag-and-drop functionality."""

import reflex as rx
from ...state.document_state import DocumentState


def upload_progress_item(progress_info) -> rx.Component:
    """Individual upload progress item."""
    return rx.box(
        rx.vstack(
            # Filename and status
            rx.hstack(
                rx.text(
                    progress_info.filename,
                    font_size="14px",
                    font_weight="500",
                    color="white"
                ),
                rx.spacer(),
                rx.badge(
                    progress_info.status.title(),
                    color_scheme=rx.cond(
                        progress_info.status == "completed",
                        "green",
                        rx.cond(
                            progress_info.status == "error",
                            "red",
                            "blue"
                        )
                    ),
                    size="1"
                ),
                width="100%",
                align="center"
            ),
            
            # Progress bar
            rx.cond(
                progress_info.status != "completed",
                rx.box(
                    rx.box(
                        width=f"{progress_info.progress}%",
                        height="4px",
                        background="blue.400",
                        border_radius="2px",
                        transition="width 0.3s ease"
                    ),
                    width="100%",
                    height="4px",
                    background="rgba(255, 255, 255, 0.1)",
                    border_radius="2px",
                    overflow="hidden"
                )
            ),
            
            # Error message
            rx.cond(
                progress_info.status == "error",
                rx.text(
                    rx.cond(
                        progress_info.error_message != "",
                        progress_info.error_message,
                        "Upload failed"
                    ),
                    font_size="12px",
                    color="red.400"
                )
            ),
            
            spacing="2",
            width="100%"
        ),
        padding="3",
        background="rgba(255, 255, 255, 0.05)",
        border="1px solid rgba(255, 255, 255, 0.1)",
        border_radius="8px",
        width="100%"
    )


def upload_drop_zone() -> rx.Component:
    """Drag and drop upload zone."""
    return rx.box(
        rx.upload(
            rx.vstack(
                rx.icon("cloud-upload", size=48, color="blue.400"),
                rx.text(
                    "Drag and drop files here",
                    font_size="18px",
                    font_weight="600",
                    color="white"
                ),
                rx.text(
                    "or click to browse for files",
                    font_size="14px",
                    color="gray.400"
                ),
                rx.text(
                    "Supports: .txt, .md files (max 10MB each)",
                    font_size="12px",
                    color="gray.500"
                ),
                spacing="3",
                align="center"
            ),
            id="document-upload",
            multiple=True,
            accept={
                "text/plain": [".txt"],
                "text/markdown": [".md"]
            },
            max_files=10,
            max_size=10 * 1024 * 1024,  # 10MB
            on_upload=DocumentState.handle_file_upload
        ),
        border="2px dashed rgba(59, 130, 246, 0.5)",
        background="rgba(59, 130, 246, 0.02)",
        border_radius="12px",
        padding="12",
        cursor="pointer",
        width="100%",
        min_height="200px",
        display="flex",
        align_items="center",
        justify_content="center",
        transition="all 0.2s ease",
        _hover={
            "border_color": "rgba(59, 130, 246, 0.8)",
            "background": "rgba(59, 130, 246, 0.05)"
        },
        _active={
            "border_color": "rgba(59, 130, 246, 1.0)",
            "background": "rgba(59, 130, 246, 0.1)"
        }
    )


def upload_modal_enhanced() -> rx.Component:
    """Enhanced document upload modal with progress tracking."""
    return rx.box(
        # Upload trigger button
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
                        
                        # Upload drop zone
                        upload_drop_zone(),
                        
                        # Active uploads progress
                        rx.cond(
                            DocumentState.uploading_files.length() > 0,
                            rx.vstack(
                                rx.divider(color="rgba(255, 255, 255, 0.1)"),
                                
                                rx.hstack(
                                    rx.icon("activity", size=16, color="blue.400"),
                                    rx.text(
                                        "Upload Progress",
                                        font_size="16px",
                                        font_weight="600",
                                        color="white"
                                    ),
                                    spacing="2",
                                    align="center"
                                ),
                                
                                rx.vstack(
                                    rx.foreach(
                                        DocumentState.uploading_files,
                                        upload_progress_item
                                    ),
                                    spacing="2",
                                    width="100%"
                                ),
                                
                                spacing="4",
                                width="100%"
                            )
                        ),
                        
                        # Upload instructions and tips
                        rx.cond(
                            DocumentState.uploading_files.length() == 0,
                            rx.box(
                                rx.vstack(
                                    rx.text(
                                        "💡 Tips for better results:",
                                        font_size="14px",
                                        font_weight="600",
                                        color="gray.300"
                                    ),
                                    rx.vstack(
                                        rx.text("• Use clear, well-formatted text files", font_size="12px", color="gray.400"),
                                        rx.text("• Break up very long documents into chapters", font_size="12px", color="gray.400"),
                                        rx.text("• Ensure proper encoding (UTF-8 recommended)", font_size="12px", color="gray.400"),
                                        spacing="1",
                                        align="start"
                                    ),
                                    spacing="2",
                                    align="start"
                                ),
                                padding="4",
                                background="rgba(255, 255, 255, 0.02)",
                                border="1px solid rgba(255, 255, 255, 0.05)",
                                border_radius="8px",
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
                            rx.cond(
                                DocumentState.uploading_files.length() > 0,
                                rx.button(
                                    "Clear Completed",
                                    on_click=DocumentState.clear_completed_uploads,
                                    variant="soft",
                                    color_scheme="blue",
                                    size="3"
                                )
                            ),
                            width="100%",
                            justify="end",
                            spacing="3"
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
                    width="600px",
                    max_width="90vw",
                    max_height="80vh",
                    overflow_y="auto",
                    z_index="999"
                )
            )
        )
    )