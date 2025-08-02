"""Global application state."""

import reflex as rx
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime
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
            # Transform backend format to frontend format
            if "components" in health_data:
                self.health_status = {
                    "llm": {"healthy": health_data["components"].get("llm", False)},
                    "vector_db": {"healthy": health_data["components"].get("vector_database", False)},
                    "embeddings": {"healthy": health_data["components"].get("embedding_model", False)}
                }
            else:
                self.health_status = health_data
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
    
    @rx.var
    def llm_healthy(self) -> bool:
        """Check if LLM is healthy."""
        return self.health_status.get("llm", {}).get("healthy", False) if self.health_status else False
    
    @rx.var
    def vector_db_healthy(self) -> bool:
        """Check if vector DB is healthy."""
        return self.health_status.get("vector_db", {}).get("healthy", False) if self.health_status else False
    
    @rx.var
    def embeddings_healthy(self) -> bool:
        """Check if embeddings are healthy."""
        return self.health_status.get("embeddings", {}).get("healthy", False) if self.health_status else False
    
    @rx.var
    def llm_status_text(self) -> str:
        """Get LLM status text."""
        if self.health_status and "llm" in self.health_status:
            return "Online" if self.health_status["llm"].get("healthy", False) else "Offline"
        return "Unknown"
    
    @rx.var
    def vector_db_status_text(self) -> str:
        """Get vector DB status text."""
        if self.health_status and "vector_db" in self.health_status:
            return "Online" if self.health_status["vector_db"].get("healthy", False) else "Offline"
        return "Unknown"
    
    @rx.var
    def embeddings_status_text(self) -> str:
        """Get embeddings status text."""
        if self.health_status and "embeddings" in self.health_status:
            return "Online" if self.health_status["embeddings"].get("healthy", False) else "Offline"
        return "Unknown"
    
    async def on_load(self):
        """Initialize the application state."""
        await self.check_health()