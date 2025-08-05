"""Enhanced main application layout with animations and responsive design."""

import reflex as rx
from ..components.sidebar.system_status import system_status_panel
from ..components.common.animations import (
    fade_in, slide_in_from_left, hover_lift, 
    animation_styles, page_transition_wrapper
)
from ..components.common.toast_notifications import toast_container, toast_animation_styles
from ..components.common.keyboard_shortcuts import (
    command_palette, help_modal, keyboard_handler, keyboard_animation_styles
)
from ..components.common.loading_spinner import pulse_animation_styles
from ..components.common.responsive_design import ResponsiveState

def header_component() -> rx.Component:
    """Enhanced header component with animations and responsive design."""
    return fade_in(
        rx.hstack(
            # Logo and title
            hover_lift(
                rx.hstack(
                    rx.icon("brain-circuit", size=24, color="violet.400"),
                    rx.heading("Local RAG System", size="4", color="gray.100"),
                    spacing="3",
                    align="center"
                ),
                lift_amount="2px"
            ),
            
            rx.spacer(),
            
            # Header actions
            rx.hstack(
                # Version badge
                rx.badge(
                    "v2.0 - Enhanced",
                    color_scheme="violet",
                    variant="outline",
                    font_size="xs"
                ),
                
                # Quick action buttons for desktop
                rx.cond(
                    ResponsiveState.is_desktop,
                    rx.hstack(
                        hover_lift(
                            rx.button(
                                rx.icon("search", size=16),
                                variant="ghost",
                                size="2",
                                color_scheme="gray",
                                aria_label="Search (Ctrl+K)"
                            ),
                            lift_amount="2px"
                        ),
                        hover_lift(
                            rx.button(
                                rx.icon("upload", size=16),
                                variant="ghost", 
                                size="2",
                                color_scheme="gray",
                                aria_label="Upload (Ctrl+U)"
                            ),
                            lift_amount="2px"
                        ),
                        hover_lift(
                            rx.button(
                                rx.icon("help-circle", size=16),
                                variant="ghost",
                                size="2", 
                                color_scheme="gray",
                                aria_label="Help (Ctrl+?)"
                            ),
                            lift_amount="2px"
                        ),
                        spacing="2"
                    ),
                    rx.fragment()
                ),
                
                spacing="4",
                align="center"
            ),
            
            width="100%",
            padding="4",
            align="center"
        ),
        
        # Enhanced glass morphism styling
        border_bottom="1px solid rgba(255, 255, 255, 0.1)",
        bg="rgba(255, 255, 255, 0.05)",
        backdrop_filter="blur(20px)",
        box_shadow="0 8px 32px rgba(0, 0, 0, 0.3)",
        border="1px solid rgba(255, 255, 255, 0.08)",
        position="sticky",
        top="0",
        z_index="100"
    )

def sidebar_component() -> rx.Component:
    """Enhanced sidebar component with animations and responsive design."""
    return slide_in_from_left(
        rx.vstack(
            # Sidebar header
            fade_in(
                rx.hstack(
                    rx.icon("layers", size=20, color="violet.400"),
                    rx.heading("RAG Controls", size="5", color="gray.100"),
                    spacing="2",
                    align="center"
                ),
                delay="0.1s"
            ),
            
            # Navigation links with staggered animation
            rx.vstack(
                hover_lift(
                    rx.link(
                        rx.hstack(
                            rx.icon("message-circle", size=16, color="violet.400"),
                            rx.cond(
                                ResponsiveState.sidebar_collapsed,
                                rx.fragment(),
                                rx.text("Chat", font_size="14px", color="gray.200")
                            ),
                            spacing="3",
                            align="center"
                        ),
                        href="/",
                        padding="3",
                        border_radius="xl",
                        width="100%",
                        border="1px solid rgba(255, 255, 255, 0.05)",
                        transition="all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                        _hover={
                            "bg": "rgba(139, 92, 246, 0.15)",
                            "border_color": "rgba(139, 92, 246, 0.3)",
                            "transform": "translateX(4px)"
                        }
                    ),
                    lift_amount="2px"
                ),
                
                hover_lift(
                    rx.link(
                        rx.hstack(
                            rx.icon("file-text", size=16, color="violet.400"),
                            rx.cond(
                                ResponsiveState.sidebar_collapsed,
                                rx.fragment(),
                                rx.text("Documents", font_size="14px", color="gray.200")
                            ),
                            spacing="3",
                            align="center"
                        ),
                        href="/documents",
                        padding="3",
                        border_radius="xl",
                        width="100%",
                        border="1px solid rgba(255, 255, 255, 0.05)",
                        transition="all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                        _hover={
                            "bg": "rgba(139, 92, 246, 0.15)",
                            "border_color": "rgba(139, 92, 246, 0.3)",
                            "transform": "translateX(4px)"
                        }
                    ),
                    lift_amount="2px"
                ),
                
                hover_lift(
                    rx.link(
                        rx.hstack(
                            rx.icon("settings", size=16, color="violet.400"),
                            rx.cond(
                                ResponsiveState.sidebar_collapsed,
                                rx.fragment(),
                                rx.text("Settings", font_size="14px", color="gray.200")
                            ),
                            spacing="3",
                            align="center"
                        ),
                        href="/settings",
                        padding="3",
                        border_radius="xl",
                        width="100%",
                        border="1px solid rgba(255, 255, 255, 0.05)",
                        transition="all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                        _hover={
                            "bg": "rgba(139, 92, 246, 0.15)",
                            "border_color": "rgba(139, 92, 246, 0.3)",
                            "transform": "translateX(4px)"
                        }
                    ),
                    lift_amount="2px"
                ),
                
                spacing="3",
                width="100%",
                margin_bottom="6"
            ),
            
            # System status with delayed animation
            fade_in(
                system_status_panel(),
                delay="0.3s"
            ),
            
            # Keyboard shortcuts hint
            rx.cond(
                ResponsiveState.is_desktop & ~ResponsiveState.sidebar_collapsed,
                fade_in(
                    rx.box(
                        rx.text(
                            "💡 Press Ctrl+K for quick actions",
                            font_size="xs",
                            color="gray.400",
                            text_align="center",
                            line_height="1.4"
                        ),
                        padding="3",
                        bg="rgba(139, 92, 246, 0.1)",
                        border="1px solid rgba(139, 92, 246, 0.2)",
                        border_radius="lg",
                        width="100%"
                    ),
                    delay="0.5s"
                ),
                rx.fragment()
            ),
            
            spacing="4",
            width=rx.cond(
                ResponsiveState.sidebar_collapsed,
                "60px",
                rx.cond(ResponsiveState.is_mobile, "85vw", "280px")
            ),
            height="100vh",
            padding="4",
            border_right="1px solid rgba(255, 255, 255, 0.08)",
            bg="rgba(255, 255, 255, 0.03)",
            backdrop_filter="blur(20px)",
            box_shadow="inset 0 1px 0 rgba(255, 255, 255, 0.1)",
            overflow_y="auto",
            transition="width 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
            position=rx.cond(ResponsiveState.is_mobile, "fixed", "relative"),
            z_index=rx.cond(ResponsiveState.is_mobile, "200", "auto")
        ),
        duration="0.4s"
    )

def main_layout(page_content: rx.Component) -> rx.Component:
    """Enhanced main application layout with animations and responsive design."""
    return rx.box(
        # Global animations and styles
        animation_styles(),
        toast_animation_styles(),
        keyboard_animation_styles(),
        pulse_animation_styles(),
        
        # Keyboard handler
        keyboard_handler(),
        
        # Mobile overlay for sidebar
        rx.cond(
            ResponsiveState.is_mobile & ResponsiveState.mobile_menu_open,
            rx.box(
                on_click=ResponsiveState.toggle_mobile_menu,
                position="fixed",
                top="0",
                left="0",
                width="100vw",
                height="100vh",
                bg="rgba(0, 0, 0, 0.6)",
                backdrop_filter="blur(4px)",
                z_index="150",
                animation="fadeIn 0.3s ease-out"
            ),
            rx.fragment()
        ),
        
        # Mobile menu button
        rx.cond(
            ResponsiveState.is_mobile,
            hover_lift(
                rx.button(
                    rx.icon(
                        rx.cond(
                            ResponsiveState.mobile_menu_open,
                            "x",
                            "menu"
                        ),
                        size=20
                    ),
                    on_click=ResponsiveState.toggle_mobile_menu,
                    position="fixed",
                    top="1rem",
                    left="1rem",
                    z_index="300",
                    bg="rgba(15, 15, 35, 0.9)",
                    border="1px solid rgba(255, 255, 255, 0.2)",
                    backdrop_filter="blur(20px)",
                    color="gray.100",
                    size="3",
                    border_radius="xl",
                    _hover={
                        "bg": "rgba(139, 92, 246, 0.2)",
                        "border_color": "rgba(139, 92, 246, 0.4)"
                    }
                ),
                lift_amount="4px"
            ),
            rx.fragment()
        ),
        
        # Main layout structure
        rx.hstack(
            # Sidebar
            rx.cond(
                ResponsiveState.is_mobile,
                rx.cond(
                    ResponsiveState.mobile_menu_open,
                    sidebar_component(),
                    rx.fragment()
                ),
                sidebar_component()
            ),
            
            # Main content area
            rx.vstack(
                # Header
                header_component(),
                
                # Page content with transition wrapper
                page_transition_wrapper(
                    rx.box(
                        page_content,
                        width="100%",
                        height="calc(100vh - 80px)",
                        overflow="auto",
                        padding=rx.cond(
                            ResponsiveState.is_mobile,
                            "4",
                            "6"
                        ),
                        # Enhanced glass morphism main content
                        bg="rgba(255, 255, 255, 0.06)",
                        backdrop_filter="blur(25px)",
                        border_radius="2xl",
                        margin=rx.cond(
                            ResponsiveState.is_mobile,
                            "2",
                            "4"
                        ),
                        border="1px solid rgba(255, 255, 255, 0.1)",
                        box_shadow="""
                            0 8px 32px rgba(0, 0, 0, 0.4),
                            inset 0 1px 0 rgba(255, 255, 255, 0.15)
                        """,
                        class_name="scroll-container"
                    )
                ),
                
                spacing="0",
                width="100%",
                margin_left=rx.cond(
                    ResponsiveState.is_mobile,
                    "0",
                    rx.cond(
                        ResponsiveState.sidebar_collapsed,
                        "60px",
                        "280px"
                    )
                ),
                transition="margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1)"
            ),
            
            spacing="0",
            width="100%",
            height="100vh",
            align="start"
        ),
        
        # Global overlays
        toast_container(),
        command_palette(),
        help_modal(),
        
        # Root container styling
        width="100%",
        height="100vh",
        overflow="hidden",
        position="relative"
    )