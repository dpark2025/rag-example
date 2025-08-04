"""
Error boundary component for graceful error handling in Reflex UI.
"""

import reflex as rx
from typing import Optional, Dict, Any


class ErrorState(rx.State):
    """State for managing application errors."""
    
    # Error tracking
    has_error: bool = False
    error_message: str = ""
    error_code: str = ""
    recovery_action: str = ""
    show_details: bool = False
    
    # Error history
    error_history: list[Dict[str, Any]] = []
    
    def handle_error(self, error_data: Dict[str, Any]):
        """Handle an error from the backend."""
        self.has_error = True
        self.error_message = error_data.get("user_message", "An unexpected error occurred")
        self.error_code = error_data.get("error_code", "UNKNOWN")
        self.recovery_action = error_data.get("recovery_action", "none")
        
        # Add to history
        self.error_history.append({
            "timestamp": error_data.get("timestamp", ""),
            "message": self.error_message,
            "code": self.error_code
        })
        
        # Keep only last 10 errors
        if len(self.error_history) > 10:
            self.error_history.pop(0)
    
    def clear_error(self):
        """Clear the current error."""
        self.has_error = False
        self.error_message = ""
        self.error_code = ""
        self.recovery_action = ""
        self.show_details = False
    
    def toggle_details(self):
        """Toggle error details display."""
        self.show_details = not self.show_details
    
    def retry_action(self):
        """Retry the failed action."""
        self.clear_error()
        # The specific retry logic would be implemented
        # by the component that failed


def error_display() -> rx.Component:
    """Display error messages with recovery options."""
    return rx.cond(
        ErrorState.has_error,
        rx.box(
            rx.vstack(
                # Error header
                rx.hstack(
                    rx.icon("alert-circle", color="red", size=20),
                    rx.text(
                        "Error Occurred",
                        font_weight="bold",
                        color="red.600"
                    ),
                    rx.spacer(),
                    rx.icon_button(
                        rx.icon("x", size=16),
                        on_click=ErrorState.clear_error,
                        variant="ghost",
                        size="sm"
                    ),
                    width="100%",
                    align_items="center"
                ),
                
                # Error message
                rx.text(
                    ErrorState.error_message,
                    color="gray.700",
                    margin_top="0.5rem"
                ),
                
                # Recovery actions
                rx.cond(
                    ErrorState.recovery_action != "none",
                    rx.hstack(
                        rx.cond(
                            ErrorState.recovery_action == "retry",
                            rx.button(
                                "Retry",
                                on_click=ErrorState.retry_action,
                                size="sm",
                                variant="outline",
                                color_scheme="blue"
                            )
                        ),
                        rx.cond(
                            ErrorState.recovery_action == "refresh",
                            rx.button(
                                "Refresh Page",
                                on_click=rx.redirect("/"),
                                size="sm",
                                variant="outline",
                                color_scheme="blue"
                            )
                        ),
                        rx.cond(
                            ErrorState.recovery_action == "check_connection",
                            rx.text(
                                "Please check your internet connection",
                                font_size="sm",
                                color="gray.600"
                            )
                        ),
                        margin_top="0.5rem"
                    )
                ),
                
                # Details toggle
                rx.button(
                    rx.cond(
                        ErrorState.show_details,
                        "Hide Details",
                        "Show Details"
                    ),
                    on_click=ErrorState.toggle_details,
                    size="sm",
                    variant="ghost",
                    margin_top="0.5rem"
                ),
                
                # Error details
                rx.cond(
                    ErrorState.show_details,
                    rx.box(
                        rx.text(
                            f"Error Code: {ErrorState.error_code}",
                            font_size="sm",
                            font_family="monospace",
                            color="gray.600"
                        ),
                        padding="0.5rem",
                        background_color="gray.50",
                        border_radius="md",
                        margin_top="0.5rem",
                        width="100%"
                    )
                ),
                
                width="100%",
                spacing="0.5rem"
            ),
            padding="1rem",
            border="1px solid",
            border_color="red.200",
            border_radius="lg",
            background_color="red.50",
            margin_bottom="1rem"
        )
    )


def error_boundary(child: rx.Component) -> rx.Component:
    """
    Wrap a component with error handling.
    
    Args:
        child: The component to wrap
        
    Returns:
        Component with error handling
    """
    return rx.vstack(
        error_display(),
        child,
        width="100%",
        spacing="0"
    )


def with_error_handling(component_func):
    """
    Decorator to add error handling to a component function.
    
    Usage:
        @with_error_handling
        def my_component():
            return rx.text("Hello")
    """
    def wrapper(*args, **kwargs):
        child = component_func(*args, **kwargs)
        return error_boundary(child)
    return wrapper