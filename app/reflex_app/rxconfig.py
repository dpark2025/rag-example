"""Reflex configuration file for RAG application - Enhanced for React DOM stability."""

import reflex as rx

config = rx.Config(
    app_name="rag_reflex_app",
    app_module_import="rag_reflex_app.rag_reflex_app_minimal",
    db_url="sqlite:///reflex_db.db",
    env=rx.Env.DEV,
    frontend_port=3000,
    backend_port=8001,  # Different from FastAPI port (8000)
    backend_host="127.0.0.1",
    frontend_host="127.0.0.1",
    
    # React DOM stability fixes
    react_strict_mode=False,  # Keep disabled to prevent double-rendering issues
    
    # Enhanced error boundaries and stability
    react_debug=True,  # Enable debug mode for better error reporting
    
    # Disable problematic plugins
    disable_plugins=[
        "reflex.plugins.sitemap.SitemapPlugin",
    ],
    
    # Development optimizations for stability
    compile=True,
    
    # Add timeout settings for better error handling
    timeout_app_start=60,  # 60 seconds for app start
    
    # Memory and performance optimizations
    memory_limit="512MB",  # Prevent memory issues
    
    # Enable CORS for development
    cors_allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
)