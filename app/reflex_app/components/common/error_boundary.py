"""Error handling components."""

import reflex as rx

def error_alert(
    message: str, 
    title: str = "Error", 
    status: str = "error",
    on_close = None
) -> rx.Component:
    """Create an error alert component."""
    return rx.alert(
        rx.alert_icon(),
        rx.vstack(
            rx.alert_title(title),
            rx.alert_description(message),
            spacing="1",
            align="start"
        ),
        status=status,
        variant="left-accent",
        margin_bottom="4",
        **{"on_close": on_close} if on_close else {}
    )

def error_fallback(error_message: str = "Something went wrong") -> rx.Component:
    """Fallback component for error states."""
    return rx.center(
        rx.vstack(
            rx.icon("alert-triangle", size=48, color="red.500"),
            rx.text(error_message, font_size="lg", color="red.600"),
            rx.text("Please try refreshing the page", font_size="sm", color="gray.600"),
            spacing="4",
            align="center",
            padding="8"
        ),
        min_height="200px"
    )