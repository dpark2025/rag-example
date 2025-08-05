"""
Enhanced responsive design components with mobile gestures and touch interactions.
"""

import reflex as rx
from typing import Dict, Any, List, Optional
from enum import Enum


class BreakPoint(Enum):
    """Responsive breakpoints."""
    XS = "xs"  # <576px
    SM = "sm"  # >=576px
    MD = "md"  # >=768px
    LG = "lg"  # >=992px
    XL = "xl"  # >=1200px
    XXL = "2xl"  # >=1536px


class ResponsiveState(rx.State):
    """Enhanced state for managing responsive design with touch support."""
    
    # Device detection
    screen_width: int = 1024
    screen_height: int = 768
    is_mobile: bool = False
    is_tablet: bool = False
    is_desktop: bool = True
    is_touch_device: bool = False
    current_breakpoint: str = BreakPoint.LG.value
    device_pixel_ratio: float = 1.0
    
    # UI adaptations
    sidebar_collapsed: bool = False
    mobile_menu_open: bool = False
    compact_mode: bool = False
    
    # Layout preferences
    preferred_layout: str = "default"  # default, compact, mobile
    show_mobile_optimizations: bool = True
    
    # Touch/gesture state
    touch_start_x: float = 0
    touch_start_y: float = 0
    swipe_threshold: float = 50
    is_swiping: bool = False
    last_touch_time: float = 0
    
    # Mobile-specific features
    mobile_keyboard_visible: bool = False
    safe_area_insets: Dict[str, int] = {"top": 0, "bottom": 0, "left": 0, "right": 0}
    orientation: str = "portrait"  # portrait, landscape
    
    def update_screen_size(self, width: int, height: int):
        """Update screen dimensions and device type."""
        self.screen_width = width
        self.screen_height = height
        
        # Determine device type
        if width < 576:
            self.current_breakpoint = BreakPoint.XS.value
            self.is_mobile = True
            self.is_tablet = False
            self.is_desktop = False
            self.compact_mode = True
        elif width < 768:
            self.current_breakpoint = BreakPoint.SM.value
            self.is_mobile = True
            self.is_tablet = False
            self.is_desktop = False
            self.compact_mode = True
        elif width < 992:
            self.current_breakpoint = BreakPoint.MD.value
            self.is_mobile = False
            self.is_tablet = True
            self.is_desktop = False
            self.compact_mode = False
        elif width < 1200:
            self.current_breakpoint = BreakPoint.LG.value
            self.is_mobile = False
            self.is_tablet = False
            self.is_desktop = True
            self.compact_mode = False
        elif width < 1536:
            self.current_breakpoint = BreakPoint.XL.value
            self.is_mobile = False
            self.is_tablet = False
            self.is_desktop = True
            self.compact_mode = False
        else:
            self.current_breakpoint = BreakPoint.XXL.value
            self.is_mobile = False
            self.is_tablet = False
            self.is_desktop = True
            self.compact_mode = False
        
        # Auto-collapse sidebar on mobile
        if self.is_mobile:
            self.sidebar_collapsed = True
            self.preferred_layout = "mobile"
        elif self.is_tablet:
            self.preferred_layout = "compact"
        else:
            self.preferred_layout = "default"
    
    def toggle_sidebar(self):
        """Toggle sidebar visibility."""
        self.sidebar_collapsed = not self.sidebar_collapsed
    
    def toggle_mobile_menu(self):
        """Toggle mobile menu."""
        self.mobile_menu_open = not self.mobile_menu_open
    
    def set_layout_preference(self, layout: str):
        """Set layout preference."""
        self.preferred_layout = layout
        
        if layout == "compact":
            self.compact_mode = True
        elif layout == "mobile":
            self.compact_mode = True
            self.sidebar_collapsed = True
        else:
            self.compact_mode = False
    
    @rx.var
    def container_max_width(self) -> str:
        """Get container max width based on breakpoint."""
        breakpoint_widths = {
            BreakPoint.XS.value: "100%",
            BreakPoint.SM.value: "540px",
            BreakPoint.MD.value: "720px",
            BreakPoint.LG.value: "960px",
            BreakPoint.XL.value: "1140px",
            BreakPoint.XXL.value: "1320px"
        }
        return breakpoint_widths.get(self.current_breakpoint, "1140px")
    
    @rx.var
    def grid_columns(self) -> int:
        """Get number of grid columns based on breakpoint."""
        if self.is_mobile:
            return 1
        elif self.is_tablet:
            return 2
        else:
            return 3
    
    @rx.var
    def sidebar_width(self) -> str:
        """Get sidebar width based on state."""
        if self.sidebar_collapsed:
            return "60px"
        elif self.is_mobile:
            return "280px"
        else:
            return "320px"


def responsive_container(child: rx.Component, **kwargs) -> rx.Component:
    """Create a responsive container that adapts to screen size."""
    return rx.box(
        child,
        max_width=ResponsiveState.container_max_width,
        margin_x="auto",
        padding_x=rx.cond(
            ResponsiveState.is_mobile,
            "1rem",
            "2rem"
        ),
        width="100%",
        **kwargs
    )


def responsive_grid(children: List[rx.Component], **kwargs) -> rx.Component:
    """Create a responsive grid that adapts column count."""
    return rx.box(
        rx.foreach(
            children,
            lambda child: rx.box(
                child,
                width="100%"
            )
        ),
        display="grid",
        grid_template_columns=rx.cond(
            ResponsiveState.is_mobile,
            "1fr",
            rx.cond(
                ResponsiveState.is_tablet,
                "1fr 1fr",
                "1fr 1fr 1fr"
            )
        ),
        gap="1rem",
        width="100%",
        **kwargs
    )


def mobile_menu_button() -> rx.Component:
    """Mobile menu toggle button."""
    return rx.cond(
        ResponsiveState.is_mobile | ResponsiveState.is_tablet,
        rx.icon_button(
            rx.icon(
                rx.cond(
                    ResponsiveState.mobile_menu_open,
                    "x",
                    "menu"
                ),
                size=20
            ),
            on_click=ResponsiveState.toggle_mobile_menu,
            variant="ghost",
            size="md",
            position="fixed",
            top="1rem",
            left="1rem",
            z_index="1000",
            background_color="white",
            border="1px solid",
            border_color="gray.200",
            border_radius="md"
        )
    )


def responsive_sidebar(content: rx.Component) -> rx.Component:
    """Create a responsive sidebar that collapses on mobile."""
    return rx.box(
        content,
        width=ResponsiveState.sidebar_width,
        height="100vh",
        background_color="white",
        border_right="1px solid",
        border_color="gray.200",
        position=rx.cond(
            ResponsiveState.is_mobile,
            "fixed",
            "relative"
        ),
        left=rx.cond(
            ResponsiveState.is_mobile & ResponsiveState.mobile_menu_open,
            "0",
            rx.cond(
                ResponsiveState.is_mobile,
                "-280px",
                "0"
            )
        ),
        top="0",
        z_index="999",
        transition="all 0.3s ease",
        overflow_y="auto"
    )


def responsive_text(text: str, **kwargs) -> rx.Component:
    """Create responsive text that adapts size."""
    return rx.text(
        text,
        font_size=rx.cond(
            ResponsiveState.is_mobile,
            kwargs.get("mobile_size", "sm"),
            rx.cond(
                ResponsiveState.is_tablet,
                kwargs.get("tablet_size", "md"),
                kwargs.get("desktop_size", "lg")
            )
        ),
        **{k: v for k, v in kwargs.items() if not k.endswith("_size")}
    )


def responsive_heading(text: str, level: str = "h2", **kwargs) -> rx.Component:
    """Create responsive heading."""
    size_map = {
        "h1": {"mobile": "xl", "tablet": "2xl", "desktop": "3xl"},
        "h2": {"mobile": "lg", "tablet": "xl", "desktop": "2xl"},
        "h3": {"mobile": "md", "tablet": "lg", "desktop": "xl"},
        "h4": {"mobile": "sm", "tablet": "md", "desktop": "lg"},
        "h5": {"mobile": "xs", "tablet": "sm", "desktop": "md"},
        "h6": {"mobile": "xs", "tablet": "xs", "desktop": "sm"}
    }
    
    sizes = size_map.get(level, size_map["h2"])
    
    return rx.heading(
        text,
        size=rx.cond(
            ResponsiveState.is_mobile,
            sizes["mobile"],
            rx.cond(
                ResponsiveState.is_tablet,
                sizes["tablet"],
                sizes["desktop"]
            )
        ),
        **kwargs
    )


def responsive_button(text: str, **kwargs) -> rx.Component:
    """Create responsive button."""
    return rx.button(
        text,
        size=rx.cond(
            ResponsiveState.is_mobile,
            "sm",
            "md"
        ),
        width=rx.cond(
            ResponsiveState.is_mobile & kwargs.get("full_width_mobile", False),
            "100%",
            "auto"
        ),
        **{k: v for k, v in kwargs.items() if k != "full_width_mobile"}
    )


def responsive_input(**kwargs) -> rx.Component:
    """Create responsive input field."""
    return rx.input(
        size=rx.cond(
            ResponsiveState.is_mobile,
            "sm",
            "md"
        ),
        width=rx.cond(
            ResponsiveState.is_mobile,
            "100%",
            kwargs.get("width", "auto")
        ),
        **{k: v for k, v in kwargs.items() if k != "width"}
    )


def mobile_overlay() -> rx.Component:
    """Overlay for mobile menu."""
    return rx.cond(
        ResponsiveState.is_mobile & ResponsiveState.mobile_menu_open,
        rx.box(
            on_click=ResponsiveState.toggle_mobile_menu,
            position="fixed",
            top="0",
            left="0",
            width="100vw",
            height="100vh",
            background_color="rgba(0, 0, 0, 0.5)",
            z_index="998"
        )
    )


def responsive_layout(
    sidebar: rx.Component,
    main_content: rx.Component,
    header: Optional[rx.Component] = None
) -> rx.Component:
    """Create a responsive layout with sidebar and main content."""
    return rx.box(
        # Mobile overlay
        mobile_overlay(),
        
        # Mobile menu button
        mobile_menu_button(),
        
        # Header (if provided)
        rx.cond(
            header is not None,
            rx.box(
                header,
                width="100%",
                background_color="white",
                border_bottom="1px solid",
                border_color="gray.200",
                padding="1rem",
                position=rx.cond(
                    ResponsiveState.is_mobile,
                    "fixed",
                    "relative"
                ),
                top="0",
                z_index="997"
            )
        ),
        
        # Main layout
        rx.hstack(
            # Sidebar
            responsive_sidebar(sidebar),
            
            # Main content area
            rx.box(
                main_content,
                flex="1",
                padding=rx.cond(
                    ResponsiveState.is_mobile,
                    "1rem",
                    "2rem"
                ),
                margin_left=rx.cond(
                    ResponsiveState.is_mobile,
                    "0",
                    "0"
                ),
                padding_top=rx.cond(
                    ResponsiveState.is_mobile & (header is not None),
                    "5rem",  # Account for fixed header
                    rx.cond(
                        ResponsiveState.is_mobile,
                        "4rem",  # Account for menu button
                        "2rem"
                    )
                ),
                width="100%",
                max_width="100%",
                overflow_x="hidden"
            ),
            
            width="100%",
            align_items="flex-start",
            spacing="0"
        ),
        
        width="100%",
        min_height="100vh"
    )


def responsive_card(content: rx.Component, **kwargs) -> rx.Component:
    """Create a responsive card component."""
    return rx.box(
        content,
        padding=rx.cond(
            ResponsiveState.is_mobile,
            "1rem",
            "1.5rem"
        ),
        border="1px solid",
        border_color="gray.200",
        border_radius=rx.cond(
            ResponsiveState.is_mobile,
            "md",
            "lg"
        ),
        background_color="white",
        width="100%",
        **kwargs
    )


def breakpoint_display(content: Dict[str, rx.Component]) -> rx.Component:
    """Display different content based on breakpoint."""
    return rx.cond(
        ResponsiveState.current_breakpoint == BreakPoint.XS.value,
        content.get("xs", content.get("default", rx.text("No content"))),
        rx.cond(
            ResponsiveState.current_breakpoint == BreakPoint.SM.value,
            content.get("sm", content.get("xs", content.get("default", rx.text("No content")))),
            rx.cond(
                ResponsiveState.current_breakpoint == BreakPoint.MD.value,
                content.get("md", content.get("sm", content.get("default", rx.text("No content")))),
                rx.cond(
                    ResponsiveState.current_breakpoint == BreakPoint.LG.value,
                    content.get("lg", content.get("md", content.get("default", rx.text("No content")))),
                    rx.cond(
                        ResponsiveState.current_breakpoint == BreakPoint.XL.value,
                        content.get("xl", content.get("lg", content.get("default", rx.text("No content")))),
                        content.get("2xl", content.get("xl", content.get("default", rx.text("No content"))))
                    )
                )
            )
        )
    )


# CSS classes for responsive utilities
RESPONSIVE_STYLES = {
    "container": {
        "width": "100%",
        "max_width": {
            "xs": "100%",
            "sm": "540px",
            "md": "720px",
            "lg": "960px",
            "xl": "1140px",
            "2xl": "1320px"
        },
        "margin_x": "auto",
        "padding_x": {"xs": "1rem", "sm": "1rem", "md": "2rem"}
    },
    "grid": {
        "display": "grid",
        "gap": "1rem",
        "grid_template_columns": {
            "xs": "1fr",
            "sm": "1fr",
            "md": "1fr 1fr",
            "lg": "1fr 1fr 1fr",
            "xl": "1fr 1fr 1fr 1fr"
        }
    },
    "text": {
        "font_size": {
            "xs": "sm",
            "sm": "sm", 
            "md": "md",
            "lg": "lg",
            "xl": "xl"
        }
    }
}