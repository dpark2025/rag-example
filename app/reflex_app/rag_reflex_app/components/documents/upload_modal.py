"""
Document upload modal component with drag-and-drop functionality and Phase 5 UX integration.

Authored by: AI/ML Engineer (Jackson Brown)  
Date: 2025-08-04
"""

import reflex as rx
from typing import Dict, Any, List
from ...state.document_state import DocumentState
from ..common.responsive_design import ResponsiveState, responsive_container, mobile_optimized
from ..common.accessibility import accessible_button, focus_trap, live_region
from ..common.error_boundary import ErrorState, error_display
from ..common.performance_optimizer import optimized_render
from .file_validator import get_validation_summary, FileValidator


def upload_progress_bar(filename: str, progress: float, status: str, error_message: str = "") -> rx.Component:
    """Individual upload progress bar with accessibility and responsive design."""
    
    # Status icon with proper accessibility
    status_icon = rx.cond(
        status == "completed",
        rx.icon("circle-check", size=16, color="green.400", aria_label="Upload completed"),
        rx.cond(
            status == "error", 
            rx.icon("circle-alert", size=16, color="red.400", aria_label="Upload failed"),
            rx.cond(
                status == "uploading",
                rx.spinner(size="2", aria_label="Uploading"),
                rx.icon("clock", size=16, color="blue.400", aria_label="Upload pending")
            )
        )
    )
    
    # Progress percentage for screen readers
    progress_text = rx.cond(
        status == "uploading",
        rx.text(
            f"{progress:.0f}%",
            font_size="12px",
            color="blue.400",
            sr_only=True,  # Screen reader only
            aria_live="polite"
        ),
        rx.fragment()
    )
    
    return rx.vstack(
        # File info row with responsive layout
        responsive_container(
            rx.hstack(
                rx.text(
                    filename,
                    font_size=mobile_optimized("12px", "14px"),
                    color="white",
                    font_weight="500",
                    overflow="hidden",
                    text_overflow="ellipsis",
                    white_space="nowrap",
                    flex="1"
                ),
                status_icon,
                progress_text,
                width="100%",
                align="center",
                spacing="2"
            )
        ),
        
        # Progress bar with ARIA attributes
        rx.progress(
            value=progress,
            width="100%",
            height="6px",
            color_scheme=rx.cond(
                status == "completed",
                "green",
                rx.cond(status == "error", "red", "blue")
            )
        ),
        
        # Error message with proper styling
        rx.cond(
            error_message != "",
            rx.text(
                error_message,
                font_size=mobile_optimized("11px", "12px"),
                color="red.400",
                font_style="italic",
                width="100%",
                role="alert",
                aria_live="assertive"
            ),
            rx.fragment()
        ),
        
        spacing="2",
        width="100%",
        padding_x=mobile_optimized("2", "0")
    )


def file_validation_info() -> rx.Component:
    """Display file validation rules and supported formats."""
    validation_info = get_validation_summary()
    
    return rx.vstack(
        rx.text(
            "File Requirements:",
            font_weight="bold",
            font_size="14px",
            color="white"
        ),
        
        rx.hstack(
            rx.icon("file-text", size=14, color="blue.400"),
            rx.text(
                f"Supported: {', '.join(validation_info['supported_types'])}",
                font_size="12px",
                color="gray.300"
            ),
            spacing="2",
            align="center"
        ),
        
        rx.hstack(
            rx.icon("hard-drive", size=14, color="blue.400"),
            rx.text(
                f"Max size: {validation_info['max_size_mb']}MB per file",
                font_size="12px",
                color="gray.300"
            ),
            spacing="2",
            align="center"
        ),
        
        rx.hstack(
            rx.icon("shield-check", size=14, color="green.400"),
            rx.text(
                "Security scanning enabled",
                font_size="12px",
                color="gray.300"
            ),
            spacing="2",
            align="center"
        ),
        
        spacing="2",
        width="100%",
        padding="3",
        bg="rgba(59, 130, 246, 0.05)",
        border="1px solid",
        border_color="rgba(59, 130, 246, 0.2)",
        border_radius="md"
    )


def drag_drop_zone() -> rx.Component:
    """Drag and drop upload zone with accessibility and responsive design."""
    return rx.box(
        rx.vstack(
            rx.icon(
                "upload-cloud",
                size=mobile_optimized(40, 48),
                color="blue.400",
                aria_hidden="true"
            ),
            
            rx.heading(
                "Drop files here",
                size=mobile_optimized("3", "4"),
                color="white",
                text_align="center"
            ),
            
            rx.text(
                "or click to select files",
                font_size=mobile_optimized("14px", "16px"),
                color="gray.300",
                text_align="center"
            ),
            
            # Validation info - responsive layout
            rx.cond(
                ResponsiveState.is_mobile,
                rx.text(
                    f"Max {FileValidator.get_max_file_size_mb()}MB • {', '.join(FileValidator.get_supported_extensions()[:3])}...",
                    font_size="12px",
                    color="gray.400",
                    text_align="center"
                ),
                file_validation_info()
            ),
            
            spacing=mobile_optimized("2", "3"),
            align="center",
            width="100%"
        ),
        
        # Responsive padding and sizing
        padding=mobile_optimized("4", "8"),
        border="2px dashed",
        border_color="rgba(59, 130, 246, 0.4)",
        border_radius="lg",
        bg="rgba(59, 130, 246, 0.05)",
        backdrop_filter="blur(10px)",
        cursor="pointer",
        width="100%",
        min_height=mobile_optimized("150px", "200px"),
        display="flex",
        align_items="center",
        justify_content="center",
        
        # Accessibility and interaction states
        role="button",
        tabindex="0",
        aria_label="Click to select files or drag and drop files here",
        
        # Hover and focus states
        _hover={
            "border_color": "rgba(59, 130, 246, 0.6)",
            "bg": "rgba(59, 130, 246, 0.1)",
            "transform": "translateY(-1px)"
        },
        
        _focus={
            "outline": "2px solid",
            "outline_color": "rgba(59, 130, 246, 0.8)",
            "outline_offset": "2px"
        },
        
        # Smooth transitions
        transition="all 0.2s ease"
    )


def upload_status_summary() -> rx.Component:
    """Summary of upload status with live updates."""
    return rx.box(
        rx.hstack(
            rx.cond(
                DocumentState.upload_in_progress,
                rx.hstack(
                    rx.spinner(size="2"),
                    rx.text(
                        "Uploading files...",
                        font_size="14px",
                        color="blue.400"
                    ),
                    spacing="2",
                    align="center"
                ),
                rx.cond(
                    DocumentState.has_upload_errors,
                    rx.hstack(
                        rx.icon("triangle-alert", size=16, color="red.400"),
                        rx.text(
                            "Some uploads failed",
                            font_size="14px", 
                            color="red.400"
                        ),
                        spacing="2",
                        align="center"
                    ),
                    rx.cond(
                        DocumentState.total_uploaded > 0,
                        rx.hstack(
                            rx.icon("circle-check", size=16, color="green.400"),
                            rx.text(
                                f"{DocumentState.total_uploaded} files uploaded successfully",
                                font_size="14px",
                                color="green.400"
                            ),
                            spacing="2",
                            align="center"
                        ),
                        rx.fragment()
                    )
                )
            ),
            width="100%",
            justify="center"
        ),
        aria_live="polite"
    )


@optimized_render
def upload_modal() -> rx.Component:
    """Document upload modal with comprehensive UX integration."""
    
    # Modal content with focus trap for accessibility
    modal_content = focus_trap(
        rx.vstack(
            # Header with responsive title
            rx.hstack(
                rx.icon("upload", size=20, color="blue.400"),
                rx.text(
                    "Upload Documents",
                    font_size=mobile_optimized("18px", "20px"),
                    font_weight="bold",
                    color="white"
                ),
                spacing="2",
                align="center",
                width="100%"
            ),
            
            rx.text(
                "Upload documents to add them to your RAG system. Files are processed locally and never leave your machine.",
                font_size=mobile_optimized("13px", "14px"),
                color="gray.300",
                line_height="1.5"
            ),
            
            # Upload zone with responsive sizing
            rx.vstack(
                rx.upload(
                    drag_drop_zone(),
                    id="document-upload",
                    multiple=True,
                    accept={
                        "text/plain": [".txt"],
                        "text/markdown": [".md"],
                        "application/pdf": [".pdf"],
                        "text/html": [".html"],
                        "application/json": [".json"],
                        "text/csv": [".csv"]
                    },
                    max_files=20,
                    max_size=FileValidator.MAX_FILE_SIZE,
                    border="none",
                    width="100%"
                ),
                
                # Upload status summary
                upload_status_summary(),
                
                spacing="3",
                width="100%"
            ),
            
            # Progress indicators with responsive container
            rx.cond(
                DocumentState.uploading_files.length() > 0,
                responsive_container(
                    rx.vstack(
                        rx.divider(color="rgba(255, 255, 255, 0.1)"),
                        
                        rx.hstack(
                            rx.text(
                                "Upload Progress",
                                font_weight="bold",
                                color="white",
                                font_size=mobile_optimized("14px", "16px")
                            ),
                            rx.spacer(),
                            rx.text(
                                f"{DocumentState.completed_uploads} / {DocumentState.total_uploads}",
                                font_size="12px",
                                color="gray.400"
                            ),
                            width="100%",
                            align="center"
                        ),
                        
                        # Progress list with virtual scrolling for performance
                        rx.box(
                            rx.foreach(
                                DocumentState.uploading_files,
                                lambda progress: upload_progress_bar(
                                    progress.filename,
                                    progress.progress,
                                    progress.status,
                                    progress.error_message
                                )
                            ),
                            max_height=mobile_optimized("200px", "300px"),
                            overflow_y="auto",
                            width="100%",
                            padding_right="2"
                        ),
                        
                        spacing="3",
                        width="100%"
                    )
                ),
                rx.fragment()
            ),
            
            # Error display with accessibility
            error_display(
                DocumentState.show_error,
                DocumentState.error_message,
                on_dismiss=DocumentState.clear_error
            ),
            
            # Action buttons with responsive layout
            responsive_container(
                rx.hstack(
                    # Cancel button
                    accessible_button(
                        "Cancel",
                        variant="outline",
                        color_scheme="gray",
                        on_click=DocumentState.close_upload_modal,
                        size=mobile_optimized("2", "3"),
                        flex=rx.cond(ResponsiveState.is_mobile, "1", "none")
                    ),
                    
                    # Clear all button (only show if has uploads)
                    rx.cond(
                        DocumentState.uploading_files.length() > 0,
                        accessible_button(
                            "Clear All",
                            variant="outline", 
                            color_scheme="red",
                            on_click=DocumentState.clear_all_uploads,
                            size=mobile_optimized("2", "3"),
                            flex=rx.cond(ResponsiveState.is_mobile, "1", "none")
                        ),
                        rx.fragment()
                    ),
                    
                    # Done button
                    accessible_button(
                        "Done",
                        color_scheme="blue",
                        on_click=DocumentState.close_upload_modal,
                        disabled=DocumentState.upload_in_progress,
                        size=mobile_optimized("2", "3"),
                        flex=rx.cond(ResponsiveState.is_mobile, "1", "none")
                    ),
                    
                    spacing="3",
                    justify="end",
                    width="100%",
                    direction=rx.cond(
                        ResponsiveState.is_mobile,
                        "column-reverse",
                        "row"
                    )
                )
            ),
            
            spacing="4",
            width="100%",
            max_width=mobile_optimized("100%", "600px")
        )
    )
    
    # Modal wrapper with responsive sizing using conditional rendering
    return rx.cond(
        DocumentState.is_upload_modal_open,
        rx.box(
            # Modal backdrop
            rx.box(
                on_click=DocumentState.close_upload_modal,
                position="fixed",
                top="0",
                left="0",
                width="100vw",
                height="100vh",
                bg="rgba(0, 0, 0, 0.5)",
                z_index="998"
            ),
            
            # Modal content
            rx.box(
                modal_content,
                position="fixed",
                top="50%",
                left="50%",
                transform="translate(-50%, -50%)",
                max_width=mobile_optimized("95vw", "600px"),
                width=mobile_optimized("95vw", "auto"),
                max_height=mobile_optimized("90vh", "80vh"),
                padding=mobile_optimized("4", "6"),
                bg="rgba(15, 15, 35, 0.95)",
                backdrop_filter="blur(20px)",
                border="1px solid",
                border_color="rgba(255, 255, 255, 0.1)",
                border_radius="xl",
                overflow_y="auto",
                z_index="999"
            ),
            
            position="fixed",
            top="0",
            left="0",
            width="100vw",
            height="100vh",
            z_index="998"
        ),
        rx.fragment()
    )


def upload_button() -> rx.Component:
    """Simple upload button that opens the modal with accessibility."""
    return accessible_button(
        "Upload Documents",
        on_click=DocumentState.open_upload_modal,
        color_scheme="blue",
        size="3",
        aria_label="Upload new documents to the system"
    )


def quick_upload_button() -> rx.Component:
    """Compact upload button for mobile/sidebar use."""
    return accessible_button(
        rx.icon("plus", size=16),
        color_scheme="blue",
        variant="ghost",
        size="2",
        on_click=DocumentState.open_upload_modal,
        aria_label="Upload documents",
        title="Upload documents"
    )