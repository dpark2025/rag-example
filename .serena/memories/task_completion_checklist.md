# Task Completion Checklist

## When a Coding Task is Completed

### 1. Code Quality Checks
- `make lint` - Run code quality and style checks
- Ensure all linting issues are resolved
- Verify type hints are properly used
- Check for any code style violations

### 2. Testing Requirements
- `make test-quick` - Run fast unit tests (minimum requirement)
- `make test-all` - Run complete test suite with coverage (for significant changes)
- Ensure test coverage remains above 80% (configured in pytest.ini)
- Add new tests for any new functionality

### 3. Health Verification
- `make health` - Verify all services are healthy
- Check that all endpoints respond correctly:
  - RAG Backend: http://localhost:8000/health
  - ChromaDB: http://localhost:8002/api/v2/heartbeat
  - Ollama: http://localhost:11434/api/tags

### 4. Integration Testing
- Test the complete workflow end-to-end
- Verify document upload and processing works
- Test query functionality through the UI
- Ensure all API endpoints function correctly

### 5. Documentation Updates
- Update relevant documentation if APIs changed
- Ensure code has proper docstrings
- Update README.md if new features added

### 6. Performance Verification
- Check that changes don't negatively impact performance
- Monitor response times through health endpoints
- Verify memory usage remains reasonable

## Before Committing Code
- All tests pass (`make test-all`)
- Linting passes (`make lint`)
- System health check passes (`make health`)
- Changes are properly documented
- No debug code or temporary changes remain

## Deployment Verification
- `make restart` - Ensure clean restart works
- Verify production deployment still works
- Check monitoring dashboards function correctly