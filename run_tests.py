#!/usr/bin/env python3
"""
Project Code Analyzer
Analyzes a project directory and extracts all functions, classes, and code elements
"""

import os
import ast
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse

class CodeAnalyzer:
    def __init__(self, project_path: str, output_file: str = "project_analysis.txt"):
        self.project_path = Path(project_path)
        self.output_file = output_file
        self.supported_extensions = {
            '.py': self.analyze_python,
            '.js': self.analyze_javascript,
            '.ts': self.analyze_typescript,
            '.jsx': self.analyze_jsx,
            '.tsx': self.analyze_tsx,
            '.java': self.analyze_java,
            '.cpp': self.analyze_cpp,
            '.c': self.analyze_c,
            '.cs': self.analyze_csharp,
            '.php': self.analyze_php,
            '.rb': self.analyze_ruby,
            '.go': self.analyze_go,
            '.rs': self.analyze_rust,
        }
        
        # Common directories to ignore
        self.ignore_dirs = {
            '__pycache__', '.git', '.svn', '.hg', 'node_modules', 
            '.venv', 'venv', 'env', '.env', 'build', 'dist', 
            '.idea', '.vscode', 'target', 'bin', 'obj', '.next',
            'coverage', '.coverage', '.pytest_cache', '.mypy_cache'
        }
        
        # Common files to ignore
        self.ignore_files = {
            '.gitignore', '.dockerignore', '.env', '.env.local',
            'package-lock.json', 'yarn.lock', 'Pipfile.lock',
            '.DS_Store', 'Thumbs.db'
        }

    def should_ignore_path(self, path: Path) -> bool:
        """Check if a path should be ignored"""
        # Check if any part of the path is in ignore_dirs
        for part in path.parts:
            if part in self.ignore_dirs:
                return True
        
        # Check if filename is in ignore_files
        if path.name in self.ignore_files:
            return True
            
        # Ignore hidden files (starting with .)
        if path.name.startswith('.') and path.name not in ['.gitignore', '.env']:
            return True
            
        return False

    def get_all_files(self) -> List[Path]:
        """Get all relevant files in the project"""
        files = []
        
        for file_path in self.project_path.rglob('*'):
            if file_path.is_file() and not self.should_ignore_path(file_path):
                files.append(file_path)
        
        return sorted(files)

    def analyze_python(self, file_path: Path) -> Dict[str, Any]:
        """Analyze Python files using AST"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            analysis = {
                'imports': [],
                'classes': [],
                'functions': [],
                'constants': [],
                'docstring': ast.get_docstring(tree)
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis['imports'].append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        analysis['imports'].append(f"{module}.{alias.name}")
                
                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        'name': node.name,
                        'bases': [ast.unparse(base) for base in node.bases],
                        'methods': [],
                        'docstring': ast.get_docstring(node),
                        'line': node.lineno
                    }
                    
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            class_info['methods'].append({
                                'name': item.name,
                                'args': [arg.arg for arg in item.args.args],
                                'docstring': ast.get_docstring(item),
                                'line': item.lineno,
                                'is_property': any(isinstance(d, ast.Name) and d.id == 'property' for d in item.decorator_list)
                            })
                    
                    analysis['classes'].append(class_info)
                
                elif isinstance(node, ast.FunctionDef):
                    # Only top-level functions (not methods)
                    if not any(isinstance(parent, ast.ClassDef) for parent in ast.walk(tree) if hasattr(parent, 'body') and node in getattr(parent, 'body', [])):
                        analysis['functions'].append({
                            'name': node.name,
                            'args': [arg.arg for arg in node.args.args],
                            'docstring': ast.get_docstring(node),
                            'line': node.lineno,
                            'is_async': isinstance(node, ast.AsyncFunctionDef)
                        })
                
                elif isinstance(node, ast.Assign):
                    # Look for constants (uppercase variables)
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.isupper():
                            analysis['constants'].append({
                                'name': target.id,
                                'line': node.lineno
                            })
            
            return analysis
            
        except Exception as e:
            return {'error': str(e)}

    def analyze_javascript(self, file_path: Path) -> Dict[str, Any]:
        """Analyze JavaScript files using regex patterns"""
        return self._analyze_js_like_file(file_path)

    def analyze_typescript(self, file_path: Path) -> Dict[str, Any]:
        """Analyze TypeScript files using regex patterns"""
        return self._analyze_js_like_file(file_path)

    def analyze_jsx(self, file_path: Path) -> Dict[str, Any]:
        """Analyze JSX files using regex patterns"""
        return self._analyze_js_like_file(file_path)

    def analyze_tsx(self, file_path: Path) -> Dict[str, Any]:
        """Analyze TSX files using regex patterns"""
        return self._analyze_js_like_file(file_path)

    def _analyze_js_like_file(self, file_path: Path) -> Dict[str, Any]:
        """Generic analyzer for JavaScript-like files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                'imports': [],
                'exports': [],
                'functions': [],
                'classes': [],
                'constants': [],
                'components': []  # For React components
            }
            
            # Find imports
            import_patterns = [
                r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]',
                r'import\s+[\'"]([^\'"]+)[\'"]',
                r'const\s+.*?=\s+require\([\'"]([^\'"]+)[\'"]\)'
            ]
            
            for pattern in import_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                analysis['imports'].extend(matches)
            
            # Find exports
            export_patterns = [
                r'export\s+(?:default\s+)?(?:function|class|const|let|var)\s+(\w+)',
                r'export\s+\{\s*([^}]+)\s*\}',
                r'module\.exports\s*=\s*(\w+)'
            ]
            
            for pattern in export_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                analysis['exports'].extend(matches)
            
            # Find functions
            function_patterns = [
                r'function\s+(\w+)\s*\([^)]*\)',
                r'const\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>',
                r'(\w+)\s*:\s*(?:async\s+)?function\s*\([^)]*\)',
                r'(\w+)\s*:\s*(?:async\s+)?\([^)]*\)\s*=>'
            ]
            
            for pattern in function_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                analysis['functions'].extend(matches)
            
            # Find classes
            class_matches = re.findall(r'class\s+(\w+)(?:\s+extends\s+(\w+))?', content, re.MULTILINE)
            for match in class_matches:
                analysis['classes'].append({
                    'name': match[0],
                    'extends': match[1] if match[1] else None
                })
            
            # Find React components (functions that return JSX)
            component_pattern = r'(?:const|function)\s+([A-Z]\w+).*?return\s*\('
            component_matches = re.findall(component_pattern, content, re.MULTILINE | re.DOTALL)
            analysis['components'] = component_matches
            
            # Find constants
            const_pattern = r'const\s+([A-Z_][A-Z0-9_]*)\s*='
            const_matches = re.findall(const_pattern, content, re.MULTILINE)
            analysis['constants'] = const_matches
            
            return analysis
            
        except Exception as e:
            return {'error': str(e)}

    def analyze_java(self, file_path: Path) -> Dict[str, Any]:
        """Analyze Java files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                'package': '',
                'imports': [],
                'classes': [],
                'interfaces': [],
                'enums': []
            }
            
            # Package declaration
            package_match = re.search(r'package\s+([^;]+);', content)
            if package_match:
                analysis['package'] = package_match.group(1)
            
            # Imports
            import_matches = re.findall(r'import\s+(?:static\s+)?([^;]+);', content)
            analysis['imports'] = import_matches
            
            # Classes
            class_matches = re.findall(r'(?:public\s+|private\s+|protected\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?', content)
            for match in class_matches:
                analysis['classes'].append({
                    'name': match[0],
                    'extends': match[1] if match[1] else None
                })
            
            # Interfaces
            interface_matches = re.findall(r'(?:public\s+|private\s+|protected\s+)?interface\s+(\w+)', content)
            analysis['interfaces'] = interface_matches
            
            # Enums
            enum_matches = re.findall(r'(?:public\s+|private\s+|protected\s+)?enum\s+(\w+)', content)
            analysis['enums'] = enum_matches
            
            return analysis
            
        except Exception as e:
            return {'error': str(e)}

    def analyze_cpp(self, file_path: Path) -> Dict[str, Any]:
        """Analyze C++ files"""
        return self._analyze_c_like_file(file_path)

    def analyze_c(self, file_path: Path) -> Dict[str, Any]:
        """Analyze C files"""
        return self._analyze_c_like_file(file_path)

    def _analyze_c_like_file(self, file_path: Path) -> Dict[str, Any]:
        """Generic analyzer for C-like files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                'includes': [],
                'functions': [],
                'classes': [],  # For C++
                'structs': [],
                'typedefs': [],
                'defines': []
            }
            
            # Includes
            include_matches = re.findall(r'#include\s+[<"]([^>"]+)[>"]', content)
            analysis['includes'] = include_matches
            
            # Functions
            function_matches = re.findall(r'^\s*(?:\w+\s+)*(\w+)\s*\([^)]*\)\s*\{', content, re.MULTILINE)
            analysis['functions'] = function_matches
            
            # Classes (C++)
            class_matches = re.findall(r'class\s+(\w+)(?:\s*:\s*[^{]+)?', content)
            analysis['classes'] = class_matches
            
            # Structs
            struct_matches = re.findall(r'struct\s+(\w+)', content)
            analysis['structs'] = struct_matches
            
            # Typedefs
            typedef_matches = re.findall(r'typedef\s+[^;]+\s+(\w+);', content)
            analysis['typedefs'] = typedef_matches
            
            # Defines
            define_matches = re.findall(r'#define\s+(\w+)', content)
            analysis['defines'] = define_matches
            
            return analysis
            
        except Exception as e:
            return {'error': str(e)}

    def analyze_csharp(self, file_path: Path) -> Dict[str, Any]:
        """Analyze C# files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                'namespaces': [],
                'usings': [],
                'classes': [],
                'interfaces': [],
                'enums': [],
                'structs': []
            }
            
            # Using statements
            using_matches = re.findall(r'using\s+([^;]+);', content)
            analysis['usings'] = using_matches
            
            # Namespaces
            namespace_matches = re.findall(r'namespace\s+([^{]+)', content)
            analysis['namespaces'] = namespace_matches
            
            # Classes
            class_matches = re.findall(r'(?:public\s+|private\s+|protected\s+|internal\s+)?class\s+(\w+)', content)
            analysis['classes'] = class_matches
            
            # Interfaces
            interface_matches = re.findall(r'(?:public\s+|private\s+|protected\s+|internal\s+)?interface\s+(\w+)', content)
            analysis['interfaces'] = interface_matches
            
            # Enums
            enum_matches = re.findall(r'(?:public\s+|private\s+|protected\s+|internal\s+)?enum\s+(\w+)', content)
            analysis['enums'] = enum_matches
            
            # Structs
            struct_matches = re.findall(r'(?:public\s+|private\s+|protected\s+|internal\s+)?struct\s+(\w+)', content)
            analysis['structs'] = struct_matches
            
            return analysis
            
        except Exception as e:
            return {'error': str(e)}

    def analyze_php(self, file_path: Path) -> Dict[str, Any]:
        """Analyze PHP files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                'classes': [],
                'functions': [],
                'includes': [],
                'constants': [],
                'variables': []
            }
            
            # Classes
            class_matches = re.findall(r'class\s+(\w+)(?:\s+extends\s+(\w+))?', content)
            for match in class_matches:
                analysis['classes'].append({
                    'name': match[0],
                    'extends': match[1] if match[1] else None
                })
            
            # Functions
            function_matches = re.findall(r'function\s+(\w+)\s*\(', content)
            analysis['functions'] = function_matches
            
            # Includes
            include_matches = re.findall(r'(?:include|require)(?:_once)?\s*\(?[\'"]([^\'"]+)[\'"]', content)
            analysis['includes'] = include_matches
            
            return analysis
            
        except Exception as e:
            return {'error': str(e)}

    def analyze_ruby(self, file_path: Path) -> Dict[str, Any]:
        """Analyze Ruby files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                'classes': [],
                'modules': [],
                'methods': [],
                'requires': [],
                'constants': []
            }
            
            # Classes
            class_matches = re.findall(r'class\s+(\w+)(?:\s*<\s*(\w+))?', content)
            for match in class_matches:
                analysis['classes'].append({
                    'name': match[0],
                    'inherits': match[1] if match[1] else None
                })
            
            # Modules
            module_matches = re.findall(r'module\s+(\w+)', content)
            analysis['modules'] = module_matches
            
            # Methods
            method_matches = re.findall(r'def\s+(\w+)', content)
            analysis['methods'] = method_matches
            
            # Requires
            require_matches = re.findall(r'require\s+[\'"]([^\'"]+)[\'"]', content)
            analysis['requires'] = require_matches
            
            return analysis
            
        except Exception as e:
            return {'error': str(e)}

    def analyze_go(self, file_path: Path) -> Dict[str, Any]:
        """Analyze Go files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                'package': '',
                'imports': [],
                'functions': [],
                'types': [],
                'constants': [],
                'variables': []
            }
            
            # Package
            package_match = re.search(r'package\s+(\w+)', content)
            if package_match:
                analysis['package'] = package_match.group(1)
            
            # Imports
            import_matches = re.findall(r'import\s+(?:\(\s*([^)]+)\s*\)|"([^"]+)")', content, re.MULTILINE | re.DOTALL)
            for match in import_matches:
                if match[0]:  # Multi-line import
                    imports = re.findall(r'"([^"]+)"', match[0])
                    analysis['imports'].extend(imports)
                else:  # Single import
                    analysis['imports'].append(match[1])
            
            # Functions
            function_matches = re.findall(r'func\s+(?:\(\s*\w+\s+\*?\w+\s*\))?\s*(\w+)\s*\(', content)
            analysis['functions'] = function_matches
            
            # Types
            type_matches = re.findall(r'type\s+(\w+)\s+(?:struct|interface)', content)
            analysis['types'] = type_matches
            
            return analysis
            
        except Exception as e:
            return {'error': str(e)}

    def analyze_rust(self, file_path: Path) -> Dict[str, Any]:
        """Analyze Rust files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                'uses': [],
                'functions': [],
                'structs': [],
                'enums': [],
                'traits': [],
                'impls': [],
                'modules': []
            }
            
            # Use statements
            use_matches = re.findall(r'use\s+([^;]+);', content)
            analysis['uses'] = use_matches
            
            # Functions
            function_matches = re.findall(r'fn\s+(\w+)\s*\(', content)
            analysis['functions'] = function_matches
            
            # Structs
            struct_matches = re.findall(r'struct\s+(\w+)', content)
            analysis['structs'] = struct_matches
            
            # Enums
            enum_matches = re.findall(r'enum\s+(\w+)', content)
            analysis['enums'] = enum_matches
            
            # Traits
            trait_matches = re.findall(r'trait\s+(\w+)', content)
            analysis['traits'] = trait_matches
            
            # Implementations
            impl_matches = re.findall(r'impl\s+(?:.*?\s+for\s+)?(\w+)', content)
            analysis['impls'] = impl_matches
            
            # Modules
            mod_matches = re.findall(r'mod\s+(\w+)', content)
            analysis['modules'] = mod_matches
            
            return analysis
            
        except Exception as e:
            return {'error': str(e)}

    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single file based on its extension"""
        extension = file_path.suffix.lower()
        
        if extension in self.supported_extensions:
            return self.supported_extensions[extension](file_path)
        else:
            # For unsupported files, just return basic info
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    return {
                        'lines': len(content.splitlines()),
                        'size': len(content),
                        'type': 'text'
                    }
            except:
                return {
                    'type': 'binary',
                    'size': file_path.stat().st_size
                }

    def generate_report(self):
        """Generate the complete project analysis report"""
        print("🔍 Analyzing project structure...")
        
        files = self.get_all_files()
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("PROJECT CODE ANALYSIS REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Project Path: {self.project_path.absolute()}\n")
            f.write(f"Total Files: {len(files)}\n")
            f.write(f"Generated: {os.getcwd()}\n\n")
            
            # Group files by extension
            files_by_ext = {}
            for file_path in files:
                ext = file_path.suffix.lower() or 'no_extension'
                if ext not in files_by_ext:
                    files_by_ext[ext] = []
                files_by_ext[ext].append(file_path)
            
            f.write("FILE TYPES SUMMARY:\n")
            f.write("-" * 40 + "\n")
            for ext, file_list in sorted(files_by_ext.items()):
                f.write(f"{ext:15} : {len(file_list):4} files\n")
            f.write("\n")
            
            # Analyze each file
            for i, file_path in enumerate(files, 1):
                relative_path = file_path.relative_to(self.project_path)
                print(f"Analyzing ({i}/{len(files)}): {relative_path}")
                
                f.write("=" * 80 + "\n")
                f.write(f"FILE: {relative_path}\n")
                f.write("=" * 80 + "\n")
                f.write(f"Path: {file_path.absolute()}\n")
                f.write(f"Size: {file_path.stat().st_size:,} bytes\n")
                f.write(f"Extension: {file_path.suffix}\n\n")
                
                analysis = self.analyze_file(file_path)
                
                if 'error' in analysis:
                    f.write(f"❌ Analysis Error: {analysis['error']}\n\n")
                    continue
                
                # Write analysis results
                self._write_analysis_results(f, analysis, file_path.suffix)
                
                f.write("\n")
        
        print(f"✅ Analysis complete! Report saved to: {self.output_file}")

    def _write_analysis_results(self, f, analysis: Dict[str, Any], extension: str):
        """Write analysis results to file"""
        
        if extension == '.py':
            if analysis.get('docstring'):
                f.write(f"📝 File Docstring:\n{analysis['docstring']}\n\n")
            
            if analysis.get('imports'):
                f.write("📦 Imports:\n")
                for imp in analysis['imports']:
                    f.write(f"  - {imp}\n")
                f.write("\n")
            
            if analysis.get('constants'):
                f.write("🔢 Constants:\n")
                for const in analysis['constants']:
                    f.write(f"  - {const['name']} (line {const['line']})\n")
                f.write("\n")
            
            if analysis.get('classes'):
                f.write("🏗️  Classes:\n")
                for cls in analysis['classes']:
                    f.write(f"  📋 {cls['name']} (line {cls['line']})\n")
                    if cls['bases']:
                        f.write(f"     Inherits from: {', '.join(cls['bases'])}\n")
                    if cls['docstring']:
                        f.write(f"     📝 {cls['docstring']}\n")
                    
                    if cls['methods']:
                        f.write("     Methods:\n")
                        for method in cls['methods']:
                            f.write(f"       - {method['name']}({', '.join(method['args'])}) (line {method['line']})\n")
                            if method['docstring']:
                                f.write(f"         📝 {method['docstring']}\n")
                    f.write("\n")
            
            if analysis.get('functions'):
                f.write("⚙️  Functions:\n")
                for func in analysis['functions']:
                    async_marker = "async " if func.get('is_async') else ""
                    f.write(f"  - {async_marker}{func['name']}({', '.join(func['args'])}) (line {func['line']})\n")
                    if func['docstring']:
                        f.write(f"    📝 {func['docstring']}\n")
                f.write("\n")
        
        elif extension in ['.js', '.ts', '.jsx', '.tsx']:
            if analysis.get('imports'):
                f.write("📦 Imports:\n")
                for imp in analysis['imports']:
                    f.write(f"  - {imp}\n")
                f.write("\n")
            
            if analysis.get('exports'):
                f.write("📤 Exports:\n")
                for exp in analysis['exports']:
                    f.write(f"  - {exp}\n")
                f.write("\n")
            
            if analysis.get('components'):
                f.write("⚛️  React Components:\n")
                for comp in analysis['components']:
                    f.write(f"  - {comp}\n")
                f.write("\n")
            
            if analysis.get('classes'):
                f.write("🏗️  Classes:\n")
                for cls in analysis['classes']:
                    extends_info = f" extends {cls['extends']}" if cls['extends'] else ""
                    f.write(f"  - {cls['name']}{extends_info}\n")
                f.write("\n")
            
            if analysis.get('functions'):
                f.write("⚙️  Functions:\n")
                for func in analysis['functions']:
                    f.write(f"  - {func}\n")
                f.write("\n")
            
            if analysis.get('constants'):
                f.write("🔢 Constants:\n")
                for const in analysis['constants']:
                    f.write(f"  - {const}\n")
                f.write("\n")
        
        elif extension == '.java':
            if analysis.get('package'):
                f.write(f"📦 Package: {analysis['package']}\n\n")
            
            if analysis.get('imports'):
                f.write("📥 Imports:\n")
                for imp in analysis['imports']:
                    f.write(f"  - {imp}\n")
                f.write("\n")
            
            if analysis.get('classes'):
                f.write("🏗️  Classes:\n")
                for cls in analysis['classes']:
                    extends_info = f" extends {cls['extends']}" if cls['extends'] else ""
                    f.write(f"  - {cls['name']}{extends_info}\n")
                f.write("\n")
            
            if analysis.get('interfaces'):
                f.write("🔌 Interfaces:\n")
                for interface in analysis['interfaces']:
                    f.write(f"  - {interface}\n")
                f.write("\n")
            
            if analysis.get('enums'):
                f.write("🔢 Enums:\n")
                for enum in analysis['enums']:
                    f.write(f"  - {enum}\n")
                f.write("\n")
        
        else:
            # Generic output for other file types
            for key, value in analysis.items():
                if value:  # Only show non-empty values
                    f.write(f"{key.title()}:\n")
                    if isinstance(value, list):
                        for item in value:
                            f.write(f"  - {item}\n")
                    else:
                        f.write(f"  {value}\n")
                    f.write("\n")

def main():
    parser = argparse.ArgumentParser(description='Analyze project code structure')
    parser.add_argument('project_path', help='Path to the project directory')
    parser.add_argument('-o', '--output', default='project_analysis.txt', 
                       help='Output file name (default: project_analysis.txt)')
    parser.add_argument('--include-hidden', action='store_true',
                       help='Include hidden files and directories')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.project_path):
        print(f"❌ Error: Path '{args.project_path}' does not exist")
        return
    
    analyzer = CodeAnalyzer(args.project_path, args.output)
    
    if args.include_hidden:
        analyzer.ignore_dirs.clear()
        analyzer.ignore_files.clear()
    
    try:
        analyzer.generate_report()
    except KeyboardInterrupt:
        print("\n⏹️  Analysis interrupted by user")
    except Exception as e:
        print(f"❌ Error during analysis: {e}")

if __name__ == "__main__":
    main()