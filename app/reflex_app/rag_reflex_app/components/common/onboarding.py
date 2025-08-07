"""
Interactive onboarding and tutorial system for new users.
"""

import reflex as rx
from typing import List, Dict, Any, Optional
from enum import Enum


class OnboardingStep(Enum):
    """Onboarding tutorial steps."""
    WELCOME = "welcome"
    UPLOAD_DOCUMENT = "upload_document"
    FIRST_QUERY = "first_query"
    EXPLORE_FEATURES = "explore_features"
    COMPLETE = "complete"


class OnboardingState(rx.State):
    """State for managing onboarding tutorial."""
    
    # Tutorial state
    show_onboarding: bool = False
    current_step: str = OnboardingStep.WELCOME.value
    completed_steps: List[str] = []
    skip_onboarding: bool = False
    
    # User progress tracking
    has_uploaded_document: bool = False
    has_made_query: bool = False
    has_explored_features: bool = False
    
    # Tutorial data
    steps_data: Dict[str, Dict[str, Any]] = {
        OnboardingStep.WELCOME.value: {
            "title": "Welcome to Your Local RAG System!",
            "content": "This system helps you chat with your documents using AI, completely locally and privately. Let's get you started!",
            "icon": "👋",
            "action_text": "Get Started",
            "features": [
                "🔒 Complete Privacy - Everything runs locally",
                "📄 Multiple Formats - TXT, PDF, and more",
                "🤖 AI-Powered - Chat with your documents",
                "⚡ Fast Search - Instant document retrieval"
            ]
        },
        OnboardingStep.UPLOAD_DOCUMENT.value: {
            "title": "Upload Your First Document",
            "content": "Start by uploading a document you'd like to chat with. We support text files (.txt) and PDFs.",
            "icon": "📄",
            "action_text": "Upload Document",
            "tips": [
                "Drag and drop files for quick upload",
                "Multiple files can be uploaded at once",
                "PDFs are automatically processed for text",
                "Documents are stored locally and securely"
            ]
        },
        OnboardingStep.FIRST_QUERY.value: {
            "title": "Ask Your First Question",
            "content": "Now that you have documents uploaded, try asking a question about their content!",
            "icon": "💬",
            "action_text": "Try Chat",
            "examples": [
                "What is this document about?",
                "Summarize the main points",
                "What are the key findings?",
                "Tell me about [specific topic]"
            ]
        },
        OnboardingStep.EXPLORE_FEATURES.value: {
            "title": "Explore Advanced Features",
            "content": "Discover more powerful features to get the most out of your RAG system.",
            "icon": "🚀",
            "action_text": "Explore",
            "features": [
                "📊 Document Management - View and organize your documents",
                "⚙️ Settings - Adjust search parameters and preferences",
                "📈 Health Monitor - Check system status and performance",
                "🔍 Advanced Search - Fine-tune search results"
            ]
        },
        OnboardingStep.COMPLETE.value: {
            "title": "You're All Set!",
            "content": "Congratulations! You've completed the tutorial. You're ready to start using your RAG system effectively.",
            "icon": "🎉",
            "action_text": "Start Using",
            "next_steps": [
                "Upload more documents to expand your knowledge base",
                "Experiment with different types of questions",
                "Check the help section if you need assistance",
                "Explore the settings to customize your experience"
            ]
        }
    }
    
    def start_onboarding(self):
        """Start the onboarding tutorial."""
        self.show_onboarding = True
        self.current_step = OnboardingStep.WELCOME.value
        self.completed_steps = []
    
    def next_step(self):
        """Move to the next onboarding step."""
        # Mark current step as completed
        if self.current_step not in self.completed_steps:
            self.completed_steps.append(self.current_step)
        
        # Determine next step
        steps = list(OnboardingStep)
        current_index = next(i for i, step in enumerate(steps) if step.value == self.current_step)
        
        if current_index < len(steps) - 1:
            self.current_step = steps[current_index + 1].value
        else:
            self.complete_onboarding()
    
    def previous_step(self):
        """Move to the previous onboarding step."""
        steps = list(OnboardingStep)
        current_index = next(i for i, step in enumerate(steps) if step.value == self.current_step)
        
        if current_index > 0:
            self.current_step = steps[current_index - 1].value
    
    def skip_to_step(self, step: str):
        """Skip to a specific step."""
        self.current_step = step
    
    def complete_onboarding(self):
        """Complete the onboarding tutorial."""
        self.show_onboarding = False
        self.current_step = OnboardingStep.COMPLETE.value
        self.completed_steps = [step.value for step in OnboardingStep]
        
        # Save completion to local storage
        self.skip_onboarding = True
    
    def skip_onboarding_tutorial(self):
        """Skip the entire onboarding tutorial."""
        self.show_onboarding = False
        self.skip_onboarding = True
    
    def reset_onboarding(self):
        """Reset onboarding tutorial."""
        self.show_onboarding = False
        self.current_step = OnboardingStep.WELCOME.value
        self.completed_steps = []
        self.skip_onboarding = False
        self.has_uploaded_document = False
        self.has_made_query = False
        self.has_explored_features = False
    
    def mark_document_uploaded(self):
        """Mark that user has uploaded a document."""
        self.has_uploaded_document = True
        if self.current_step == OnboardingStep.UPLOAD_DOCUMENT.value:
            self.next_step()
    
    def mark_query_made(self):
        """Mark that user has made a query."""
        self.has_made_query = True
        if self.current_step == OnboardingStep.FIRST_QUERY.value:
            self.next_step()
    
    def mark_features_explored(self):
        """Mark that user has explored features."""
        self.has_explored_features = True
        if self.current_step == OnboardingStep.EXPLORE_FEATURES.value:
            self.next_step()


def progress_indicator() -> rx.Component:
    """Display onboarding progress indicator."""
    steps = list(OnboardingStep)
    current_index = rx.State.get_substate(OnboardingState).computed_vars.get(
        "current_step_index", 
        lambda: next(i for i, step in enumerate(steps) if step.value == OnboardingState.current_step)
    )
    
    return rx.hstack(
        rx.foreach(
            rx.State.get_substate(OnboardingState).computed_vars.get("progress_dots", lambda: [
                {
                    "step": i,
                    "completed": i < current_index,
                    "current": i == current_index,
                    "title": step.value.replace("_", " ").title()
                }
                for i, step in enumerate(steps[:-1])  # Exclude complete step
            ]),
            lambda dot: rx.box(
                rx.circle(
                    rx.cond(
                        dot["completed"],
                        rx.icon("check", size=12, color="white"),
                        rx.text(
                            str(dot["step"] + 1),
                            font_size="xs",
                            color=rx.cond(dot["current"], "white", "gray.500")
                        )
                    ),
                    size="24px",
                    bg=rx.cond(
                        dot["completed"] | dot["current"],
                        "blue.500",
                        "gray.200"
                    ),
                    display="flex",
                    align_items="center",
                    justify_content="center"
                ),
                rx.text(
                    dot["title"],
                    font_size="xs",
                    color=rx.cond(dot["current"], "blue.600", "gray.500"),
                    text_align="center",
                    margin_top="0.25rem",
                    width="80px"
                ),
                display="flex",
                flex_direction="column",
                align_items="center"
            )
        ),
        spacing="2rem",
        justify_content="center",
        width="100%",
        margin_bottom="2rem"
    )


def step_content() -> rx.Component:
    """Display current step content."""
    current_step_data = OnboardingState.steps_data[OnboardingState.current_step]
    
    return rx.vstack(
        # Step icon and title
        rx.vstack(
            rx.text(
                current_step_data.get("icon", ""),
                font_size="4xl",
                margin_bottom="0.5rem"
            ),
            rx.heading(
                current_step_data.get("title", ""),
                size="xl",
                text_align="center",
                color="gray.800"
            ),
            rx.text(
                current_step_data.get("content", ""),
                font_size="lg",
                color="gray.600",
                text_align="center",
                line_height="1.6",
                max_width="500px"
            ),
            align_items="center",
            spacing="0.5rem",
            margin_bottom="2rem"
        ),
        
        # Step-specific content
        rx.cond(
            OnboardingState.current_step == OnboardingStep.WELCOME.value,
            rx.vstack(
                rx.foreach(
                    current_step_data.get("features", []),
                    lambda feature: rx.hstack(
                        rx.text(feature, color="gray.700"),
                        justify_content="flex-start",
                        width="100%"
                    )
                ),
                spacing="0.5rem",
                width="100%",
                max_width="400px"
            )
        ),
        
        rx.cond(
            OnboardingState.current_step == OnboardingStep.UPLOAD_DOCUMENT.value,
            rx.vstack(
                rx.text(
                    "Tips:",
                    font_weight="bold",
                    color="gray.700",
                    margin_bottom="0.5rem"
                ),
                rx.foreach(
                    current_step_data.get("tips", []),
                    lambda tip: rx.hstack(
                        rx.icon("info", size=16, color="blue.500"),
                        rx.text(tip, color="gray.600", font_size="sm"),
                        align_items="flex-start",
                        spacing="0.5rem",
                        width="100%"
                    )
                ),
                spacing="0.5rem",
                width="100%",
                max_width="500px"
            )
        ),
        
        rx.cond(
            OnboardingState.current_step == OnboardingStep.FIRST_QUERY.value,
            rx.vstack(
                rx.text(
                    "Try these example questions:",
                    font_weight="bold",
                    color="gray.700",
                    margin_bottom="0.5rem"
                ),
                rx.foreach(
                    current_step_data.get("examples", []),
                    lambda example: rx.button(
                        f'"{example}"',
                        variant="outline",
                        size="sm",
                        color_scheme="blue",
                        width="100%",
                        on_click=lambda: None  # Would set chat input
                    )
                ),
                spacing="0.5rem",
                width="100%",
                max_width="400px"
            )
        ),
        
        rx.cond(
            OnboardingState.current_step == OnboardingStep.EXPLORE_FEATURES.value,
            rx.vstack(
                rx.foreach(
                    current_step_data.get("features", []),
                    lambda feature: rx.hstack(
                        rx.text(feature, color="gray.700"),
                        justify_content="flex-start",
                        width="100%"
                    )
                ),
                spacing="0.5rem",
                width="100%",
                max_width="500px"
            )
        ),
        
        rx.cond(
            OnboardingState.current_step == OnboardingStep.COMPLETE.value,
            rx.vstack(
                rx.text(
                    "What's next?",
                    font_weight="bold",
                    color="gray.700",
                    margin_bottom="0.5rem"
                ),
                rx.foreach(
                    current_step_data.get("next_steps", []),
                    lambda step: rx.hstack(
                        rx.icon("arrow-right", size=16, color="green.500"),
                        rx.text(step, color="gray.600"),
                        align_items="flex-start",
                        spacing="0.5rem",
                        width="100%"
                    )
                ),
                spacing="0.5rem",
                width="100%",
                max_width="500px"
            )
        ),
        
        align_items="center",
        width="100%"
    )


def navigation_buttons() -> rx.Component:
    """Display navigation buttons for onboarding."""
    return rx.hstack(
        # Previous button
        rx.cond(
            OnboardingState.current_step != OnboardingStep.WELCOME.value,
            rx.button(
                "Previous",
                on_click=OnboardingState.previous_step,
                variant="outline",
                size="md"
            )
        ),
        
        rx.spacer(),
        
        # Skip button (not on last step)
        rx.cond(
            OnboardingState.current_step != OnboardingStep.COMPLETE.value,
            rx.button(
                "Skip Tutorial",
                on_click=OnboardingState.skip_onboarding_tutorial,
                variant="ghost",
                size="sm",
                color="gray.500"
            )
        ),
        
        rx.spacer(),
        
        # Next/Complete button
        rx.cond(
            OnboardingState.current_step == OnboardingStep.COMPLETE.value,
            rx.button(
                "Start Using RAG System",
                on_click=OnboardingState.complete_onboarding,
                color_scheme="green",
                size="lg"
            ),
            rx.button(
                OnboardingState.steps_data[OnboardingState.current_step].get("action_text", "Next"),
                on_click=OnboardingState.next_step,
                color_scheme="blue",
                size="md"
            )
        ),
        
        width="100%",
        align_items="center"
    )


def onboarding_modal() -> rx.Component:
    """Main onboarding modal component."""
    return rx.modal(
        rx.modal_overlay(
            rx.modal_content(
                rx.modal_body(
                    rx.vstack(
                        progress_indicator(),
                        step_content(),
                        navigation_buttons(),
                        spacing="2rem",
                        padding="2rem",
                        width="100%",
                        max_width="600px"
                    ),
                    padding="0"
                ),
                max_width="700px",
                width="90vw"
            )
        ),
        is_open=OnboardingState.show_onboarding,
        close_on_overlay_click=False,
        close_on_esc=False
    )


def onboarding_trigger() -> rx.Component:
    """Button to trigger onboarding for existing users."""
    return rx.button(
        rx.icon("circle-help", size=16),
        "Tutorial",
        on_click=OnboardingState.start_onboarding,
        variant="ghost",
        size="sm",
        color_scheme="blue"
    )


def welcome_banner() -> rx.Component:
    """Welcome banner for first-time users."""
    return rx.cond(
        ~OnboardingState.skip_onboarding & ~OnboardingState.show_onboarding,
        rx.box(
            rx.hstack(
                rx.vstack(
                    rx.heading(
                        "Welcome to Your Local RAG System! 👋",
                        size="md",
                        color="blue.700"
                    ),
                    rx.text(
                        "New here? Take a quick 2-minute tutorial to get started.",
                        color="gray.600",
                        font_size="sm"
                    ),
                    align_items="flex-start",
                    spacing="0.25rem"
                ),
                rx.spacer(),
                rx.hstack(
                    rx.button(
                        "Start Tutorial",
                        on_click=OnboardingState.start_onboarding,
                        color_scheme="blue",
                        size="sm"
                    ),
                    rx.button(
                        "Skip",
                        on_click=OnboardingState.skip_onboarding_tutorial,
                        variant="ghost",
                        size="sm"
                    ),
                    spacing="0.5rem"
                ),
                width="100%",
                align_items="center"
            ),
            padding="1rem",
            background="linear-gradient(90deg, rgba(59, 130, 246, 0.1) 0%, rgba(147, 197, 253, 0.1) 100%)",
            border="1px solid",
            border_color="blue.200",
            border_radius="lg",
            margin_bottom="1rem"
        )
    )