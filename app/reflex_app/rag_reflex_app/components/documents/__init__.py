"""
Document management components with Phase 5 UX integration.

Authored by: AI/ML Engineer (Jackson Brown)
Date: 2025-08-04
"""

# Core components
from .document_card import (
    document_card,
    empty_state,
    loading_skeleton,
    document_details_modal,
    status_badge,
    file_type_icon
)

from .document_list import (
    document_list,
    documents_header,
    search_bar,
    filter_controls,
    bulk_selection_controls,
    document_stats,
    list_view_controls,
    document_grid,
    document_list_view,
    confirmation_dialog
)

from .upload_modal import (
    upload_modal,
    upload_button,
    quick_upload_button,
    drag_drop_zone,
    upload_progress_bar,
    file_validation_info
)

# Utilities
from .file_validator import (
    FileValidator,
    ValidationResult,
    FileValidationError,
    validate_upload_file,
    get_validation_summary
)

__all__ = [
    # Document cards
    "document_card",
    "empty_state", 
    "loading_skeleton",
    "document_details_modal",
    "status_badge",
    "file_type_icon",
    
    # Document list
    "document_list",
    "documents_header",
    "search_bar",
    "filter_controls",
    "bulk_selection_controls",
    "document_stats",
    "list_view_controls",
    "document_grid",
    "document_list_view",
    "confirmation_dialog",
    
    # Upload components
    "upload_modal",
    "upload_button",
    "quick_upload_button",
    "drag_drop_zone",
    "upload_progress_bar",
    "file_validation_info",
    
    # File validation
    "FileValidator",
    "ValidationResult",
    "FileValidationError",
    "validate_upload_file",
    "get_validation_summary"
]