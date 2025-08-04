"""
Performance optimization components for enhanced user experience.
"""

import reflex as rx
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class PerformanceState(rx.State):
    """State for managing performance optimizations."""
    
    # Caching
    cached_responses: Dict[str, Dict[str, Any]] = {}
    cache_hits: int = 0
    cache_misses: int = 0
    cache_enabled: bool = True
    cache_ttl: int = 300  # 5 minutes
    
    # Lazy loading
    loaded_components: List[str] = []
    loading_states: Dict[str, bool] = {}
    
    # Performance metrics
    response_times: List[float] = []
    component_load_times: Dict[str, float] = {}
    
    # Optimization settings
    enable_component_caching: bool = True
    enable_response_caching: bool = True
    enable_lazy_loading: bool = True
    preload_critical_components: bool = True
    
    def get_cached_response(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available and fresh."""
        if not self.cache_enabled or not self.enable_response_caching:
            return None
            
        cache_key = self._hash_query(query)
        if cache_key in self.cached_responses:
            cached_item = self.cached_responses[cache_key]
            
            # Check if cache is still valid
            cached_time = datetime.fromisoformat(cached_item["timestamp"])
            if datetime.now() - cached_time < timedelta(seconds=self.cache_ttl):
                self.cache_hits += 1
                return cached_item["response"]
            else:
                # Remove expired cache
                del self.cached_responses[cache_key]
        
        self.cache_misses += 1
        return None
    
    def cache_response(self, query: str, response: Dict[str, Any]):
        """Cache a response for future use."""
        if not self.cache_enabled or not self.enable_response_caching:
            return
            
        cache_key = self._hash_query(query)
        self.cached_responses[cache_key] = {
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
        
        # Limit cache size (keep last 100 responses)
        if len(self.cached_responses) > 100:
            oldest_key = min(self.cached_responses.keys(), 
                           key=lambda k: self.cached_responses[k]["timestamp"])
            del self.cached_responses[oldest_key]
    
    def _hash_query(self, query: str) -> str:
        """Create a hash key for the query."""
        import hashlib
        return hashlib.md5(query.lower().strip().encode()).hexdigest()
    
    def mark_component_loaded(self, component_id: str, load_time: float = 0):
        """Mark a component as loaded."""
        if component_id not in self.loaded_components:
            self.loaded_components.append(component_id)
        
        if load_time > 0:
            self.component_load_times[component_id] = load_time
        
        # Remove from loading states
        if component_id in self.loading_states:
            del self.loading_states[component_id]
    
    def set_component_loading(self, component_id: str):
        """Set a component as loading."""
        self.loading_states[component_id] = True
    
    def is_component_loaded(self, component_id: str) -> bool:
        """Check if a component is loaded."""
        return component_id in self.loaded_components
    
    def is_component_loading(self, component_id: str) -> bool:
        """Check if a component is currently loading."""
        return self.loading_states.get(component_id, False)
    
    def add_response_time(self, time: float):
        """Add a response time measurement."""
        self.response_times.append(time)
        
        # Keep only last 50 measurements
        if len(self.response_times) > 50:
            self.response_times.pop(0)
    
    def clear_cache(self):
        """Clear all cached responses."""
        self.cached_responses = {}
        self.cache_hits = 0
        self.cache_misses = 0
    
    def toggle_caching(self):
        """Toggle response caching."""
        self.cache_enabled = not self.cache_enabled
        if not self.cache_enabled:
            self.clear_cache()
    
    def update_cache_ttl(self, ttl: int):
        """Update cache time-to-live."""
        self.cache_ttl = max(60, min(3600, ttl))  # Between 1 minute and 1 hour
    
    @rx.var
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage."""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return (self.cache_hits / total) * 100
    
    @rx.var
    def average_response_time(self) -> float:
        """Calculate average response time."""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    @rx.var
    def performance_score(self) -> str:
        """Calculate overall performance score."""
        score = 100
        
        # Factor in response time (target: <2s)
        avg_time = self.average_response_time
        if avg_time > 5:
            score -= 30
        elif avg_time > 3:
            score -= 20
        elif avg_time > 2:
            score -= 10
        
        # Factor in cache efficiency
        if self.cache_hit_rate < 20:
            score -= 15
        elif self.cache_hit_rate < 40:
            score -= 10
        elif self.cache_hit_rate < 60:
            score -= 5
        
        # Component loading efficiency
        slow_components = sum(1 for t in self.component_load_times.values() if t > 1)
        score -= slow_components * 5
        
        score = max(0, score)
        
        if score >= 90:
            return f"Excellent ({score}%)"
        elif score >= 75:
            return f"Good ({score}%)"
        elif score >= 60:
            return f"Fair ({score}%)"
        else:
            return f"Poor ({score}%)"


def lazy_component(component_id: str, loader_func, placeholder=None) -> rx.Component:
    """Create a lazy-loaded component."""
    
    def lazy_loader():
        if not PerformanceState.is_component_loaded(component_id):
            PerformanceState.set_component_loading(component_id)
            # In a real implementation, this would trigger async loading
            # For now, we'll mark as loaded immediately
            PerformanceState.mark_component_loaded(component_id)
        
        return loader_func()
    
    if placeholder is None:
        placeholder = rx.box(
            rx.spinner(size="md"),
            display="flex",
            justify_content="center",
            align_items="center",
            height="100px",
            width="100%"
        )
    
    return rx.cond(
        PerformanceState.is_component_loaded(component_id),
        lazy_loader(),
        rx.cond(
            PerformanceState.is_component_loading(component_id),
            placeholder,
            rx.box(
                rx.button(
                    "Load Component",
                    on_click=lambda: PerformanceState.set_component_loading(component_id),
                    size="sm",
                    variant="outline"
                ),
                display="flex",
                justify_content="center",
                align_items="center",
                height="100px",
                width="100%"
            )
        )
    )


def performance_metrics_panel() -> rx.Component:
    """Display performance metrics panel."""
    return rx.box(
        rx.vstack(
            rx.heading(
                "Performance Metrics",
                size="md",
                margin_bottom="0.5rem"
            ),
            
            # Cache statistics
            rx.hstack(
                rx.vstack(
                    rx.text("Cache Hit Rate", font_size="sm", color="gray.600"),
                    rx.text(
                        f"{PerformanceState.cache_hit_rate:.1f}%",
                        font_size="lg",
                        font_weight="bold",
                        color=rx.cond(
                            PerformanceState.cache_hit_rate > 60,
                            "green.600",
                            rx.cond(
                                PerformanceState.cache_hit_rate > 30,
                                "yellow.600",
                                "red.600"
                            )
                        )
                    ),
                    align_items="center"
                ),
                rx.vstack(
                    rx.text("Avg Response", font_size="sm", color="gray.600"),
                    rx.text(
                        f"{PerformanceState.average_response_time:.2f}s",
                        font_size="lg",
                        font_weight="bold",
                        color=rx.cond(
                            PerformanceState.average_response_time < 2,
                            "green.600",
                            rx.cond(
                                PerformanceState.average_response_time < 5,
                                "yellow.600",
                                "red.600"
                            )
                        )
                    ),
                    align_items="center"
                ),
                rx.vstack(
                    rx.text("Performance", font_size="sm", color="gray.600"),
                    rx.text(
                        PerformanceState.performance_score,
                        font_size="lg",
                        font_weight="bold",
                        color="blue.600"
                    ),
                    align_items="center"
                ),
                spacing="2rem",
                width="100%",
                justify_content="space-around"
            ),
            
            rx.divider(margin_y="1rem"),
            
            # Cache controls
            rx.vstack(
                rx.text(
                    "Cache Settings",
                    font_size="sm",
                    font_weight="semibold",
                    color="gray.700"
                ),
                rx.hstack(
                    rx.switch(
                        is_checked=PerformanceState.cache_enabled,
                        on_change=PerformanceState.toggle_caching,
                        size="sm"
                    ),
                    rx.text("Enable Caching", font_size="sm"),
                    rx.spacer(),
                    rx.button(
                        "Clear Cache",
                        on_click=PerformanceState.clear_cache,
                        size="sm",
                        variant="outline",
                        color_scheme="red"
                    ),
                    width="100%",
                    align_items="center"
                ),
                rx.hstack(
                    rx.text("Cache TTL:", font_size="sm"),
                    rx.number_input(
                        value=str(PerformanceState.cache_ttl),
                        on_change=lambda v: PerformanceState.update_cache_ttl(int(v) if v else 300),
                        min_=60,
                        max_=3600,
                        size="sm",
                        width="100px"
                    ),
                    rx.text("seconds", font_size="sm", color="gray.500"),
                    width="100%",
                    align_items="center"
                ),
                spacing="0.5rem",
                width="100%"
            ),
            
            spacing="0.5rem",
            width="100%"
        ),
        padding="1rem",
        border="1px solid",
        border_color="gray.200",
        border_radius="lg",
        background_color="white",
        width="100%"
    )


def performance_indicator() -> rx.Component:
    """Small performance indicator for the UI."""
    return rx.hstack(
        rx.icon("zap", size=16, color="blue.500"),
        rx.text(
            f"{PerformanceState.cache_hit_rate:.0f}% cached",
            font_size="xs",
            color="gray.600"
        ),
        rx.text(
            f"{PerformanceState.average_response_time:.1f}s avg",
            font_size="xs",
            color="gray.600"
        ),
        spacing="0.5rem",
        align_items="center"
    )


# Preloader for critical components
def preload_critical_components():
    """Preload critical components."""
    critical_components = [
        "chat-interface",
        "document-manager",
        "health-monitor"
    ]
    
    for component_id in critical_components:
        if not PerformanceState.is_component_loaded(component_id):
            PerformanceState.mark_component_loaded(component_id)


# Enhanced caching decorator
def cached_component(cache_key: str, ttl: int = 300):
    """Decorator for caching component output."""
    def decorator(component_func):
        def wrapper(*args, **kwargs):
            # For simplicity, we'll just call the component
            # In a full implementation, this would check component cache
            return component_func(*args, **kwargs)
        return wrapper
    return decorator