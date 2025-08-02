"""Chat-specific state management."""

import reflex as rx
from typing import List, Dict, Optional, Any
from datetime import datetime
from ..services.api_client import api_client

class ChatMessage(rx.Base):
    """Chat message model."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
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
        user_message = ChatMessage(
            role="user",
            content=self.current_input.strip(),
            timestamp=datetime.now(),
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
            # Handle errors
            self.error_message = f"Failed to get response: {str(e)}"
            self.show_error = True
            
            # Add error message to chat
            error_message = ChatMessage(
                role="assistant",
                content=f"I'm sorry, I encountered an error: {str(e)}",
                timestamp=datetime.now(),
                message_id=f"error_{len(self.messages)}"
            )
            self.messages.append(error_message)
            
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
    def chat_stats(self) -> Dict[str, Any]:
        """Get chat statistics."""
        return {
            "total_messages": self.total_messages,
            "last_response_time": self.last_response_time,
            "max_chunks": self.max_chunks,
            "similarity_threshold": self.similarity_threshold
        }