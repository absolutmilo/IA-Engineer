"""
Dependency Analyzer - Advanced dependency analysis for MCP compliance
"""

import ast
import json
import os
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict, Counter
import re

from .findings_tracker import FindingsTracker, Severity, Category, FindingLocation
from utils.logger import get_logger

class DependencyAnalyzer:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.tracker = FindingsTracker()
        self.python_files = self._get_python_files()
        self.logger = get_logger(__name__)
        
        # Analysis results
        self.imports_by_file: Dict[str, Set[str]] = {}
        self.defined_functions: Dict[str, Set[str]] = {}
        self.defined_classes: Dict[str, Set[str]] = {}
        self.used_functions: Dict[str, Set[str]] = {}
        self.used_classes: Dict[str, Set[str]] = {}
        self.external_imports: Set[str] = set()
        self.internal_imports: Set[str] = set()
        
    def _get_python_files(self) -> List[Path]:
        """Get all Python files excluding common directories"""
        exclude_dirs = {'.venv', '__pycache__', '.git', 'node_modules', '.pytest_cache', '.tox'}
        files = []
        
        for file_path in self.project_path.rglob("*.py"):
            if any(exclude_dir in file_path.parts for exclude_dir in exclude_dirs):
                continue
            files.append(file_path)
        
        return files
    
    def analyze_imports_and_usage(self) -> Dict[str, List[str]]:
        """Analyze imports and their usage across the project"""
        finding_ids = []
        
        print(f"🔍 Analyzing {len(self.python_files)} Python files for dependencies...")
        
        # First pass: collect all imports and definitions
        for file_path in self.python_files:
            try:
                self._analyze_file_imports_and_definitions(file_path)
            except Exception as e:
                self.logger.error(f"Error analyzing {file_path}: {e}")
        
        # Second pass: analyze usage
        for file_path in self.python_files:
            try:
                self._analyze_file_usage(file_path)
            except Exception as e:
                self.logger.error(f"Error analyzing usage in {file_path}: {e}")
        
        # Find unused imports
        unused_imports = self._find_unused_imports()
        for file_path, imports in unused_imports.items():
            for import_name in imports:
                finding_id = self.tracker.add_finding(
                    title="Unused Import",
                    description=f"Import '{import_name}' is never used in this file",
                    severity=Severity.MEDIUM,
                    category=Category.MAINTAINABILITY,
                    recommendation="Remove unused import to reduce clutter",
                    effort_estimate="2 minutes",
                    tags=["cleanup", "imports", "unused"]
                )
                
                self.tracker.findings[finding_id].add_location(
                    file_path=str(file_path),
                    line=None,  # Would need more detailed AST tracking for line numbers
                    function=None,
                    snippet=f"import {import_name}"
                )
                finding_ids.append(finding_id)
        
        # Find potentially decomposable libraries
        decomposable = self._find_decomposable_libraries()
        for lib_info in decomposable:
            finding_id = self.tracker.add_finding(
                title="Potentially Decomposable Library",
                description=f"Library '{lib_info['name']}' imports {lib_info['total_imports']} items but only uses {lib_info['used_imports']} ({lib_info['usage_pct']}% usage)",
                severity=Severity.LOW,
                category=Category.MAINTAINABILITY,
                recommendation=f"Consider replacing with targeted imports or lighter alternative",
                effort_estimate="30 minutes",
                tags=["optimization", "dependencies", "bloat"]
            )
            
            finding_ids.append(finding_id)
        
        # Find unused external dependencies
        unused_deps = self._find_unused_dependencies()
        for dep in unused_deps:
            finding_id = self.tracker.add_finding(
                title="Unused External Dependency",
                description=f"Dependency '{dep}' is installed but never imported in the codebase",
                severity=Severity.HIGH,
                category=Category.MAINTAINABILITY,
                recommendation="Remove from requirements.txt to reduce bloat",
                effort_estimate="5 minutes",
                tags=["dependencies", "unused", "cleanup"]
            )
            
            finding_ids.append(finding_id)
        
        return {
            "unused_imports": finding_ids,
            "decomposable_libraries": finding_ids,
            "unused_dependencies": finding_ids
        }
    
    def _analyze_file_imports_and_definitions(self, file_path: Path):
        """Analyze a single file for imports and definitions"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            file_key = str(file_path.relative_to(self.project_path))
            
            # Track imports
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                        if '.' not in alias.name:  # External import
                            self.external_imports.add(alias.name.split('.')[0])
                        else:  # Internal import
                            self.internal_imports.add(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
                        if '.' not in node.module:  # External import
                            self.external_imports.add(node.module.split('.')[0])
                        else:  # Internal import
                            self.internal_imports.add(node.module)
            
            self.imports_by_file[file_key] = imports
            
            # Track function and class definitions
            functions = set()
            classes = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.add(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.add(node.name)
            
            self.defined_functions[file_key] = functions
            self.defined_classes[file_key] = classes
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    
    def _analyze_file_usage(self, file_path: Path):
        """Analyze a single file for usage of functions and classes"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            file_key = str(file_path.relative_to(self.project_path))
            
            # Track usage
            used_functions = set()
            used_classes = set()
            
            for node in ast.walk(tree):
                # Function calls
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        used_functions.add(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        # Handle method calls and attribute access
                        if isinstance(node.func.value, ast.Name):
                            used_functions.add(node.func.attr)
                
                # Class instantiation and type annotation
                elif isinstance(node, ast.Name):
                    # This is a simplified check - could be improved
                    if node.id in self.defined_classes.get(file_key, set()):
                        used_classes.add(node.id)
            
            self.used_functions[file_key] = used_functions
            self.used_classes[file_key] = used_classes
            
        except Exception as e:
            print(f"Error analyzing usage in {file_path}: {e}")
    
    def _find_unused_imports(self) -> Dict[str, Set[str]]:
        """Find imports that are never used"""
        unused = defaultdict(set)
        
        for file_path, imports in self.imports_by_file.items():
            # Get all used names in this file
            used_names = set()
            used_names.update(self.used_functions.get(file_path, set()))
            used_names.update(self.used_classes.get(file_path, set()))
            
            # Check each import
            for import_name in imports:
                # Simple check - could be improved for more complex cases
                import_base = import_name.split('.')[0]
                if import_base not in used_names and import_name not in used_names:
                    unused[file_path].add(import_name)
        
        return unused
    
    def _find_decomposable_libraries(self) -> List[Dict]:
        """Find libraries that import many things but use few"""
        # Group imports by library
        library_stats = defaultdict(lambda: {'total_imports': set(), 'used_imports': set()})
        
        for file_path, imports in self.imports_by_file.items():
            used_names = set()
            used_names.update(self.used_functions.get(file_path, set()))
            used_names.update(self.used_classes.get(file_path, set()))
            
            for import_name in imports:
                lib_base = import_name.split('.')[0]
                library_stats[lib_base]['total_imports'].add(import_name)
                
                # Check if this import is actually used
                if import_name in used_names or any(name.startswith(import_name) for name in used_names):
                    library_stats[lib_base]['used_imports'].add(import_name)
        
        # Find libraries with low usage
        decomposable = []
        for lib_name, stats in library_stats.items():
            total = len(stats['total_imports'])
            used = len(stats['used_imports'])
            
            if total > 3 and used / total < 0.5:  # Less than 50% usage
                decomposable.append({
                    'name': lib_name,
                    'total_imports': total,
                    'used_imports': used,
                    'usage_pct': round(used / total * 100, 1)
                })
        
        return sorted(decomposable, key=lambda x: x['usage_pct'])
    
    def _find_unused_dependencies(self) -> Set[str]:
        """Find dependencies that are installed but never used"""
        # Try to read requirements.txt
        requirements_file = self.project_path / "requirements.txt"
        installed_deps = set()
        
        if requirements_file.exists():
            try:
                with open(requirements_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Extract package name (before any version specifiers)
                            dep_name = re.split(r'[<>=!]', line)[0].strip()
                            installed_deps.add(dep_name.lower())
            except Exception as e:
                print(f"Error reading requirements.txt: {e}")
        
        # Find which installed deps are actually used
        used_deps = set()
        for import_name in self.external_imports:
            # Map common import names to package names
            pkg_mapping = {
                'yaml': 'pyyaml',
                'PIL': 'pillow',
                'cv2': 'opencv-python',
                'sklearn': 'scikit-learn',
                'tf': 'tensorflow',
                'torch': 'pytorch',
                'pd': 'pandas',
                'np': 'numpy',
                'plt': 'matplotlib',
            }
            
            # Check direct mapping
            mapped_name = pkg_mapping.get(import_name, import_name)
            used_deps.add(mapped_name.lower())
            
            # Also check the base name
            base_name = import_name.split('.')[0].lower()
            used_deps.add(base_name)
        
        # Find unused dependencies
        unused = installed_deps - used_deps
        
        # Remove common development dependencies that might not be imported
        dev_deps = {'pytest', 'black', 'flake8', 'mypy', 'coverage', 'setuptools', 'wheel'}
        unused -= dev_deps
        
        return unused
    
    def generate_dependency_report(self) -> Dict:
        """Generate comprehensive dependency analysis report"""
        return {
            'summary': {
                'total_files_analyzed': len(self.python_files),
                'total_imports': sum(len(imports) for imports in self.imports_by_file.values()),
                'external_libraries': len(self.external_imports),
                'internal_modules': len(self.internal_imports),
                'defined_functions': sum(len(funcs) for funcs in self.defined_functions.values()),
                'defined_classes': sum(len(classes) for classes in self.defined_classes.values())
            },
            'library_usage': self._analyze_library_usage(),
            'import_frequency': self._analyze_import_frequency(),
            'dependency_graph': self._build_dependency_summary()
        }
    
    def _analyze_library_usage(self) -> Dict:
        """Analyze which libraries are most frequently used"""
        lib_counter = Counter()
        
        for imports in self.imports_by_file.values():
            for import_name in imports:
                lib_base = import_name.split('.')[0]
                lib_counter[lib_base] += 1
        
        return {
            'most_used': dict(lib_counter.most_common(10)),
            'least_used': dict(lib_counter.most_common()[-10:]),
            'total_unique_libraries': len(lib_counter)
        }
    
    def _analyze_import_frequency(self) -> Dict:
        """Analyze import patterns"""
        import_types = Counter()
        import_style = Counter()
        
        for file_path, imports in self.imports_by_file.items():
            for import_name in imports:
                # Classify import type
                if '.' in import_name:
                    import_types['from_import'] += 1
                else:
                    import_types['direct_import'] += 1
                
                # Classify by library type
                lib_base = import_name.split('.')[0]
                if lib_base in ['os', 'sys', 'pathlib', 'json', 'datetime']:
                    import_style['standard_library'] += 1
                elif lib_base in ['numpy', 'pandas', 'matplotlib', 'scipy']:
                    import_style['data_science'] += 1
                elif lib_base in ['flask', 'django', 'fastapi']:
                    import_style['web_framework'] += 1
                else:
                    import_style['other'] += 1
        
        return dict(import_types), dict(import_style)
    
    def _build_dependency_summary(self) -> Dict:
        """Build a summary of dependency relationships"""
        summary = {
            'files_with_most_imports': [],
            'files_with_fewest_imports': [],
            'most_coupled_files': []
        }
        
        # Files with most/fewest imports
        import_counts = [(file_path, len(imports)) for file_path, imports in self.imports_by_file.items()]
        import_counts.sort(key=lambda x: x[1], reverse=True)
        
        summary['files_with_most_imports'] = import_counts[:5]
        summary['files_with_fewest_imports'] = import_counts[-5:]
        
        return summary
