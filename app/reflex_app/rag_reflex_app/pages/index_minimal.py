"""Minimal index page without complex components."""

import reflex as rx

class MinimalChatState(rx.State):
    """Enhanced minimal chat state with system status and document features."""
    messages: list[dict] = []
    current_input: str = ""
    
    # System status features
    show_system_panel: bool = False
    llm_healthy: bool = True
    vector_db_healthy: bool = True
    embeddings_healthy: bool = False
    
    # Document management features
    documents_count: int = 3
    show_upload_modal: bool = False
    
    def add_message(self):
        """Add a message with enhanced functionality."""
        if self.current_input.strip():
            # Add user message
            self.messages.append({
                "text": self.current_input,
                "sender": "user",
                "timestamp": "now"
            })
            
            # Mock AI response
            self.messages.append({
                "text": f"I understand you asked: '{self.current_input}'. This is a mock response showing the enhanced RAG system.",
                "sender": "assistant",
                "timestamp": "now"
            })
            
            self.current_input = ""
    
    def toggle_system_panel(self):
        """Toggle the system status panel."""
        self.show_system_panel = not self.show_system_panel
    
    def toggle_upload_modal(self):
        """Toggle document upload modal."""
        self.show_upload_modal = not self.show_upload_modal
    
    def refresh_health(self):
        """Simulate health check refresh."""
        self.embeddings_healthy = not self.embeddings_healthy

def minimal_index_page() -> rx.Component:
    """Minimal functional page."""
    return rx.box(
        rx.vstack(
            # Header
            rx.heading(
                "🤖 RAG System",
                size="8",
                color="violet.400",
                text_align="center",
                margin_bottom="1rem"
            ),
            
            # System Status Panel
            rx.box(
                rx.hstack(
                    rx.button(
                        rx.hstack(
                            rx.icon("activity", size=16),
                            rx.text("System Status", font_weight="500"),
                            spacing="2"
                        ),
                        on_click=MinimalChatState.toggle_system_panel,
                        variant="outline",
                        color_scheme="violet",
                        size="2"
                    ),
                    rx.hstack(
                        rx.icon("database", size=16, color="violet.400"),
                        rx.text(f"{MinimalChatState.documents_count} documents", font_size="sm", color="gray.400"),
                        spacing="1"
                    ),
                    rx.button(
                        rx.hstack(
                            rx.icon("upload", size=14),
                            rx.text("Upload", font_size="sm"),
                            spacing="1"
                        ),
                        on_click=MinimalChatState.toggle_upload_modal,
                        variant="ghost",
                        color_scheme="violet",
                        size="2"
                    ),
                    justify="between",
                    width="100%"
                ),
                
                # Collapsible system panel
                rx.cond(
                    MinimalChatState.show_system_panel,
                    rx.vstack(
                        rx.text("Service Health", font_weight="bold", color="violet.300", margin_top="3"),
                        rx.vstack(
                            rx.hstack(
                                rx.cond(
                                    MinimalChatState.llm_healthy,
                                    rx.box(width="8px", height="8px", bg="green.400", border_radius="50%"),
                                    rx.box(width="8px", height="8px", bg="red.400", border_radius="50%")
                                ),
                                rx.text("LLM Service", font_size="sm", color="gray.200"),
                                rx.cond(
                                    MinimalChatState.llm_healthy,
                                    rx.text("Ready", font_size="xs", color="green.400"),
                                    rx.text("Down", font_size="xs", color="red.400")
                                ),
                                justify="between",
                                width="100%"
                            ),
                            rx.hstack(
                                rx.cond(
                                    MinimalChatState.vector_db_healthy,
                                    rx.box(width="8px", height="8px", bg="green.400", border_radius="50%"),
                                    rx.box(width="8px", height="8px", bg="red.400", border_radius="50%")
                                ),
                                rx.text("Vector DB", font_size="sm", color="gray.200"),
                                rx.cond(
                                    MinimalChatState.vector_db_healthy,
                                    rx.text("Ready", font_size="xs", color="green.400"),
                                    rx.text("Down", font_size="xs", color="red.400")
                                ),
                                justify="between",
                                width="100%"
                            ),
                            rx.hstack(
                                rx.cond(
                                    MinimalChatState.embeddings_healthy,
                                    rx.box(width="8px", height="8px", bg="green.400", border_radius="50%"),
                                    rx.box(width="8px", height="8px", bg="red.400", border_radius="50%")
                                ),
                                rx.text("Embeddings", font_size="sm", color="gray.200"),
                                rx.cond(
                                    MinimalChatState.embeddings_healthy,
                                    rx.text("Ready", font_size="xs", color="green.400"),
                                    rx.text("Down", font_size="xs", color="red.400")
                                ),
                                justify="between",
                                width="100%"
                            ),
                            spacing="2",
                            width="100%"
                        ),
                        rx.button(
                            rx.hstack(
                                rx.icon("refresh-cw", size=14),
                                rx.text("Refresh", font_size="sm"),
                                spacing="1"
                            ),
                            on_click=MinimalChatState.refresh_health,
                            variant="ghost",
                            color_scheme="violet",
                            size="2",
                            margin_top="2"
                        ),
                        spacing="2",
                        align="start",
                        width="100%",
                        padding="3",
                        bg="rgba(139, 92, 246, 0.05)",
                        border="1px solid",
                        border_color="rgba(139, 92, 246, 0.2)",
                        border_radius="md"
                    )
                ),
                
                margin_bottom="2rem",
                width="100%"
            ),
            
            # Chat messages area
            rx.box(
                rx.vstack(
                    rx.cond(
                        MinimalChatState.messages.length() > 0,
                        rx.vstack(
                            rx.foreach(
                                MinimalChatState.messages,
                                lambda msg: rx.box(
                                    rx.hstack(
                                        rx.cond(
                                            msg["sender"] == "user",
                                            rx.box(
                                                rx.icon("user", size=16, color="violet.400"),
                                                bg="rgba(139, 92, 246, 0.2)",
                                                padding="2",
                                                border_radius="50%"
                                            ),
                                            rx.box(
                                                rx.icon("bot", size=16, color="green.400"),
                                                bg="rgba(34, 197, 94, 0.2)",
                                                padding="2", 
                                                border_radius="50%"
                                            )
                                        ),
                                        rx.vstack(
                                            rx.text(
                                                msg["text"], 
                                                color="gray.100",
                                                font_size="sm",
                                                line_height="1.5"
                                            ),
                                            rx.cond(
                                                msg["sender"] == "assistant",
                                                rx.hstack(
                                                    rx.icon("file-text", size=12, color="violet.400"),
                                                    rx.text(
                                                        "Sources available",
                                                        font_size="xs",
                                                        color="violet.300"
                                                    ),
                                                    spacing="1"
                                                )
                                            ),
                                            spacing="1",
                                            align="start",
                                            flex="1"
                                        ),
                                        spacing="3",
                                        align="start",
                                        width="100%"
                                    ),
                                    bg="gray.800",
                                    padding="1rem",
                                    border_radius="lg",
                                    border="1px solid",
                                    border_color="gray.700",
                                    margin_bottom="0.5rem"
                                )
                            ),
                            spacing="2",
                            width="100%"
                        ),
                        rx.box(
                            rx.vstack(
                                rx.icon("message-circle", size=48, color="gray.600"),
                                rx.text(
                                    "Welcome to RAG System",
                                    font_size="xl",
                                    color="gray.300",
                                    font_weight="600"
                                ),
                                rx.text(
                                    "Ask questions about your documents",
                                    font_size="sm",
                                    color="gray.500"
                                ),
                                spacing="2",
                                align="center"
                            ),
                            padding="3rem",
                            text_align="center"
                        )
                    ),
                    spacing="2",
                    width="100%"
                ),
                height="400px",
                overflow_y="auto",
                border="1px solid",
                border_color="gray.700",
                border_radius="lg",
                padding="1rem",
                bg="gray.900",
                margin_bottom="1rem"
            ),
            
            # Input area
            rx.hstack(
                rx.input(
                    placeholder="Type your message...",
                    value=MinimalChatState.current_input,
                    on_change=MinimalChatState.set_current_input,
                    flex="1",
                    size="3"
                ),
                rx.button(
                    "Send",
                    on_click=MinimalChatState.add_message,
                    color_scheme="violet",
                    size="3"
                ),
                spacing="3",
                width="100%"
            ),
            
            # Status
            rx.text(
                "✅ System Ready",
                color="green.400",
                font_size="sm",
                margin_top="1rem"
            ),
            
            spacing="4",
            width="100%",
            max_width="800px",
            margin="0 auto"
        ),
        
        # Document Upload Modal
        rx.cond(
            MinimalChatState.show_upload_modal,
            rx.box(
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.heading("Upload Documents", size="6", color="violet.400"),
                            rx.button(
                                rx.icon("x", size=16),
                                on_click=MinimalChatState.toggle_upload_modal,
                                variant="ghost",
                                color_scheme="gray",
                                size="2"
                            ),
                            justify="between",
                            width="100%"
                        ),
                        
                        # Drag and drop area
                        rx.box(
                            rx.vstack(
                                rx.icon("cloud_upload", size=32, color="violet.400"),
                                rx.text(
                                    "Drag and drop files here",
                                    font_size="lg",
                                    color="gray.200",
                                    font_weight="500"
                                ),
                                rx.text(
                                    "or click to browse",
                                    font_size="sm",
                                    color="gray.400"
                                ),
                                rx.text(
                                    "Supported: PDF, TXT, MD, HTML",
                                    font_size="xs",
                                    color="gray.500",
                                    margin_top="2"
                                ),
                                spacing="2",
                                align="center"
                            ),
                            border="2px dashed",
                            border_color="violet.400",
                            border_radius="lg",
                            padding="3rem",
                            text_align="center",
                            bg="rgba(139, 92, 246, 0.05)",
                            cursor="pointer",
                            _hover={"bg": "rgba(139, 92, 246, 0.1)"},
                            width="100%",
                            margin="2rem 0"
                        ),
                        
                        rx.hstack(
                            rx.button(
                                "Cancel",
                                on_click=MinimalChatState.toggle_upload_modal,
                                variant="outline",
                                color_scheme="gray",
                                size="3"
                            ),
                            rx.button(
                                "Upload Files",
                                color_scheme="violet",
                                size="3"
                            ),
                            spacing="3",
                            justify="end",
                            width="100%"
                        ),
                        
                        spacing="4",
                        width="100%"
                    ),
                    bg="gray.900",
                    border="1px solid",
                    border_color="gray.700",
                    border_radius="lg",
                    padding="2rem",
                    width="500px",
                    max_width="90vw"
                ),
                position="fixed",
                top="0",
                left="0",
                width="100vw",
                height="100vh",
                bg="rgba(0, 0, 0, 0.7)",
                z_index="1000",
                display="flex",
                align_items="center",
                justify_content="center"
            )
        ),
        
        padding="2rem",
        min_height="100vh",
        bg="gray.950"
    )