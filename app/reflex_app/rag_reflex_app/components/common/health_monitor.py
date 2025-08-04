"""
System health monitoring dashboard component.
"""

import reflex as rx
from typing import Dict, Any, List
from datetime import datetime


class HealthMonitorState(rx.State):
    """State for system health monitoring."""
    
    # Health status
    overall_status: str = "unknown"
    components: Dict[str, bool] = {}
    component_details: Dict[str, Dict[str, Any]] = {}
    
    # Metrics
    system_metrics: Dict[str, float] = {}
    metrics_history: List[Dict[str, Any]] = []
    
    # Error stats
    error_stats: Dict[str, Any] = {}
    
    # UI state
    show_details: bool = False
    auto_refresh: bool = True
    refresh_interval: int = 30  # seconds
    
    async def check_health(self):
        """Check system health status."""
        try:
            # Call health endpoint
            response = await self.api_client.get("/health")
            
            if response.get("status"):
                self.overall_status = response["status"]
                self.components = response.get("components", {})
                
                # Extract detailed health info
                health_details = response.get("health_details", {})
                self.component_details = health_details.get("checks", {})
                
                # Extract latest metrics
                latest_metrics = health_details.get("latest_metrics", {})
                if latest_metrics:
                    self.system_metrics = {
                        "CPU": latest_metrics.get("cpu_percent", 0),
                        "Memory": latest_metrics.get("memory_percent", 0),
                        "Disk": latest_metrics.get("disk_percent", 0),
                        "Connections": latest_metrics.get("active_connections", 0)
                    }
                
                # Get error statistics
                self.error_stats = response.get("error_statistics", {})
                
        except Exception as e:
            self.overall_status = "error"
            print(f"Health check failed: {e}")
    
    async def get_metrics_history(self):
        """Get system metrics history."""
        try:
            response = await self.api_client.get("/health/metrics?minutes=30")
            
            if response.get("success"):
                self.metrics_history = response.get("metrics", [])
                
        except Exception as e:
            print(f"Failed to get metrics history: {e}")
    
    def toggle_details(self):
        """Toggle detailed view."""
        self.show_details = not self.show_details
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh."""
        self.auto_refresh = not self.auto_refresh


def status_icon(status: str) -> rx.Component:
    """Get status icon based on health status."""
    icons = {
        "healthy": rx.icon("check-circle", color="green.500", size=20),
        "degraded": rx.icon("alert-triangle", color="yellow.500", size=20),
        "unhealthy": rx.icon("x-circle", color="red.500", size=20),
        "unknown": rx.icon("help-circle", color="gray.500", size=20),
        "error": rx.icon("x-octagon", color="red.600", size=20)
    }
    return icons.get(status, icons["unknown"])


def status_badge(status: str) -> rx.Component:
    """Create a status badge with appropriate styling."""
    colors = {
        "healthy": "green",
        "degraded": "yellow",
        "unhealthy": "red",
        "unknown": "gray",
        "error": "red"
    }
    
    return rx.badge(
        status.upper(),
        color_scheme=colors.get(status, "gray"),
        variant="subtle",
        size="sm"
    )


def component_status_row(name: str, is_healthy: bool) -> rx.Component:
    """Display status for a single component."""
    return rx.hstack(
        rx.cond(
            is_healthy,
            rx.icon("check", color="green.500", size=16),
            rx.icon("x", color="red.500", size=16)
        ),
        rx.text(
            name.replace("_", " ").title(),
            font_size="sm",
            color="gray.700"
        ),
        rx.spacer(),
        rx.cond(
            is_healthy,
            rx.text("Operational", font_size="xs", color="green.600"),
            rx.text("Failed", font_size="xs", color="red.600")
        ),
        width="100%",
        padding="0.25rem"
    )


def metric_display(label: str, value: float, unit: str = "%") -> rx.Component:
    """Display a single metric."""
    # Determine color based on value
    color = "green.600"
    if unit == "%":
        if value > 80:
            color = "red.600"
        elif value > 60:
            color = "yellow.600"
    
    return rx.vstack(
        rx.text(label, font_size="xs", color="gray.600"),
        rx.hstack(
            rx.text(
                f"{value:.1f}",
                font_size="lg",
                font_weight="bold",
                color=color
            ),
            rx.text(unit, font_size="sm", color="gray.500"),
            spacing="0.25rem"
        ),
        spacing="0.25rem",
        align_items="center"
    )


def health_summary_card() -> rx.Component:
    """Display health summary card."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                status_icon(HealthMonitorState.overall_status),
                rx.text(
                    "System Health",
                    font_size="lg",
                    font_weight="bold"
                ),
                rx.spacer(),
                status_badge(HealthMonitorState.overall_status),
                width="100%",
                align_items="center"
            ),
            
            rx.divider(margin_y="0.5rem"),
            
            # Component status
            rx.vstack(
                rx.text(
                    "Components",
                    font_size="sm",
                    font_weight="semibold",
                    color="gray.700"
                ),
                rx.foreach(
                    HealthMonitorState.components.items(),
                    lambda item: component_status_row(item[0], item[1])
                ),
                spacing="0.25rem",
                width="100%"
            ),
            
            rx.divider(margin_y="0.5rem"),
            
            # System metrics
            rx.vstack(
                rx.text(
                    "System Metrics",
                    font_size="sm",
                    font_weight="semibold",
                    color="gray.700"
                ),
                rx.hstack(
                    rx.foreach(
                        HealthMonitorState.system_metrics.items(),
                        lambda item: metric_display(
                            item[0],
                            item[1],
                            "%" if item[0] != "Connections" else ""
                        )
                    ),
                    spacing="1rem",
                    wrap="wrap"
                ),
                spacing="0.5rem",
                width="100%"
            ),
            
            # Actions
            rx.hstack(
                rx.button(
                    "Refresh",
                    on_click=HealthMonitorState.check_health,
                    size="sm",
                    variant="outline"
                ),
                rx.button(
                    rx.cond(
                        HealthMonitorState.show_details,
                        "Hide Details",
                        "Show Details"
                    ),
                    on_click=HealthMonitorState.toggle_details,
                    size="sm",
                    variant="ghost"
                ),
                rx.checkbox(
                    "Auto-refresh",
                    is_checked=HealthMonitorState.auto_refresh,
                    on_change=HealthMonitorState.toggle_auto_refresh,
                    size="sm"
                ),
                spacing="0.5rem",
                margin_top="0.5rem"
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


def error_stats_display() -> rx.Component:
    """Display error statistics."""
    return rx.cond(
        HealthMonitorState.error_stats.get("total", 0) > 0,
        rx.box(
            rx.vstack(
                rx.text(
                    "Error Statistics",
                    font_size="sm",
                    font_weight="semibold",
                    color="gray.700"
                ),
                rx.hstack(
                    rx.text(
                        f"Total Errors: {HealthMonitorState.error_stats.get('total', 0)}",
                        font_size="sm",
                        color="gray.600"
                    ),
                    rx.spacer(),
                    rx.text(
                        "Last 24 hours",
                        font_size="xs",
                        color="gray.500"
                    ),
                    width="100%"
                ),
                spacing="0.5rem",
                width="100%"
            ),
            padding="0.75rem",
            background_color="red.50",
            border_radius="md",
            margin_top="0.5rem",
            width="100%"
        )
    )


def health_monitor_widget() -> rx.Component:
    """Complete health monitoring widget."""
    return rx.vstack(
        health_summary_card(),
        
        rx.cond(
            HealthMonitorState.show_details,
            rx.vstack(
                error_stats_display(),
                spacing="0.5rem",
                width="100%"
            )
        ),
        
        spacing="0.5rem",
        width="100%",
        on_mount=HealthMonitorState.check_health
    )