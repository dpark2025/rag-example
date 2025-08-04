"""Document list component with search, filtering, and bulk operations."""

import reflex as rx
from ...state.document_state import DocumentState
from .document_card import document_card, empty_state, loading_skeleton
from .upload_modal import upload_button

def search_and_filters() -> rx.Component:
    """Search bar and filter controls."""
    return rx.vstack(
        # Search and primary filters
        rx.hstack(
            rx.input(
                placeholder="Search documents...",
                value=DocumentState.search_query,
                on_change=DocumentState.set_search_query,
                width="300px",
                size="3",
                color="white"
            ),
            rx.select(
                ["all", "txt", "processing", "error"],
                value=DocumentState.filter_type,
                on_change=DocumentState.set_filter_type,
                placeholder="Filter by type",
                size="3"
            ),
            rx.select(
                ["newest", "oldest", "name", "size"],
                value=DocumentState.sort_by,
                on_change=DocumentState.set_sort_by,
                placeholder="Sort by",
                size="3"
            ),
            rx.spacer(),
            upload_button(),
            spacing="3",
            align="center",
            width="100%"
        ),
        
        # Selection and bulk operations
        rx.cond(
            DocumentState.total_documents > 0,
            rx.hstack(
                rx.hstack(
                    rx.checkbox(
                        on_change=DocumentState.toggle_select_all,
                        color_scheme="blue"
                    ),
                    rx.text(
                        f"Select all ({DocumentState.total_documents})",
                        font_size="14px",
                        color="gray.300"
                    ),
                    spacing="2",
                    align="center"
                ),
                rx.spacer(),
                rx.cond(
                    DocumentState.selected_count > 0,
                    rx.hstack(
                        rx.text(
                            f"{DocumentState.selected_count} selected",
                            font_size="14px",
                            color="blue.400",
                            font_weight="500"
                        ),
                        rx.button(
                            "Clear Selection",
                            size="2",
                            variant="ghost",
                            color_scheme="gray",
                            on_click=DocumentState.clear_selection
                        ),
                        rx.button(
                            rx.icon("trash-2", size=14),
                            f"Delete ({DocumentState.selected_count})",
                            size="2",
                            color_scheme="red",
                            variant="outline",
                            loading=DocumentState.is_deleting,
                            on_click=DocumentState.delete_selected_documents
                        ),
                        spacing="3",
                        align="center"
                    ),
                    rx.fragment()
                ),
                width="100%",
                align="center"
            ),
            rx.fragment()
        ),
        
        spacing="3",
        width="100%"
    )

def document_stats() -> rx.Component:
    """Document statistics display."""
    return rx.hstack(
        rx.badge(
            f"Total: {DocumentState.total_documents}",
            color_scheme="blue",
            variant="outline"
        ),
        rx.cond(
            DocumentState.search_query != "",
            rx.badge(
                rx.text(f"Filtered: ", DocumentState.filtered_count),
                color_scheme="gray",
                variant="outline"
            ),
            rx.fragment()
        ),
        spacing="2"
    )

def document_list() -> rx.Component:
    """Main document list component."""
    return rx.vstack(
        # Header
        rx.hstack(
            rx.hstack(
                rx.icon("folder", size=24, color="blue.400"),
                rx.heading("Document Management", size="5", color="white"),
                spacing="2",
                align="center"
            ),
            rx.spacer(),
            document_stats(),
            width="100%",
            align="center",
            padding_bottom="4"
        ),
        
        # Search and controls
        search_and_filters(),
        
        rx.divider(color="rgba(255, 255, 255, 0.1)"),
        
        # Document list or empty state
        rx.cond(
            DocumentState.is_loading_documents,
            loading_skeleton(),
            rx.cond(
                DocumentState.filtered_count > 0,
                rx.vstack(
                    rx.foreach(
                        DocumentState.get_filtered_documents,
                        document_card
                    ),
                    spacing="3",
                    width="100%"
                ),
                rx.cond(
                    DocumentState.total_documents == 0,
                    empty_state(),
                    rx.center(
                        rx.vstack(
                            rx.icon("search", size=48, color="gray.500"),
                            rx.text(
                                "No documents match your search",
                                font_size="18px",
                                color="gray.400"
                            ),
                            rx.text(
                                f'Try adjusting your filters or search for "{DocumentState.search_query}"',
                                font_size="14px",
                                color="gray.500",
                                text_align="center"
                            ),
                            spacing="3",
                            align="center"
                        ),
                        height="300px",
                        width="100%"
                    )
                )
            )
        ),
        
        # Error display
        rx.cond(
            DocumentState.show_error,
            rx.box(
                rx.hstack(
                    rx.icon("triangle-alert", size=16, color="red.400"),
                    rx.text("Error:", font_weight="bold", color="red.400"),
                    rx.text(DocumentState.error_message, color="red.400"),
                    rx.spacer(),
                    rx.button(
                        "×",
                        size="1",
                        variant="ghost",
                        color_scheme="red",
                        on_click=DocumentState.clear_error
                    ),
                    spacing="2",
                    align="center",
                    width="100%"
                ),
                padding="3",
                bg="rgba(248, 113, 113, 0.1)",
                border="1px solid",
                border_color="rgba(248, 113, 113, 0.3)",
                border_radius="md",
                margin_top="4"
            ),
            rx.fragment()
        ),
        
        spacing="4",
        width="100%",
        padding="6"
    )