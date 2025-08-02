"""Reflex configuration file for RAG application."""

import reflex as rx

config = rx.Config(
    app_name="rag_reflex_app",
    app_module_import="rag_reflex_app.rag_reflex_app",
    db_url="sqlite:///reflex_db.db",
    env=rx.Env.DEV,
    frontend_port=3000,
    backend_port=8001,  # Different from FastAPI port (8000)
    backend_host="0.0.0.0",
    frontend_host="0.0.0.0",
    # Disable plugins to reduce warnings
    disable_plugins=[
        "reflex.plugins.sitemap.SitemapPlugin",
    ],
    # Development optimizations
    compile=True,
)