"""
Document card component for displaying individual documents with Phase 5 UX integration.

Authored by: AI/ML Engineer (Jackson Brown)
Date: 2025-08-04
"""

import reflex as rx
from typing import Dict, Any
from ...state.document_state import DocumentState, DocumentInfo
from ..common.responsive_design import ResponsiveState, responsive_container, mobile_optimized
from ..common.accessibility import accessible_button, aria_live_region, focus_trap
from ..common.error_boundary import error_display
from ..common.performance_optimizer import optimized_render
from .file_validator import FileValidator


def status_badge(status: str) -> rx.Component:
    """Status badge for document processing state with accessibility."""
    status_config = {
        "ready": {
            "icon": "check-circle",
            "color": "green",
            "label": "Ready for queries",
            "text": "Ready"
        },
        "processing": {
            "icon": "clock",
            "color": "blue", 
            "label": "Processing document",
            "text": "Processing"
        },
        "error": {
            "icon": "alert-circle",
            "color": "red",
            "label": "Processing failed",
            "text": "Error"
        }
    }
    
    config = status_config.get(status, status_config["error"])
    
    return rx.badge(
        rx.icon(config["icon"], size=12, aria_hidden="true"),
        config["text"],
        color_scheme=config["color"],
        variant="outline",
        size="1",
        aria_label=config["label"],
        title=config["label"]
    )


def file_type_icon(file_type: str) -> rx.Component:
    """File type icon with accessibility."""
    icon_map = {
        'txt': 'file-text',
        'md': 'file-text',
        'pdf': 'file',
        'doc': 'file-text',
        'docx': 'file-text',
        'html': 'code',
        'json': 'code',
        'csv': 'table',
        'xml': 'code'
    }
    
    icon = icon_map.get(file_type.lower(), 'file')
    
    return rx.icon(
        icon,
        size=16,
        color="blue.400",
        aria_label=f"{file_type.upper()} file",
        title=f"{file_type.upper()} document"
    )


def document_metadata(doc: DocumentInfo) -> rx.Component:
    """Document metadata display with responsive layout."""
    return rx.vstack(
        # Primary metadata row
        rx.hstack(
            file_type_icon(doc.file_type),
            rx.text(
                doc.title,
                font_weight="600",
                font_size=mobile_optimized("14px", "16px"),
                color="white",
                overflow="hidden",
                text_overflow="ellipsis",
                white_space="nowrap",
                flex="1"
            ),
            status_badge(doc.status),
            width="100%",
            align="center",
            spacing="2"
        ),
        
        # Secondary metadata - responsive layout
        rx.cond(
            ResponsiveState.is_mobile,
            # Mobile: stacked layout
            rx.vstack(
                rx.text(
                    f"{doc.chunk_count} chunks",
                    font_size="12px",
                    color="gray.400"
                ),
                rx.text(
                    FileValidator.format_file_size(doc.file_size),
                    font_size="12px",
                    color="gray.400"
                ),
                rx.text(
                    doc.upload_date,
                    font_size="12px",
                    color="gray.400"
                ),
                spacing="1",
                align="start",
                width="100%"
            ),
            # Desktop: horizontal layout
            rx.hstack(
                rx.hstack(
                    rx.icon("layers", size=12, color="gray.500"),
                    rx.text(
                        f"{doc.chunk_count} chunks",
                        font_size="12px",
                        color="gray.400"
                    ),
                    spacing="1",
                    align="center"
                ),
                rx.hstack(
                    rx.icon("hard-drive", size=12, color="gray.500"),
                    rx.text(
                        FileValidator.format_file_size(doc.file_size),
                        font_size="12px",
                        color="gray.400"
                    ),
                    spacing="1",
                    align="center"
                ),
                rx.hstack(
                    rx.icon("calendar", size=12, color="gray.500"),
                    rx.text(
                        doc.upload_date,
                        font_size="12px",
                        color="gray.400"
                    ),
                    spacing="1",
                    align="center"
                ),
                spacing="4",
                align="center",
                width="100%"
            )
        ),
        
        # Error message if present
        rx.cond(
            doc.error_message != "",
            rx.hstack(
                rx.icon("alert-triangle", size=12, color="red.400"),
                rx.text(
                    doc.error_message,
                    font_size="11px",
                    color="red.400",
                    font_style="italic",
                    overflow="hidden",
                    text_overflow="ellipsis"
                ),
                spacing="2",
                align="center",
                width="100%",
                role="alert"
            ),
            rx.fragment()
        ),
        
        spacing="2",
        align="start",
        width="100%"
    )


def document_actions(doc: DocumentInfo) -> rx.Component:
    """Action buttons for document operations with accessibility."""
    return rx.hstack(
        # View document details
        accessible_button(
            rx.icon("eye", size=14),
            variant="ghost",
            color_scheme="blue",
            size="1",
            on_click=lambda: DocumentState.view_document_details(doc.doc_id),
            aria_label=f"View details for {doc.title}",
            title="View document details"
        ),
        
        # Download document (if available)
        rx.cond(
            doc.status == "ready",
            accessible_button(
                rx.icon("download", size=14),
                variant="ghost",
                color_scheme="gray",
                size="1",
                on_click=lambda: DocumentState.download_document(doc.doc_id),
                aria_label=f"Download {doc.title}",
                title="Download document"
            ),
            rx.fragment()
        ),
        
        # Delete document with confirmation
        accessible_button(
            rx.icon("trash-2", size=14),
            variant="ghost",
            color_scheme="red",
            size="1",
            on_click=lambda: DocumentState.confirm_delete_document(doc.doc_id),
            aria_label=f"Delete {doc.title}",
            title="Delete document"
        ),
        
        spacing="1",
        align="center"
    )


def selection_checkbox(doc: DocumentInfo) -> rx.Component:
    """Document selection checkbox with accessibility."""
    return rx.checkbox(
        checked=DocumentState.selected_documents.contains(doc.doc_id),
        on_change=lambda checked: DocumentState.toggle_document_selection(doc.doc_id, checked),
        color_scheme="blue",
        size="2",
        aria_label=f"Select {doc.title}",
        title=f"Select {doc.title}"
    )


@optimized_render
def document_card(doc: DocumentInfo) -> rx.Component:
    """Individual document card component with Phase 5 UX integration."""
    return rx.box(
        rx.hstack(
            # Selection checkbox - responsive positioning
            rx.cond(
                DocumentState.selection_mode,
                selection_checkbox(doc),
                rx.fragment()
            ),
            
            # Main content area
            rx.vstack(
                document_metadata(doc),
                spacing="2",
                align="start",
                flex="1",
                width="100%"
            ),
            
            # Actions - responsive layout
            rx.cond(
                ResponsiveState.is_mobile,
                # Mobile: single menu button
                accessible_button(
                    rx.icon("more-vertical", size=16),
                    variant="ghost",
                    color_scheme="gray",
                    size="2",
                    on_click=lambda: DocumentState.show_document_menu(doc.doc_id),
                    aria_label=f"Actions for {doc.title}",
                    title="Document actions"
                ),
                # Desktop: full action buttons
                document_actions(doc)
            ),
            
            spacing="3",
            align="start",
            width="100%",
            padding=mobile_optimized("3", "4")
        ),
        
        # Card styling with interaction states
        bg="rgba(255, 255, 255, 0.02)",
        border="1px solid",
        border_color="rgba(255, 255, 255, 0.1)",
        border_radius="lg",
        width="100%",
        cursor="pointer",
        
        # Interactive states
        _hover={
            "bg": "rgba(255, 255, 255, 0.05)",
            "border_color": "rgba(59, 130, 246, 0.3)",
            "transform": "translateY(-1px)"
        },
        
        _focus_within={
            "outline": "2px solid",
            "outline_color": "rgba(59, 130, 246, 0.5)",
            "outline_offset": "2px"
        },
        
        # Accessibility
        role="article",
        aria_label=f"Document: {doc.title}",
        tabindex="0",
        
        # Smooth transitions
        transition="all 0.2s ease",
        
        # Selection state styling
        style={
            "border_color": rx.cond(
                DocumentState.selected_documents.contains(doc.doc_id),
                "rgba(59, 130, 246, 0.5)",
                "rgba(255, 255, 255, 0.1)"
            ),
            "bg": rx.cond(
                DocumentState.selected_documents.contains(doc.doc_id),
                "rgba(59, 130, 246, 0.05)",
                "rgba(255, 255, 255, 0.02)"
            )
        }
    )


def empty_state() -> rx.Component:
    """Empty state when no documents are available."""
    return responsive_container(
        rx.vstack(
            rx.icon(
                "file-plus",
                size=mobile_optimized(48, 64),
                color="gray.500",
                aria_hidden="true"
            ),
            
            rx.heading(
                "No documents yet",
                size=mobile_optimized("4", "5"),
                color="gray.300",
                text_align="center"
            ),
            
            rx.text(
                "Upload your first document to get started with RAG queries",
                font_size=mobile_optimized("14px", "16px"),
                color="gray.400",
                text_align="center",
                max_width="400px"
            ),
            
            # Import upload button
            rx.box(
                accessible_button(
                    rx.icon("upload", size=16),
                    "Upload Documents",
                    color_scheme="blue",
                    size="3",
                    on_click=DocumentState.open_upload_modal,
                    aria_label="Upload your first documents"
                ),
                margin_top="4"
            ),
            
            spacing=mobile_optimized("4", "6"),
            align="center",
            padding=mobile_optimized("8", "12"),
            width="100%"
        ),
        padding=mobile_optimized("4", "8")
    )


def loading_skeleton() -> rx.Component:
    """Loading skeleton for document cards."""
    return rx.box(
        rx.hstack(
            # Checkbox skeleton
            rx.box(
                width="16px",
                height="16px",
                bg="rgba(255, 255, 255, 0.1)",
                border_radius="sm"
            ),
            
            # Content skeleton
            rx.vstack(
                rx.hstack(
                    rx.box(
                        width="20px",
                        height="20px",
                        bg="rgba(255, 255, 255, 0.1)",
                        border_radius="sm"
                    ),
                    rx.box(
                        width="200px",
                        height="16px",
                        bg="rgba(255, 255, 255, 0.1)",
                        border_radius="sm"
                    ),
                    rx.box(
                        width="60px",
                        height="20px",
                        bg="rgba(255, 255, 255, 0.1)",
                        border_radius="sm"
                    ),
                    width="100%",
                    align="center",
                    spacing="2"
                ),
                
                rx.hstack(
                    rx.box(
                        width="80px",
                        height="12px",
                        bg="rgba(255, 255, 255, 0.1)",
                        border_radius="sm"
                    ),
                    rx.box(
                        width="60px",
                        height="12px",
                        bg="rgba(255, 255, 255, 0.1)",
                        border_radius="sm"
                    ),
                    rx.box(
                        width="100px",
                        height="12px",
                        bg="rgba(255, 255, 255, 0.1)",
                        border_radius="sm"
                    ),
                    spacing="4",
                    align="center"
                ),
                
                spacing="2",
                align="start",
                flex="1"
            ),
            
            # Actions skeleton
            rx.hstack(
                rx.box(
                    width="24px",
                    height="24px",
                    bg="rgba(255, 255, 255, 0.1)",
                    border_radius="sm"
                ),
                rx.box(
                    width="24px",
                    height="24px",
                    bg="rgba(255, 255, 255, 0.1)",
                    border_radius="sm"
                ),
                spacing="1"
            ),
            
            spacing="3",
            align="center",
            width="100%",
            padding="4"
        ),
        
        bg="rgba(255, 255, 255, 0.02)",
        border="1px solid",
        border_color="rgba(255, 255, 255, 0.1)",
        border_radius="lg",
        width="100%",
        
        # Shimmer animation
        position="relative",
        overflow="hidden",
        _before={
            "content": '""',
            "position": "absolute",
            "top": "0",
            "left": "-100%",
            "width": "100%",
            "height": "100%",
            "background": "linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)",
            "animation": "shimmer 2s infinite"
        }
    )


def document_details_modal(doc: DocumentInfo) -> rx.Component:
    """Document details modal with comprehensive information."""
    return rx.dialog(
        rx.dialog_content(
            focus_trap(
                rx.vstack(
                    # Header
                    rx.hstack(
                        file_type_icon(doc.file_type),
                        rx.text(
                            doc.title,
                            font_size="18px",
                            font_weight="bold",
                            color="white"
                        ),
                        status_badge(doc.status),
                        spacing="2",
                        align="center",
                        width="100%"
                    ),
                    
                    # Metadata grid
                    rx.grid(
                        rx.vstack(
                            rx.text("File Size", font_size="12px", color="gray.400"),
                            rx.text(
                                FileValidator.format_file_size(doc.file_size),
                                font_weight="500",
                                color="white"
                            ),
                            spacing="1"
                        ),
                        
                        rx.vstack(
                            rx.text("Chunks", font_size="12px", color="gray.400"),
                            rx.text(
                                str(doc.chunk_count),
                                font_weight="500",
                                color="white"
                            ),
                            spacing="1"
                        ),
                        
                        rx.vstack(
                            rx.text("Upload Date", font_size="12px", color="gray.400"),
                            rx.text(
                                doc.upload_date,
                                font_weight="500",
                                color="white"
                            ),
                            spacing="1"
                        ),
                        
                        rx.vstack(
                            rx.text("Status", font_size="12px", color="gray.400"),
                            status_badge(doc.status),
                            spacing="1"
                        ),
                        
                        columns=mobile_optimized(2, 4),
                        spacing="4",
                        width="100%"
                    ),
                    
                    # Error details if present
                    rx.cond(
                        doc.error_message != "",
                        rx.vstack(
                            rx.text(
                                "Error Details",
                                font_size="14px",
                                font_weight="bold",
                                color="red.400"
                            ),
                            rx.text(
                                doc.error_message,
                                font_size="14px",
                                color="red.400",
                                padding="3",
                                bg="rgba(248, 113, 113, 0.1)",
                                border="1px solid",
                                border_color="rgba(248, 113, 113, 0.3)",
                                border_radius="md",
                                width="100%"
                            ),
                            spacing="2",
                            width="100%"
                        ),
                        rx.fragment()
                    ),
                    
                    # Actions
                    rx.hstack(
                        accessible_button(
                            "Close",
                            variant="outline",
                            color_scheme="gray",
                            on_click=DocumentState.close_document_details
                        ),
                        
                        rx.cond(
                            doc.status == "ready",
                            accessible_button(
                                rx.icon("download", size=16),
                                "Download",
                                color_scheme="blue",
                                on_click=lambda: DocumentState.download_document(doc.doc_id)
                            ),
                            rx.fragment()
                        ),
                        
                        accessible_button(
                            rx.icon("trash-2", size=16),
                            "Delete",
                            color_scheme="red",
                            variant="outline",
                            on_click=lambda: DocumentState.confirm_delete_document(doc.doc_id)
                        ),
                        
                        spacing="3",
                        justify="end",
                        width="100%"
                    ),
                    
                    spacing="4",
                    width="100%"
                )
            ),
            
            max_width=mobile_optimized("95vw", "500px"),
            padding=mobile_optimized("4", "6"),
            bg="rgba(15, 15, 35, 0.95)",
            backdrop_filter="blur(20px)",
            border="1px solid",
            border_color="rgba(255, 255, 255, 0.1)",
            border_radius="xl"
        ),
        
        open=DocumentState.show_document_details,
        on_open_change=DocumentState.set_show_document_details
    )