"""
Audit Analyzer - Enhanced analysis with systematic finding capture
"""

from typing import Dict, List, Any, Optional
import ast
import re
from pathlib import Path

from .findings_tracker import FindingsTracker, Severity, Category, FindingLocation
from .dependency_analyzer import DependencyAnalyzer
from .mcp_structure_validator import MCPStructureValidator

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
        
        # Pattern for Windows absolute paths (more precise - must start with drive letter)
        windows_pattern = r'[A-Z]:\\[^"\'\s\\][^"\'\s\\]*'
        # Pattern for Unix absolute paths (must start with / and contain path separators)
        unix_pattern = r'/[a-zA-Z0-9_\-\.]+(/[a-zA-Z0-9_\-\.]+)+'
        
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
                        
                        # Skip common non-problematic paths (expanded list)
                        if any(skip in path.lower() for skip in [
                            # System paths
                            'python', 'program files', 'windows', 'usr/bin', 
                            'usr/local/bin', '/bin/', '/sbin/', '/opt/',
                            # Development paths
                            'site-packages', 'node_modules', '.venv', '__pycache__',
                            # Common directories
                            'appdata', 'temp', 'tmp', 'users', 'home',
                            # Version control
                            '.git', '.svn', '.hg',
                            # Build/CI paths
                            'build', 'dist', 'target', 'out',
                            # IDE paths
                            '.vscode', '.idea', 'eclipse',
                            # Common patterns
                            'c:\\users\\', '/home/', '/var/', '/etc/'
                        ]):
                            continue
                        
                        # Skip if it's in a comment (check if # appears before the path)
                        comment_pos = line.find('#')
                        if comment_pos != -1 and match.start() > comment_pos:
                            continue
                        
                        # Skip if it's in a string that's clearly not a path
                        # Check for common string patterns that aren't paths
                        line_stripped = line.strip()
                        if any(pattern in line_stripped.lower() for pattern in [
                            # URLs and web patterns
                            'http://', 'https://', 'ftp://', 'file://',
                            'www.', '.com', '.org', '.net',
                            # Documentation patterns
                            'example', 'test', 'demo', 'sample',
                            'TODO:', 'FIXME:', 'NOTE:', 'XXX:',
                            # Rich console formatting tags (major source of false positives)
                            '[bold]', '[/bold]', '[red]', '[/red]', '[green]', '[/green]',
                            '[blue]', '[/blue]', '[yellow]', '[/yellow]', '[cyan]', '[/cyan]',
                            '[magenta]', '[/magenta]', '[white]', '[/white]',
                            '[dim]', '[/dim]', '[bright]', '[/bright]',
                            # Console formatting patterns
                            '[bold red]', '[/bold red]', '[bold green]', '[/bold green]',
                            '[bold blue]', '[/bold blue]', '[bold yellow]', '[/bold yellow]',
                            '[orange1]', '[/orange1]', '[bright_green]', '[/bright_green]',
                            # Other common formatting
                            '[/]', '[*]', '[+]', '[-]', '[✓]', '[❌]', '[⚠️]', '[🚨]',
                            # ANSI escape sequences
                            '\x1b[', '\033[', '\\033[', '\\x1b['
                        ]):
                            continue
                        
                        # Skip Rich console formatting patterns specifically
                        if re.search(r'\[\/?[a-zA-Z0-9_\-\s]+\]', line_stripped):
                            continue
                        
                        # Skip if it's a path-like pattern that's actually something else
                        # Check for common non-path patterns
                        if any(path.startswith(pattern) for pattern in [
                            'C:\\', 'D:\\', 'E:\\', 'F:\\', 'G:\\', 'H:\\',
                            '/tmp/', '/var/', '/etc/', '/usr/', '/opt/',
                            '/dev/', '/proc/', '/sys/', '/home/'
                        ]) and any(keyword in line_stripped for keyword in [
                            'example', 'test', 'sample', 'demo', 'placeholder',
                            'your_path', 'path_to', 'folder', 'directory'
                        ]):
                            continue
                        
                        # Additional context check - skip if line looks like documentation
                        if any(doc_pattern in line_stripped for doc_pattern in [
                            '#', '//', '"""', "'''", '"""', "'''",
                            'example:', 'e.g.', 'for example:',
                            'usage:', 'note:', 'see:'
                        ]):
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
                logger.exception(f"Error analyzing {file_path}: {e}")
        
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
                logger.exception(f"Error analyzing {file_path}: {e}")
        
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
                logger.exception(f"Error analyzing {file_path}: {e}")
        
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
                logger.exception(f"Error analyzing {file_path}: {e}")
        
        return finding_ids
    
    def analyze_dependencies(self) -> List[str]:
        """Analyze dependencies for unused imports and decomposable libraries"""
        finding_ids = []
        
        try:
            dep_analyzer = DependencyAnalyzer(str(self.project_path))
            results = dep_analyzer.analyze_imports_and_usage()
            
            # Merge all finding IDs and import actual findings into our tracker
            for category, ids in results.items():
                for fid in ids:
                    if fid in dep_analyzer.tracker.findings:
                        old_f = dep_analyzer.tracker.findings[fid]
                        # Re-add to our tracker to centralize all findings
                        new_id = self.tracker.add_finding(
                            title=old_f.title, description=old_f.description,
                            severity=old_f.severity, category=old_f.category,
                            recommendation=old_f.recommendation, effort_estimate=old_f.effort_estimate,
                            tags=old_f.tags
                        )
                        for loc in old_f.locations:
                            self.tracker.findings[new_id].locations.append(loc)
                        finding_ids.append(new_id)
            
            # Generate and save dependency report
            dep_report = dep_analyzer.generate_dependency_report()
            report_path = Path(str(self.project_path)) / "audit_reports" / "dependency_report.json"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            
            import json
            with open(report_path, 'w') as f:
                json.dump(dep_report, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error analyzing dependencies: {e}")
        
        return finding_ids
    
    def analyze_mcp_structure(self) -> List[str]:
        """Analyze MCP project structure compliance"""
        finding_ids = []
        
        try:
            structure_validator = MCPStructureValidator(str(self.project_path))
            structure_results = structure_validator.validate_structure()
            
            # Generate findings based on structure results
            score = structure_results.get("overall_score", 0)
            level = structure_results.get("compliance_level")
            
            # Create finding for overall structure compliance
            if level.value in ["NON_COMPLIANT", "PARTIAL"]:
                finding_id = self.tracker.add_finding(
                    title="MCP Project Structure Issues",
                    description=f"Project has MCP structure compliance level: {level.value} ({score}%)",
                    severity=Severity.HIGH if level.value == "NON_COMPLIANT" else Severity.MEDIUM,
                    category=Category.ARCHITECTURE,
                    recommendation="Reorganize project structure according to MCP standards",
                    effort_estimate="1-3 hours",
                    tags=["mcp", "structure", "project-organization", "standards"]
                )
                finding_ids.append(finding_id)
            
            # Add findings for critical structure issues
            for req_path, result in structure_results.get("requirement_results", {}).items():
                if not result.get("compliant", True):
                    requirement = next((r for r in structure_validator.requirements if r.path == req_path), None)
                    if requirement and requirement.level == "REQUIRED":
                        finding_id = self.tracker.add_finding(
                            title=f"MCP Structure Required: {requirement.description}",
                            description=f"Missing required MCP structure element: {req_path}",
                            severity=Severity.HIGH,
                            category=Category.ARCHITECTURE,
                            recommendation=f"Create {req_path} for MCP compliance",
                            effort_estimate="15 minutes",
                            tags=["mcp", "structure", "required"]
                        )
                        finding_ids.append(finding_id)
            
            # Export structure report
            output_dir = Path(str(self.project_path)) / "audit_reports"
            output_dir.mkdir(parents=True, exist_ok=True)
            structure_validator.export_structure_report(str(output_dir))
            
        except Exception as e:
            print(f"Error analyzing MCP structure: {e}")
        
        return finding_ids
    
    def run_full_analysis(self) -> Dict[str, List[str]]:
        """Run all analysis methods"""
        results = {
            "hardcoded_paths": self.analyze_hardcoded_paths(),
            "print_statements": self.analyze_print_statements(),
            "broad_exceptions": self.analyze_broad_exceptions(),
            "llm_integration": self.analyze_llm_integration(),
            "dependencies": self.analyze_dependencies(),
            "mcp_structure": self.analyze_mcp_structure()
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
