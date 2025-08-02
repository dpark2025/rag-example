"""Loading spinner component."""

import reflex as rx

def loading_spinner(size: str = "2", text: str = "Loading...") -> rx.Component:
    """Create a loading spinner with optional text."""
    # Map common size names to valid Reflex spinner sizes
    size_map = {
        "sm": "1",
        "md": "2", 
        "lg": "3",
        "1": "1",
        "2": "2",
        "3": "3"
    }
    
    valid_size = size_map.get(size, "2")
    
    return rx.center(
        rx.vstack(
            rx.spinner(size=valid_size, color="blue.500"),
            rx.text(text, font_size="14px", color="gray.600") if text else rx.fragment(),
            spacing="2",
            align="center"
        ),
        padding="4"
    )