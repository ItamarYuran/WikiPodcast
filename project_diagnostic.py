#!/usr/bin/env python3
"""
Project Diagnostic Tool
=======================
Comprehensive analysis tool for the Wikipedia Podcast Pipeline project.
Run this from outside your project directory to get a complete health report.

Usage: python project_diagnostic.py [project_path]
"""

import os
import sys
import json
import ast
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import re

class ProjectDiagnostic:
    """Comprehensive project analysis and health check"""
    
    def __init__(self, project_path: str = None):
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.report = {
            'timestamp': datetime.now().isoformat(),
            'project_path': str(self.project_path.absolute()),
            'structure': {},
            'dependencies': {},
            'code_analysis': {},
            'health_score': 0,
            'issues': [],
            'recommendations': []
        }
        
    def run_full_diagnostic(self) -> Dict[str, Any]:
        """Run complete project diagnostic"""
        print("🔍 Starting Project Diagnostic...")
        print("=" * 50)
        
        # Core analyses
        self._analyze_project_structure()
        self._analyze_dependencies()
        self._analyze_code_quality()
        self._analyze_imports_and_dependencies()
        self._analyze_file_sizes_and_complexity()
        self._check_configuration_files()
        self._analyze_git_status()
        self._calculate_health_score()
        
        print("\n📊 Diagnostic Complete!")
        return self.report
    
    def _analyze_project_structure(self):
        """Analyze project directory structure"""
        print("📁 Analyzing project structure...")
        
        structure = {}
        file_count = 0
        total_size = 0
        
        expected_files = [
            'main.py', 'requirements.txt', 'README.md',
            'interactive_menus.py', 'audio_pipeline.py', 
            'content_pipeline.py', 'pipeline.py'
        ]
        
        for root, dirs, files in os.walk(self.project_path):
            rel_root = os.path.relpath(root, self.project_path)
            if rel_root == '.':
                rel_root = 'root'
            
            structure[rel_root] = {
                'directories': dirs.copy(),
                'files': [],
                'file_count': len(files),
                'total_size': 0
            }
            
            for file in files:
                file_path = Path(root) / file
                try:
                    file_size = file_path.stat().st_size
                    file_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    file_info = {
                        'name': file,
                        'size': file_size,
                        'size_human': self._human_readable_size(file_size),
                        'modified': file_modified.isoformat(),
                        'extension': file_path.suffix,
                        'is_python': file.endswith('.py')
                    }
                    
                    # Add Python-specific analysis
                    if file.endswith('.py'):
                        file_info.update(self._analyze_python_file(file_path))
                    
                    structure[rel_root]['files'].append(file_info)
                    structure[rel_root]['total_size'] += file_size
                    total_size += file_size
                    file_count += 1
                    
                except (OSError, PermissionError):
                    self.report['issues'].append(f"Cannot access file: {file_path}")
        
        # Check for expected files
        root_files = [f['name'] for f in structure.get('root', {}).get('files', [])]
        missing_files = [f for f in expected_files if f not in root_files]
        
        self.report['structure'] = {
            'total_files': file_count,
            'total_size': total_size,
            'total_size_human': self._human_readable_size(total_size),
            'directory_tree': structure,
            'expected_files': expected_files,
            'missing_files': missing_files,
            'python_files': sum(1 for root in structure.values() 
                              for f in root['files'] if f['is_python'])
        }
        
        if missing_files:
            self.report['issues'].append(f"Missing expected files: {', '.join(missing_files)}")
    
    def _analyze_python_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a Python file for metadata"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            try:
                tree = ast.parse(content)
                
                # Count elements
                classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
                functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
                
                # Get docstring
                docstring = ast.get_docstring(tree) or ""
                
                return {
                    'lines_of_code': len(content.splitlines()),
                    'classes': len(classes),
                    'functions': len(functions),
                    'imports': len(imports),
                    'has_docstring': bool(docstring),
                    'docstring_length': len(docstring),
                    'class_names': [cls.name for cls in classes],
                    'function_names': [func.name for func in functions[:10]]  # Limit for readability
                }
                
            except SyntaxError as e:
                return {
                    'syntax_error': str(e),
                    'lines_of_code': len(content.splitlines())
                }
                
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_dependencies(self):
        """Analyze project dependencies"""
        print("📦 Analyzing dependencies...")
        
        deps_info = {
            'requirements_file': None,
            'installed_packages': [],
            'import_analysis': {},
            'potential_issues': []
        }
        
        # Check requirements.txt
        req_file = self.project_path / 'requirements.txt'
        if req_file.exists():
            try:
                with open(req_file, 'r') as f:
                    requirements = f.read().strip().split('\n')
                deps_info['requirements_file'] = {
                    'exists': True,
                    'packages': [line.strip() for line in requirements if line.strip() and not line.startswith('#')],
                    'count': len([line for line in requirements if line.strip() and not line.startswith('#')])
                }
            except Exception as e:
                deps_info['requirements_file'] = {'error': str(e)}
        else:
            deps_info['requirements_file'] = {'exists': False}
            self.report['issues'].append("No requirements.txt found")
        
        # Try to get installed packages
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'list', '--format=json'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                deps_info['installed_packages'] = json.loads(result.stdout)
        except Exception as e:
            deps_info['potential_issues'].append(f"Cannot check installed packages: {e}")
        
        self.report['dependencies'] = deps_info
    
    def _analyze_code_quality(self):
        """Analyze code quality metrics"""
        print("🔍 Analyzing code quality...")
        
        quality_metrics = {
            'total_python_files': 0,
            'total_lines': 0,
            'files_with_docstrings': 0,
            'average_file_size': 0,
            'complexity_analysis': {},
            'common_imports': {},
            'potential_issues': []
        }
        
        python_files = []
        all_imports = []
        
        # Collect all Python files
        for root, dirs, files in os.walk(self.project_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    python_files.append(file_path)
        
        quality_metrics['total_python_files'] = len(python_files)
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.splitlines()
                quality_metrics['total_lines'] += len(lines)
                
                # Parse for analysis
                try:
                    tree = ast.parse(content)
                    
                    # Check docstring
                    if ast.get_docstring(tree):
                        quality_metrics['files_with_docstrings'] += 1
                    
                    # Collect imports
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                all_imports.append(alias.name.split('.')[0])
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                all_imports.append(node.module.split('.')[0])
                    
                    # Complexity analysis
                    complexity = self._calculate_complexity(tree)
                    quality_metrics['complexity_analysis'][py_file.name] = complexity
                    
                except SyntaxError:
                    quality_metrics['potential_issues'].append(f"Syntax error in {py_file.name}")
                    
            except Exception as e:
                quality_metrics['potential_issues'].append(f"Cannot analyze {py_file.name}: {e}")
        
        # Calculate averages
        if python_files:
            quality_metrics['average_file_size'] = quality_metrics['total_lines'] / len(python_files)
        
        # Count common imports
        from collections import Counter
        import_counts = Counter(all_imports)
        quality_metrics['common_imports'] = dict(import_counts.most_common(10))
        
        self.report['code_analysis'] = quality_metrics
    
    def _calculate_complexity(self, tree) -> Dict[str, int]:
        """Calculate code complexity metrics"""
        complexity = {
            'functions': 0,
            'classes': 0,
            'if_statements': 0,
            'loops': 0,
            'try_blocks': 0
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity['functions'] += 1
            elif isinstance(node, ast.ClassDef):
                complexity['classes'] += 1
            elif isinstance(node, ast.If):
                complexity['if_statements'] += 1
            elif isinstance(node, (ast.For, ast.While)):
                complexity['loops'] += 1
            elif isinstance(node, ast.Try):
                complexity['try_blocks'] += 1
        
        return complexity
    
    def _analyze_imports_and_dependencies(self):
        """Analyze import patterns and dependencies"""
        print("🔗 Analyzing imports and dependencies...")
        
        import_analysis = {
            'internal_imports': [],
            'external_imports': set(),
            'import_graph': {},
            'circular_imports': [],
            'unused_imports': []
        }
        
        # Map of file -> imports
        file_imports = {}
        
        for root, dirs, files in os.walk(self.project_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    rel_path = file_path.relative_to(self.project_path)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        tree = ast.parse(content)
                        imports = []
                        
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ImportFrom):
                                if node.module and node.module.startswith('.'):
                                    # Relative import - internal
                                    imports.append(f"(relative) {node.module}")
                                    import_analysis['internal_imports'].append({
                                        'from': str(rel_path),
                                        'imports': node.module
                                    })
                                elif node.module:
                                    imports.append(node.module)
                                    import_analysis['external_imports'].add(node.module.split('.')[0])
                            
                            elif isinstance(node, ast.Import):
                                for alias in node.names:
                                    imports.append(alias.name)
                                    import_analysis['external_imports'].add(alias.name.split('.')[0])
                        
                        file_imports[str(rel_path)] = imports
                        
                    except Exception as e:
                        self.report['issues'].append(f"Cannot analyze imports in {file}: {e}")
        
        import_analysis['import_graph'] = file_imports
        import_analysis['external_imports'] = list(import_analysis['external_imports'])
        
        self.report['code_analysis']['import_analysis'] = import_analysis
    
    def _analyze_file_sizes_and_complexity(self):
        """Analyze file sizes and identify complex files"""
        print("📏 Analyzing file complexity...")
        
        complexity_analysis = {
            'large_files': [],
            'complex_files': [],
            'file_metrics': {}
        }
        
        for root, dirs, files in os.walk(self.project_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        lines = len(content.splitlines())
                        size = len(content)
                        
                        metrics = {
                            'lines': lines,
                            'size_bytes': size,
                            'size_human': self._human_readable_size(size)
                        }
                        
                        # Flag large files
                        if lines > 500:
                            complexity_analysis['large_files'].append({
                                'file': file,
                                'lines': lines,
                                'recommendation': 'Consider splitting into smaller modules'
                            })
                        
                        # Try to parse and analyze complexity
                        try:
                            tree = ast.parse(content)
                            complexity = self._calculate_complexity(tree)
                            metrics['complexity'] = complexity
                            
                            # Flag complex files
                            total_complexity = sum(complexity.values())
                            if total_complexity > 50:
                                complexity_analysis['complex_files'].append({
                                    'file': file,
                                    'complexity_score': total_complexity,
                                    'metrics': complexity
                                })
                        
                        except SyntaxError:
                            metrics['syntax_error'] = True
                        
                        complexity_analysis['file_metrics'][file] = metrics
                        
                    except Exception as e:
                        self.report['issues'].append(f"Cannot analyze complexity of {file}: {e}")
        
        self.report['code_analysis']['complexity_analysis'] = complexity_analysis
    
    def _check_configuration_files(self):
        """Check for configuration and setup files"""
        print("⚙️ Checking configuration files...")
        
        config_files = {
            'setup.py': self.project_path / 'setup.py',
            'pyproject.toml': self.project_path / 'pyproject.toml',
            '.gitignore': self.project_path / '.gitignore',
            'README.md': self.project_path / 'README.md',
            'LICENSE': self.project_path / 'LICENSE',
            '.env': self.project_path / '.env',
            'config.py': self.project_path / 'config.py',
            'settings.py': self.project_path / 'settings.py'
        }
        
        config_status = {}
        
        for name, path in config_files.items():
            if path.exists():
                try:
                    stat = path.stat()
                    config_status[name] = {
                        'exists': True,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    }
                    
                    # Read content for specific files
                    if name in ['.gitignore', 'README.md'] and stat.st_size < 10000:
                        with open(path, 'r', encoding='utf-8') as f:
                            config_status[name]['preview'] = f.read()[:500]
                            
                except Exception as e:
                    config_status[name] = {'exists': True, 'error': str(e)}
            else:
                config_status[name] = {'exists': False}
        
        self.report['configuration_files'] = config_status
        
        # Add recommendations
        if not config_status['.gitignore']['exists']:
            self.report['recommendations'].append("Add .gitignore file to exclude cache files and sensitive data")
        
        if not config_status['README.md']['exists']:
            self.report['recommendations'].append("Add README.md with project description and usage instructions")
    
    def _analyze_git_status(self):
        """Analyze git repository status if available"""
        print("📋 Checking git status...")
        
        git_info = {
            'is_git_repo': False,
            'current_branch': None,
            'status': None,
            'recent_commits': [],
            'remote_info': None
        }
        
        try:
            # Check if it's a git repo
            result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                                  cwd=self.project_path, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                git_info['is_git_repo'] = True
                
                # Get current branch
                result = subprocess.run(['git', 'branch', '--show-current'], 
                                      cwd=self.project_path, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    git_info['current_branch'] = result.stdout.strip()
                
                # Get status
                result = subprocess.run(['git', 'status', '--porcelain'], 
                                      cwd=self.project_path, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    status_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
                    git_info['status'] = {
                        'clean': len(status_lines) == 0,
                        'changes': len(status_lines),
                        'files': status_lines[:10]  # Limit output
                    }
                
                # Get recent commits
                result = subprocess.run(['git', 'log', '--oneline', '-5'], 
                                      cwd=self.project_path, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    git_info['recent_commits'] = result.stdout.strip().split('\n')
                
                # Get remote info
                result = subprocess.run(['git', 'remote', '-v'], 
                                      cwd=self.project_path, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    git_info['remote_info'] = result.stdout.strip()
        
        except Exception as e:
            git_info['error'] = str(e)
        
        self.report['git_status'] = git_info
    
    def _calculate_health_score(self):
        """Calculate overall project health score"""
        print("💚 Calculating health score...")
        
        score = 100
        issues = []
        
        # Structure checks (20 points)
        missing_files = len(self.report['structure']['missing_files'])
        if missing_files > 0:
            score -= missing_files * 5
            issues.append(f"Missing {missing_files} expected files")
        
        # Code quality checks (30 points)
        python_files = self.report['structure']['python_files']
        if python_files > 0:
            files_with_docs = self.report['code_analysis']['files_with_docstrings']
            doc_ratio = files_with_docs / python_files
            if doc_ratio < 0.5:
                score -= 15
                issues.append("Low documentation coverage")
        
        # Dependency checks (20 points)
        if not self.report['dependencies']['requirements_file']['exists']:
            score -= 10
            issues.append("No requirements.txt file")
        
        # Configuration checks (15 points)
        config_files = self.report['configuration_files']
        if not config_files['.gitignore']['exists']:
            score -= 5
            issues.append("No .gitignore file")
        if not config_files['README.md']['exists']:
            score -= 5
            issues.append("No README.md file")
        
        # Git checks (15 points)
        if not self.report['git_status']['is_git_repo']:
            score -= 10
            issues.append("Not a git repository")
        elif not self.report['git_status']['status']['clean']:
            score -= 5
            issues.append("Uncommitted changes")
        
        # Ensure score doesn't go below 0
        score = max(0, score)
        
        self.report['health_score'] = score
        self.report['health_issues'] = issues
        
        # Add health-based recommendations
        if score < 70:
            self.report['recommendations'].append("🚨 Project health is below 70% - consider addressing critical issues")
        elif score < 85:
            self.report['recommendations'].append("⚠️ Project health is good but could be improved")
        else:
            self.report['recommendations'].append("✅ Project health is excellent!")
    
    def _human_readable_size(self, size_bytes: int) -> str:
        """Convert bytes to human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def generate_report(self, format_type: str = 'detailed') -> str:
        """Generate formatted diagnostic report"""
        if format_type == 'summary':
            return self._generate_summary_report()
        else:
            return self._generate_detailed_report()
    
    def _generate_summary_report(self) -> str:
        """Generate a concise summary report"""
        report = []
        report.append("🔍 PROJECT DIAGNOSTIC SUMMARY")
        report.append("=" * 50)
        report.append(f"📅 Timestamp: {self.report['timestamp']}")
        report.append(f"📁 Project: {self.report['project_path']}")
        report.append(f"💚 Health Score: {self.report['health_score']}/100")
        report.append("")
        
        # Quick stats
        structure = self.report['structure']
        report.append("📊 QUICK STATS:")
        report.append(f"  • Total files: {structure['total_files']}")
        report.append(f"  • Python files: {structure['python_files']}")
        report.append(f"  • Total size: {structure['total_size_human']}")
        report.append(f"  • Lines of code: {self.report['code_analysis']['total_lines']:,}")
        report.append("")
        
        # Issues
        if self.report['issues']:
            report.append("❌ ISSUES:")
            for issue in self.report['issues'][:5]:
                report.append(f"  • {issue}")
            if len(self.report['issues']) > 5:
                report.append(f"  • ... and {len(self.report['issues']) - 5} more")
            report.append("")
        
        # Recommendations
        if self.report['recommendations']:
            report.append("💡 TOP RECOMMENDATIONS:")
            for rec in self.report['recommendations'][:3]:
                report.append(f"  • {rec}")
            report.append("")
        
        return "\n".join(report)
    
    def _generate_detailed_report(self) -> str:
        """Generate a comprehensive detailed report"""
        report = []
        report.append("🔍 PROJECT DIAGNOSTIC REPORT")
        report.append("=" * 60)
        report.append(f"📅 Generated: {self.report['timestamp']}")
        report.append(f"📁 Project Path: {self.report['project_path']}")
        report.append(f"💚 Overall Health Score: {self.report['health_score']}/100")
        report.append("")
        
        # Project Structure
        report.append("📁 PROJECT STRUCTURE")
        report.append("-" * 30)
        structure = self.report['structure']
        report.append(f"Total Files: {structure['total_files']}")
        report.append(f"Python Files: {structure['python_files']}")
        report.append(f"Total Size: {structure['total_size_human']}")
        report.append("")
        
        # Directory breakdown
        for dir_name, dir_info in structure['directory_tree'].items():
            if dir_info['files']:
                report.append(f"📂 {dir_name}/ ({dir_info['file_count']} files)")
                for file_info in dir_info['files'][:5]:  # Limit files shown
                    report.append(f"  📄 {file_info['name']} ({file_info['size_human']})")
                if len(dir_info['files']) > 5:
                    report.append(f"  ... and {len(dir_info['files']) - 5} more files")
                report.append("")
        
        # Missing files
        if structure['missing_files']:
            report.append("❌ Missing Expected Files:")
            for file in structure['missing_files']:
                report.append(f"  • {file}")
            report.append("")
        
        # Code Analysis
        report.append("🔍 CODE ANALYSIS")
        report.append("-" * 25)
        code_analysis = self.report['code_analysis']
        report.append(f"Total Lines of Code: {code_analysis['total_lines']:,}")
        report.append(f"Average File Size: {code_analysis['average_file_size']:.1f} lines")
        report.append(f"Files with Docstrings: {code_analysis['files_with_docstrings']}/{code_analysis['total_python_files']}")
        report.append("")
        
        # Common imports
        if code_analysis['common_imports']:
            report.append("📦 Most Common Imports:")
            for imp, count in list(code_analysis['common_imports'].items())[:5]:
                report.append(f"  • {imp}: {count} times")
            report.append("")
        
        # Dependencies
        report.append("📦 DEPENDENCIES")
        report.append("-" * 20)
        deps = self.report['dependencies']
        if deps['requirements_file']['exists']:
            req_count = deps['requirements_file']['count']
            report.append(f"Requirements.txt: ✅ ({req_count} packages)")
            if deps['requirements_file']['packages']:
                report.append("Required packages:")
                for pkg in deps['requirements_file']['packages'][:10]:
                    report.append(f"  • {pkg}")
        else:
            report.append("Requirements.txt: ❌ Missing")
        report.append("")
        
        # Configuration Files
        report.append("⚙️ CONFIGURATION FILES")
        report.append("-" * 30)
        config = self.report['configuration_files']
        for name, info in config.items():
            status = "✅" if info['exists'] else "❌"
            report.append(f"{name}: {status}")
        report.append("")
        
        # Git Status
        report.append("📋 GIT STATUS")
        report.append("-" * 20)
        git = self.report['git_status']
        if git['is_git_repo']:
            report.append(f"Git Repository: ✅")
            report.append(f"Current Branch: {git['current_branch']}")
            if git['status']:
                status_emoji = "✅" if git['status']['clean'] else "⚠️"
                status_text = "Clean" if git['status']['clean'] else f"{git['status']['changes']} changes"
                report.append(f"Working Directory: {status_emoji} {status_text}")
        else:
            report.append("Git Repository: ❌ Not initialized")
        report.append("")
        
        # Issues
        if self.report['issues']:
            report.append("❌ ISSUES FOUND")
            report.append("-" * 20)
            for i, issue in enumerate(self.report['issues'], 1):
                report.append(f"{i:2d}. {issue}")
            report.append("")
        
        # Recommendations
        if self.report['recommendations']:
            report.append("💡 RECOMMENDATIONS")
            report.append("-" * 25)
            for i, rec in enumerate(self.report['recommendations'], 1):
                report.append(f"{i:2d}. {rec}")
            report.append("")
        
        # Health breakdown
        report.append("💚 HEALTH SCORE BREAKDOWN")
        report.append("-" * 35)
        if hasattr(self.report, 'health_issues') and self.report['health_issues']:
            for issue in self.report['health_issues']:
                report.append(f"  • {issue}")
        else:
            report.append("  ✅ No major health issues detected")
        
        return "\n".join(report)
    
    def save_report(self, filename: str = None, format_type: str = 'detailed'):
        """Save diagnostic report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"project_diagnostic_{timestamp}.txt"
        
        report_content = self.generate_report(format_type)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📄 Report saved to: {filename}")
        return filename
    
    def save_json_report(self, filename: str = None):
        """Save full diagnostic data as JSON"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"project_diagnostic_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, default=str)
        
        print(f"📊 JSON data saved to: {filename}")
        return filename

def main():
    """Main diagnostic runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive project diagnostic tool")
    parser.add_argument("project_path", nargs="?", default=".", 
                       help="Path to project directory (default: current directory)")
    parser.add_argument("--format", choices=["summary", "detailed"], default="detailed",
                       help="Report format (default: detailed)")
    parser.add_argument("--save", action="store_true", 
                       help="Save report to file")
    parser.add_argument("--json", action="store_true",
                       help="Also save JSON data")
    parser.add_argument("--output", help="Output filename")
    
    args = parser.parse_args()
    
    # Run diagnostic
    diagnostic = ProjectDiagnostic(args.project_path)
    diagnostic.run_full_diagnostic()
    
    # Generate and display report
    report = diagnostic.generate_report(args.format)
    print(report)
    
    # Save if requested
    if args.save:
        diagnostic.save_report(args.output, args.format)
    
    if args.json:
        json_filename = args.output.replace('.txt', '.json') if args.output else None
        diagnostic.save_json_report(json_filename)
    
    # Print final summary
    score = diagnostic.report['health_score']
    if score >= 85:
        print("\n🎉 Excellent project health!")
    elif score >= 70:
        print("\n👍 Good project health with room for improvement")
    else:
        print("\n⚠️  Project needs attention - consider addressing the issues above")

if __name__ == "__main__":
    main()