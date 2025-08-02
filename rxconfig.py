"""Reflex configuration file for RAG application."""

import reflex as rx

class ReflexConfig(rx.Config):
    app_name = "rag_reflex_app"
    db_url = "sqlite:///reflex_db.db"
    env = rx.Env.DEV
    frontend_port = 3000
    backend_port = 8001  # Different from FastAPI port (8000)
    deploy_url = None
    backend_host = "0.0.0.0"
    frontend_host = "0.0.0.0"

config = ReflexConfig()