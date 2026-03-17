"""
Static Analysis - Core code analysis functionality
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict
from pydantic import BaseModel

from .findings_tracker import FindingsTracker, Severity, Category, FindingLocation
from utils.logger import get_logger

class FileStats(BaseModel):
    loc: int = 0
    classes: List[str] = []
    functions: List[str] = []
    imports: List[str] = []
    has_global_vars: bool = False
    broad_except_count: int = 0
    hardcoded_secrets: List[str] = []
    # New fields
    cyclomatic_complexity: int = 0
    has_subprocess_call: bool = False
    print_count: int = 0
    uses_logging: bool = False
    has_retry_pattern: bool = False
    has_timeout_pattern: bool = False
    has_hardcoded_path: bool = False
    hardcoded_paths: List[str] = []
    direct_llm_calls: List[str] = []


class StaticAnalyzer(ast.NodeVisitor):
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.stats = FileStats()
        self.source_code = ""
        self.logger = get_logger(__name__)

        self._secret_patterns = [
            re.compile(r"(?i)(api_key|secret|token|password)\s*=\s*['\"](?!os\.|env\.)[a-zA-Z0-9_\-\.]{20,}['\"]"),
            re.compile(r"(?i)bearer\s+[a-zA-Z0-9\-\._~+/]+=*")
        ]
        # Windows/Unix absolute or user-specific paths hardcoded as strings
        self._hardcoded_path_pattern = re.compile(
            r"['\"]([A-Za-z]:\\\\[^'\"]{5,}|/home/[^'\"]{5,}|/Users/[^'\"]{5,})['\"]"
        )
        # LLM direct call signatures
        self._llm_call_patterns = [
            re.compile(r"ollama\.Client\("),
            re.compile(r"openai\.ChatCompletion"),
            re.compile(r"anthropic\.Anthropic\("),
            re.compile(r"client\.chat\.completions\.create"),
            re.compile(r"\.generate\("),
        ]

    def analyze(self) -> FileStats:
        try:
            self.source_code = self.file_path.read_text(encoding="utf-8", errors="ignore")
            self.stats.loc = len(self.source_code.splitlines())

            # Regex scans on raw source
            for pat in self._secret_patterns:
                matches = pat.findall(self.source_code)
                self.stats.hardcoded_secrets.extend([str(m) for m in matches])

            hp_matches = self._hardcoded_path_pattern.findall(self.source_code)
            if hp_matches:
                self.stats.has_hardcoded_path = True
                self.stats.hardcoded_paths = list(set(hp_matches))[:5]

            for pat in self._llm_call_patterns:
                if pat.search(self.source_code):
                    self.stats.direct_llm_calls.append(pat.pattern)

            # Count print() calls
            self.stats.print_count = len(re.findall(r"\bprint\s*\(", self.source_code))

            # Retry/timeout heuristics
            if re.search(r"\btenacity\b|\bbackoff\b|\bretry\b|\bmax_retries\b|\bfor attempt in\b", self.source_code, re.IGNORECASE):
                self.stats.has_retry_pattern = True
            if re.search(r"\btimeout\s*=\s*\d+|\bsocket\.setdefaulttimeout\b|\bhttpx\b|\brequests\.get.*timeout\b", self.source_code, re.IGNORECASE):
                self.stats.has_timeout_pattern = True
            if re.search(r"\bimport logging\b|\bfrom logging\b|\blogging\.(info|warning|error|debug|critical)\b", self.source_code):
                self.stats.uses_logging = True

            # AST Parse
            tree = ast.parse(self.source_code)
            self.visit(tree)

        except Exception as e:
            self.logger.exception(f"Error analyzing {self.file_path.name}")

        return self.stats

    def visit_ClassDef(self, node):
        self.stats.classes.append(node.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.stats.functions.append(node.name)
        # Cyclomatic complexity: count branch nodes inside function
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler,
                                   ast.With, ast.Assert, ast.comprehension)):
                self.stats.cyclomatic_complexity += 1
            elif isinstance(child, ast.BoolOp):
                self.stats.cyclomatic_complexity += len(child.values) - 1
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.stats.functions.append(node.name)
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            self.stats.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self.stats.imports.append(node.module)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        if node.type is None:
            self.stats.broad_except_count += 1
        elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
            self.stats.broad_except_count += 1
        self.generic_visit(node)

    def visit_Global(self, node):
        self.stats.has_global_vars = True
        self.generic_visit(node)

    def visit_Call(self, node):
        # Detect subprocess calls
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in ("call", "run", "Popen", "check_output", "check_call"):
            if isinstance(func.value, ast.Name) and func.value.id == "subprocess":
                self.stats.has_subprocess_call = True
        elif isinstance(func, ast.Name) and func.id in ("subprocess",):
            self.stats.has_subprocess_call = True
        self.generic_visit(node)


class ProjectLevelStats:
    """Gather project-level signals beyond per-file analysis."""

    def __init__(self, root_path: Path):
        self.root_path = root_path

    def analyze(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {
            "has_tests": False,
            "has_dockerfile": False,
            "has_requirements": False,
            "has_env_example": False,
            "has_ci_config": False,
            "has_config_file": False,
            "test_file_count": 0,
            "total_python_files": 0,
        }

        for f in self.root_path.rglob("*"):
            name = f.name.lower()
            if name.startswith("test_") or name.endswith("_test.py"):
                results["has_tests"] = True
                results["test_file_count"] += 1
            if "dockerfile" in name:
                results["has_dockerfile"] = True
            if name in ("requirements.txt", "pyproject.toml", "setup.py", "setup.cfg"):
                results["has_requirements"] = True
            if name in (".env.example", ".env.template", ".env.sample"):
                results["has_env_example"] = True
            if name in (".github", "ci.yml", ".gitlab-ci.yml", "azure-pipelines.yml"):
                results["has_ci_config"] = True
            if name in ("config.yaml", "config.yml", "config.json", "settings.py", "audit_config.yaml"):
                results["has_config_file"] = True
            if f.suffix == ".py" and ".venv" not in str(f):
                results["total_python_files"] += 1

        return results
