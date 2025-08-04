"""Document upload modal component with drag-and-drop functionality."""

import reflex as rx
from ...state.document_state import DocumentState

def upload_progress_bar(filename: str, progress: float, status: str, error_message: str = "") -> rx.Component:
    """Individual upload progress bar."""
    return rx.vstack(
        rx.hstack(
            rx.text(filename, font_size="14px", color="white", font_weight="500"),
            rx.spacer(),
            rx.cond(
                status == "completed",
                rx.icon("check", size=16, color="green.400"),
                rx.cond(
                    status == "error",
                    rx.icon("x", size=16, color="red.400"),
                    rx.cond(
                        status == "uploading",
                        rx.spinner(size="2"),
                        rx.icon("clock", size=16, color="blue.400")
                    )
                )
            ),
            width="100%",
            align="center"
        ),
        rx.progress(
            value=progress,
            max=100,
            width="100%",
            height="6px",
            color_scheme=rx.cond(
                status == "completed", 
                "green",
                rx.cond(status == "error", "red", "blue")
            )
        ),
        rx.cond(
            error_message != "",
            rx.text(
                error_message,
                font_size="12px",
                color="red.400",
                font_style="italic"
            ),
            rx.fragment()
        ),
        spacing="2",
        width="100%"
    )

def drag_drop_zone() -> rx.Component:
    """Drag and drop upload zone."""
    return rx.box(
        rx.vstack(
            rx.icon("upload-cloud", size=48, color="blue.400"),
            rx.heading("Drop files here", size="4", color="white"),
            rx.text(
                "or click to select files",
                font_size="16px",
                color="gray.300",
                text_align="center"
            ),
            rx.text(
                "Supported formats: TXT files up to 10MB",
                font_size="14px",
                color="gray.400",
                text_align="center"
            ),
            spacing="3",
            align="center"
        ),
        padding="8",
        border="2px dashed",
        border_color="rgba(59, 130, 246, 0.4)",
        border_radius="lg",
        bg="rgba(59, 130, 246, 0.05)",
        backdrop_filter="blur(10px)",
        cursor="pointer",
        _hover={
            "border_color": "rgba(59, 130, 246, 0.6)",
            "bg": "rgba(59, 130, 246, 0.1)"
        },
        transition="all 0.2s ease",
        width="100%",
        min_height="200px",
        display="flex",
        align_items="center",
        justify_content="center"
    )

def upload_modal() -> rx.Component:
    """Document upload modal with drag-and-drop support."""
    return rx.dialog(
        rx.dialog_trigger(
            rx.button(
                rx.icon("upload", size=16),
                "Upload Documents",
                color_scheme="blue",
                size="3"
            )
        ),
        rx.dialog_content(
            rx.dialog_title(
                rx.hstack(
                    rx.icon("upload", size=20, color="blue.400"),
                    "Upload Documents",
                    spacing="2",
                    align="center"
                )
            ),
            rx.dialog_description(
                "Upload text documents to add them to your RAG system",
                color="gray.300"
            ),
            
            # Upload zone
            rx.vstack(
                # File input (hidden, triggered by drag-drop zone)
                rx.upload(
                    drag_drop_zone(),
                    id="document-upload",
                    multiple=True,
                    accept={
                        "text/plain": [".txt"],
                        "text/markdown": [".md"]
                    },
                    max_files=10,
                    max_size=10 * 1024 * 1024,  # 10MB
                    on_upload=DocumentState.handle_file_upload,
                    border="none",
                    width="100%"
                ),
                
                # Progress indicators
                rx.cond(
                    DocumentState.uploading_files.length() > 0,
                    rx.vstack(
                        rx.divider(color="rgba(255, 255, 255, 0.1)"),
                        rx.text("Upload Progress", font_weight="bold", color="white"),
                        rx.foreach(
                            DocumentState.uploading_files,
                            lambda progress: upload_progress_bar(
                                progress.filename,
                                progress.progress,
                                progress.status,
                                progress.error_message
                            )
                        ),
                        spacing="3",
                        width="100%"
                    ),
                    rx.fragment()
                ),
                
                # Error display
                rx.cond(
                    DocumentState.show_error,
                    rx.box(
                        rx.hstack(
                            rx.icon("alert-triangle", size=16, color="red.400"),
                            rx.text("Error:", font_weight="bold", color="red.400"),
                            rx.text(DocumentState.error_message, color="red.400"),
                            spacing="2",
                            align="center"
                        ),
                        padding="3",
                        bg="rgba(248, 113, 113, 0.1)",
                        border="1px solid",
                        border_color="rgba(248, 113, 113, 0.3)",
                        border_radius="md"
                    ),
                    rx.fragment()
                ),
                
                spacing="4",
                width="100%"
            ),
            
            # Footer with actions
            rx.hstack(
                rx.dialog_close(
                    rx.button(
                        "Cancel",
                        variant="outline",
                        color_scheme="gray"
                    )
                ),
                rx.button(
                    "Clear All",
                    variant="outline",
                    color_scheme="red",
                    on_click=lambda: DocumentState.set_upload_progress({})
                ),
                rx.dialog_close(
                    rx.button(
                        "Done",
                        color_scheme="blue",
                        on_click=DocumentState.close_upload_modal
                    )
                ),
                spacing="3",
                justify="end",
                width="100%"
            ),
            
            max_width="500px",
            padding="6",
            bg="rgba(15, 15, 35, 0.95)",
            backdrop_filter="blur(20px)",
            border="1px solid",
            border_color="rgba(255, 255, 255, 0.1)",
            border_radius="xl"
        ),
        open=DocumentState.is_upload_modal_open,
        on_open_change=DocumentState.set_is_upload_modal_open
    )

def upload_button() -> rx.Component:
    """Simple upload button that opens the modal."""
    return rx.button(
        rx.icon("upload", size=16),
        "Upload Documents",
        color_scheme="blue",
        size="3",
        on_click=DocumentState.open_upload_modal
    )