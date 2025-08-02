"""Chat input form component."""

import reflex as rx
from ...state.chat_state import ChatState

def chat_input_form() -> rx.Component:
    """Chat input form with send button and settings."""
    return rx.vstack(
        # Main input area
        rx.hstack(
            rx.text_area(
                placeholder="Ask me anything about your documents...",
                value=ChatState.current_input,
                on_change=ChatState.set_input,
                on_key_down=ChatState.handle_enter_key,
                resize="none",
                rows="3",
                width="100%",
                disabled=ChatState.is_sending,
                border_color="gray.300",
                _focus={"border_color": "blue.500", "box_shadow": "0 0 0 1px blue.500"}
            ),
            rx.vstack(
                rx.button(
                    rx.cond(
                        ChatState.is_sending,
                        rx.spinner(size="2"),
                        rx.icon("send", size=16)
                    ),
                    on_click=ChatState.send_message,
                    disabled=ChatState.is_sending,
                    color_scheme="blue",
                    size="4",
                    height="60px",
                    width="60px",
                    **{"data-send": "true"}  # For JavaScript integration
                ),
                rx.button(
                    rx.icon("trash-2", size=14),
                    on_click=ChatState.clear_chat,
                    variant="ghost",
                    size="2",
                    color_scheme="red",
                    width="60px",
                    disabled=ChatState.is_sending
                ),
                spacing="2"
            ),
            spacing="3",
            width="100%",
            align="end"
        ),
        
        # Settings row
        rx.hstack(
            rx.hstack(
                rx.text("Max chunks:", font_size="14px", color="white"),
                rx.input(
                    value=ChatState.max_chunks,
                    on_change=ChatState.set_max_chunks,
                    width="80px",
                    size="2",
                    type="number",
                    min="1",
                    max="10"
                ),
                spacing="2",
                align="center"
            ),
            rx.hstack(
                rx.text("Similarity:", font_size="14px", color="white"),
                rx.input(
                    value=ChatState.similarity_threshold,
                    on_change=ChatState.set_similarity_threshold,
                    width="80px",
                    size="2",
                    type="number",
                    min="0.0",
                    max="1.0",
                    step="0.1"
                ),
                spacing="2",
                align="center"
            ),
            rx.spacer(),
            rx.cond(
                ChatState.last_response_time,
                rx.text(
                    ChatState.last_response_time_display,
                    font_size="14px",
                    color="white"
                ),
                rx.fragment()
            ),
            width="100%",
            align="center"
        ),
        
        # Error display
        rx.cond(
            ChatState.show_error,
            rx.box(
                rx.hstack(
                    rx.text("⚠️", font_size="16px"),
                    rx.text("Error:", font_weight="bold", color="red.600"),
                    rx.text(ChatState.error_message, color="red.600"),
                    rx.button("×", on_click=ChatState.clear_error, size="1", variant="ghost"),
                    spacing="2",
                    align="center"
                ),
                padding="3",
                bg="rgba(248, 113, 113, 0.1)",
                border="1px solid",
                border_color="rgba(248, 113, 113, 0.3)",
                border_radius="lg",
                backdrop_filter="blur(10px)"
            ),
            rx.fragment()
        ),
        
        spacing="3",
        width="100%",
        padding="4",
        border_top="1px solid",
        border_color="rgba(255, 255, 255, 0.1)",
        bg="rgba(255, 255, 255, 0.04)",
        backdrop_filter="blur(15px)",
        border_radius="xl"
    )

def quick_prompts() -> rx.Component:
    """Quick prompt buttons for common queries."""
    prompts = [
        "What are the main topics in the documents?",
        "Summarize the key findings",
        "What are the most important insights?",
        "Find information about methodology"
    ]
    
    return rx.cond(
        ~ChatState.has_messages,
        rx.vstack(
            rx.text("Quick prompts:", font_size="14px", color="white", font_weight="bold"),
            rx.hstack(
                *[
                    rx.button(
                        prompt,
                        on_click=lambda p=prompt: ChatState.set_input(p),
                        size="2",
                        variant="outline",
                        color_scheme="gray",
                        font_size="14px"
                    )
                    for prompt in prompts
                ],
                spacing="2",
                wrap="wrap"
            ),
            spacing="2",
            width="100%",
            padding="4",
            bg="rgba(255, 255, 255, 0.06)",
            border_radius="xl",
            margin_bottom="4",
            backdrop_filter="blur(15px)",
            border="1px solid",
            border_color="rgba(255, 255, 255, 0.1)"
        ),
        rx.fragment()
    )