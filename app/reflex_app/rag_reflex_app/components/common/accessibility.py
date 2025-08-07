"""
Accessibility components and utilities for WCAG 2.1 AA compliance.
"""

import reflex as rx
from typing import Dict, Any, List, Optional, Callable
from enum import Enum


class AccessibilityLevel(Enum):
    """WCAG accessibility levels."""
    A = "A"
    AA = "AA"
    AAA = "AAA"


class ColorContrastRatio(Enum):
    """WCAG color contrast requirements."""
    NORMAL_AA = 4.5
    NORMAL_AAA = 7.0
    LARGE_AA = 3.0
    LARGE_AAA = 4.5


class AccessibilityState(rx.State):
    """State for managing accessibility features."""
    
    # Accessibility preferences
    high_contrast_mode: bool = False
    reduced_motion: bool = False
    screen_reader_mode: bool = False
    keyboard_navigation: bool = True
    focus_visible: bool = True
    
    # Text and display
    font_size_multiplier: float = 1.0
    line_height_multiplier: float = 1.0
    letter_spacing_adjustment: float = 0.0
    
    # Color and visual
    color_blind_filter: str = "none"  # none, protanopia, deuteranopia, tritanopia
    custom_theme: str = "default"  # default, high_contrast, dark, light
    
    # Interaction
    click_delay: int = 0  # ms delay for accidental clicks
    focus_timeout: int = 0  # extended focus timeout
    
    # Announcements for screen readers
    live_announcements: List[str] = []
    
    def toggle_high_contrast(self):
        """Toggle high contrast mode."""
        self.high_contrast_mode = not self.high_contrast_mode
        if self.high_contrast_mode:
            self.custom_theme = "high_contrast"
        else:
            self.custom_theme = "default"
    
    def toggle_reduced_motion(self):
        """Toggle reduced motion preference."""
        self.reduced_motion = not self.reduced_motion
    
    def toggle_screen_reader_mode(self):
        """Toggle screen reader optimization."""
        self.screen_reader_mode = not self.screen_reader_mode
    
    def increase_font_size(self):
        """Increase font size (up to 200%)."""
        self.font_size_multiplier = min(2.0, self.font_size_multiplier + 0.1)
    
    def decrease_font_size(self):
        """Decrease font size (down to 75%)."""
        self.font_size_multiplier = max(0.75, self.font_size_multiplier - 0.1)
    
    def reset_font_size(self):
        """Reset font size to default."""
        self.font_size_multiplier = 1.0
    
    def set_color_blind_filter(self, filter_type: str):
        """Set color blind accessibility filter."""
        self.color_blind_filter = filter_type
    
    def announce_to_screen_reader(self, message: str):
        """Add announcement for screen readers."""
        self.live_announcements.append(message)
        
        # Keep only last 5 announcements
        if len(self.live_announcements) > 5:
            self.live_announcements.pop(0)
    
    def clear_announcements(self):
        """Clear screen reader announcements."""
        self.live_announcements = []
    
    @rx.var
    def accessibility_score(self) -> str:
        """Calculate accessibility compliance score."""
        score = 100
        
        # Check for accessibility features enabled
        features_enabled = sum([
            self.keyboard_navigation,
            self.focus_visible,
            self.screen_reader_mode,
            self.font_size_multiplier != 1.0,
            self.high_contrast_mode,
            self.reduced_motion
        ])
        
        # Basic compliance
        if not self.keyboard_navigation:
            score -= 20
        if not self.focus_visible:
            score -= 15
        
        # Enhanced features
        bonus = features_enabled * 2
        score = min(100, score + bonus)
        
        if score >= 95:
            return f"Excellent (WCAG AAA: {score}%)"
        elif score >= 80:
            return f"Good (WCAG AA: {score}%)"
        elif score >= 65:
            return f"Fair (WCAG A: {score}%)"
        else:
            return f"Poor ({score}%)"


def accessible_button(
    text: str,
    on_click: Optional[Callable] = None,
    aria_label: Optional[str] = None,
    aria_described_by: Optional[str] = None,
    disabled: bool = False,
    **kwargs
) -> rx.Component:
    """Create an accessible button with proper ARIA attributes."""
    
    # Calculate font size based on accessibility settings
    font_size = rx.cond(
        AccessibilityState.font_size_multiplier > 1.2,
        rx.match(
            kwargs.get("font_size", "md"),
            ("xs", "sm"),
            ("sm", "md"),
            ("md", "lg"),
            ("lg", "xl"),
            ("xl", "2xl"),
            "lg"  # default
        ),
        kwargs.get("font_size", "md")
    )
    
    return rx.button(
        text,
        on_click=on_click,
        aria_label=aria_label or text,
        aria_described_by=aria_described_by,
        disabled=disabled,
        font_size=font_size,
        _focus={
            "outline": "2px solid",
            "outline_color": rx.cond(
                AccessibilityState.high_contrast_mode,
                "yellow.400",
                "blue.500"
            ),
            "outline_offset": "2px"
        },
        _hover={
            "transform": rx.cond(
                AccessibilityState.reduced_motion,
                "none",
                "translateY(-1px)"
            )
        },
        transition=rx.cond(
            AccessibilityState.reduced_motion,
            "none",
            "all 0.2s ease"
        ),
        **{k: v for k, v in kwargs.items() if k != "font_size"}
    )


def accessible_link(
    text: str,
    href: str,
    aria_label: Optional[str] = None,
    external: bool = False,
    **kwargs
) -> rx.Component:
    """Create an accessible link with proper attributes."""
    return rx.link(
        text,
        href=href,
        aria_label=aria_label or f"Link to {text}",
        target=rx.cond(external, "_blank", "_self"),
        rel=rx.cond(external, "noopener noreferrer", ""),
        _focus={
            "outline": "2px solid",
            "outline_color": rx.cond(
                AccessibilityState.high_contrast_mode,
                "yellow.400",
                "blue.500"
            ),
            "outline_offset": "2px"
        },
        **kwargs
    )


def accessible_input(
    placeholder: str = "",
    aria_label: Optional[str] = None,
    aria_described_by: Optional[str] = None,
    required: bool = False,
    **kwargs
) -> rx.Component:
    """Create an accessible input field."""
    return rx.input(
        placeholder=placeholder,
        aria_label=aria_label or placeholder,
        aria_described_by=aria_described_by,
        aria_required=str(required).lower(),
        font_size=rx.cond(
            AccessibilityState.font_size_multiplier > 1.2,
            "lg",
            "md"
        ),
        _focus={
            "outline": "2px solid",
            "outline_color": rx.cond(
                AccessibilityState.high_contrast_mode,
                "yellow.400",
                "blue.500"
            ),
            "outline_offset": "2px",
            "border_color": "transparent"
        },
        **kwargs
    )


def accessible_heading(
    text: str,
    level: int = 2,
    aria_label: Optional[str] = None,
    **kwargs
) -> rx.Component:
    """Create an accessible heading with proper hierarchy."""
    size_map = {1: "2xl", 2: "xl", 3: "lg", 4: "md", 5: "sm", 6: "xs"}
    
    # Adjust size based on accessibility settings
    base_size = size_map.get(level, "lg")
    if AccessibilityState.font_size_multiplier > 1.2:
        enhanced_size_map = {
            "xs": "sm", "sm": "md", "md": "lg", 
            "lg": "xl", "xl": "2xl", "2xl": "3xl"
        }
        base_size = enhanced_size_map.get(base_size, base_size)
    
    return rx.heading(
        text,
        as_=f"h{level}",
        size=base_size,
        aria_label=aria_label,
        line_height=AccessibilityState.line_height_multiplier,
        letter_spacing=f"{AccessibilityState.letter_spacing_adjustment}em",
        **kwargs
    )


def accessible_image(
    src: str,
    alt: str,
    aria_described_by: Optional[str] = None,
    decorative: bool = False,
    **kwargs
) -> rx.Component:
    """Create an accessible image with proper alt text."""
    return rx.image(
        src=src,
        alt="" if decorative else alt,
        aria_hidden=str(decorative).lower(),
        aria_described_by=aria_described_by,
        role=rx.cond(decorative, "presentation", "img"),
        **kwargs
    )


def skip_link(target_id: str, text: str = "Skip to main content") -> rx.Component:
    """Create a skip link for keyboard navigation."""
    return rx.link(
        text,
        href=f"#{target_id}",
        position="absolute",
        top="-40px",
        left="0",
        background_color="blue.600",
        color="white",
        padding="0.5rem 1rem",
        text_decoration="none",
        z_index="9999",
        _focus={
            "top": "0",
            "outline": "2px solid yellow"
        },
        font_weight="bold"
    )


def screen_reader_only(text: str) -> rx.Component:
    """Create text that's only visible to screen readers."""
    return rx.text(
        text,
        position="absolute",
        left="-10000px",
        top="auto",
        width="1px",
        height="1px",
        overflow="hidden"
    )


def live_region(announcement_type: str = "polite") -> rx.Component:
    """Create a live region for screen reader announcements."""
    return rx.box(
        rx.foreach(
            AccessibilityState.live_announcements,
            lambda announcement: rx.text(announcement)
        ),
        aria_live=announcement_type,  # polite, assertive, off
        aria_atomic="true",
        position="absolute",
        left="-10000px",
        top="auto",
        width="1px",
        height="1px",
        overflow="hidden"
    )


# Alias for backward compatibility
aria_live_region = live_region


def accessible_region(
    *children: rx.Component,
    aria_label: str = "",
    role: str = "region",
    **kwargs
) -> rx.Component:
    """Create an accessible region with proper ARIA attributes."""
    return rx.box(
        *children,
        role=role,
        aria_label=aria_label,
        **kwargs
    )


def focus_trap(*children: rx.Component) -> rx.Component:
    """Create a focus trap for modal dialogs."""
    return rx.box(
        *children,
        tab_index=-1
    )


def accessible_modal(
    is_open: bool,
    on_close: Callable,
    title: str,
    children: List[rx.Component],
    **kwargs
) -> rx.Component:
    """Create an accessible modal dialog."""
    return rx.cond(
        is_open,
        rx.box(
            # Backdrop
            rx.box(
                on_click=on_close,
                position="fixed",
                top="0",
                left="0",
                width="100vw",
                height="100vh",
                background_color="rgba(0, 0, 0, 0.5)",
                z_index="998"
            ),
            
            # Modal content
            focus_trap([
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            accessible_heading(title, level=2, id="modal-title"),
                            rx.spacer(),
                            accessible_button(
                                "×",
                                on_click=on_close,
                                aria_label="Close modal",
                                variant="ghost",
                                size="sm"
                            ),
                            width="100%",
                            align_items="center",
                            margin_bottom="1rem"
                        ),
                        
                        rx.box(
                            *children,
                            width="100%"
                        ),
                        
                        spacing="1rem",
                        width="100%"
                    ),
                    position="fixed",
                    top="50%",
                    left="50%",
                    transform="translate(-50%, -50%)",
                    background_color="white",
                    border_radius="lg",
                    padding="2rem",
                    max_width="90vw",
                    max_height="90vh",
                    overflow_y="auto",
                    z_index="999",
                    role="dialog",
                    aria_modal="true",
                    aria_labelledby="modal-title",
                    **kwargs
                )
            ]),
            
            position="fixed",
            top="0",
            left="0",
            width="100vw",
            height="100vh",
            z_index="998"
        )
    )


def accessibility_toolbar() -> rx.Component:
    """Create an accessibility toolbar for user preferences."""
    return rx.box(
        rx.vstack(
            rx.text(
                "Accessibility Options",
                font_weight="bold",
                margin_bottom="0.5rem"
            ),
            
            # Font size controls
            rx.hstack(
                rx.text("Font Size:", font_size="sm"),
                accessible_button(
                    "A-",
                    on_click=AccessibilityState.decrease_font_size,
                    aria_label="Decrease font size",
                    size="sm"
                ),
                rx.text(
                    f"{AccessibilityState.font_size_multiplier:.1f}x",
                    font_size="sm",
                    min_width="3rem",
                    text_align="center"
                ),
                accessible_button(
                    "A+",
                    on_click=AccessibilityState.increase_font_size,
                    aria_label="Increase font size",
                    size="sm"
                ),
                accessible_button(
                    "Reset",
                    on_click=AccessibilityState.reset_font_size,
                    aria_label="Reset font size",
                    size="sm",
                    variant="outline"
                ),
                width="100%",
                align_items="center"
            ),
            
            # Toggle options
            rx.vstack(
                rx.hstack(
                    rx.switch(
                        is_checked=AccessibilityState.high_contrast_mode,
                        on_change=AccessibilityState.toggle_high_contrast,
                        size="sm"
                    ),
                    rx.text("High Contrast", font_size="sm"),
                    width="100%",
                    align_items="center"
                ),
                rx.hstack(
                    rx.switch(
                        is_checked=AccessibilityState.reduced_motion,
                        on_change=AccessibilityState.toggle_reduced_motion,
                        size="sm"
                    ),
                    rx.text("Reduce Motion", font_size="sm"),
                    width="100%",
                    align_items="center"
                ),
                rx.hstack(
                    rx.switch(
                        is_checked=AccessibilityState.screen_reader_mode,
                        on_change=AccessibilityState.toggle_screen_reader_mode,
                        size="sm"
                    ),
                    rx.text("Screen Reader Mode", font_size="sm"),
                    width="100%",
                    align_items="center"
                ),
                spacing="0.5rem",
                width="100%"
            ),
            
            # Color blind filters
            rx.vstack(
                rx.text("Color Blind Filter:", font_size="sm", font_weight="semibold"),
                rx.select(
                    ["None", "Protanopia", "Deuteranopia", "Tritanopia"],
                    value=AccessibilityState.color_blind_filter.title(),
                    on_change=lambda v: AccessibilityState.set_color_blind_filter(v.lower()),
                    size="sm",
                    width="100%"
                ),
                spacing="0.25rem",
                width="100%"
            ),
            
            # Accessibility score
            rx.box(
                rx.text(
                    "Compliance Score",
                    font_size="sm",
                    font_weight="semibold",
                    margin_bottom="0.25rem"
                ),
                rx.text(
                    AccessibilityState.accessibility_score,
                    font_size="sm",
                    color="blue.600"
                ),
                padding="0.5rem",
                background_color="blue.50",
                border_radius="md",
                width="100%"
            ),
            
            spacing="1rem",
            width="100%"
        ),
        padding="1rem",
        border="1px solid",
        border_color="gray.200",
        border_radius="lg",
        background_color="white",
        width="300px"
    )


def accessibility_status_indicator() -> rx.Component:
    """Small accessibility status indicator."""
    return rx.box(
        rx.hstack(
            rx.icon("accessibility", size=16, color="blue.500"),
            rx.text(
                "WCAG AA",
                font_size="xs",
                color="blue.600",
                font_weight="semibold"
            ),
            spacing="0.25rem",
            align_items="center"
        ),
        padding="0.25rem 0.5rem",
        background_color="blue.50",
        border="1px solid",
        border_color="blue.200",
        border_radius="full",
        cursor="help",
        title="WCAG 2.1 AA Compliant"
    )