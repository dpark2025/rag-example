"""
Documents management page with Phase 5 UX integration.

Authored by: AI/ML Engineer (Jackson Brown)
Date: 2025-08-04
"""

import reflex as rx
from ..layouts.main_layout import main_layout
from ..components.documents.document_list import document_list, documents_header
from ..components.documents.upload_modal import upload_modal
from ..components.documents.document_card import document_details_modal
from ..components.common.responsive_design import ResponsiveState, responsive_container
from ..components.common.accessibility import accessible_region, skip_link
from ..components.common.error_boundary import error_boundary
from ..components.common.performance_optimizer import optimized_render
from ..state.document_state import DocumentState


@optimized_render
def documents_page() -> rx.Component:
    """Documents management page with comprehensive UX integration."""
    
    # Page content with error boundary
    page_content = error_boundary(
        responsive_container(
            rx.vstack(
                # Skip link for accessibility
                skip_link("main-content", "Skip to document list"),
                
                # Page header with breadcrumbs and actions
                documents_header(),
                
                # Main content area
                accessible_region(
                    document_list(),
                    aria_label="Document management interface",
                    role="main",
                    id="main-content"
                ),
                
                spacing="0",
                width="100%",
                min_height="100vh"
            )
        )
    )
    
    # Modal overlays
    modal_overlays = rx.fragment(
        # Upload modal
        upload_modal(),
        
        # Document details modal (temporarily disabled)
        rx.fragment()
    )
    
    # Complete page structure
    return main_layout(
        rx.vstack(
            # Page content
            page_content,
            
            # Modal overlays rendered at top level
            modal_overlays,
            
            width="100%",
            height="100%",
            spacing="0"
        )
    )


# Page route configuration
documents_page.route = "/documents"
documents_page.title = "Documents"
documents_page.description = "Document Management"