#!/bin/bash
# Clean test runner script that suppresses external library warnings
# Usage: ./run_clean_tests.sh [test_path]

# Activate virtual environment if not already active
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Set environment variables to suppress warnings (simpler approach)
export PYTHONWARNINGS="ignore::DeprecationWarning,ignore::UserWarning"

# Run tests with clean output
if [ $# -eq 0 ]; then
    pytest tests/ -v --disable-warnings
else
    pytest "$1" -v --disable-warnings
fi