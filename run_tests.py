#!/usr/bin/env python3
"""
Test Runner for Wikipedia Podcast Pipeline
Runs all tests with proper configuration and reporting
"""

import unittest
import sys
import os
import time
from pathlib import Path
from io import StringIO

# Add src directory to path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

class ColoredTextTestResult(unittest.TextTestResult):
    """Custom test result class with colored output"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_start_time = None
    
    def startTest(self, test):
        super().startTest(test)
        self.test_start_time = time.time()
        if self.showAll:
            self.stream.write(f"  🧪 {self.getDescription(test)} ... ")
            self.stream.flush()
    
    def addSuccess(self, test):
        super().addSuccess(test)
        if self.showAll:
            duration = time.time() - self.test_start_time
            self.stream.writeln(f"✅ ok ({duration:.3f}s)")
        elif self.dots:
            self.stream.write('✅')
            self.stream.flush()
    
    def addError(self, test, err):
        super().addError(test, err)
        if self.showAll:
            duration = time.time() - self.test_start_time
            self.stream.writeln(f"❌ ERROR ({duration:.3f}s)")
        elif self.dots:
            self.stream.write('❌')
            self.stream.flush()
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        if self.showAll:
            duration = time.time() - self.test_start_time
            self.stream.writeln(f"❌ FAIL ({duration:.3f}s)")
        elif self.dots:
            self.stream.write('❌')
            self.stream.flush()
    
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        if self.showAll:
            self.stream.writeln(f"⏭️  SKIP ({reason})")
        elif self.dots:
            self.stream.write('⏭️')
            self.stream.flush()

class ColoredTextTestRunner(unittest.TextTestRunner):
    """Custom test runner with colored output"""
    resultclass = ColoredTextTestResult

def discover_and_run_tests():
    """Discover and run all tests"""
    
    print("🧪 WIKIPEDIA PODCAST PIPELINE - TEST SUITE")
    print("=" * 60)
    
    # Setup test discovery
    test_dir = Path(__file__).parent / 'tests'
    
    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        print("Please create tests/ directory with test files")
        return False
    
    # Discover tests
    loader = unittest.TestLoader()
    start_dir = str(test_dir)
    
    try:
        suite = loader.discover(start_dir, pattern='test_*.py')
    except Exception as e:
        print(f"❌ Error discovering tests: {e}")
        return False
    
    # Count tests
    test_count = suite.countTestCases()
    
    if test_count == 0:
        print("⚠️  No tests found!")
        print("Please create test files with pattern test_*.py in tests/ directory")
        return False
    
    print(f"📊 Found {test_count} tests")
    print()
    
    # Run tests
    runner = ColoredTextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        failfast=False,
        buffer=True
    )
    
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    total_time = end_time - start_time
    print(f"⏱️  Total time: {total_time:.2f} seconds")
    print(f"🧪 Tests run: {result.testsRun}")
    print(f"✅ Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    
    if result.failures:
        print(f"❌ Failures: {len(result.failures)}")
        for test, traceback in result.failures:
            print(f"   • {test}")
    
    if result.errors:
        print(f"❌ Errors: {len(result.errors)}")
        for test, traceback in result.errors:
            print(f"   • {test}")
    
    if result.skipped:
        print(f"⏭️  Skipped: {len(result.skipped)}")
        for test, reason in result.skipped:
            print(f"   • {test}: {reason}")
    
    # Final status
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED!")
        return True
    else:
        print(f"\n💥 TESTS FAILED!")
        print(f"   {len(result.failures)} failures, {len(result.errors)} errors")
        return False

def run_specific_test(test_name):
    """Run a specific test file or test case"""
    
    print(f"🧪 Running specific test: {test_name}")
    print("=" * 60)
    
    # Try to load specific test
    loader = unittest.TestLoader()
    
    try:
        if '.' in test_name:
            # Specific test method (e.g., test_content_fetcher.TestWikipediaArticle.test_article_creation)
            suite = loader.loadTestsFromName(test_name)
        else:
            # Test file (e.g., test_content_fetcher)
            suite = loader.loadTestsFromName(f"tests.{test_name}")
    except Exception as e:
        print(f"❌ Error loading test '{test_name}': {e}")
        return False
    
    # Run the test
    runner = ColoredTextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def check_dependencies():
    """Check if test dependencies are available"""
    
    print("🔍 Checking test dependencies...")
    
    missing_deps = []
    
    # Check for required modules
    try:
        import unittest
        print("  ✅ unittest - available")
    except ImportError:
        missing_deps.append("unittest")
    
    try:
        from unittest.mock import Mock, patch
        print("  ✅ unittest.mock - available")
    except ImportError:
        missing_deps.append("unittest.mock")
    
    # Check for source modules
    try:
        sys.path.insert(0, str(Path(__file__).parent / 'src'))
        import content_fetcher
        print("  ✅ content_fetcher - available")
    except ImportError as e:
        print(f"  ❌ content_fetcher - missing: {e}")
        missing_deps.append("content_fetcher")
    
    try:
        import script_formatter
        print("  ✅ script_formatter - available")
    except ImportError as e:
        print(f"  ❌ script_formatter - missing: {e}")
        missing_deps.append("script_formatter")
    
    if missing_deps:
        print(f"\n❌ Missing dependencies: {', '.join(missing_deps)}")
        return False
    
    print("✅ All dependencies available")
    return True

def create_test_directory_structure():
    """Create test directory structure if it doesn't exist"""
    
    test_dir = Path(__file__).parent / 'tests'
    test_dir.mkdir(exist_ok=True)
    
    # Create __init__.py for tests package
    init_file = test_dir / '__init__.py'
    if not init_file.exists():
        init_file.write_text('"""Test package for Wikipedia Podcast Pipeline"""')
    
    print(f"📁 Test directory ready: {test_dir}")

def main():
    """Main test runner function"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Run tests for Wikipedia Podcast Pipeline")
    parser.add_argument('--test', '-t', help='Run specific test (e.g., test_content_fetcher)')
    parser.add_argument('--check-deps', action='store_true', help='Check test dependencies')
    parser.add_argument('--create-dirs', action='store_true', help='Create test directory structure')
    parser.add_argument('--integration', action='store_true', help='Include integration tests (requires internet)')
    
    args = parser.parse_args()
    
    # Set environment variable for integration tests
    if args.integration:
        os.environ['RUN_INTEGRATION_TESTS'] = '1'
        print("🌐 Integration tests enabled (requires internet connection)")
    
    # Handle specific commands
    if args.check_deps:
        return 0 if check_dependencies() else 1
    
    if args.create_dirs:
        create_test_directory_structure()
        return 0
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Cannot run tests due to missing dependencies")
        return 1
    
    # Create test directories if needed
    create_test_directory_structure()
    
    # Run specific test or all tests
    if args.test:
        success = run_specific_test(args.test)
    else:
        success = discover_and_run_tests()
    
    return 0 if success else 1

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)