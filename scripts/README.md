# Scripts Directory

This directory contains utility scripts for the Local RAG System.

## Container Management Scripts

### build-unified.sh
Builds the unified RAG container with all services.
- Detects Podman/Docker automatically  
- Cleans up existing containers
- Builds the unified image
- Provides run instructions

**Usage:**
```bash
./scripts/build-unified.sh
# or use convenience script
./build.sh
```

### run-unified.sh  
Runs the unified container with proper configuration.
- Stops existing containers
- Starts unified container with all ports
- Waits for readiness (up to 90 seconds)
- Shows access URLs and status

**Usage:**
```bash
./scripts/run-unified.sh
# or use convenience script  
./run.sh
```

## Testing Scripts

### run_clean_tests.sh
Runs tests with clean output and suppressed warnings.
- Activates virtual environment if needed
- Suppresses external library warnings
- Runs pytest with verbose output

**Usage:**
```bash
./scripts/run_clean_tests.sh              # Run all tests
./scripts/run_clean_tests.sh tests/unit/  # Run specific tests
```

## Convenience Scripts (Root Level)

For easier access, convenience scripts are provided in the root:

- `./build.sh` → `./scripts/build-unified.sh`
- `./run.sh` → `./scripts/run-unified.sh`

## Script Organization

Scripts are organized by purpose:
- **Container Management**: Building and running containers
- **Testing**: Test execution and validation
- **Development**: Development workflow helpers

All scripts include:
- Error handling with `set -e`
- Clear status messages with emoji indicators
- Help text and usage examples
- Cross-platform compatibility (Podman/Docker)