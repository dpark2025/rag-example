"""Chat input form component."""

import reflex as rx
from ...state.chat_state import ChatState

def chat_input_form() -> rx.Component:
    """Chat input form with send button and settings."""
    return rx.vstack(
        # Main input area
        rx.hstack(
            rx.textarea(
                placeholder="Ask me anything about your documents...",
                value=ChatState.current_input,
                on_change=ChatState.set_input,
                on_key_down=ChatState.handle_enter_key,
                resize="none",
                rows=3,
                width="100%",
                disabled=ChatState.is_sending,
                border_color="gray.300",
                _focus={"border_color": "blue.500", "box_shadow": "0 0 0 1px blue.500"}
            ),
            rx.vstack(
                rx.button(
                    rx.cond(
                        ChatState.is_sending,
                        rx.spinner(size="sm"),
                        rx.icon("send", size=16)
                    ),
                    on_click=ChatState.send_message,
                    disabled=ChatState.is_sending,
                    color_scheme="blue",
                    size="lg",
                    height="60px",
                    width="60px",
                    **{"data-send": "true"}  # For JavaScript integration
                ),
                rx.button(
                    rx.icon("trash-2", size=14),
                    on_click=ChatState.clear_chat,
                    variant="ghost",
                    size="sm",
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
                rx.text("Max chunks:", font_size="sm", color="gray.600"),
                rx.number_input(
                    value=ChatState.max_chunks,
                    on_change=lambda x: ChatState.update_settings(max_chunks=int(x) if x else 5),
                    min=1,
                    max=10,
                    width="80px",
                    size="sm"
                ),
                spacing="2",
                align="center"
            ),
            rx.hstack(
                rx.text("Similarity:", font_size="sm", color="gray.600"),
                rx.number_input(
                    value=ChatState.similarity_threshold,
                    on_change=lambda x: ChatState.update_settings(similarity_threshold=float(x) if x else 0.7),
                    min=0.0,
                    max=1.0,
                    step=0.1,
                    width="80px",
                    size="sm"
                ),
                spacing="2",
                align="center"
            ),
            rx.spacer(),
            rx.cond(
                ChatState.last_response_time,
                rx.text(
                    f"Last response: {ChatState.last_response_time:.2f}s",
                    font_size="sm",
                    color="gray.500"
                ),
                rx.fragment()
            ),
            width="100%",
            align="center"
        ),
        
        # Error display
        rx.cond(
            ChatState.show_error,
            rx.alert(
                rx.alert_icon(),
                rx.alert_title("Error"),
                rx.alert_description(ChatState.error_message),
                status="error",
                variant="left-accent",
                on_close=ChatState.clear_error
            ),
            rx.fragment()
        ),
        
        spacing="3",
        width="100%",
        padding="4",
        border_top="1px solid",
        border_color="gray.200",
        bg="white"
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
            rx.text("Quick prompts:", font_size="sm", color="gray.600", font_weight="bold"),
            rx.wrap(
                *[
                    rx.button(
                        prompt,
                        on_click=lambda p=prompt: ChatState.set_input(p),
                        size="sm",
                        variant="outline",
                        color_scheme="gray",
                        font_size="sm"
                    )
                    for prompt in prompts
                ],
                spacing="2"
            ),
            spacing="2",
            width="100%",
            padding="4",
            bg="gray.50",
            border_radius="md",
            margin_bottom="4"
        ),
        rx.fragment()
    )