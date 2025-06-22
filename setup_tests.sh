#!/bin/bash
# Test Setup Script for Wikipedia Podcast Pipeline
# Creates test directory structure and runs test suite

echo "🧪 SETTING UP WIKIPEDIA PODCAST PIPELINE TESTS"
echo "================================================"

# Create tests directory if it doesn't exist
if [ ! -d "tests" ]; then
    echo "📁 Creating tests directory..."
    mkdir -p tests
    echo "✅ Tests directory created"
fi

# Create test data directory
if [ ! -d "tests/data" ]; then
    echo "📁 Creating test data directory..."
    mkdir -p tests/data
    echo "✅ Test data directory created"
fi

# Check Python version
echo "🐍 Checking Python version..."
python_version=$(python3 --version 2>&1)
echo "   $python_version"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "❌ Python 3.8+ required"
    exit 1
fi
echo "✅ Python version OK"

# Check required modules
echo "📦 Checking required modules..."

required_modules=("unittest" "unittest.mock" "pathlib" "json" "tempfile")
missing_modules=()

for module in "${required_modules[@]}"; do
    if python3 -c "import $module" 2>/dev/null; then
        echo "   ✅ $module"
    else
        echo "   ❌ $module (missing)"
        missing_modules+=("$module")
    fi
done

if [ ${#missing_modules[@]} -ne 0 ]; then
    echo "❌ Missing required modules: ${missing_modules[*]}"
    echo "Please install missing modules and try again"
    exit 1
fi

# Check if source files exist
echo "📄 Checking source files..."
source_files=("src/content_fetcher.py" "src/script_formatter.py" "src/pipeline.py")
missing_files=()

for file in "${source_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (missing)"
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -ne 0 ]; then
    echo "❌ Missing source files: ${missing_files[*]}"
    echo "Please ensure all source files exist before running tests"
    exit 1
fi

# Set up environment for tests
echo "⚙️  Setting up test environment..."

# Create temporary API key for tests (if not already set)
if [ -z "$OPENAI_API_KEY" ]; then
    export OPENAI_API_KEY="sk-test-key-12345"
    echo "   🔑 Using mock API key for tests"
else
    echo "   🔑 Using existing API key"
fi

echo "✅ Test environment ready"

# Run dependency check
echo "🔍 Running dependency check..."
if python3 run_tests.py --check-deps; then
    echo "✅ All dependencies available"
else
    echo "❌ Dependency check failed"
    exit 1
fi

# Display test options
echo ""
echo "🎯 TEST OPTIONS"
echo "==============="
echo "Run all tests:                  python3 run_tests.py"
echo "Run specific test file:         python3 run_tests.py --test test_content_fetcher"
echo "Run with integration tests:     python3 run_tests.py --integration"
echo "Check dependencies only:        python3 run_tests.py --check-deps"
echo ""

# Ask if user wants to run tests now
read -p "🚀 Run all tests now? (y/N): " run_tests

if [[ $run_tests =~ ^[Yy]$ ]]; then
    echo ""
    echo "🧪 RUNNING ALL TESTS"
    echo "===================="
    python3 run_tests.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 ALL TESTS COMPLETED SUCCESSFULLY!"
    else
        echo ""
        echo "💥 SOME TESTS FAILED"
        echo "Check the output above for details"
        exit 1
    fi
else
    echo ""
    echo "✅ Test setup complete!"
    echo "Run 'python3 run_tests.py' when ready to test"
fi