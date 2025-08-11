# Code Style and Conventions

## Code Style Guidelines
- **Python Style**: Follow PEP 8 standards
- **Type Hints**: Use type annotations throughout the codebase
- **Async/Await**: Prefer async patterns for I/O operations
- **Error Handling**: Comprehensive error handling with meaningful error messages

## Project Structure Patterns
```
rag-example/
├── app/                    # Main application code
│   ├── reflex_app/        # Reflex UI application
│   │   ├── components/    # UI components
│   │   ├── state/         # State management
│   │   ├── services/      # API client
│   │   └── pages/         # Page routes
│   ├── main.py            # FastAPI backend entry point
│   ├── rag_backend.py     # RAG processing engine
│   └── *.py               # Various service modules
├── tests/                 # Test files
├── requirements*.txt      # Dependency management
└── Makefile              # Build and development commands
```

## Naming Conventions
- **Files**: snake_case for Python files
- **Classes**: PascalCase (e.g., `DocumentInfo`, `QueryRequest`)
- **Functions**: snake_case (e.g., `health_check`, `upload_files`)
- **Variables**: snake_case
- **Constants**: UPPER_SNAKE_CASE

## API Design Patterns
- **RESTful Endpoints**: Following REST conventions
- **Response Models**: Pydantic models for all API responses
- **Versioned APIs**: `/api/v1/` prefix for versioned endpoints
- **Error Responses**: Consistent error response format

## Documentation Style
- **Docstrings**: Use for all public functions and classes
- **Type Annotations**: Required for function parameters and return types
- **API Documentation**: Auto-generated via FastAPI/OpenAPI