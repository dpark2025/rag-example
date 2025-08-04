# RAG System Testing Guide

**Authored by:** QA/Test Engineer (Darren Fong)  
**Date:** 2025-08-04  
**Version:** 1.0

---

## Overview

This guide provides comprehensive instructions for running tests, understanding the testing infrastructure, and contributing to the RAG system's quality assurance.

## Quick Start

### Prerequisites

1. **Install testing dependencies:**
   ```bash
   make install-test-deps
   # or
   pip install -r requirements-test.txt
   ```

2. **Ensure services are running:**
   ```bash
   # Start RAG backend
   make start
   # or manually
   cd app && python main.py
   ```

### Running Tests

```bash
# Quick unit tests (recommended for development)
make test-quick

# Complete unit test suite
make test-unit

# Integration tests (requires running backend)
make test-integration

# All tests with coverage
make test-all

# Generate HTML coverage report
make coverage
```

## Test Structure

```
tests/
├── conftest.py              # Global fixtures and configuration
├── fixtures/                # Test data and fixtures
│   └── documents/           # Sample documents for testing
├── unit/                    # Unit tests (70% of test pyramid)
│   ├── backend/             # Backend component tests
│   │   ├── test_document_manager.py
│   │   ├── test_upload_handler.py
│   │   └── test_rag_backend.py
│   └── frontend/            # Frontend component tests
│       └── test_document_state.py
├── integration/             # Integration tests (20% of test pyramid)
│   └── test_api_endpoints.py
├── e2e/                     # End-to-end tests (10% of test pyramid)
├── performance/             # Performance and load tests
└── accessibility/           # WCAG compliance tests
```

## Test Categories

### Unit Tests

Test individual components in isolation with mocked dependencies.

**Backend Unit Tests:**
- `test_document_manager.py` - Document CRUD operations, filtering, bulk operations
- `test_upload_handler.py` - File upload processing, WebSocket communication, task management
- `test_rag_backend.py` - RAG core functionality, embedding generation, similarity search

**Frontend Unit Tests:**
- `test_document_state.py` - Reflex state management, async operations, UI synchronization

**Running Unit Tests:**
```bash
# All unit tests
pytest tests/unit/ -v

# Specific component
pytest tests/unit/backend/test_document_manager.py -v

# With coverage
pytest tests/unit/ --cov=app --cov-report=html
```

### Integration Tests

Test interaction between components and external services.

**API Integration Tests:**
- Document management endpoints
- File upload workflows
- Query processing
- Error handling scenarios
- Performance validation

**Running Integration Tests:**
```bash
# All integration tests
pytest tests/integration/ -v

# Specific test class
pytest tests/integration/test_api_endpoints.py::TestDocumentEndpoints -v

# With service health check
make test-with-health
```

### End-to-End Tests

Test complete user workflows from UI to backend.

**Coverage:**
- Document upload and management workflows
- Chat interface with document retrieval
- Cross-browser compatibility
- Mobile responsive design

**Running E2E Tests:**
```bash
# Requires running services
make test-e2e

# Specific browser
pytest tests/e2e/ --browser chromium -v
```

## Test Configuration

### Pytest Configuration

Key settings in `pytest.ini`:

```ini
[tool:pytest]
testpaths = tests
addopts = 
    --verbose
    --cov=app
    --cov-report=html
    --cov-fail-under=80
    --strict-markers
markers =
    unit: Unit tests for individual components
    integration: Integration tests for component interaction
    slow: Slow tests that take >10 seconds
```

### Environment Variables

```bash
# For testing against different environments
export RAG_BACKEND_URL=http://localhost:8000
export CHROMADB_URL=http://localhost:8002
export OLLAMA_URL=http://localhost:11434

# Test database (uses in-memory by default)
export TEST_DATABASE=memory
```

## Test Data Management

### Fixtures

Global fixtures in `conftest.py`:
- `clean_chromadb` - Fresh database for each test
- `rag_system` - RAG system with mocked dependencies
- `sample_documents` - Standard test documents
- `mock_llm_client` - Mocked Ollama LLM client

### Sample Documents

Located in `tests/fixtures/documents/`:
- `sample.txt` - AI/ML overview document
- `technical_doc.txt` - RAG system architecture documentation

### Custom Test Data

```python
@pytest.fixture
def custom_document():
    return {
        "title": "Custom Test Document",
        "content": "Test content for specific scenarios",
        "source": "test_fixture",
        "doc_id": "custom_test_doc"
    }
```

## Mocking Strategy

### External Services

**Ollama LLM Client:**
```python
@pytest.fixture
def mock_llm_client():
    mock_client = Mock(spec=LocalLLMClient)
    mock_client.chat.return_value = "Test response from LLM."
    mock_client.health_check.return_value = True
    return mock_client
```

**ChromaDB:**
```python
@pytest.fixture
def clean_chromadb():
    client = chromadb.Client(Settings(
        persist_directory=":memory:",
        is_persistent=False
    ))
    yield client
```

**HTTP Requests:**
```python
with patch('httpx.AsyncClient') as mock_client:
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True}
    mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
```

## Performance Testing

### Benchmarking

Using `pytest-benchmark` for performance validation:

```python
def test_document_processing_performance(benchmark, rag_system, sample_documents):
    result = benchmark(rag_system.add_documents, sample_documents)
    assert "Successfully added" in result
```

**Running Performance Tests:**
```bash
# All performance tests
pytest tests/performance/ --benchmark-only

# Compare benchmarks
pytest-benchmark compare
```

### Performance Targets

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Document Upload | <30s | Processing time |
| API Response | <200ms | Response time |
| Query Processing | <2s | End-to-end time |
| Memory Usage | <512MB | Peak memory |

## Accessibility Testing

### WCAG 2.1 AA Compliance

Using `axe-core` for automated accessibility testing:

```python
def test_document_list_accessibility(selenium_driver):
    selenium_driver.get("http://localhost:3000/documents")
    results = Axe(selenium_driver).run()
    assert len(results["violations"]) == 0
```

**Manual Accessibility Checks:**
- Keyboard navigation
- Screen reader compatibility
- Color contrast validation
- Focus management

## Continuous Integration

### GitHub Actions Workflow

Automated testing on every push and pull request:

1. **Code Quality Checks:**
   - Black formatting
   - Flake8 linting
   - MyPy type checking
   - Security scanning

2. **Test Execution:**
   - Unit tests across Python 3.11/3.12
   - Integration tests with service dependencies
   - Coverage reporting

3. **Performance Validation:**
   - Benchmark execution on PR
   - Performance regression detection

### Local CI Simulation

```bash
# Run full CI pipeline locally
make ci-cycle

# Individual CI steps
make format-check
make lint
make test-ci
make coverage
```

## Debugging Tests

### Common Issues

**Import Errors:**
```bash
# Ensure proper Python path
export PYTHONPATH=/path/to/rag-example/app:$PYTHONPATH
```

**Service Dependencies:**
```bash
# Check service health
make health-check

# Start required services
make start
```

**Database Issues:**
```bash
# Clean test artifacts
make clean-tests

# Use fresh database
pytest --create-db
```

### Debug Techniques

**Verbose Output:**
```bash
pytest -v -s tests/unit/backend/test_document_manager.py::TestDocumentManager::test_list_documents
```

**Debug with pdb:**
```python
import pdb; pdb.set_trace()
```

**Logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing to Tests

### Writing New Tests

1. **Follow naming conventions:**
   - Test files: `test_*.py`
   - Test classes: `Test*`
   - Test methods: `test_*`

2. **Use appropriate markers:**
   ```python
   @pytest.mark.unit
   @pytest.mark.slow
   @pytest.mark.integration
   ```

3. **Include docstrings:**
   ```python
   def test_document_upload_success(self, upload_handler, sample_upload_file):
       """Test successful single file upload processing."""
   ```

### Test Review Checklist

- [ ] Tests cover both success and failure scenarios
- [ ] Edge cases and boundary conditions tested
- [ ] Appropriate mocking of external dependencies
- [ ] Performance considerations addressed
- [ ] Accessibility requirements validated
- [ ] Clear, descriptive test names and documentation

### Quality Gates

**Pre-commit:**
- Unit tests pass
- Code formatted (Black)
- Linting passes (Flake8)

**Pull Request:**
- All tests pass
- Coverage ≥80% for new code
- Integration tests validate API changes
- Performance regression check

**Pre-deployment:**
- End-to-end tests pass
- Accessibility compliance verified
- Security scan clean
- Load testing passed (if applicable)

## Monitoring and Metrics

### Test Execution Metrics

- Test execution time trends
- Test reliability/flakiness rates
- Coverage trend analysis
- Performance benchmark trends

### Quality Metrics

- Defect detection rate by test type
- Production incident correlation
- Customer satisfaction impact
- Development velocity impact

### Reports and Dashboards

**Coverage Report:** `htmlcov/index.html`
**Test Results:** `test-results.xml`
**Performance Benchmarks:** `benchmark.json`
**Security Scan:** `bandit-report.json`

## Troubleshooting

### Common Test Failures

**ChromaDB Connection Issues:**
```bash
# Check ChromaDB service
curl http://localhost:8002/api/v1/heartbeat

# Restart ChromaDB
make restart
```

**Ollama Dependency:**
```bash
# Tests should use mocked LLM client
# For integration tests requiring real Ollama:
ollama serve
ollama pull llama3.2:3b
```

**Port Conflicts:**
```bash
# Check for port usage
lsof -i :8000 -i :8002 -i :11434

# Kill conflicting processes
make stop
```

### Getting Help

1. **Check test logs:** Review detailed error messages and stack traces
2. **Verify environment:** Ensure all dependencies and services are available
3. **Run health checks:** Use `make health-check` to validate system state
4. **Consult documentation:** Review test strategy and implementation guides
5. **Create an issue:** Document problems for team resolution

---

## Summary

The RAG system testing infrastructure provides comprehensive quality assurance through:

- **90%+ test coverage** across unit, integration, and end-to-end tests
- **Automated CI/CD pipeline** with quality gates and performance validation
- **Accessibility compliance** testing for WCAG 2.1 AA standards
- **Performance benchmarking** with regression detection
- **Security scanning** for vulnerability identification

Use `make help` to see all available testing commands and get started with quality assurance for the RAG system.