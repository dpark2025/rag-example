"""Minimal RAG Application - Clean Architecture for DOM Stability."""

import reflex as rx
from .pages.index_minimal import minimal_index_page

# Minimal theme with no custom head components
theme = rx.theme(
    appearance="dark",
    accent_color="violet", 
    has_background=True
)

# Clean app with no head component conflicts
app = rx.App(
    theme=theme
)

# Add single page
app.add_page(
    minimal_index_page,
    route="/",
    title="RAG System"
)