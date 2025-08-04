"""
Enhanced main page with all Phase 5 Week 2 UX improvements.
"""

import reflex as rx
from ..components.chat.chat_interface import chat_interface
from ..components.documents.document_manager import document_manager_section
from ..components.common.error_boundary import error_boundary
from ..components.common.health_monitor import health_monitor_widget
from ..components.common.onboarding import (
    onboarding_modal, welcome_banner, onboarding_trigger
)
from ..components.common.performance_optimizer import (
    performance_indicator, performance_metrics_panel
)
from ..components.common.responsive_design import (
    responsive_layout, responsive_container, mobile_menu_button
)
from ..components.common.accessibility import (
    accessibility_toolbar, accessibility_status_indicator, skip_link
)
from ..components.common.help_system import (
    help_panel, help_button, quick_help_shortcuts
)
from ..state.chat_state import ChatState


def enhanced_sidebar() -> rx.Component:
    """Enhanced sidebar with all UX improvements."""
    return rx.vstack(
        # Logo and title
        rx.hstack(
            rx.text(
                "🤖",
                font_size="2xl"
            ),
            rx.vstack(
                rx.text(
                    "RAG System",
                    font_size="lg",
                    font_weight="bold",
                    color="gray.800"
                ),
                rx.text(
                    "Local & Private",
                    font_size="xs",
                    color="gray.500"
                ),
                align_items="flex-start",
                spacing="0"
            ),
            spacing="0.5rem",
            align_items="center",
            margin_bottom="2rem"
        ),
        
        # Navigation
        rx.vstack(
            rx.button(
                rx.hstack(
                    rx.icon("message-circle", size=16),
                    rx.text("Chat", font_size="sm"),
                    spacing="0.5rem",
                    align_items="center"
                ),
                variant="ghost",
                size="sm",
                width="100%",
                justify_content="flex-start",
                color_scheme="blue"
            ),
            rx.button(
                rx.hstack(
                    rx.icon("file-plus", size=16),
                    rx.text("Documents", font_size="sm"),
                    spacing="0.5rem",
                    align_items="center"
                ),
                variant="ghost",
                size="sm",
                width="100%",
                justify_content="flex-start"
            ),
            rx.button(
                rx.hstack(
                    rx.icon("settings", size=16),
                    rx.text("Settings", font_size="sm"),
                    spacing="0.5rem",
                    align_items="center"
                ),
                variant="ghost",
                size="sm",
                width="100%",
                justify_content="flex-start"
            ),
            spacing="0.25rem",
            width="100%",
            margin_bottom="2rem"
        ),
        
        # Quick stats
        rx.box(
            rx.vstack(
                rx.text(
                    "Quick Stats",
                    font_size="sm",
                    font_weight="semibold",
                    color="gray.700",
                    margin_bottom="0.5rem"
                ),
                rx.hstack(
                    rx.vstack(
                        rx.text(
                            f"{ChatState.total_messages}",
                            font_size="lg",
                            font_weight="bold",
                            color="blue.600"
                        ),
                        rx.text("Messages", font_size="xs", color="gray.500"),
                        align_items="center",
                        spacing="0"
                    ),
                    rx.vstack(
                        rx.text(
                            f"{ChatState.last_response_time:.1f}s" if ChatState.last_response_time else "0.0s",
                            font_size="lg",
                            font_weight="bold",
                            color="green.600"
                        ),
                        rx.text("Last Response", font_size="xs", color="gray.500"),
                        align_items="center",
                        spacing="0"
                    ),
                    spacing="1rem",
                    width="100%",
                    justify_content="space-around"
                ),
                spacing="0.5rem",
                width="100%"
            ),
            padding="1rem",
            background_color="gray.50",
            border_radius="lg",
            margin_bottom="2rem",
            width="100%"
        ),
        
        # Performance indicator
        performance_indicator(),
        
        rx.spacer(),
        
        # Bottom actions
        rx.vstack(
            # Accessibility status
            accessibility_status_indicator(),
            
            # Help and onboarding
            rx.hstack(
                help_button(),
                onboarding_trigger(),
                spacing="0.5rem",
                width="100%",
                justify_content="center"
            ),
            
            spacing="0.5rem",
            width="100%"
        ),
        
        spacing="0.5rem",
        width="100%",
        height="100%",
        padding="1rem",
        align_items="flex-start"
    )


def enhanced_header() -> rx.Component:
    """Enhanced header with accessibility and help."""
    return rx.hstack(
        # Main title (hidden on mobile, handled by sidebar)
        rx.heading(
            "Local RAG System",
            size="lg",
            color="gray.800",
            display=["none", "none", "block"]  # Hidden on mobile/tablet
        ),
        
        rx.spacer(),
        
        # Header actions
        rx.hstack(
            # Quick help shortcuts
            quick_help_shortcuts(),
            
            # Accessibility toolbar toggle
            rx.button(
                rx.icon("accessibility", size=16),
                "A11y",
                variant="ghost",
                size="sm",
                aria_label="Accessibility options"
            ),
            
            # Settings
            rx.button(
                rx.icon("settings", size=16),
                variant="ghost",
                size="sm",
                aria_label="Settings"
            ),
            
            spacing="0.5rem",
            align_items="center"
        ),
        
        width="100%",
        align_items="center",
        padding="0.5rem 0"
    )


def main_content_area() -> rx.Component:
    """Main content area with chat and document management."""
    return rx.vstack(
        # Welcome banner for new users
        welcome_banner(),
        
        # Main chat interface
        error_boundary(
            rx.box(
                chat_interface(),
                width="100%",
                min_height="60vh"
            )
        ),
        
        # Additional sections
        rx.cond(
            ChatState.has_messages,
            rx.box(
                rx.vstack(
                    rx.divider(margin_y="2rem"),
                    
                    # Document management section
                    rx.heading("Document Management", size="lg", margin_bottom="1rem"),
                    error_boundary(document_manager_section()),
                    
                    # System health monitoring
                    rx.heading("System Status", size="lg", margin_top="2rem", margin_bottom="1rem"),
                    health_monitor_widget(),
                    
                    # Performance metrics (collapsible)
                    rx.details(
                        rx.summary(
                            rx.text("Performance Metrics", font_weight="semibold"),
                            cursor="pointer",
                            _hover={"color": "blue.600"}
                        ),
                        performance_metrics_panel(),
                        margin_top="1rem"
                    ),
                    
                    spacing="1rem",
                    width="100%",
                    align_items="flex-start"
                ),
                width="100%"
            )
        ),
        
        spacing="1rem",
        width="100%",
        align_items="flex-start"
    )


@rx.page(route="/enhanced", title="Enhanced RAG System")
def enhanced_main() -> rx.Component:
    """Enhanced main page with all UX improvements."""
    return rx.box(
        # Skip link for accessibility
        skip_link("main-content", "Skip to main content"),
        
        # Onboarding modal
        onboarding_modal(),
        
        # Help panel
        help_panel(),
        
        # Accessibility toolbar (could be toggled)
        rx.box(
            accessibility_toolbar(),
            position="fixed",
            top="100px",
            right="20px",
            z_index="999",
            display="none",  # Hidden by default, would be toggled
            id="accessibility-toolbar"
        ),
        
        # Main layout
        responsive_layout(
            sidebar=enhanced_sidebar(),
            header=enhanced_header(),
            main_content=rx.box(
                responsive_container(
                    main_content_area()
                ),
                id="main-content",  # For skip link
                width="100%"
            )
        ),
        
        # Global styles and scripts
        rx.script("""
            // Keyboard shortcuts
            document.addEventListener('keydown', function(e) {
                // Ctrl+/ for help
                if (e.ctrlKey && e.key === '/') {
                    e.preventDefault();
                    // Toggle help panel
                }
                
                // Ctrl+K for search focus
                if (e.ctrlKey && e.key === 'k') {
                    e.preventDefault();
                    const chatInput = document.querySelector('[placeholder*="message"]');
                    if (chatInput) chatInput.focus();
                }
                
                // Escape to close modals
                if (e.key === 'Escape') {
                    // Close any open modals or panels
                }
            });
            
            // Responsive design updates
            function updateScreenSize() {
                const width = window.innerWidth;
                const height = window.innerHeight;
                // This would trigger responsive state updates in a real implementation
                console.log('Screen size:', width, 'x', height);
            }
            
            window.addEventListener('resize', updateScreenSize);
            updateScreenSize();
            
            // Accessibility features
            function initAccessibility() {
                // Focus management
                document.addEventListener('keydown', function(e) {
                    if (e.key === 'Tab') {
                        document.body.classList.add('keyboard-navigation');
                    }
                });
                
                document.addEventListener('mousedown', function() {
                    document.body.classList.remove('keyboard-navigation');
                });
                
                // High contrast detection
                if (window.matchMedia('(prefers-contrast: high)').matches) {
                    document.body.classList.add('high-contrast');
                }
                
                // Reduced motion detection
                if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
                    document.body.classList.add('reduced-motion');
                }
            }
            
            initAccessibility();
        """),
        
        # Enhanced CSS
        rx.style("""
            .keyboard-navigation *:focus {
                outline: 2px solid #3182ce !important;
                outline-offset: 2px !important;
            }
            
            .high-contrast {
                filter: contrast(150%);
            }
            
            .reduced-motion * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
            
            @media (prefers-reduced-motion: reduce) {
                * {
                    animation-duration: 0.01ms !important;
                    animation-iteration-count: 1 !important;
                    transition-duration: 0.01ms !important;
                }
            }
            
            /* Mobile optimizations */
            @media (max-width: 768px) {
                .mobile-hide {
                    display: none !important;
                }
                
                .mobile-full-width {
                    width: 100% !important;
                }
                
                .mobile-small-text {
                    font-size: 0.875rem !important;
                }
            }
            
            /* Print styles */
            @media print {
                .no-print {
                    display: none !important;
                }
                
                .print-break-before {
                    page-break-before: always;
                }
            }
        """),
        
        width="100%",
        min_height="100vh",
        background_color="gray.50"
    )