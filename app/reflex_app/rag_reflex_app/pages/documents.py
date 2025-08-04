"""Documents management page."""

import reflex as rx
from ..layouts.main_layout import main_layout
from ..components.documents.document_list import document_list
from ..components.documents.upload_modal_simple import upload_modal
from ..state.document_state import DocumentState

def documents_page() -> rx.Component:
    """Documents management page with upload and management capabilities."""
    return main_layout(
        rx.vstack(
            # Main document management interface
            document_list(),
            
            # Upload modal
            upload_modal(),
            
            width="100%",
            height="100%"
        )
    )