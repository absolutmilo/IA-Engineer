"""
Audit Analyzer - Enhanced analysis with systematic finding capture
"""

from typing import Dict, List, Any, Optional
import ast
import re
from pathlib import Path

from .findings_tracker import FindingsTracker, Severity, Category, FindingLocation

class AuditAnalyzer:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.tracker = FindingsTracker()
        
        # Get all Python files but exclude common non-project directories
        self.python_files = []
        exclude_dirs = {'.venv', '__pycache__', '.git', 'node_modules', '.pytest_cache', '.tox'}
        
        for file_path in self.project_path.rglob("*.py"):
            # Skip if any parent directory is in exclude list
            if any(exclude_dir in file_path.parts for exclude_dir in exclude_dirs):
                continue
            self.python_files.append(file_path)
    
    def analyze_hardcoded_paths(self) -> List[str]:
        """Find hardcoded absolute paths that prevent deployment"""
        finding_ids = []
        
        # Pattern for Windows absolute paths
        windows_pattern = r'[A-Z]:\\[^"\'\s\\]+'
        # Pattern for Unix absolute paths (minimum 3 characters to avoid false positives)
        unix_pattern = r'/[^"\'\s\\]{3,}'
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                # Skip log files and test files
                if any(skip in str(file_path) for skip in ['logs/', 'test_', '__pycache__']):
                    continue
                
                # Track if we're inside a docstring
                in_docstring = False
                docstring_char = None
                
                for line_num, line in enumerate(lines, 1):
                    stripped = line.strip()
                    
                    # Handle docstring detection
                    if not in_docstring:
                        if stripped.startswith('"""') or stripped.startswith("'''"):
                            in_docstring = True
                            docstring_char = '"""' if stripped.startswith('"""') else "'''"
                            # Check if docstring ends on same line
                            if stripped.count(docstring_char) >= 2:
                                in_docstring = False
                                docstring_char = None
                            continue
                    else:
                        # Check if docstring ends on this line
                        if docstring_char in line:
                            # Count occurrences to see if it really ends
                            if line.count(docstring_char) >= 2:
                                in_docstring = False
                                docstring_char = None
                            continue
                        # Skip everything inside docstrings
                        continue
                    
                    # Skip comments
                    if stripped.startswith('#'):
                        continue
                    
                    # Skip shebang lines
                    if line_num == 1 and stripped.startswith('#!'):
                        continue
                    
                    # Check for hardcoded paths in actual code
                    windows_matches = re.finditer(windows_pattern, line)
                    unix_matches = re.finditer(unix_pattern, line)
                    
                    for match in list(windows_matches) + list(unix_matches):
                        path = match.group()
                        
                        # Skip common non-problematic paths
                        if any(skip in path.lower() for skip in [
                            'python', 'program files', 'windows', 'usr/bin', 
                            'usr/local/bin', '/bin/', '/sbin/', '/opt/'
                        ]):
                            continue
                        
                        # Skip if it's in a comment (check if # appears before the path)
                        comment_pos = line.find('#')
                        if comment_pos != -1 and match.start() > comment_pos:
                            continue
                        
                        # Get code context
                        code_snippet = line.strip()
                        
                        finding_id = self.tracker.add_finding(
                            title="Hardcoded Absolute Path",
                            description=f"Hardcoded path '{path}' prevents deployment to other machines",
                            severity=Severity.CRITICAL,
                            category=Category.CONFIGURATION,
                            recommendation="Use environment variables or configuration files",
                            effort_estimate="15 minutes",
                            tags=["deployment", "configuration", "path"]
                        )
                        
                        self.tracker.findings[finding_id].add_location(
                            file_path=str(file_path.relative_to(self.project_path)),
                            line=line_num,
                            function=None,
                            snippet=code_snippet
                        )
                        
                        finding_ids.append(finding_id)
                        
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
        
        return finding_ids
    
    def analyze_print_statements(self) -> List[str]:
        """Find print() statements that should be logging"""
        finding_ids = []
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse AST to find print statements
                try:
                    tree = ast.parse(content)
                except SyntaxError:
                    continue
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'print':
                        line_num = node.lineno
                        
                        # Get the line content
                        lines = content.split('\n')
                        if line_num <= len(lines):
                            line_content = lines[line_num - 1]
                            stripped = line_content.strip()
                            
                            # Skip if it's in a comment
                            if stripped.startswith('#'):
                                continue
                            
                            # Check if print is within a docstring context
                            # This is a simplified check - could be improved with more sophisticated parsing
                            if '"""' in line_content or "'''" in line_content:
                                # Look for the start of docstring in previous lines
                                docstring_start = None
                                for i in range(max(0, line_num - 10), line_num):
                                    if '"""' in lines[i] or "'''" in lines[i]:
                                        docstring_start = i
                                        break
                                
                                # If we're in a docstring, skip
                                if docstring_start is not None:
                                    continue
                            
                            code_snippet = stripped
                            
                            finding_id = self.tracker.add_finding(
                                title="Print Statement Instead of Logging",
                                description="Using print() instead of proper logging",
                                severity=Severity.MEDIUM,
                                category=Category.LOGGING,
                                recommendation="Replace with logger.info/debug/error/etc.",
                                effort_estimate="5 minutes",
                                tags=["logging", "production"]
                            )
                            
                            self.tracker.findings[finding_id].add_location(
                                file_path=str(file_path.relative_to(self.project_path)),
                                line=line_num,
                                function=None,
                                snippet=code_snippet
                            )
                            
                            finding_ids.append(finding_id)
                        
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
        
        return finding_ids
    
    def analyze_broad_exceptions(self) -> List[str]:
        """Find broad exception handlers"""
        finding_ids = []
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                try:
                    tree = ast.parse(content)
                except SyntaxError:
                    continue
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ExceptHandler):
                        if node.type is None:  # bare except
                            line_num = node.lineno
                            lines = content.split('\n')
                            code_snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""
                            
                            finding_id = self.tracker.add_finding(
                                title="Broad Exception Handler",
                                description="Bare except clause catches all exceptions",
                                severity=Severity.HIGH,
                                category=Category.RELIABILITY,
                                recommendation="Catch specific exception types",
                                effort_estimate="10 minutes",
                                tags=["error-handling", "reliability"]
                            )
                            
                            self.tracker.findings[finding_id].add_location(
                                file_path=str(file_path.relative_to(self.project_path)),
                                line=line_num,
                                function=None,
                                snippet=code_snippet
                            )
                            
                            finding_ids.append(finding_id)
                        
                        elif isinstance(node.type, ast.Name) and node.type.id == 'Exception':
                            line_num = node.lineno
                            lines = content.split('\n')
                            code_snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""
                            
                            finding_id = self.tracker.add_finding(
                                title="Broad Exception Handler",
                                description="Catching generic Exception type",
                                severity=Severity.MEDIUM,
                                category=Category.RELIABILITY,
                                recommendation="Catch more specific exception types",
                                effort_estimate="10 minutes",
                                tags=["error-handling", "reliability"]
                            )
                            
                            self.tracker.findings[finding_id].add_location(
                                file_path=str(file_path.relative_to(self.project_path)),
                                line=line_num,
                                function=None,
                                snippet=code_snippet
                            )
                            
                            finding_ids.append(finding_id)
                            
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
        
        return finding_ids
    
    def analyze_llm_integration(self) -> List[str]:
        """Analyze LLM integration issues"""
        finding_ids = []
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    # Check for direct ollama client usage
                    if 'ollama.Client' in line:
                        finding_id = self.tracker.add_finding(
                            title="Direct LLM Client Usage",
                            description="Using direct ollama.Client() instead of abstraction layer",
                            severity=Severity.HIGH,
                            category=Category.ARCHITECTURE,
                            recommendation="Use LLM abstraction layer for provider switching",
                            effort_estimate="30 minutes",
                            tags=["llm", "architecture", "abstraction"]
                        )
                        
                        self.tracker.findings[finding_id].add_location(
                            file_path=str(file_path.relative_to(self.project_path)),
                            line=line_num,
                            function=None,
                            snippet=line.strip()
                        )
                        
                        finding_ids.append(finding_id)
                    
                    # Check for hardcoded models
                    if 'llama3.2:3b-instruct-q4_0' in line:
                        finding_id = self.tracker.add_finding(
                            title="Hardcoded Model Name",
                            description="Model name hardcoded prevents easy switching",
                            severity=Severity.MEDIUM,
                            category=Category.CONFIGURATION,
                            recommendation="Move model name to configuration",
                            effort_estimate="5 minutes",
                            tags=["llm", "configuration"]
                        )
                        
                        self.tracker.findings[finding_id].add_location(
                            file_path=str(file_path.relative_to(self.project_path)),
                            line=line_num,
                            function=None,
                            snippet=line.strip()
                        )
                        
                        finding_ids.append(finding_id)
                        
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
        
        return finding_ids
    
    def run_full_analysis(self) -> Dict[str, List[str]]:
        """Run all analysis methods"""
        results = {
            "hardcoded_paths": self.analyze_hardcoded_paths(),
            "print_statements": self.analyze_print_statements(),
            "broad_exceptions": self.analyze_broad_exceptions(),
            "llm_integration": self.analyze_llm_integration()
        }
        
        return results
    
    def export_findings(self, output_dir: str):
        """Export findings to JSON files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Export all findings
        self.tracker.export_to_json(str(output_path / "findings.json"))
        
        # Export roadmap
        roadmap = self.tracker.generate_roadmap()
        with open(output_path / "roadmap.json", 'w') as f:
            import json
            json.dump(roadmap, f, indent=2)
        
        # Export summary
        summary = self.tracker._generate_summary()
        with open(output_path / "summary.json", 'w') as f:
            import json
            json.dump(summary, f, indent=2)
