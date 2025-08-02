"""Global application state."""

import reflex as rx
from typing import Dict, Any, Optional
import asyncio
from ..services.api_client import api_client

class AppState(rx.State):
    """Global application state management."""
    
    # Health monitoring
    health_status: Dict[str, Any] = {}
    is_checking_health: bool = False
    last_health_check: Optional[str] = None
    
    # Error handling
    error_message: str = ""
    show_error: bool = False
    
    # Loading states
    is_loading: bool = False
    
    async def check_health(self):
        """Check the health of all system components."""
        self.is_checking_health = True
        self.error_message = ""
        self.show_error = False
        
        try:
            health_data = await api_client.health_check()
            self.health_status = health_data
            from datetime import datetime
            self.last_health_check = datetime.now().strftime("%H:%M:%S")
        except Exception as e:
            self.error_message = f"Health check failed: {str(e)}"
            self.show_error = True
            # Set default unhealthy state
            self.health_status = {
                "llm": {"healthy": False},
                "vector_db": {"healthy": False},
                "embeddings": {"healthy": False}
            }
        finally:
            self.is_checking_health = False
    
    def clear_error(self):
        """Clear error message."""
        self.error_message = ""
        self.show_error = False
    
    def set_loading(self, loading: bool):
        """Set global loading state."""
        self.is_loading = loading
    
    async def on_load(self):
        """Initialize the application state."""
        await self.check_health()