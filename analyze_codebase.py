#!/usr/bin/env python3
"""
Simple Codebase Analyzer - More Reliable Version
Analyzes Python files without complex AST parsing that might fail
"""

import os
import re
from pathlib import Path
from collections import defaultdict

def analyze_file(filepath):
    """Analyze a single Python file with basic regex parsing"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.splitlines()
        
        # Basic counts
        info = {
            'filename': filepath.name,
            'path': str(filepath),
            'lines': len(lines),
            'size_kb': len(content) / 1024,
            'classes': [],
            'functions': [],
            'imports': [],
            'has_main': False
        }
        
        # Find classes
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Classes
            if stripped.startswith('class ') and ':' in stripped:
                class_match = re.match(r'class\s+(\w+)', stripped)
                if class_match:
                    info['classes'].append({
                        'name': class_match.group(1),
                        'line': i + 1
                    })
            
            # Functions (not inside classes - rough heuristic)
            elif stripped.startswith('def ') and ':' in stripped:
                func_match = re.match(r'def\s+(\w+)', stripped)
                if func_match:
                    # Check indentation to see if it's a top-level function
                    if len(line) - len(line.lstrip()) == 0:  # No indentation
                        info['functions'].append({
                            'name': func_match.group(1),
                            'line': i + 1,
                            'is_private': func_match.group(1).startswith('_')
                        })
            
            # Imports
            elif stripped.startswith('import ') or stripped.startswith('from '):
                info['imports'].append(stripped)
            
            # Check for main
            elif '__name__' in stripped and '__main__' in stripped:
                info['has_main'] = True
        
        # Count methods in classes (rough estimate)
        method_count = 0
        in_class = False
        class_indent = 0
        
        for line in lines:
            stripped = line.strip()
            current_indent = len(line) - len(line.lstrip())
            
            if stripped.startswith('class ') and ':' in stripped:
                in_class = True
                class_indent = current_indent
            elif in_class and current_indent <= class_indent and stripped and not stripped.startswith('#'):
                if not stripped.startswith('class '):
                    in_class = False
            elif in_class and stripped.startswith('def ') and current_indent > class_indent:
                method_count += 1
        
        info['methods'] = method_count
        
        return info
        
    except Exception as e:
        return {
            'filename': filepath.name,
            'path': str(filepath),
            'lines': 0,
            'size_kb': 0,
            'classes': [],
            'functions': [],
            'imports': [],
            'methods': 0,
            'has_main': False,
            'error': str(e)
        }

def analyze_codebase(src_dir="./src"):
    """Analyze all Python files in source directory"""
    src_path = Path(src_dir)
    
    if not src_path.exists():
        print(f"❌ Directory not found: {src_dir}")
        return
    
    # Find Python files
    python_files = [f for f in src_path.glob("*.py") if not f.name.startswith('.')]
    
    if not python_files:
        print("❌ No Python files found")
        return
    
    print(f"🔍 Analyzing {len(python_files)} Python files in {src_path.absolute()}")
    print("=" * 80)
    
    # Analyze each file
    modules = []
    for filepath in sorted(python_files):
        info = analyze_file(filepath)
        modules.append(info)
    
    # Generate summary
    total_lines = sum(m['lines'] for m in modules)
    total_classes = sum(len(m['classes']) for m in modules)
    total_functions = sum(len(m['functions']) for m in modules)
    total_methods = sum(m['methods'] for m in modules)
    total_size = sum(m['size_kb'] for m in modules)
    executable_count = sum(1 for m in modules if m['has_main'])
    
    # Print overview
    print(f"📊 OVERVIEW")
    print(f"Files: {len(modules)}")
    print(f"Total lines: {total_lines:,}")
    print(f"Total size: {total_size:.1f} KB")
    print(f"Classes: {total_classes}")
    print(f"Functions: {total_functions}")  
    print(f"Methods: {total_methods}")
    print(f"Executable files: {executable_count}")
    print()
    
    # Print file details
    print(f"📁 FILE BREAKDOWN")
    print("-" * 50)
    
    for module in sorted(modules, key=lambda x: x['lines'], reverse=True):
        print(f"📄 {module['filename']}")
        print(f"   📊 {module['lines']:,} lines ({module['size_kb']:.1f} KB)")
        
        if 'error' in module:
            print(f"   ❌ Error: {module['error']}")
            continue
        
        if module['classes']:
            class_names = [c['name'] for c in module['classes']]
            print(f"   🏗️  Classes ({len(module['classes'])}): {', '.join(class_names)}")
        
        if module['functions']:
            func_names = [f['name'] for f in module['functions']]
            public_funcs = [f for f in func_names if not f.startswith('_')]
            if public_funcs:
                print(f"   ⚙️  Functions ({len(public_funcs)}): {', '.join(public_funcs[:5])}")
                if len(public_funcs) > 5:
                    print(f"      ... and {len(public_funcs) - 5} more")
        
        if module['methods'] > 0:
            print(f"   🔧 Methods: {module['methods']}")
        
        if module['imports']:
            unique_imports = set()
            for imp in module['imports']:
                if imp.startswith('import '):
                    unique_imports.add(imp.replace('import ', '').split()[0])
                elif imp.startswith('from '):
                    module_name = imp.split()[1]
                    unique_imports.add(module_name)
            
            print(f"   📦 Imports ({len(unique_imports)}): {', '.join(sorted(list(unique_imports))[:5])}")
            if len(unique_imports) > 5:
                print(f"      ... and {len(unique_imports) - 5} more")
        
        if module['has_main']:
            print(f"   🚀 Executable")
        
        print()
    
    # Dependencies
    all_imports = set()
    for module in modules:
        for imp in module['imports']:
            if imp.startswith('import '):
                all_imports.add(imp.replace('import ', '').split()[0])
            elif imp.startswith('from '):
                module_name = imp.split()[1]
                all_imports.add(module_name)
    
    print(f"📦 ALL DEPENDENCIES ({len(all_imports)})")
    print("-" * 30)
    external_deps = sorted([imp for imp in all_imports if not any(imp == m['filename'][:-3] for m in modules)])
    internal_deps = sorted([imp for imp in all_imports if any(imp == m['filename'][:-3] for m in modules)])
    
    if external_deps:
        print(f"External: {', '.join(external_deps)}")
    if internal_deps:
        print(f"Internal: {', '.join(internal_deps)}")
    
    print(f"\n🎉 Analysis complete!")

if __name__ == "__main__":
    import sys
    src_dir = sys.argv[1] if len(sys.argv) > 1 else "./src"
    analyze_codebase(src_dir)