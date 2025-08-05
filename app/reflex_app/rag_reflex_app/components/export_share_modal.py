"""
Authored by: Integration Specialist (Barry Young)  
Date: 2025-08-05

Export and Share Modal Component

React-style component for the Reflex UI that provides export and sharing capabilities
with a modern, user-friendly interface.
"""

import reflex as rx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

class ExportShareModal(rx.Component):
    """Modal component for document export and sharing functionality."""
    
    def __init__(
        self,
        doc_id: str,
        doc_title: str,
        is_open: bool = False,
        **props
    ):
        super().__init__(**props)
        self.doc_id = doc_id
        self.doc_title = doc_title
        self.is_open = is_open
    
    @staticmethod
    def create_export_section():
        """Create the export section of the modal."""
        return rx.vstack(
            rx.heading("Export Document", size="md", color="gray.700"),
            rx.text(
                "Export this document in various formats for sharing or archival.",
                font_size="sm",
                color="gray.600",
                margin_bottom="1rem"
            ),
            
            # Format selection
            rx.hstack(
                rx.text("Format:", font_weight="semibold", font_size="sm"),
                rx.select(
                    ["PDF", "Markdown", "HTML", "JSON", "Text"],
                    placeholder="Select format",
                    value="PDF",
                    name="export_format",
                    width="150px"
                ),
                spacing="0.5rem",
                align="center"
            ),
            
            # Export options
            rx.vstack(
                rx.text("Export Options:", font_weight="semibold", font_size="sm"),
                rx.checkbox(
                    "Include metadata",
                    is_checked=True,
                    name="include_metadata"
                ),
                rx.checkbox(
                    "Include sources", 
                    is_checked=True,
                    name="include_sources"
                ),
                rx.checkbox(
                    "Include timestamps",
                    is_checked=True, 
                    name="include_timestamps"
                ),
                spacing="0.25rem",
                align_items="flex-start",
                padding_left="1rem"
            ),
            
            # Export button
            rx.button(
                "Export Document",
                bg="blue.500",
                color="white",
                _hover={"bg": "blue.600"},
                width="100%",
                margin_top="1rem",
                on_click=lambda: print("Export clicked")  # Will be replaced with actual handler
            ),
            
            spacing="1rem",
            align_items="stretch",
            width="100%"
        )
    
    @staticmethod
    def create_share_section():
        """Create the sharing section of the modal."""
        return rx.vstack(
            rx.heading("Share Document", size="md", color="gray.700"),
            rx.text(
                "Create a secure link to share this document with others.",
                font_size="sm",
                color="gray.600", 
                margin_bottom="1rem"
            ),
            
            # Access level selection
            rx.hstack(
                rx.text("Access Level:", font_weight="semibold", font_size="sm"),
                rx.select(
                    ["View Only", "Download", "Edit", "Admin"],
                    placeholder="Select access level",
                    value="View Only",
                    name="access_level",
                    width="150px"
                ),
                spacing="0.5rem",
                align="center"
            ),
            
            # Expiration settings
            rx.hstack(
                rx.text("Expires in:", font_weight="semibold", font_size="sm"),
                rx.select(
                    ["1 hour", "24 hours", "7 days", "30 days", "Never"],
                    placeholder="Select expiration",
                    value="7 days",
                    name="expiration",
                    width="150px"
                ),
                spacing="0.5rem",
                align="center"
            ),
            
            # Security options
            rx.vstack(
                rx.text("Security Options:", font_weight="semibold", font_size="sm"),
                rx.checkbox(
                    "Require password",
                    name="require_password"
                ),
                rx.input(
                    placeholder="Enter password (optional)",
                    type_="password",
                    name="share_password",
                    width="100%",
                    display="none"  # Show only when checkbox is checked
                ),
                rx.checkbox(
                    "Restrict to specific IPs",
                    name="ip_restriction"
                ),
                rx.textarea(
                    placeholder="Enter IP addresses (one per line)",
                    name="allowed_ips",
                    width="100%",
                    height="60px",
                    display="none"  # Show only when checkbox is checked
                ),
                spacing="0.25rem",
                align_items="flex-start",
                padding_left="1rem"
            ),
            
            # Custom message
            rx.vstack(
                rx.text("Custom Message:", font_weight="semibold", font_size="sm"),
                rx.textarea(
                    placeholder="Add a personal message for recipients (optional)",
                    name="custom_message",
                    width="100%",
                    height="80px"
                ),
                spacing="0.25rem",
                align_items="flex-start"
            ),
            
            # Share button
            rx.button(
                "Create Share Link",
                bg="green.500",
                color="white",
                _hover={"bg": "green.600"},
                width="100%",
                margin_top="1rem",
                on_click=lambda: print("Share clicked")  # Will be replaced with actual handler
            ),
            
            spacing="1rem",
            align_items="stretch",
            width="100%"
        )
    
    @staticmethod 
    def create_bulk_export_section():
        """Create the bulk export section for multiple documents."""
        return rx.vstack(
            rx.heading("Bulk Export", size="md", color="gray.700"),
            rx.text(
                "Export multiple documents in a ZIP archive.",
                font_size="sm",
                color="gray.600",
                margin_bottom="1rem"
            ),
            
            # Document selection (placeholder - would be populated dynamically)
            rx.vstack(
                rx.text("Selected Documents:", font_weight="semibold", font_size="sm"),
                rx.box(
                    rx.text("Document 1.pdf"),
                    rx.text("Document 2.md"),
                    rx.text("Technical Report.docx"),
                    padding="0.5rem",
                    border="1px solid",
                    border_color="gray.200",
                    border_radius="md",
                    bg="gray.50",
                    font_size="sm"
                ),
                spacing="0.25rem",
                align_items="flex-start",
                width="100%"
            ),
            
            # Format for bulk export
            rx.hstack(
                rx.text("Export all as:", font_weight="semibold", font_size="sm"),
                rx.select(
                    ["Mixed Formats", "All as PDF", "All as Markdown", "All as HTML"],
                    placeholder="Select format",
                    value="Mixed Formats",
                    name="bulk_format",
                    width="150px"
                ),
                spacing="0.5rem",
                align="center"
            ),
            
            # Bulk export button
            rx.button(
                "Export as ZIP",
                bg="purple.500",
                color="white",
                _hover={"bg": "purple.600"},
                width="100%",
                margin_top="1rem",
                on_click=lambda: print("Bulk export clicked")  # Will be replaced with actual handler
            ),
            
            spacing="1rem",
            align_items="stretch",
            width="100%"
        )
    
    def render(self):
        """Render the complete export and share modal."""
        return rx.modal(
            rx.modal_overlay(
                rx.modal_content(
                    rx.modal_header(
                        rx.hstack(
                            rx.icon(tag="share", size="lg", color="blue.500"),
                            rx.vstack(
                                rx.heading(
                                    "Export & Share",
                                    size="lg"
                                ),
                                rx.text(
                                    f'"{self.doc_title}"',
                                    font_size="sm",
                                    color="gray.600",
                                    font_style="italic"
                                ),
                                spacing="0.25rem",
                                align_items="flex-start"
                            ),
                            spacing="1rem",
                            align="center"
                        )
                    ),
                    rx.modal_body(
                        rx.tabs(
                            rx.tab_list(
                                rx.tab("Export", _selected={"color": "blue.500", "border_color": "blue.500"}),
                                rx.tab("Share", _selected={"color": "green.500", "border_color": "green.500"}),
                                rx.tab("Bulk Export", _selected={"color": "purple.500", "border_color": "purple.500"}),
                            ),
                            rx.tab_panels(
                                rx.tab_panel(
                                    self.create_export_section(),
                                    padding="1rem 0"
                                ),
                                rx.tab_panel(
                                    self.create_share_section(),
                                    padding="1rem 0"
                                ),
                                rx.tab_panel(
                                    self.create_bulk_export_section(),
                                    padding="1rem 0"
                                ),
                            ),
                            width="100%"
                        )
                    ),
                    rx.modal_footer(
                        rx.hstack(
                            rx.button(
                                "Close",
                                variant="ghost",
                                on_click=lambda: print("Close clicked")  # Will close modal
                            ),
                            rx.text(
                                "All exports and shares are tracked in your activity log.",
                                font_size="xs",
                                color="gray.500",
                                flex="1",
                                text_align="left"
                            ),
                            justify="space-between",
                            width="100%"
                        )
                    ),
                    max_width="600px",
                    width="90%"
                )
            ),
            is_open=self.is_open,
            on_close=lambda: print("Modal closed")  # Will update state
        )

class ShareLinkDisplay(rx.Component):
    """Component to display created share links with management options."""
    
    def __init__(
        self,
        share_url: str,
        access_level: str,
        expires_at: Optional[str] = None,
        view_count: int = 0,
        **props
    ):
        super().__init__(**props)
        self.share_url = share_url
        self.access_level = access_level
        self.expires_at = expires_at
        self.view_count = view_count
    
    def render(self):
        """Render the share link display component."""
        return rx.box(
            rx.vstack(
                # Share link header
                rx.hstack(
                    rx.icon(tag="link", color="green.500"),
                    rx.heading("Share Link Created", size="sm", color="green.600"),
                    rx.badge(
                        f"{self.access_level} Access",
                        color_scheme="green",
                        variant="subtle"
                    ),
                    justify="space-between",
                    align="center",
                    width="100%"
                ),
                
                # Share URL with copy button
                rx.hstack(
                    rx.input(
                        value=self.share_url,
                        is_read_only=True,
                        font_size="sm",
                        flex="1"
                    ),
                    rx.button(
                        rx.icon(tag="copy"),
                        size="sm",
                        color_scheme="blue",
                        on_click=lambda: print(f"Copy {self.share_url}")  # Copy to clipboard
                    ),
                    spacing="0.5rem",
                    width="100%"
                ),
                
                # Share info
                rx.hstack(
                    rx.text(
                        f"Views: {self.view_count}",
                        font_size="xs",
                        color="gray.600"
                    ),
                    rx.text(
                        f"Expires: {self.expires_at or 'Never'}",
                        font_size="xs",
                        color="gray.600"
                    ),
                    justify="space-between",
                    width="100%"
                ),
                
                # Management buttons
                rx.hstack(
                    rx.button(
                        "View Analytics",
                        size="xs",
                        variant="outline",
                        color_scheme="blue",
                        on_click=lambda: print("View analytics")
                    ),
                    rx.button(
                        "Extend Expiration",
                        size="xs",
                        variant="outline",
                        color_scheme="orange",
                        on_click=lambda: print("Extend expiration")
                    ),
                    rx.button(
                        "Revoke",
                        size="xs",
                        variant="outline",
                        color_scheme="red",
                        on_click=lambda: print("Revoke share")
                    ),
                    spacing="0.5rem",
                    width="100%",
                    justify="flex-end"
                ),
                
                spacing="0.75rem",
                align_items="stretch",
                width="100%"
            ),
            padding="1rem",
            border="1px solid",
            border_color="green.200",
            border_radius="md",
            bg="green.50",
            width="100%"
        )

class ExportProgress(rx.Component):
    """Component to show export progress and results."""
    
    def __init__(
        self,
        filename: str,
        format: str,
        status: str = "processing",  # processing, completed, failed
        progress: int = 0,
        file_size: Optional[int] = None,
        download_url: Optional[str] = None,
        **props
    ):
        super().__init__(**props)
        self.filename = filename
        self.format = format
        self.status = status
        self.progress = progress
        self.file_size = file_size
        self.download_url = download_url
    
    def render(self):
        """Render the export progress component."""
        if self.status == "processing":
            return rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.spinner(size="sm"),
                        rx.text(f"Exporting as {self.format.upper()}...", font_weight="semibold"),
                        spacing="0.5rem",
                        align="center"
                    ),
                    rx.progress(
                        value=self.progress,
                        width="100%",
                        color_scheme="blue"
                    ),
                    rx.text(
                        f"{self.progress}% complete",
                        font_size="sm",
                        color="gray.600"
                    ),
                    spacing="0.5rem",
                    align_items="stretch",
                    width="100%"
                ),
                padding="1rem",
                border="1px solid",
                border_color="blue.200",
                border_radius="md",
                bg="blue.50",
                width="100%"
            )
        
        elif self.status == "completed":
            return rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon(tag="check_circle", color="green.500"),
                        rx.text("Export Completed", font_weight="semibold", color="green.600"),
                        justify="flex-start",
                        align="center",
                        spacing="0.5rem"
                    ),
                    rx.hstack(
                        rx.text(
                            self.filename,
                            font_size="sm",
                            font_weight="medium"
                        ),
                        rx.badge(
                            self.format.upper(),
                            color_scheme="blue",
                            variant="subtle"
                        ),
                        justify="space-between",
                        align="center",
                        width="100%"
                    ),
                    rx.text(
                        f"File size: {self._format_file_size(self.file_size or 0)}",
                        font_size="xs",
                        color="gray.600"
                    ),
                    rx.hstack(
                        rx.button(
                            rx.icon(tag="download", margin_right="0.25rem"),
                            "Download",
                            size="sm",
                            color_scheme="green",
                            on_click=lambda: print(f"Download {self.download_url}")
                        ),
                        rx.button(
                            "Share",
                            size="sm",
                            variant="outline",
                            color_scheme="blue",
                            on_click=lambda: print("Share export")
                        ),
                        spacing="0.5rem",
                        justify="flex-end",
                        width="100%"
                    ),
                    spacing="0.5rem",
                    align_items="stretch",
                    width="100%"
                ),
                padding="1rem",
                border="1px solid",
                border_color="green.200",
                border_radius="md",
                bg="green.50",
                width="100%"
            )
        
        else:  # failed
            return rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon(tag="warning", color="red.500"),
                        rx.text("Export Failed", font_weight="semibold", color="red.600"),
                        justify="flex-start",
                        align="center",
                        spacing="0.5rem"
                    ),
                    rx.text(
                        "The export operation encountered an error. Please try again.",
                        font_size="sm",
                        color="red.600"
                    ),
                    rx.button(
                        "Retry Export",
                        size="sm",
                        color_scheme="red",
                        variant="outline",
                        on_click=lambda: print("Retry export")
                    ),
                    spacing="0.5rem",
                    align_items="stretch",
                    width="100%"
                ),
                padding="1rem",
                border="1px solid",
                border_color="red.200",
                border_radius="md",
                bg="red.50",
                width="100%"
            )
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"

# Usage example for the document management interface
def create_export_share_button(doc_id: str, doc_title: str):
    """Create a button that opens the export/share modal."""
    return rx.button(
        rx.icon(tag="share", margin_right="0.25rem"),
        "Export & Share",
        size="sm",
        color_scheme="blue",
        variant="outline",
        on_click=lambda: print(f"Open export/share modal for {doc_id}")
        # In actual implementation, this would update state to show the modal
    )