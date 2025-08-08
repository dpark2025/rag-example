# ISSUES.md - Known Issues and Future Work

This document tracks known issues and future work items for the RAG Example project after the repository cleanup.

## Backend & Infrastructure Issues

### 1. Backend Services Not Running
- [ ] **Short description:** Backend services (FastAPI and ChromaDB) are not currently running in containers.
- **Description:** The `make health` command shows that RAG Backend and ChromaDB are unhealthy. These services need to be started with `make start` but appear to not be running. This is expected as containers were cleaned during the cleanup process, but users will need to run `make start` to begin using the system.

### 2. Test Scripts Reference Removed Components
- [ ] **Short description:** Test scripts in the scripts directory still reference the removed components directory structure.
- **Description:** Files like `scripts/test_reflex_phase1.py` contain references to the old component structure that was removed during cleanup (e.g., `components/common`, `components/sidebar`). These test scripts need to be updated to reflect the new minimal architecture or removed if no longer needed.

### 3. Missing Backend Container Build Files
- [ ] **Short description:** Some docker-compose files may reference configurations that need validation.
- **Description:** While docker-compose.backend.yml exists and builds successfully, the full production deployment files (docker-compose.production.yml, docker-compose.monitoring.yml) referenced in documentation need to be verified to ensure they work with the cleaned structure.

## Documentation Issues

### 4. MASTER_DOCUMENTATION.md Is Overly Detailed
- [ ] **Short description:** The master documentation still contains extensive references to features and structures that may not align with the minimal version.
- **Description:** The MASTER_DOCUMENTATION.md file (1199 lines) contains detailed information about production deployment, monitoring, and advanced features that may not be fully implemented or tested with the new minimal architecture. This document should be reviewed and potentially simplified to match the current minimal implementation state.

### 5. Command Validation Plan References Missing Tests
- [ ] **Short description:** COMMAND_VALIDATION_PLAN.md references test commands that were removed from the Makefile.
- **Description:** The command validation plan includes references to test commands (test-quick, test-unit, test-integration, etc.) that were removed from the Makefile during cleanup. The validation plan should be updated to reflect only the commands that remain, or the test commands should be restored if testing is needed.

## UI/Frontend Issues

### 6. Upload Functionality Not Connected to Backend
- [ ] **Short description:** The document upload modal in the UI is not connected to the backend API.
- **Description:** The upload modal in `index_minimal.py` displays correctly but doesn't actually upload files to the backend. The upload button and drag-and-drop zone need to be connected to the actual file upload API endpoints to make document management functional.

### 7. Chat Messages Not Using Real RAG Pipeline
- [ ] **Short description:** Chat functionality shows mock responses instead of real RAG responses.
- **Description:** The chat interface in `index_minimal.py` generates mock responses (line 32-35) instead of calling the actual RAG backend API. The chat needs to be integrated with the `/query` endpoint to provide real document-based responses.

### 8. System Health Checks Are Simulated
- [ ] **Short description:** System status panel shows simulated health data instead of real service status.
- **Description:** The system status panel uses hardcoded boolean values for service health (lines 12-14 in MinimalChatState) and the refresh button only toggles the embeddings status. This needs to be connected to actual health check endpoints to show real service status.

## Development Workflow Issues

### 9. No Development Environment Variables File
- [ ] **Short description:** Missing .env or .env.example file for configuration.
- **Description:** The project doesn't have a .env.example file to guide users on what environment variables need to be set. This would help with configuration of Ollama host, API URLs, and other settings that might vary between development and production.

### 10. Scripts Directory Needs Cleanup
- [ ] **Short description:** Scripts directory contains many scripts that may no longer be relevant.
- **Description:** The scripts directory contains numerous validation and test scripts that reference the old architecture. A review is needed to determine which scripts are still relevant for the minimal architecture and which should be removed or updated.

## Performance & Optimization

### 11. No Caching Implementation
- [ ] **Short description:** The system doesn't implement caching for embeddings or query results.
- **Description:** For better performance, the system should implement caching for document embeddings and frequently asked queries. This would reduce processing time and improve response times for common questions.

### 12. No Batch Document Processing
- [ ] **Short description:** Document upload doesn't support efficient batch processing.
- **Description:** While the UI suggests bulk upload capability, the backend doesn't efficiently handle batch document processing. Implementing parallel processing for multiple document uploads would significantly improve performance when adding many documents.

## Testing & Quality Assurance

### 13. No Test Suite for Minimal Version
- [ ] **Short description:** The minimal version lacks unit and integration tests.
- **Description:** After removing the test commands from the Makefile, there's no clear testing strategy for the minimal version. A basic test suite should be created to ensure the core functionality (document upload, chat, health checks) works correctly.

### 14. No Validation for Supported File Types
- [ ] **Short description:** File type validation is only cosmetic in the UI.
- **Description:** The UI shows "Supported: PDF, TXT, MD, HTML" but doesn't actually validate file types before upload. Both frontend and backend validation should be implemented to prevent unsupported files from being processed.

## Security & Production Readiness

### 15. No Authentication or User Management
- [ ] **Short description:** The system has no authentication or user isolation.
- **Description:** The current implementation has no user authentication, meaning anyone with access to the URL can upload documents and query the system. For production use, authentication and user session management should be implemented.

### 16. No Rate Limiting or Resource Quotas
- [ ] **Short description:** API endpoints have no rate limiting or resource protection.
- **Description:** The backend API endpoints don't implement rate limiting or resource quotas, which could lead to abuse or resource exhaustion. Basic rate limiting should be added to protect the system from overuse.

## Next Steps Priority

### High Priority (Blocking Basic Functionality)
1. Connect upload functionality to backend (#6)
2. Connect chat to real RAG pipeline (#7)
3. Connect health checks to real endpoints (#8)
4. Create .env.example file (#9)

### Medium Priority (Enhancing Usability)
5. Add file type validation (#14)
6. Implement basic caching (#11)
7. Create minimal test suite (#13)
8. Clean up scripts directory (#10)

### Low Priority (Future Enhancements)
9. Add authentication (#15)
10. Implement rate limiting (#16)
11. Add batch processing (#12)
12. Simplify documentation (#4, #5)

---

*Last Updated: 2025-08-08*
*Status: Post-cleanup assessment complete*