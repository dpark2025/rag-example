"""Chat-specific state management."""

import reflex as rx
from typing import List, Dict, Optional, Any
from datetime import datetime
from ..services.api_client import api_client
from ..components.common.error_boundary import ErrorState

class ChatMessage(rx.Base):
    """Chat message model."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    timestamp_str: str = ""  # Formatted timestamp string
    sources: Optional[List[Dict[str, Any]]] = None
    metrics: Optional[Dict[str, Any]] = None
    message_id: str

class ChatState(rx.State):
    """Chat interface state management."""
    
    # Message history
    messages: List[ChatMessage] = []
    
    # Input handling
    current_input: str = ""
    
    # UI states
    is_sending: bool = False
    is_typing: bool = False
    
    # Error handling
    error_message: str = ""
    show_error: bool = False
    
    # Settings
    max_chunks: int = 5
    similarity_threshold: float = 0.7
    
    # Metrics
    last_response_time: Optional[float] = None
    total_messages: int = 0
    
    def set_input(self, value: str):
        """Update the current input value."""
        self.current_input = value
    
    def clear_input(self):
        """Clear the input field."""
        self.current_input = ""
    
    def clear_error(self):
        """Clear any error messages."""
        self.error_message = ""
        self.show_error = False
    
    def clear_chat(self):
        """Clear all chat messages."""
        self.messages = []
        self.total_messages = 0
        self.clear_error()
    
    async def send_message(self):
        """Send a message to the RAG system."""
        if not self.current_input.strip():
            return
        
        # Clear any previous errors
        self.clear_error()
        
        # Create user message
        now = datetime.now()
        user_message = ChatMessage(
            role="user",
            content=self.current_input.strip(),
            timestamp=now,
            timestamp_str=now.strftime("%H:%M:%S"),
            message_id=f"user_{len(self.messages)}"
        )
        
        # Add user message to history
        self.messages.append(user_message)
        query = self.current_input
        self.clear_input()
        
        # Set loading states
        self.is_sending = True
        self.is_typing = True
        
        try:
            # Measure response time
            start_time = datetime.now()
            
            # Call RAG API
            response = await api_client.query(
                question=query,
                max_chunks=self.max_chunks,
                similarity_threshold=self.similarity_threshold
            )
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            self.last_response_time = response_time
            
            # Create assistant message
            assistant_message = ChatMessage(
                role="assistant",
                content=response.get("answer", "No response received"),
                timestamp=end_time,
                timestamp_str=end_time.strftime("%H:%M:%S"),
                sources=response.get("sources", []),
                metrics={
                    "response_time": response_time,
                    "chunks_used": len(response.get("sources", [])),
                    "similarity_scores": [s.get("similarity", 0) for s in response.get("sources", [])],
                    **response.get("metrics", {})
                },
                message_id=f"assistant_{len(self.messages)}"
            )
            
            # Add assistant message to history
            self.messages.append(assistant_message)
            self.total_messages += 2  # user + assistant
            
        except Exception as e:
            # Enhanced error handling with graceful degradation
            error_time = datetime.now()
            
            # Check if response has error info from backend
            if hasattr(e, 'response') and e.response:
                try:
                    error_data = e.response.json()
                    if error_data.get("error"):
                        # Use structured error from backend
                        error_info = error_data["error"]
                        user_message = error_info.get("user_message", str(e))
                        recovery_action = error_info.get("recovery_action", "none")
                        
                        # Update error state for display
                        await ErrorState.handle_error(error_info)
                        
                        error_content = f"I'm sorry, {user_message}"
                        if recovery_action == "retry":
                            error_content += " Please try asking again."
                        elif recovery_action == "check_connection":
                            error_content += " Please check your connection and try again."
                    else:
                        error_content = f"I encountered an unexpected error: {str(e)}"
                except:
                    error_content = f"I encountered an unexpected error: {str(e)}"
            else:
                error_content = f"I encountered an unexpected error: {str(e)}"
            
            # Add graceful error message to chat
            error_message = ChatMessage(
                role="assistant",
                content=error_content,
                timestamp=error_time,
                timestamp_str=error_time.strftime("%H:%M:%S"),
                message_id=f"error_{len(self.messages)}"
            )
            self.messages.append(error_message)
            
            # Set error states
            self.error_message = error_content
            self.show_error = True
            
        finally:
            # Reset loading states
            self.is_sending = False
            self.is_typing = False
    
    async def handle_enter_key(self, key: str):
        """Handle Enter key press in input field."""
        if key == "Enter" and not self.is_sending:
            await self.send_message()
    
    def update_settings(self, max_chunks: int = None, similarity_threshold: float = None):
        """Update chat settings."""
        if max_chunks is not None:
            self.max_chunks = max_chunks
        if similarity_threshold is not None:
            self.similarity_threshold = similarity_threshold
    
    def set_max_chunks(self, value: str):
        """Set max chunks from input."""
        try:
            self.max_chunks = int(value) if value else 5
        except ValueError:
            self.max_chunks = 5
    
    def set_similarity_threshold(self, value: str):
        """Set similarity threshold from input."""
        try:
            self.similarity_threshold = float(value) if value else 0.7
        except ValueError:
            self.similarity_threshold = 0.7
    
    @rx.var
    def has_messages(self) -> bool:
        """Check if there are any messages."""
        return len(self.messages) > 0
    
    @rx.var
    def last_message_sources(self) -> List[Dict[str, Any]]:
        """Get sources from the last assistant message."""
        if not self.messages:
            return []
        
        # Find the last assistant message with sources
        for message in reversed(self.messages):
            if message.role == "assistant" and message.sources:
                return message.sources
        
        return []
    
    @rx.var
    def last_response_time_display(self) -> str:
        """Format last response time for display."""
        if self.last_response_time is None:
            return ""
        return f"Last response: {self.last_response_time:.2f}s"
    
    @rx.var
    def total_messages_display(self) -> str:
        """Format total messages for display."""
        return f"{self.total_messages} messages"
    
    @rx.var
    def chat_stats(self) -> Dict[str, Any]:
        """Get chat statistics."""
        return {
            "total_messages": self.total_messages,
            "last_response_time": self.last_response_time,
            "max_chunks": self.max_chunks,
            "similarity_threshold": self.similarity_threshold
        }