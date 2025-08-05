"""
Smooth animations and transitions for enhanced user experience.
"""

import reflex as rx
from typing import Optional, Dict, Any, Union, List
from enum import Enum

class AnimationType(Enum):
    """Animation types."""
    FADE_IN = "fadeIn"
    FADE_OUT = "fadeOut"
    SLIDE_IN_LEFT = "slideInLeft"
    SLIDE_IN_RIGHT = "slideInRight"
    SLIDE_IN_UP = "slideInUp"
    SLIDE_IN_DOWN = "slideInDown"
    SLIDE_OUT_LEFT = "slideOutLeft"
    SLIDE_OUT_RIGHT = "slideOutRight"
    SLIDE_OUT_UP = "slideOutUp"
    SLIDE_OUT_DOWN = "slideOutDown"
    SCALE_IN = "scaleIn"
    SCALE_OUT = "scaleOut"
    BOUNCE_IN = "bounceIn"
    PULSE = "pulse"
    SHAKE = "shake"
    FLIP_IN_X = "flipInX"
    FLIP_IN_Y = "flipInY"
    ROTATE_IN = "rotateIn"
    ZOOM_IN = "zoomIn"
    ZOOM_OUT = "zoomOut"

class AnimationState(rx.State):
    """State for managing animations and transitions."""
    
    # Animation preferences
    enable_animations: bool = True
    reduce_motion: bool = False
    animation_speed: float = 1.0  # Speed multiplier
    
    # Current animations
    active_animations: Dict[str, str] = {}
    
    # Page transition state
    page_transitioning: bool = False
    transition_direction: str = "right"  # left, right, up, down
    
    def set_reduce_motion(self, reduce: bool):
        """Set reduced motion preference."""
        self.reduce_motion = reduce
        if reduce:
            self.enable_animations = False
        else:
            self.enable_animations = True
    
    def set_animation_speed(self, speed: float):
        """Set animation speed multiplier."""
        self.animation_speed = max(0.1, min(3.0, speed))
    
    def start_animation(self, element_id: str, animation: AnimationType):
        """Start an animation for an element."""
        if self.enable_animations and not self.reduce_motion:
            self.active_animations[element_id] = animation.value
    
    def stop_animation(self, element_id: str):
        """Stop an animation for an element."""
        if element_id in self.active_animations:
            del self.active_animations[element_id]
    
    def clear_all_animations(self):
        """Clear all active animations."""
        self.active_animations = {}
    
    def start_page_transition(self, direction: str = "right"):
        """Start page transition."""
        self.page_transitioning = True
        self.transition_direction = direction
    
    def end_page_transition(self):
        """End page transition."""
        self.page_transitioning = False

def animated_box(
    children: Union[rx.Component, List[rx.Component]],
    animation: AnimationType = AnimationType.FADE_IN,
    duration: str = "0.5s",
    delay: str = "0s",
    easing: str = "ease-out",
    infinite: bool = False,
    **kwargs
) -> rx.Component:
    """Create an animated box with specified animation."""
    
    if not isinstance(children, list):
        children = [children]
    
    animation_props = {
        "animation": f"{animation.value} {duration} {delay} {easing}",
        "animation_fill_mode": "both"
    }
    
    if infinite:
        animation_props["animation_iteration_count"] = "infinite"
    
    # Respect reduced motion preference
    animation_props["animation"] = rx.cond(
        AnimationState.reduce_motion,
        "none",
        animation_props["animation"]
    )
    
    return rx.box(
        *children,
        **animation_props,
        **kwargs
    )

def fade_in(
    children: Union[rx.Component, List[rx.Component]],
    duration: str = "0.5s",
    delay: str = "0s",
    **kwargs
) -> rx.Component:
    """Fade in animation wrapper."""
    return animated_box(
        children,
        animation=AnimationType.FADE_IN,
        duration=duration,
        delay=delay,
        **kwargs
    )

def slide_in_from_left(
    children: Union[rx.Component, List[rx.Component]],
    duration: str = "0.4s",
    delay: str = "0s",
    **kwargs
) -> rx.Component:
    """Slide in from left animation wrapper."""
    return animated_box(
        children,
        animation=AnimationType.SLIDE_IN_LEFT,
        duration=duration,
        delay=delay,
        **kwargs
    )

def slide_in_from_right(
    children: Union[rx.Component, List[rx.Component]],
    duration: str = "0.4s",
    delay: str = "0s",
    **kwargs
) -> rx.Component:
    """Slide in from right animation wrapper."""
    return animated_box(
        children,
        animation=AnimationType.SLIDE_IN_RIGHT,
        duration=duration,
        delay=delay,
        **kwargs
    )

def slide_in_from_up(
    children: Union[rx.Component, List[rx.Component]],
    duration: str = "0.4s",
    delay: str = "0s",
    **kwargs
) -> rx.Component:
    """Slide in from top animation wrapper."""
    return animated_box(
        children,
        animation=AnimationType.SLIDE_IN_UP,
        duration=duration,
        delay=delay,
        **kwargs
    )

def scale_in(
    children: Union[rx.Component, List[rx.Component]],
    duration: str = "0.3s",
    delay: str = "0s",
    **kwargs
) -> rx.Component:
    """Scale in animation wrapper."""
    return animated_box(
        children,
        animation=AnimationType.SCALE_IN,
        duration=duration,
        delay=delay,
        **kwargs
    )

def staggered_fade_in(
    children: List[rx.Component],
    stagger_delay: float = 0.1,
    base_duration: str = "0.5s",
    **kwargs
) -> rx.Component:
    """Create staggered fade-in animations for a list of components."""
    animated_children = []
    
    for i, child in enumerate(children):
        delay = f"{i * stagger_delay}s"
        animated_children.append(
            fade_in(
                child,
                duration=base_duration,
                delay=delay,
                **kwargs
            )
        )
    
    return rx.vstack(*animated_children, spacing="0")

def hover_lift(
    children: Union[rx.Component, List[rx.Component]],
    lift_amount: str = "4px",
    **kwargs
) -> rx.Component:
    """Add hover lift effect to components."""
    
    if not isinstance(children, list):
        children = [children]
    
    return rx.box(
        *children,
        transition=rx.cond(
            AnimationState.reduce_motion,
            "none",
            "all 0.2s ease-out"
        ),
        _hover={
            "transform": rx.cond(
                AnimationState.reduce_motion,
                "none",
                f"translateY(-{lift_amount})"
            ),
            "box_shadow": rx.cond(
                AnimationState.reduce_motion,
                "none",
                "0 8px 25px rgba(0, 0, 0, 0.15)"
            )
        },
        **kwargs
    )

def micro_interaction_button(
    text: str,
    on_click: Optional[callable] = None,
    variant: str = "default",
    **kwargs
) -> rx.Component:
    """Button with micro-interaction animations."""
    return rx.button(
        text,
        on_click=on_click,
        transition=rx.cond(
            AnimationState.reduce_motion,
            "none",
            "all 0.15s ease-out"
        ),
        _hover={
            "transform": rx.cond(
                AnimationState.reduce_motion,
                "none",
                "translateY(-1px)"
            ),
            "box_shadow": rx.cond(
                AnimationState.reduce_motion,
                "none",
                "0 4px 12px rgba(139, 92, 246, 0.4)"
            )
        },
        _active={
            "transform": rx.cond(
                AnimationState.reduce_motion,
                "none",
                "translateY(0) scale(0.98)"
            )
        },
        **kwargs
    )

def loading_pulse(
    children: Union[rx.Component, List[rx.Component]],
    **kwargs
) -> rx.Component:
    """Add pulsing animation for loading states."""
    return animated_box(
        children,
        animation=AnimationType.PULSE,
        duration="2s",
        infinite=True,
        **kwargs
    )

def attention_shake(
    children: Union[rx.Component, List[rx.Component]],
    trigger_shake: bool = False,
    **kwargs
) -> rx.Component:
    """Add shake animation for attention/error states."""
    return rx.box(
        *children if isinstance(children, list) else [children],
        animation=rx.cond(
            trigger_shake & ~AnimationState.reduce_motion,
            "shake 0.6s ease-in-out",
            "none"
        ),
        **kwargs
    )

def page_transition_wrapper(
    children: Union[rx.Component, List[rx.Component]],
    **kwargs
) -> rx.Component:
    """Wrapper for page transitions."""
    
    if not isinstance(children, list):
        children = [children]
    
    return rx.box(
        *children,
        opacity=rx.cond(
            AnimationState.page_transitioning,
            "0",
            "1"
        ),
        transform=rx.cond(
            AnimationState.page_transitioning,
            rx.cond(
                AnimationState.transition_direction == "right",
                "translateX(20px)",
                rx.cond(
                    AnimationState.transition_direction == "left",
                    "translateX(-20px)",
                    rx.cond(
                        AnimationState.transition_direction == "up",
                        "translateY(-20px)",
                        "translateY(20px)"
                    )
                )
            ),
            "translateX(0) translateY(0)"
        ),
        transition=rx.cond(
            AnimationState.reduce_motion,
            "none",
            "all 0.3s ease-out"
        ),
        **kwargs
    )

def reveal_on_scroll(
    children: Union[rx.Component, List[rx.Component]],
    threshold: float = 0.1,
    **kwargs
) -> rx.Component:
    """Reveal animation when element comes into view."""
    
    if not isinstance(children, list):
        children = [children]
    
    return rx.box(
        *children,
        class_name="reveal-on-scroll",
        style={
            "opacity": "0",
            "transform": "translateY(30px)",
            "transition": rx.cond(
                AnimationState.reduce_motion,
                "none",
                "all 0.6s ease-out"
            )
        },
        **kwargs
    )

def floating_action_button(
    icon: str,
    on_click: Optional[callable] = None,
    position: Dict[str, str] = None,
    **kwargs
) -> rx.Component:
    """Floating action button with animation."""
    
    if position is None:
        position = {"bottom": "2rem", "right": "2rem"}
    
    return rx.button(
        rx.icon(icon, size=24),
        on_click=on_click,
        position="fixed",
        z_index="1000",
        width="56px",
        height="56px",
        border_radius="50%",
        bg="violet.500",
        color="white",
        box_shadow="0 4px 20px rgba(139, 92, 246, 0.4)",
        transition=rx.cond(
            AnimationState.reduce_motion,
            "none",
            "all 0.3s ease-out"
        ),
        _hover={
            "transform": rx.cond(
                AnimationState.reduce_motion,
                "none",
                "scale(1.1)"
            ),
            "box_shadow": rx.cond(
                AnimationState.reduce_motion,
                "0 4px 20px rgba(139, 92, 246, 0.4)",
                "0 6px 25px rgba(139, 92, 246, 0.6)"
            )
        },
        _active={
            "transform": rx.cond(
                AnimationState.reduce_motion,
                "none",
                "scale(0.95)"
            )
        },
        **position,
        **kwargs
    )

def progress_bar_animated(
    progress: float,
    height: str = "4px",
    color: str = "violet.500",
    bg_color: str = "gray.200",
    **kwargs
) -> rx.Component:
    """Animated progress bar."""
    return rx.box(
        rx.box(
            width=f"{progress}%",
            height="100%",
            bg=color,
            border_radius="full",
            transition=rx.cond(
                AnimationState.reduce_motion,
                "none",
                "width 0.5s ease-out"
            )
        ),
        width="100%",
        height=height,
        bg=bg_color,
        border_radius="full",
        overflow="hidden",
        **kwargs
    )

def typewriter_text(
    text: str,
    speed: int = 50,  # milliseconds per character
    **kwargs
) -> rx.Component:
    """Typewriter animation effect for text."""
    return rx.text(
        text,
        class_name="typewriter-text",
        **kwargs
    )

def morph_button(
    default_text: str,
    loading_text: str,
    success_text: str,
    is_loading: bool = False,
    is_success: bool = False,
    on_click: Optional[callable] = None,
    **kwargs
) -> rx.Component:
    """Button that morphs between states with animations."""
    
    return rx.button(
        rx.cond(
            is_loading,
            rx.hstack(
                rx.spinner(size="1", color="white"),
                rx.text(loading_text),
                spacing="2",
                align="center"
            ),
            rx.cond(
                is_success,
                rx.hstack(
                    rx.icon("check", size=16, color="white"),
                    rx.text(success_text),
                    spacing="2",
                    align="center"
                ),
                rx.text(default_text)
            )
        ),
        on_click=on_click,
        disabled=is_loading,
        bg=rx.cond(
            is_success,
            "green.500",
            rx.cond(is_loading, "violet.400", "violet.500")
        ),
        transition=rx.cond(
            AnimationState.reduce_motion,
            "none",
            "all 0.3s ease-out"
        ),
        **kwargs
    )

def animation_styles() -> rx.Component:
    """CSS animations and keyframes."""
    return rx.html(
        """
        <style>
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes fadeOut {
            from { opacity: 1; }
            to { opacity: 0; }
        }
        
        @keyframes slideInLeft {
            from { 
                opacity: 0; 
                transform: translateX(-30px); 
            }
            to { 
                opacity: 1; 
                transform: translateX(0); 
            }
        }
        
        @keyframes slideInRight {
            from { 
                opacity: 0; 
                transform: translateX(30px); 
            }
            to { 
                opacity: 1; 
                transform: translateX(0); 
            }
        }
        
        @keyframes slideInUp {
            from { 
                opacity: 0; 
                transform: translateY(30px); 
            }
            to { 
                opacity: 1; 
                transform: translateY(0); 
            }
        }
        
        @keyframes slideInDown {
            from { 
                opacity: 0; 
                transform: translateY(-30px); 
            }
            to { 
                opacity: 1; 
                transform: translateY(0); 
            }
        }
        
        @keyframes slideOutLeft {
            from { 
                opacity: 1; 
                transform: translateX(0); 
            }
            to { 
                opacity: 0; 
                transform: translateX(-30px); 
            }
        }
        
        @keyframes slideOutRight {
            from { 
                opacity: 1; 
                transform: translateX(0); 
            }
            to { 
                opacity: 0; 
                transform: translateX(30px); 
            }
        }
        
        @keyframes slideOutUp {
            from { 
                opacity: 1; 
                transform: translateY(0); 
            }
            to { 
                opacity: 0; 
                transform: translateY(-30px); 
            }
        }
        
        @keyframes slideOutDown {
            from { 
                opacity: 1; 
                transform: translateY(0); 
            }
            to { 
                opacity: 0; 
                transform: translateY(30px); 
            }
        }
        
        @keyframes scaleIn {
            from { 
                opacity: 0; 
                transform: scale(0.8); 
            }
            to { 
                opacity: 1; 
                transform: scale(1); 
            }
        }
        
        @keyframes scaleOut {
            from { 
                opacity: 1; 
                transform: scale(1); 
            }
            to { 
                opacity: 0; 
                transform: scale(0.8); 
            }
        }
        
        @keyframes bounceIn {
            0% {
                opacity: 0;
                transform: scale(0.3);
            }
            50% {
                opacity: 1;
                transform: scale(1.1);
            }
            70% {
                transform: scale(0.9);
            }
            100% {
                opacity: 1;
                transform: scale(1);
            }
        }
        
        @keyframes pulse {
            0%, 100% { 
                opacity: 1; 
            }
            50% { 
                opacity: 0.6; 
            }
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-4px); }
            20%, 40%, 60%, 80% { transform: translateX(4px); }
        }
        
        @keyframes flipInX {
            from {
                transform: perspective(400px) rotateX(90deg);
                opacity: 0;
            }
            40% {
                transform: perspective(400px) rotateX(-20deg);
            }
            60% {
                transform: perspective(400px) rotateX(10deg);
                opacity: 1;
            }
            80% {
                transform: perspective(400px) rotateX(-5deg);
            }
            to {
                transform: perspective(400px) rotateX(0deg);
                opacity: 1;
            }
        }
        
        @keyframes flipInY {
            from {
                transform: perspective(400px) rotateY(90deg);
                opacity: 0;
            }
            40% {
                transform: perspective(400px) rotateY(-20deg);
            }
            60% {
                transform: perspective(400px) rotateY(10deg);
                opacity: 1;
            }
            80% {
                transform: perspective(400px) rotateY(-5deg);
            }
            to {
                transform: perspective(400px) rotateY(0deg);
                opacity: 1;
            }
        }
        
        @keyframes rotateIn {
            from {
                transform: rotate(-200deg);
                opacity: 0;
            }
            to {
                transform: rotate(0deg);
                opacity: 1;
            }
        }
        
        @keyframes zoomIn {
            from {
                opacity: 0;
                transform: scale3d(0.3, 0.3, 0.3);
            }
            50% {
                opacity: 1;
            }
            to {
                opacity: 1;
                transform: scale3d(1, 1, 1);
            }
        }
        
        @keyframes zoomOut {
            from {
                opacity: 1;
                transform: scale3d(1, 1, 1);
            }
            50% {
                opacity: 0;
                transform: scale3d(0.3, 0.3, 0.3);
            }
            to {
                opacity: 0;
                transform: scale3d(0.3, 0.3, 0.3);
            }
        }
        
        /* Typewriter effect */
        .typewriter-text {
            overflow: hidden;
            border-right: 2px solid #8b5cf6;
            white-space: nowrap;
            margin: 0 auto;
            animation: typing 3.5s steps(40, end), blink-caret 0.75s step-end infinite;
        }
        
        @keyframes typing {
            from { width: 0; }
            to { width: 100%; }
        }
        
        @keyframes blink-caret {
            from, to { border-color: transparent; }
            50% { border-color: #8b5cf6; }
        }
        
        /* Scroll reveal */
        .reveal-on-scroll.revealed {
            opacity: 1 !important;
            transform: translateY(0) !important;
        }
        
        /* Smooth focus transitions */
        *:focus-visible {
            transition: outline 0.2s ease-out;
        }
        
        /* Reduced motion support */
        @media (prefers-reduced-motion: reduce) {
            *,
            *::before,
            *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
                scroll-behavior: auto !important;
            }
        }
        </style>
        
        <script>
        // Intersection Observer for scroll reveals
        document.addEventListener('DOMContentLoaded', function() {
            const observerOptions = {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            };
            
            const observer = new IntersectionObserver(function(entries) {
                entries.forEach(function(entry) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('revealed');
                        observer.unobserve(entry.target);
                    }
                });
            }, observerOptions);
            
            document.querySelectorAll('.reveal-on-scroll').forEach(function(el) {
                observer.observe(el);
            });
        });
        </script>
        """,
        tag="head"
    )