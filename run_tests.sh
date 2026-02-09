#!/bin/bash

# Run all tests across packages
# Usage: ./run_tests.sh

set -e  # Exit on first error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "Running all tests for human-checkphrase"
echo "========================================"
echo ""

# Track results
PASSED=0
FAILED=0

run_test() {
    local name="$1"
    local dir="$2"
    local cmd="$3"
    
    echo "----------------------------------------"
    echo "[$name]"
    echo "----------------------------------------"
    
    if [ -n "$dir" ]; then
        cd "$SCRIPT_DIR/$dir"
    else
        cd "$SCRIPT_DIR"
    fi
    
    if eval "$cmd"; then
        echo "✓ $name: PASSED"
        ((PASSED++))
    else
        echo "✗ $name: FAILED"
        ((FAILED++))
    fi
    echo ""
}

# Rust tests
run_test "Rust" "" "cargo test -- --nocapture"

# JavaScript tests (install deps if needed)
run_test "JavaScript" "js" "npm install --silent && npm test"

# Dart tests (install deps if needed)
run_test "Dart" "dart" "dart pub get --no-precompile && dart test"

# Summary
echo "========================================"
echo "SUMMARY"
echo "========================================"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "========================================"

if [ $FAILED -gt 0 ]; then
    exit 1
fi
