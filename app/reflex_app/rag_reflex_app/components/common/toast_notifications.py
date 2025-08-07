"""
Enhanced toast notification system with animations and accessibility.
"""

import reflex as rx
from typing import Literal, Optional
from enum import Enum

ToastType = Literal["success", "error", "warning", "info", "loading"]

class ToastState(rx.State):
    """State management for toast notifications."""
    
    # Current toasts list
    toasts: list[dict] = []
    
    # Auto-increment ID for unique toasts
    _next_toast_id: int = 1
    
    def add_toast(
        self, 
        message: str, 
        toast_type: ToastType = "info",
        duration: int = 5000,
        action_label: Optional[str] = None,
        action_handler: Optional[str] = None
    ):
        """Add a new toast notification."""
        toast_id = f"toast-{self._next_toast_id}"
        self._next_toast_id += 1
        
        new_toast = {
            "id": toast_id,
            "message": message,
            "type": toast_type,
            "duration": duration,
            "action_label": action_label,
            "action_handler": action_handler,
            "timestamp": rx.get_now().timestamp()
        }
        
        self.toasts.append(new_toast)
        
        # Auto-remove toast after duration (except for loading toasts)
        if toast_type != "loading" and duration > 0:
            self.set_timeout(self.remove_toast, duration / 1000, toast_id)
    
    def remove_toast(self, toast_id: str):
        """Remove a specific toast by ID."""
        self.toasts = [t for t in self.toasts if t["id"] != toast_id]
    
    def clear_all_toasts(self):
        """Clear all toast notifications."""
        self.toasts = []
    
    def update_toast(self, toast_id: str, **updates):
        """Update an existing toast (useful for loading states)."""
        for i, toast in enumerate(self.toasts):
            if toast["id"] == toast_id:
                self.toasts[i] = {**toast, **updates}
                break
    
    # Convenience methods for different toast types
    def toast_success(self, message: str, duration: int = 4000):
        """Show success toast."""
        self.add_toast(message, "success", duration)
    
    def toast_error(self, message: str, duration: int = 6000):
        """Show error toast."""
        self.add_toast(message, "error", duration)
    
    def toast_warning(self, message: str, duration: int = 5000):
        """Show warning toast."""
        self.add_toast(message, "warning", duration)
    
    def toast_info(self, message: str, duration: int = 4000):
        """Show info toast."""
        self.add_toast(message, "info", duration)
    
    def toast_loading(self, message: str) -> str:
        """Show loading toast and return its ID for later updating."""
        toast_id = f"toast-{self._next_toast_id}"
        self.add_toast(message, "loading", 0)  # No auto-dismiss
        return toast_id
    
    def dismiss_loading(self, toast_id: str, success_message: Optional[str] = None, error_message: Optional[str] = None):
        """Dismiss a loading toast and optionally show success/error."""
        self.remove_toast(toast_id)
        
        if success_message:
            self.toast_success(success_message)
        elif error_message:
            self.toast_error(error_message)


def get_toast_styles(toast_type: ToastType) -> dict:
    """Get styling for different toast types."""
    base_styles = {
        "border_radius": "xl",
        "padding": "4",
        "margin_bottom": "3",
        "backdrop_filter": "blur(20px)",
        "border": "1px solid",
        "box_shadow": "0 8px 32px rgba(0, 0, 0, 0.3)",
        "min_width": "320px",
        "max_width": "480px",
        "animation": "slideInRight 0.4s ease-out"
    }
    
    type_styles = {
        "success": {
            "bg": "rgba(34, 197, 94, 0.15)",
            "border_color": "rgba(34, 197, 94, 0.3)",
            "color": "green.100"
        },
        "error": {
            "bg": "rgba(239, 68, 68, 0.15)",
            "border_color": "rgba(239, 68, 68, 0.3)",
            "color": "red.100"
        },
        "warning": {
            "bg": "rgba(245, 158, 11, 0.15)",
            "border_color": "rgba(245, 158, 11, 0.3)",
            "color": "yellow.100"
        },
        "info": {
            "bg": "rgba(59, 130, 246, 0.15)",
            "border_color": "rgba(59, 130, 246, 0.3)",
            "color": "blue.100"
        },
        "loading": {
            "bg": "rgba(139, 92, 246, 0.15)",
            "border_color": "rgba(139, 92, 246, 0.3)",
            "color": "violet.100"
        }
    }
    
    return {**base_styles, **type_styles.get(toast_type, type_styles["info"])}


def get_toast_icon(toast_type: ToastType) -> rx.Component:
    """Get icon for toast type."""
    icons = {
        "success": rx.icon("circle-check", size=20, color="green.400"),
        "error": rx.icon("circle-x", size=20, color="red.400"),
        "warning": rx.icon("triangle-alert", size=20, color="yellow.400"),
        "info": rx.icon("info", size=20, color="blue.400"),
        "loading": rx.spinner(size="1", color="violet.400")
    }
    return icons.get(toast_type, icons["info"])


def toast_notification(toast_data: dict) -> rx.Component:
    """Individual toast notification component."""
    toast_type = toast_data.get("type", "info")
    message = toast_data.get("message", "")
    toast_id = toast_data.get("id", "")
    action_label = toast_data.get("action_label")
    
    return rx.box(
        rx.hstack(
            # Icon
            get_toast_icon(toast_type),
            
            # Message content
            rx.vstack(
                rx.text(
                    message,
                    font_size="sm",
                    font_weight="500",
                    line_height="1.4",
                    color="inherit"
                ),
                
                # Action button if provided
                rx.cond(
                    action_label,
                    rx.button(
                        action_label,
                        size="1",
                        variant="outline",
                        color_scheme="gray",
                        margin_top="2"
                    ),
                    rx.fragment()
                ),
                
                align="start",
                spacing="2",
                flex="1"
            ),
            
            # Close button
            rx.button(
                rx.icon("x", size=16),
                on_click=lambda: ToastState.remove_toast(toast_id),
                size="1",
                variant="ghost",
                color_scheme="gray",
                aria_label="Dismiss notification"
            ),
            
            align="start",
            spacing="3",
            width="100%"
        ),
        
        **get_toast_styles(toast_type),
        role="alert",
        aria_live="polite"
    )


def toast_container() -> rx.Component:
    """Container for all toast notifications."""
    return rx.box(
        rx.vstack(
            rx.foreach(
                ToastState.toasts,
                toast_notification
            ),
            spacing="0",
            align="end"
        ),
        position="fixed",
        top="20px",
        right="20px",
        z_index="9998",
        width="auto",
        max_width="500px",
        pointer_events="none",
        
        # Enable pointer events on children
        style={
            "& > *": {
                "pointer-events": "auto"
            }
        }
    )


def progress_toast(
    message: str,
    progress: float,
    toast_id: Optional[str] = None,
    show_percentage: bool = True
) -> rx.Component:
    """Special progress toast for long-running operations."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.spinner(size="1", color="violet.400"),
                rx.text(
                    message,
                    font_size="sm",
                    font_weight="500",
                    color="violet.100"
                ),
                rx.spacer(),
                rx.text(
                    f"{progress:.0f}%" if show_percentage else "",
                    font_size="xs",
                    color="violet.300"
                ),
                align="center",
                width="100%"
            ),
            
            # Progress bar
            rx.box(
                rx.box(
                    width=f"{progress}%",
                    height="100%",
                    bg="violet.400",
                    border_radius="full",
                    transition="width 0.3s ease"
                ),
                width="100%",
                height="4px",
                bg="rgba(139, 92, 246, 0.2)",
                border_radius="full",
                margin_top="2"
            ),
            
            spacing="2",
            width="100%"
        ),
        
        **get_toast_styles("loading")
    )


# Toast animation styles
def toast_animation_styles() -> rx.Component:
    """CSS animations for toast notifications."""
    return rx.html(
        """
        <style>
        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(100%);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes slideOutRight {
            from {
                opacity: 1;
                transform: translateX(0);
            }
            to {
                opacity: 0;
                transform: translateX(100%);
            }
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
            20%, 40%, 60%, 80% { transform: translateX(5px); }
        }
        
        .toast-shake {
            animation: shake 0.6s ease-in-out;
        }
        </style>
        """,
        tag="head"
    )


# Utility functions for common toast patterns
def upload_progress_toast(filename: str, progress: float) -> rx.Component:
    """Specialized toast for file upload progress."""
    return progress_toast(
        f"Uploading {filename}...",
        progress,
        show_percentage=True
    )


def batch_operation_toast(operation: str, completed: int, total: int) -> rx.Component:
    """Toast for batch operations like bulk document processing."""
    progress = (completed / total) * 100 if total > 0 else 0
    return progress_toast(
        f"{operation}: {completed}/{total} items",
        progress,
        show_percentage=False
    )


# Integration helper functions
def show_upload_success(filename: str):
    """Show success toast for successful upload."""
    ToastState.toast_success(f"✓ {filename} uploaded successfully")


def show_upload_error(filename: str, error: str):
    """Show error toast for failed upload."""
    ToastState.toast_error(f"✗ Failed to upload {filename}: {error}")


def show_processing_status(filename: str, status: str):
    """Show info toast for document processing status."""
    ToastState.toast_info(f"📄 {filename}: {status}")


def show_chat_error(error: str):
    """Show error toast for chat-related errors."""
    ToastState.toast_error(f"Chat Error: {error}")


def show_system_status(message: str, is_error: bool = False):
    """Show system status notifications."""
    if is_error:
        ToastState.toast_error(f"System: {message}")
    else:
        ToastState.toast_info(f"System: {message}")