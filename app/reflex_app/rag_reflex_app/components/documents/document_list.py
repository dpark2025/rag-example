"""
Document list component with search, filtering, and bulk operations integrated with Phase 5 UX.

Authored by: AI/ML Engineer (Jackson Brown)
Date: 2025-08-04
"""

import reflex as rx
from typing import List, Dict, Any
from ...state.document_state import DocumentState
from ..common.responsive_design import ResponsiveState, responsive_container, mobile_optimized
from ..common.accessibility import accessible_button, aria_live_region, focus_trap
from ..common.error_boundary import error_display
from ..common.performance_optimizer import optimized_render, virtualized_list
from .document_card import document_card, empty_state, loading_skeleton
from .upload_modal import upload_button, quick_upload_button


def search_bar() -> rx.Component:
    """Search bar with accessibility and responsive design."""
    return rx.hstack(
        rx.icon("search", size=16, color="gray.400"),
        rx.input(
            placeholder="Search documents...",
            value=DocumentState.search_query,
            on_change=DocumentState.set_search_query,
            width="100%",
            size=mobile_optimized("2", "3"),
            color="white",
            bg="rgba(255, 255, 255, 0.05)",
            border="1px solid",
            border_color="rgba(255, 255, 255, 0.1)",
            _focus={
                "border_color": "rgba(59, 130, 246, 0.5)",
                "outline": "none"
            },
            aria_label="Search documents by name or content"
        ),
        spacing="2",
        align="center",
        width="100%",
        padding="2",
        bg="rgba(255, 255, 255, 0.02)",
        border="1px solid",
        border_color="rgba(255, 255, 255, 0.1)",
        border_radius="lg"
    )


def filter_controls() -> rx.Component:
    """Filter and sort controls with responsive layout."""
    return rx.cond(
        ResponsiveState.is_mobile,
        # Mobile: stacked layout with collapsible filters
        rx.vstack(
            rx.hstack(
                accessible_button(
                    rx.icon("filter", size=16),
                    f"Filters ({DocumentState.active_filter_count})",
                    variant="outline",
                    size="2",
                    on_click=DocumentState.toggle_filter_panel,
                    aria_label="Toggle filter panel",
                    flex="1"
                ),
                accessible_button(
                    rx.icon("arrow-up-down", size=16),
                    DocumentState.sort_by.title(),
                    variant="outline", 
                    size="2",
                    on_click=DocumentState.toggle_sort_menu,
                    aria_label="Change sort order",
                    flex="1"
                ),
                spacing="2",
                width="100%"
            ),
            
            # Collapsible filter panel
            rx.cond(
                DocumentState.show_filter_panel,
                rx.vstack(
                    rx.select(
                        ["all", "txt", "md", "pdf", "processing", "error"],
                        value=DocumentState.filter_type,
                        on_change=DocumentState.set_filter_type,
                        placeholder="Filter by type",
                        size="2",
                        width="100%"
                    ),
                    rx.select(
                        ["newest", "oldest", "name", "size"],
                        value=DocumentState.sort_by,
                        on_change=DocumentState.set_sort_by,
                        placeholder="Sort by",
                        size="2",
                        width="100%"
                    ),
                    spacing="2",
                    width="100%",
                    padding="3",
                    bg="rgba(255, 255, 255, 0.02)",
                    border="1px solid",
                    border_color="rgba(255, 255, 255, 0.1)",
                    border_radius="md"
                ),
                rx.fragment()
            ),
            
            spacing="2",
            width="100%"
        ),
        
        # Desktop: horizontal layout
        rx.hstack(
            rx.select(
                ["all", "txt", "md", "pdf", "processing", "error"],
                value=DocumentState.filter_type,
                on_change=DocumentState.set_filter_type,
                placeholder="Filter by type",
                size="3",
                width="150px"
            ),
            rx.select(
                ["newest", "oldest", "name", "size"],
                value=DocumentState.sort_by,
                on_change=DocumentState.set_sort_by,
                placeholder="Sort by",
                size="3",
                width="150px"
            ),
            rx.spacer(),
            upload_button(),
            spacing="3",
            align="center",
            width="100%"
        )
    )


def bulk_selection_controls() -> rx.Component:
    """Bulk selection and operations controls."""
    return aria_live_region(
        rx.hstack(
            # Selection controls
            rx.hstack(
                rx.checkbox(
                    checked=DocumentState.all_selected,
                    indeterminate=DocumentState.some_selected,
                    on_change=DocumentState.toggle_select_all,
                    color_scheme="blue",
                    size="2",
                    aria_label="Select all documents"
                ),
                rx.text(
                    rx.cond(
                        DocumentState.selected_count > 0,
                        f"{DocumentState.selected_count} selected",
                        "Select all"
                    ),
                    font_size=mobile_optimized("13px", "14px"),
                    color="gray.300"
                ),
                spacing="2",
                align="center"
            ),
            
            rx.spacer(),
            
            # Bulk actions (only show when items selected)
            rx.cond(
                DocumentState.selected_count > 0,
                rx.hstack(
                    accessible_button(
                        rx.icon("download", size=14),
                        rx.cond(
                            ResponsiveState.is_mobile,
                            "",
                            "Download"
                        ),
                        variant="outline",
                        color_scheme="blue",
                        size=mobile_optimized("2", "3"),
                        on_click=DocumentState.download_selected_documents,
                        aria_label="Download selected documents",
                        disabled=DocumentState.is_processing
                    ),
                    
                    accessible_button(
                        rx.icon("trash-2", size=14),
                        rx.cond(
                            ResponsiveState.is_mobile,
                            "",
                            "Delete"
                        ),
                        variant="outline",
                        color_scheme="red",
                        size=mobile_optimized("2", "3"),
                        on_click=DocumentState.confirm_delete_selected,
                        aria_label="Delete selected documents",
                        disabled=DocumentState.is_processing
                    ),
                    
                    spacing="2"
                ),
                rx.fragment()
            ),
            
            spacing="3",
            align="center",
            width="100%",
            padding="3",
            bg="rgba(59, 130, 246, 0.05)",
            border="1px solid",
            border_color="rgba(59, 130, 246, 0.2)",
            border_radius="md"
        ),
        aria_live="polite"
    )


def document_stats() -> rx.Component:
    """Document statistics display."""
    return rx.hstack(
        rx.hstack(
            rx.icon("file-text", size=14, color="gray.500"),
            rx.text(
                f"{DocumentState.total_documents} documents",
                font_size="12px",
                color="gray.400"
            ),
            spacing="1",
            align="center"
        ),
        
        rx.hstack(
            rx.icon("hard-drive", size=14, color="gray.500"),
            rx.text(
                DocumentState.total_size_formatted,
                font_size="12px",
                color="gray.400"
            ),
            spacing="1",
            align="center"
        ),
        
        rx.hstack(
            rx.icon("layers", size=14, color="gray.500"),
            rx.text(
                f"{DocumentState.total_chunks} chunks",
                font_size="12px",
                color="gray.400"
            ),
            spacing="1",
            align="center"
        ),
        
        spacing="4",
        align="center",
        wrap="wrap"
    )


def list_view_controls() -> rx.Component:
    """List view controls (grid/list, pagination, etc.)."""
    return rx.hstack(
        # View mode toggle
        rx.hstack(
            accessible_button(
                rx.icon("grid-3x3", size=14),
                variant=rx.cond(
                    DocumentState.view_mode == "grid",
                    "solid",
                    "ghost"
                ),
                color_scheme="gray",
                size="2",
                on_click=lambda: DocumentState.set_view_mode("grid"),
                aria_label="Grid view",
                title="Grid view"
            ),
            accessible_button(
                rx.icon("list", size=14),
                variant=rx.cond(
                    DocumentState.view_mode == "list",
                    "solid",
                    "ghost"
                ),
                color_scheme="gray",
                size="2",
                on_click=lambda: DocumentState.set_view_mode("list"),
                aria_label="List view",
                title="List view"
            ),
            spacing="1",
            border="1px solid",
            border_color="rgba(255, 255, 255, 0.1)",
            border_radius="md",
            padding="1"
        ),
        
        rx.spacer(),
        
        # Pagination info
        rx.cond(
            DocumentState.total_documents > DocumentState.page_size,
            rx.text(
                f"{DocumentState.start_index + 1}-{DocumentState.end_index} of {DocumentState.total_documents}",
                font_size="12px",
                color="gray.400"
            ),
            rx.fragment()
        ),
        
        # Page navigation
        rx.cond(
            DocumentState.total_pages > 1,
            rx.hstack(
                accessible_button(
                    rx.icon("chevron-left", size=14),
                    variant="ghost",
                    color_scheme="gray",
                    size="2",
                    on_click=DocumentState.previous_page,
                    disabled=DocumentState.current_page == 1,
                    aria_label="Previous page"
                ),
                rx.text(
                    f"{DocumentState.current_page} / {DocumentState.total_pages}",
                    font_size="12px",
                    color="gray.400"
                ),
                accessible_button(
                    rx.icon("chevron-right", size=14),
                    variant="ghost",
                    color_scheme="gray",
                    size="2",
                    on_click=DocumentState.next_page,
                    disabled=DocumentState.current_page == DocumentState.total_pages,
                    aria_label="Next page"
                ),
                spacing="2",
                align="center"
            ),
            rx.fragment()
        ),
        
        spacing="3",
        align="center",
        width="100%"
    )


@optimized_render
def document_grid() -> rx.Component:
    """Document grid with responsive layout and virtualization."""
    return rx.cond(
        DocumentState.total_documents > 0,
        virtualized_list(
            rx.grid(
                rx.foreach(
                    DocumentState.filtered_documents,
                    document_card
                ),
                columns=rx.cond(
                    ResponsiveState.is_mobile,
                    1,
                    rx.cond(
                        ResponsiveState.is_tablet,
                        2,
                        3
                    )
                ),
                spacing="4",
                width="100%"
            ),
            item_height=mobile_optimized(120, 140),
            container_height="calc(100vh - 300px)"
        ),
        empty_state()
    )


@optimized_render
def document_list_view() -> rx.Component:
    """Document list view with compact layout."""
    return rx.cond(
        DocumentState.total_documents > 0,
        virtualized_list(
            rx.vstack(
                rx.foreach(
                    DocumentState.filtered_documents,
                    lambda doc: rx.box(
                        document_card(doc),
                        width="100%"
                    )
                ),
                spacing="2",
                width="100%"
            ),
            item_height=mobile_optimized(80, 100),
            container_height="calc(100vh - 300px)"
        ),
        empty_state()
    )


def confirmation_dialog() -> rx.Component:
    """Confirmation dialog for bulk operations."""
    return rx.dialog(
        rx.dialog_content(
            focus_trap(
                rx.vstack(
                    rx.hstack(
                        rx.icon("alert-triangle", size=20, color="red.400"),
                        rx.text(
                            "Confirm Action",
                            font_size="18px",
                            font_weight="bold",
                            color="white"
                        ),
                        spacing="2",
                        align="center"
                    ),
                    
                    rx.text(
                        DocumentState.confirmation_message,
                        font_size="14px",
                        color="gray.300",
                        line_height="1.5"
                    ),
                    
                    rx.hstack(
                        accessible_button(
                            "Cancel",
                            variant="outline",
                            color_scheme="gray",
                            on_click=DocumentState.cancel_confirmation,
                            size="3",
                            flex="1" if ResponsiveState.is_mobile else "none"
                        ),
                        
                        accessible_button(
                            "Confirm",
                            color_scheme="red",
                            on_click=DocumentState.confirm_action,
                            disabled=DocumentState.is_processing,
                            size="3",
                            flex="1" if ResponsiveState.is_mobile else "none"
                        ),
                        
                        spacing="3",
                        justify="end",
                        width="100%",
                        direction=rx.cond(
                            ResponsiveState.is_mobile,
                            "column-reverse",
                            "row"
                        )
                    ),
                    
                    spacing="4",
                    width="100%"
                )
            ),
            
            max_width=mobile_optimized("95vw", "400px"),
            padding=mobile_optimized("4", "6"),
            bg="rgba(15, 15, 35, 0.95)",
            backdrop_filter="blur(20px)",
            border="1px solid",
            border_color="rgba(255, 255, 255, 0.1)",
            border_radius="xl"
        ),
        
        open=DocumentState.show_confirmation_dialog,
        on_open_change=DocumentState.set_show_confirmation_dialog
    )


@optimized_render
def document_list() -> rx.Component:
    """Main document list component with Phase 5 UX integration."""
    return responsive_container(
        rx.vstack(
            # Header with search and quick actions
            rx.hstack(
                rx.text(
                    "Documents",
                    font_size=mobile_optimized("20px", "24px"),
                    font_weight="bold",
                    color="white"
                ),
                rx.spacer(),
                rx.cond(
                    ResponsiveState.is_mobile,
                    quick_upload_button(),
                    rx.fragment()
                ),
                width="100%",
                align="center"
            ),
            
            # Search bar
            search_bar(),
            
            # Filter controls and stats
            rx.vstack(
                filter_controls(),
                
                # Document stats
                rx.cond(
                    DocumentState.total_documents > 0,
                    document_stats(),
                    rx.fragment()
                ),
                
                spacing="3",
                width="100%"
            ),
            
            # Bulk selection controls (show when selection mode active)
            rx.cond(
                DocumentState.selection_mode | (DocumentState.selected_count > 0),
                bulk_selection_controls(),
                rx.fragment()
            ),
            
            # View controls
            rx.cond(
                DocumentState.total_documents > 0,
                list_view_controls(),
                rx.fragment()
            ),
            
            # Loading state
            rx.cond(
                DocumentState.is_loading_documents,
                rx.vstack(
                    rx.foreach(
                        range(6),
                        lambda _: loading_skeleton()
                    ),
                    spacing="4",
                    width="100%"
                ),
                # Document list/grid
                rx.cond(
                    DocumentState.view_mode == "grid",
                    document_grid(),
                    document_list_view()
                )
            ),
            
            # Error display
            error_display(
                DocumentState.show_error,
                DocumentState.error_message,
                on_dismiss=DocumentState.clear_error
            ),
            
            # Confirmation dialog
            confirmation_dialog(),
            
            spacing="4",
            width="100%",
            padding=mobile_optimized("4", "6")
        )
    )


def documents_header() -> rx.Component:
    """Documents page header with breadcrumbs and actions."""
    return responsive_container(
        rx.vstack(
            # Breadcrumbs
            rx.hstack(
                accessible_button(
                    rx.icon("home", size=14),
                    variant="ghost",
                    color_scheme="gray",
                    size="2",
                    on_click=lambda: rx.redirect("/"),
                    aria_label="Home"
                ),
                rx.icon("chevron-right", size=14, color="gray.500"),
                rx.text(
                    "Documents",
                    font_size="14px",
                    color="gray.300"
                ),
                spacing="2",
                align="center"
            ),
            
            # Page title and primary actions
            rx.hstack(
                rx.vstack(
                    rx.heading(
                        "Document Management",
                        size=mobile_optimized("5", "6"),
                        color="white"
                    ),
                    rx.text(
                        "Manage your RAG knowledge base documents",
                        font_size=mobile_optimized("14px", "16px"),
                        color="gray.400"
                    ),
                    spacing="1",
                    align="start"
                ),
                
                rx.spacer(),
                
                # Quick actions
                rx.cond(
                    ResponsiveState.is_desktop,
                    rx.hstack(
                        accessible_button(
                            rx.icon("settings", size=16),
                            "Settings",
                            variant="outline",
                            color_scheme="gray",
                            size="3",
                            on_click=DocumentState.open_settings,
                            aria_label="Document management settings"
                        ),
                        
                        upload_button(),
                        
                        spacing="3"
                    ),
                    rx.fragment()
                ),
                
                width="100%",
                align="start"
            ),
            
            spacing="3",
            width="100%",
            padding=mobile_optimized("4", "6"),
            border_bottom="1px solid",
            border_color="rgba(255, 255, 255, 0.1)"
        )
    )