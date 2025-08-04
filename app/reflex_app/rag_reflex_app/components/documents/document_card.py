"""Document card component for displaying individual documents."""

import reflex as rx
from ...state.document_state import DocumentState, DocumentInfo

def status_badge(status: str) -> rx.Component:
    """Status badge for document processing state."""
    color_map = {
        "ready": "green",
        "processing": "blue", 
        "error": "red"
    }
    
    icon_map = {
        "ready": "check-circle",
        "processing": "clock",
        "error": "alert-circle"
    }
    
    return rx.badge(
        rx.icon(icon_map.get(status, "circle-help"), size=12),
        status.title(),
        color_scheme=color_map.get(status, "gray"),
        variant="outline",
        size="1"
    )

def document_actions(doc: DocumentInfo) -> rx.Component:
    """Action buttons for document operations."""
    return rx.hstack(
        rx.button(
            rx.icon("eye", size=14),
            size="1",
            variant="ghost",
            color_scheme="blue",
            title="View document details"
        ),
        rx.button(
            rx.icon("trash-2", size=14),
            size="1",
            variant="ghost",
            color_scheme="red",
            title="Delete document",
            on_click=lambda: DocumentState.delete_single_document(doc.doc_id)
        ),
        spacing="1"
    )

def document_card(doc: DocumentInfo) -> rx.Component:
    """Individual document card component."""
    return rx.box(
        rx.hstack(
            # Selection checkbox
            rx.checkbox(
                on_change=lambda _: DocumentState.toggle_document_selection(doc.doc_id),
                color_scheme="blue"
            ),
            
            # Document icon and info
            rx.hstack(
                rx.icon("file-text", size=20, color="blue.400"),
                rx.vstack(
                    rx.hstack(
                        rx.text(
                            doc.title,
                            font_weight="600",
                            color="white",
                            font_size="16px"
                        ),
                        status_badge(doc.status),
                        spacing="2",
                        align="center"
                    ),
                    rx.hstack(
                        rx.text(
                            f"Type: {doc.file_type.upper()}",
                            font_size="14px",
                            color="gray.400"
                        ),
                        rx.text("•", color="gray.500"),
                        rx.text(
                            f"Size: {DocumentState.format_file_size(doc.file_size)}",
                            font_size="14px",
                            color="gray.400"
                        ),
                        rx.text("•", color="gray.500"),
                        rx.text(
                            f"Chunks: {doc.chunk_count}",
                            font_size="14px",
                            color="gray.400"
                        ),
                        spacing="2",
                        align="center"
                    ),
                    rx.text(
                        f"Uploaded: {DocumentState.format_upload_date(doc.upload_date)}",
                        font_size="12px",
                        color="gray.500"
                    ),
                    align="start",
                    spacing="1"
                ),
                spacing="3",
                align="center",
                flex="1"
            ),
            
            # Actions
            document_actions(doc),
            
            width="100%",
            align="center",
            justify="between"
        ),
        
        # Error message for failed documents
        rx.cond(
            doc.status == "error",
            rx.box(
                rx.hstack(
                    rx.icon("triangle-alert", size=14, color="red.400"),
                    rx.text(
                        rx.cond(
                            doc.error_message != "",
                            doc.error_message,
                            "Processing failed"
                        ),
                        font_size="14px",
                        color="red.400"
                    ),
                    spacing="2",
                    align="center"
                ),
                padding="3",
                margin_top="3",
                bg="rgba(248, 113, 113, 0.1)",
                border="1px solid",
                border_color="rgba(248, 113, 113, 0.3)",
                border_radius="md"
            ),
            rx.fragment()
        ),
        
        padding="4",
        bg="rgba(255, 255, 255, 0.04)",
        border="1px solid",
        border_color="rgba(255, 255, 255, 0.1)",
        border_radius="lg",
        backdrop_filter="blur(15px)",
        _hover={
            "bg": "rgba(255, 255, 255, 0.06)",
            "border_color": "rgba(255, 255, 255, 0.2)"
        },
        transition="all 0.2s ease",
        width="100%"
    )

def empty_state() -> rx.Component:
    """Empty state when no documents are available."""
    return rx.center(
        rx.vstack(
            rx.icon("folder-open", size=64, color="gray.500"),
            rx.heading("No documents found", size="4", color="gray.300"),
            rx.text(
                "Upload your first document to get started",
                font_size="16px",
                color="gray.400",
                text_align="center"
            ),
            rx.box(height="4"),
            rx.button(
                rx.icon("upload", size=16),
                "Upload Documents",
                color_scheme="blue",
                size="3",
                on_click=DocumentState.open_upload_modal
            ),
            spacing="4",
            align="center",
            padding="8"
        ),
        height="400px",
        width="100%"
    )

def loading_skeleton() -> rx.Component:
    """Loading skeleton for document cards."""
    return rx.vstack(
        *[
            rx.box(
                rx.hstack(
                    rx.skeleton(width="20px", height="20px", border_radius="md"),
                    rx.hstack(
                        rx.skeleton(width="20px", height="20px", border_radius="md"),
                        rx.vstack(
                            rx.skeleton(width="200px", height="16px", border_radius="md"),
                            rx.skeleton(width="150px", height="12px", border_radius="md"),
                            rx.skeleton(width="120px", height="10px", border_radius="md"),
                            spacing="2",
                            align="start"
                        ),
                        spacing="3",
                        align="center",
                        flex="1"
                    ),
                    rx.skeleton(width="60px", height="24px", border_radius="md"),
                    width="100%",
                    align="center",
                    justify="between"
                ),
                padding="4",
                bg="rgba(255, 255, 255, 0.04)",
                border="1px solid",
                border_color="rgba(255, 255, 255, 0.1)",
                border_radius="lg",
                width="100%"
            )
            for _ in range(3)
        ],
        spacing="3",
        width="100%"
    )