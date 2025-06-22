#!/usr/bin/env python3
"""
Test Issue Fixer
Diagnoses and attempts to fix common test issues
"""

import sys
import os
from pathlib import Path

def check_file_exists(filepath):
    """Check if a file exists and is readable"""
    path = Path(filepath)
    if not path.exists():
        return False, f"File does not exist: {filepath}"
    
    if not path.is_file():
        return False, f"Path is not a file: {filepath}"
    
    try:
        with open(path, 'r') as f:
            f.read(100)  # Try to read first 100 chars
        return True, "File is readable"
    except Exception as e:
        return False, f"Cannot read file: {e}"

def check_python_syntax(filepath):
    """Check if a Python file has valid syntax"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        compile(content, filepath, 'exec')
        return True, "Syntax is valid"
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error checking syntax: {e}"

def test_imports():
    """Test importing each module"""
    sys.path.insert(0, 'src')
    
    modules_to_test = [
        ('content_fetcher', 'WikipediaContentFetcher'),
        ('script_formatter', 'PodcastScriptFormatter'), 
        ('pipeline', 'PodcastPipeline')
    ]
    
    results = []
    
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name)
            if hasattr(module, class_name):
                results.append((module_name, True, f"✅ {class_name} available"))
            else:
                results.append((module_name, False, f"❌ {class_name} not found in module"))
        except ImportError as e:
            results.append((module_name, False, f"❌ Import error: {e}"))
        except Exception as e:
            results.append((module_name, False, f"❌ Unexpected error: {e}"))
    
    return results

def check_test_files():
    """Check test files for issues"""
    test_files = [
        'tests/test_content_fetcher.py',
        'tests/test_script_formatter.py',
        'tests/test_pipeline.py'
    ]
    
    results = []
    
    for test_file in test_files:
        exists, msg = check_file_exists(test_file)
        if exists:
            syntax_ok, syntax_msg = check_python_syntax(test_file)
            results.append((test_file, exists and syntax_ok, f"{msg}, {syntax_msg}"))
        else:
            results.append((test_file, False, msg))
    
    return results

def main():
    """Main diagnostic function"""
    print("🔍 DIAGNOSING TEST ISSUES")
    print("=" * 40)
    
    # Check source files
    print("\n📄 Checking source files...")
    source_files = ['src/content_fetcher.py', 'src/script_formatter.py', 'src/pipeline.py']
    
    for src_file in source_files:
        exists, msg = check_file_exists(src_file)
        status = "✅" if exists else "❌"
        print(f"   {status} {src_file}: {msg}")
        
        if exists:
            syntax_ok, syntax_msg = check_python_syntax(src_file)
            syntax_status = "✅" if syntax_ok else "❌"
            print(f"      {syntax_status} Syntax: {syntax_msg}")
    
    # Test imports
    print("\n📦 Testing imports...")
    import_results = test_imports()
    
    for module_name, success, msg in import_results:
        status = "✅" if success else "❌"
        print(f"   {status} {module_name}: {msg}")
    
    # Check test files
    print("\n🧪 Checking test files...")
    test_results = check_test_files()
    
    for test_file, success, msg in test_results:
        status = "✅" if success else "❌"
        print(f"   {status} {test_file}: {msg}")
    
    # Summary
    print("\n📊 SUMMARY")
    print("-" * 20)
    
    all_imports_ok = all(result[1] for result in import_results)
    all_tests_ok = all(result[1] for result in test_results)
    
    if all_imports_ok:
        print("✅ All modules can be imported")
    else:
        print("❌ Some modules have import issues")
        print("   Fix source file syntax errors first")
    
    if all_tests_ok:
        print("✅ All test files are readable")
    else:
        print("❌ Some test files have issues")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS")
    print("-" * 20)
    
    if not all_imports_ok:
        print("1. Fix syntax errors in source files")
        print("2. Check for missing dependencies")
        print("3. Verify file paths and permissions")
    
    print("4. Run simple test first: python3 tests/test_simple.py")
    print("5. Then run individual tests: python3 run_tests.py --test test_content_fetcher")

if __name__ == '__main__':
    main()