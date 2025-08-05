"""Enhanced loading components with skeleton screens and smooth animations."""

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
            rx.spinner(
                size=valid_size, 
                color="violet.400",
                # Smooth spinning animation
                animation="spin 1s linear infinite"
            ),
            rx.text(
                text, 
                font_size="14px", 
                color="gray.300",
                # Subtle fade animation
                animation="pulse 2s ease-in-out infinite"
            ) if text else rx.fragment(),
            spacing="2",
            align="center"
        ),
        padding="4"
    )

def skeleton_box(width: str = "100%", height: str = "1rem", **kwargs) -> rx.Component:
    """Create a skeleton loading box with shimmer effect."""
    return rx.box(
        width=width,
        height=height,
        bg="""
            linear-gradient(90deg, 
                rgba(255, 255, 255, 0.05) 25%, 
                rgba(255, 255, 255, 0.15) 50%, 
                rgba(255, 255, 255, 0.05) 75%
            )
        """,
        background_size="200% 100%",
        animation="shimmer 2s ease-in-out infinite",
        border_radius="md",
        **kwargs
    )

def skeleton_text(lines: int = 3, width_variations: list = None) -> rx.Component:
    """Create skeleton text lines with varying widths."""
    if width_variations is None:
        width_variations = ["100%", "75%", "90%", "60%", "85%"]
    
    skeleton_lines = []
    for i in range(lines):
        width = width_variations[i % len(width_variations)]
        skeleton_lines.append(
            skeleton_box(
                width=width,
                height="0.875rem",
                margin_bottom="0.5rem"
            )
        )
    
    return rx.vstack(
        *skeleton_lines,
        spacing="2",
        width="100%"
    )

def skeleton_document_card() -> rx.Component:
    """Skeleton loader for document cards."""
    return rx.box(
        rx.vstack(
            # Document icon placeholder
            skeleton_box(width="2.5rem", height="2.5rem", border_radius="lg"),
            
            # Title placeholder
            skeleton_box(width="80%", height="1.25rem"),
            
            # Description placeholder
            skeleton_text(lines=2, width_variations=["100%", "60%"]),
            
            # Metadata row
            rx.hstack(
                skeleton_box(width="4rem", height="0.75rem"),
                skeleton_box(width="3rem", height="0.75rem"),
                skeleton_box(width="5rem", height="0.75rem"),
                spacing="4",
                width="100%"
            ),
            
            spacing="3",
            align="start",
            width="100%"
        ),
        padding="6",
        border="1px solid rgba(255, 255, 255, 0.1)",
        border_radius="xl",
        bg="rgba(255, 255, 255, 0.02)",
        backdrop_filter="blur(10px)",
        width="100%",
        min_height="200px"
    )

def skeleton_document_list(count: int = 6) -> rx.Component:
    """Skeleton loader for document list."""
    return rx.vstack(
        *[skeleton_document_card() for _ in range(count)],
        spacing="4",
        width="100%"
    )

def skeleton_chat_message(is_user: bool = False) -> rx.Component:
    """Skeleton loader for chat messages."""
    return rx.hstack(
        # Avatar placeholder
        skeleton_box(
            width="2.5rem", 
            height="2.5rem", 
            border_radius="full"
        ) if not is_user else rx.spacer(),
        
        # Message content
        rx.vstack(
            # Message header
            rx.hstack(
                skeleton_box(width="6rem", height="0.875rem") if not is_user else rx.spacer(),
                skeleton_box(width="4rem", height="0.75rem"),
                spacing="2",
                width="100%",
                justify="space_between" if is_user else "start"
            ),
            
            # Message text
            skeleton_text(
                lines=2 if not is_user else 1,
                width_variations=["95%", "70%"] if not is_user else ["80%"]
            ),
            
            spacing="2",
            align="start" if not is_user else "end",
            width="100%",
            max_width="70%"
        ),
        
        # User avatar placeholder
        skeleton_box(
            width="2.5rem", 
            height="2.5rem", 
            border_radius="full"
        ) if is_user else rx.spacer(),
        
        spacing="3",
        width="100%",
        justify="end" if is_user else "start",
        margin_bottom="4"
    )

def skeleton_chat_history(message_count: int = 4) -> rx.Component:
    """Skeleton loader for chat message history."""
    messages = []
    for i in range(message_count):
        # Alternate between user and assistant messages
        is_user = i % 2 == 1
        messages.append(skeleton_chat_message(is_user=is_user))
    
    return rx.vstack(
        *messages,
        spacing="4",
        width="100%",
        padding="4"
    )

def pulse_animation_styles() -> rx.Component:
    """Add CSS animations for skeleton loading effects."""
    return rx.html(
        """
        <style>
        @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 0.6; }
            50% { opacity: 1; }
        }
        
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes slideInLeft {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        @keyframes slideInRight {
            from { opacity: 0; transform: translateX(20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        .fade-in { animation: fadeIn 0.5s ease-out; }
        .slide-in-left { animation: slideInLeft 0.4s ease-out; }
        .slide-in-right { animation: slideInRight 0.4s ease-out; }
        </style>
        """,
        tag="head"
    )

def loading_overlay(text: str = "Loading...", show: bool = True) -> rx.Component:
    """Full-screen loading overlay with blur effect."""
    return rx.cond(
        show,
        rx.box(
            rx.center(
                rx.vstack(
                    rx.spinner(size="3", color="violet.400", speed="0.8s"),
                    rx.text(
                        text,
                        font_size="lg",
                        color="gray.200",
                        font_weight="500"
                    ),
                    spacing="4",
                    align="center"
                ),
                height="100%"
            ),
            position="fixed",
            top="0",
            left="0",
            width="100vw",
            height="100vh",
            bg="rgba(15, 15, 35, 0.95)",
            backdrop_filter="blur(12px)",
            z_index="9999",
            animation="fadeIn 0.3s ease-out"
        ),
        rx.fragment()
    )