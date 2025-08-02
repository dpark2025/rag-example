"""Loading spinner component."""

import reflex as rx

def loading_spinner(size: str = "md", text: str = "Loading...") -> rx.Component:
    """Create a loading spinner with optional text."""
    return rx.center(
        rx.vstack(
            rx.spinner(size=size, color="blue.500"),
            rx.text(text, font_size="sm", color="gray.600") if text else rx.fragment(),
            spacing="2",
            align="center"
        ),
        padding="4"
    )