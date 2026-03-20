"""
MCP Project Structure Validator - Validates MCP-compliant project structure
Ensures projects follow recommended folder organization for MCP tools
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .findings_tracker import FindingsTracker, Severity, Category, FindingLocation


class StructureComplianceLevel(Enum):
    """Project structure compliance levels"""
    COMPLIANT = "COMPLIANT"
    PARTIAL = "PARTIAL"
    NON_COMPLIANT = "NON_COMPLIANT"


@dataclass
class StructureRequirement:
    """MCP project structure requirement"""
    path: str
    description: str
    level: str  # REQUIRED, RECOMMENDED, OPTIONAL
    is_directory: bool
    expected_content: Optional[List[str]] = None
    validation_func: Optional[callable] = None


class MCPStructureValidator:
    """Validates MCP project structure compliance"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.tracker = FindingsTracker()
        
        # MCP project structure requirements
        self.requirements = self._define_structure_requirements()
        
        # Analysis results
        self.structure_results: Dict[str, Dict] = {}
    
    def _define_structure_requirements(self) -> List[StructureRequirement]:
        """Define MCP project structure requirements"""
        return [
            # Core MCP Structure (REQUIRED)
            StructureRequirement(
                path="pyproject.toml",
                description="Python project configuration file",
                level="REQUIRED",
                is_directory=False,
                validation_func=self._validate_pyproject_toml
            ),
            StructureRequirement(
                path="README.md",
                description="Project documentation and usage instructions",
                level="REQUIRED",
                is_directory=False,
                validation_func=self._validate_readme
            ),
            
            # Source Code Organization (REQUIRED)
            StructureRequirement(
                path="src/",
                description="Source code directory following Python packaging standards",
                level="REQUIRED",
                is_directory=True,
                validation_func=self._validate_src_structure
            ),
            StructureRequirement(
                path="src/mcp_tools/",
                description="MCP tools directory with tool implementations",
                level="REQUIRED", 
                is_directory=True,
                validation_func=self._validate_mcp_tools_structure
            ),
            
            # Configuration Management (REQUIRED)
            StructureRequirement(
                path="config/",
                description="Configuration files and settings",
                level="REQUIRED",
                is_directory=True,
                validation_func=self._validate_config_structure
            ),
            StructureRequirement(
                path=".env.example",
                description="Environment variables template",
                level="REQUIRED",
                is_directory=False,
                validation_func=self._validate_env_example
            ),
            
            # Testing Structure (REQUIRED)
            StructureRequirement(
                path="tests/",
                description="Test suite directory",
                level="REQUIRED",
                is_directory=True,
                validation_func=self._validate_tests_structure
            ),
            StructureRequirement(
                path="tests/test_mcp_tools.py",
                description="MCP tools test file",
                level="RECOMMENDED",
                is_directory=False,
                validation_func=self._validate_mcp_tools_tests
            ),
            
            # Documentation (RECOMMENDED)
            StructureRequirement(
                path="docs/",
                description="Comprehensive documentation directory",
                level="RECOMMENDED",
                is_directory=True,
                validation_func=self._validate_docs_structure
            ),
            StructureRequirement(
                path="docs/api.md",
                description="API documentation",
                level="RECOMMENDED",
                is_directory=False,
                validation_func=self._validate_api_docs
            ),
            StructureRequirement(
                path="docs/examples/",
                description="Usage examples and integration guides",
                level="RECOMMENDED",
                is_directory=True,
                validation_func=self._validate_examples_structure
            ),
            
            # Tool Structure (REQUIRED)
            StructureRequirement(
                path="src/mcp_tools/__init__.py",
                description="MCP tools package initialization",
                level="REQUIRED",
                is_directory=False,
                validation_func=self._validate_mcp_tools_init
            ),
            StructureRequirement(
                path="src/mcp_tools/schemas.py",
                description="Tool schema definitions",
                level="REQUIRED",
                is_directory=False,
                validation_func=self._validate_schemas
            ),
            StructureRequirement(
                path="src/mcp_tools/validators.py",
                description="Input validation functions",
                level="RECOMMENDED",
                is_directory=False,
                validation_func=self._validate_validators
            ),
            
            # Error Handling (REQUIRED)
            StructureRequirement(
                path="src/mcp_tools/exceptions.py",
                description="Custom exception definitions",
                level="REQUIRED",
                is_directory=False,
                validation_func=self._validate_exceptions
            ),
            
            # Configuration (RECOMMENDED)
            StructureRequirement(
                path="src/mcp_tools/config.py",
                description="Configuration management with environment variables",
                level="RECOMMENDED",
                is_directory=False,
                validation_func=self._validate_config_py
            ),
            
            # Logging (REQUIRED)
            StructureRequirement(
                path="src/mcp_tools/logger.py",
                description="Structured logging configuration",
                level="REQUIRED",
                is_directory=False,
                validation_func=self._validate_logger_py
            ),
            
            # Development Tools (OPTIONAL)
            StructureRequirement(
                path=".github/workflows/",
                description="GitHub Actions CI/CD workflows",
                level="OPTIONAL",
                is_directory=True,
                validation_func=self._validate_github_workflows
            ),
            StructureRequirement(
                path="Dockerfile",
                description="Docker containerization",
                level="OPTIONAL",
                is_directory=False,
                validation_func=self._validate_dockerfile
            ),
            StructureRequirement(
                path="requirements-dev.txt",
                description="Development dependencies",
                level="OPTIONAL",
                is_directory=False,
                validation_func=self._validate_dev_requirements
            )
        ]
    
    def validate_structure(self) -> Dict[str, any]:
        """Validate project structure against MCP standards"""
        print(f"🏗️ Analyzing MCP project structure for: {self.project_path}")
        
        structure_results = {
            "overall_score": 0,
            "compliance_level": StructureComplianceLevel.NON_COMPLIANT,
            "requirement_results": {},
            "category_scores": {},
            "findings": [],
            "recommendations": [],
            "structure_analysis": {}
        }
        
        total_score = 0
        max_score = 0
        
        # Analyze each requirement
        for requirement in self.requirements:
            try:
                result = self._check_requirement(requirement)
                structure_results["requirement_results"][requirement.path] = result
                
                # Calculate scores
                if result["compliant"]:
                    score = 100 if requirement.level == "REQUIRED" else 50
                else:
                    score = 0 if requirement.level == "REQUIRED" else 25
                
                total_score += score
                max_score += 100 if requirement.level == "REQUIRED" else 50
                
                # Track category scores
                category = self._get_requirement_category(requirement)
                if category not in structure_results["category_scores"]:
                    structure_results["category_scores"][category] = {"score": 0, "max": 0}
                
                structure_results["category_scores"][category]["score"] += score
                structure_results["category_scores"][category]["max"] += 100 if requirement.level == "REQUIRED" else 50
                
            except Exception as e:
                print(f"Error analyzing requirement {requirement.path}: {e}")
                structure_results["requirement_results"][requirement.path] = {
                    "compliant": False,
                    "score": 0,
                    "issues": [f"Analysis error: {e}"],
                    "recommendations": ["Fix analysis error and re-run"]
                }
        
        # Calculate overall compliance
        if max_score > 0:
            structure_results["overall_score"] = int((total_score / max_score) * 100)
        
        # Determine compliance level
        score = structure_results["overall_score"]
        if score >= 90:
            structure_results["compliance_level"] = StructureComplianceLevel.COMPLIANT
        elif score >= 70:
            structure_results["compliance_level"] = StructureComplianceLevel.PARTIAL
        else:
            structure_results["compliance_level"] = StructureComplianceLevel.NON_COMPLIANT
        
        # Generate recommendations
        structure_results["recommendations"] = self._generate_structure_recommendations(structure_results)
        
        # Analyze current structure
        structure_results["structure_analysis"] = self._analyze_current_structure()
        
        self.structure_results = structure_results
        return structure_results
    
    def _check_requirement(self, requirement: StructureRequirement) -> Dict:
        """Check a specific structure requirement"""
        result = {"compliant": True, "score": 100, "issues": [], "recommendations": []}
        
        full_path = self.project_path / requirement.path
        
        if requirement.is_directory:
            if not full_path.is_dir():
                result["compliant"] = False
                result["score"] = 0
                result["issues"].append(f"Missing required directory: {requirement.path}")
                result["recommendations"].append(f"Create directory: {requirement.path}")
            else:
                # Directory exists, check content if specified
                if requirement.expected_content:
                    existing_files = [f.name for f in full_path.iterdir() if f.is_file()]
                    missing_files = [f for f in requirement.expected_content if f not in existing_files]
                    if missing_files:
                        result["compliant"] = False
                        result["score"] = 50
                        result["issues"].append(f"Missing files in {requirement.path}: {missing_files}")
                        result["recommendations"].append(f"Create missing files: {missing_files}")
        else:
            if not full_path.is_file():
                result["compliant"] = False
                result["score"] = 0
                result["issues"].append(f"Missing required file: {requirement.path}")
                result["recommendations"].append(f"Create file: {requirement.path}")
        
        # Run custom validation if provided
        if requirement.validation_func and result["compliant"]:
            try:
                validation_result = requirement.validation_func(full_path)
                if not validation_result["valid"]:
                    result["compliant"] = False
                    result["score"] = validation_result.get("score", 50)
                    result["issues"].extend(validation_result.get("issues", []))
                    result["recommendations"].extend(validation_result.get("recommendations", []))
            except Exception as e:
                result["issues"].append(f"Validation error: {e}")
                result["recommendations"].append("Fix validation issues")
        
        return result
    
    def _validate_pyproject_toml(self, file_path: Path) -> Dict:
        """Validate pyproject.toml structure"""
        result = {"valid": True, "issues": [], "recommendations": []}
        
        try:
            import tomllib
            with open(file_path, 'rb') as f:
                config = tomllib.load(f)
            
            # Check for required sections
            if "project" not in config:
                result["valid"] = False
                result["issues"].append("Missing [project] section in pyproject.toml")
                result["recommendations"].append("Add [project] section with project metadata")
            
            if "build-system" not in config:
                result["valid"] = False
                result["issues"].append("Missing [build-system] section in pyproject.toml")
                result["recommendations"].append("Add [build-system] section")
            
            # Check for project metadata
            if "project" in config:
                project = config["project"]
                required_fields = ["name", "version", "description"]
                for field in required_fields:
                    if field not in project:
                        result["valid"] = False
                        result["issues"].append(f"Missing project.{field} in pyproject.toml")
                        result["recommendations"].append(f"Add {field} to [project] section")
            
        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"Error parsing pyproject.toml: {e}")
            result["recommendations"].append("Fix pyproject.toml syntax")
        
        return result
    
    def _validate_readme(self, file_path: Path) -> Dict:
        """Validate README.md content"""
        result = {"valid": True, "issues": [], "recommendations": []}
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Check for required sections
            required_sections = ["## Installation", "## Usage", "## Configuration"]
            for section in required_sections:
                if section not in content:
                    result["valid"] = False
                    result["issues"].append(f"Missing section: {section}")
                    result["recommendations"].append(f"Add {section} section to README")
            
            # Check for MCP-specific content
            if "MCP" not in content and "Model Context Protocol" not in content:
                result["valid"] = False
                result["score"] = 75
                result["issues"].append("README doesn't mention MCP or Model Context Protocol")
                result["recommendations"].append("Add MCP integration information to README")
            
        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"Error reading README.md: {e}")
            result["recommendations"].append("Fix README.md encoding")
        
        return result
    
    def _validate_src_structure(self, dir_path: Path) -> Dict:
        """Validate src/ directory structure"""
        result = {"valid": True, "issues": [], "recommendations": []}
        
        if not dir_path.is_dir():
            return result
        
        # Check for __init__.py
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            result["valid"] = False
            result["issues"].append("Missing src/__init__.py")
            result["recommendations"].append("Create src/__init__.py for proper package structure")
        
        return result
    
    def _validate_mcp_tools_structure(self, dir_path: Path) -> Dict:
        """Validate mcp_tools directory structure"""
        result = {"valid": True, "issues": [], "recommendations": []}
        
        if not dir_path.is_dir():
            return result
        
        # Check for __init__.py
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            result["valid"] = False
            result["issues"].append("Missing src/mcp_tools/__init__.py")
            result["recommendations"].append("Create src/mcp_tools/__init__.py")
        
        # Check for tool files
        tool_files = [f for f in dir_path.glob("*.py") if f.name != "__init__.py"]
        if not tool_files:
            result["valid"] = False
            result["score"] = 50
            result["issues"].append("No tool implementation files found")
            result["recommendations"].append("Add tool implementation files to mcp_tools directory")
        
        return result
    
    def _validate_config_structure(self, dir_path: Path) -> Dict:
        """Validate config/ directory structure"""
        result = {"valid": True, "issues": [], "recommendations": []}
        
        if not dir_path.is_dir():
            return result
        
        # Check for configuration files
        config_files = list(dir_path.glob("*"))
        if not config_files:
            result["valid"] = False
            result["score"] = 50
            result["issues"].append("Config directory is empty")
            result["recommendations"].append("Add configuration files to config/ directory")
        
        return result
    
    def _validate_env_example(self, file_path: Path) -> Dict:
        """Validate .env.example file"""
        result = {"valid": True, "issues": [], "recommendations": []}
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Check for common environment variables
            common_vars = ["API_KEY", "LOG_LEVEL", "DATABASE_URL"]
            found_vars = [line.split('=')[0] for line in content.split('\n') if '=' in line and not line.startswith('#')]
            
            missing_vars = [var for var in common_vars if var not in found_vars]
            if missing_vars:
                result["valid"] = False
                result["score"] = 75
                result["issues"].append(f"Missing environment variables: {missing_vars}")
                result["recommendations"].append(f"Add missing variables to .env.example: {missing_vars}")
            
        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"Error reading .env.example: {e}")
            result["recommendations"].append("Fix .env.example format")
        
        return result
    
    def _validate_tests_structure(self, dir_path: Path) -> Dict:
        """Validate tests/ directory structure"""
        result = {"valid": True, "issues": [], "recommendations": []}
        
        if not dir_path.is_dir():
            return result
        
        # Check for test files
        test_files = list(dir_path.glob("test_*.py"))
        if not test_files:
            result["valid"] = False
            result["score"] = 50
            result["issues"].append("No test files found")
            result["recommendations"].append("Add test files to tests/ directory")
        
        return result
    
    def _validate_mcp_tools_tests(self, file_path: Path) -> Dict:
        """Validate MCP tools test file"""
        result = {"valid": True, "issues": [], "recommendations": []}
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Check for test functions
            if "def test_" not in content:
                result["valid"] = False
                result["score"] = 50
                result["issues"].append("No test functions found")
                result["recommendations"].append("Add test functions to test_mcp_tools.py")
            
        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"Error reading test file: {e}")
            result["recommendations"].append("Fix test file format")
        
        return result
    
    def _validate_docs_structure(self, dir_path: Path) -> Dict:
        """Validate docs/ directory structure"""
        result = {"valid": True, "issues": [], "recommendations": []}
        
        if not dir_path.is_dir():
            return result
        
        # Check for documentation files
        doc_files = list(dir_path.glob("*.md"))
        if not doc_files:
            result["valid"] = False
            result["score"] = 50
            result["issues"].append("No documentation files found")
            result["recommendations"].append("Add documentation files to docs/ directory")
        
        return result
    
    def _validate_api_docs(self, file_path: Path) -> Dict:
        """Validate API documentation"""
        result = {"valid": True, "issues": [], "recommendations": []}
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Check for API documentation sections
            required_sections = ["## API Reference", "## Tools", "## Examples"]
            for section in required_sections:
                if section not in content:
                    result["valid"] = False
                    result["score"] = 75
                    result["issues"].append(f"Missing API documentation section: {section}")
                    result["recommendations"].append(f"Add {section} section to API docs")
            
        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"Error reading API docs: {e}")
            result["recommendations"].append("Fix API documentation format")
        
        return result
    
    def _validate_examples_structure(self, dir_path: Path) -> Dict:
        """Validate examples/ directory structure"""
        result = {"valid": True, "issues": [], "recommendations": []}
        
        if not dir_path.is_dir():
            return result
        
        # Check for example files
        example_files = list(dir_path.glob("*"))
        if not example_files:
            result["valid"] = False
            result["score"] = 50
            result["issues"].append("No example files found")
            result["recommendations"].append("Add usage examples to docs/examples/")
        
        return result
    
    def _validate_mcp_tools_init(self, file_path: Path) -> Dict:
        """Validate mcp_tools/__init__.py"""
        result = {"valid": True, "issues": [], "recommendations": []}
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Check for tool exports
            if "__all__" not in content:
                result["valid"] = False
                result["score"] = 75
                result["issues"].append("Missing __all__ export list")
                result["recommendations"].append("Add __all__ list to export tools")
            
        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"Error reading __init__.py: {e}")
            result["recommendations"].append("Fix __init__.py format")
        
        return result
    
    def _validate_schemas(self, file_path: Path) -> Dict:
        """Validate schemas.py file"""
        result = {"valid": True, "issues": [], "recommendations": []}
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Check for schema definitions
            if "schema" not in content.lower() or "pydantic" not in content.lower():
                result["valid"] = False
                result["score"] = 50
                result["issues"].append("No schema definitions found")
                result["recommendations"].append("Add Pydantic schema definitions")
            
        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"Error reading schemas.py: {e}")
            result["recommendations"].append("Fix schemas.py format")
        
        return result
    
    def _validate_validators(self, file_path: Path) -> Dict:
        """Validate validators.py file"""
        result = {"valid": True, "issues": [], "recommendations": []}
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Check for validation functions
            if "validate" not in content.lower():
                result["valid"] = False
                result["score"] = 50
                result["issues"].append("No validation functions found")
                result["recommendations"].append("Add input validation functions")
            
        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"Error reading validators.py: {e}")
            result["recommendations"].append("Fix validators.py format")
        
        return result
    
    def _validate_exceptions(self, file_path: Path) -> Dict:
        """Validate exceptions.py file"""
        result = {"valid": True, "issues": [], "recommendations": []}
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Check for custom exception classes
            if "class" not in content or "Exception" not in content:
                result["valid"] = False
                result["score"] = 50
                result["issues"].append("No custom exception classes found")
                result["recommendations"].append("Add custom exception classes")
            
        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"Error reading exceptions.py: {e}")
            result["recommendations"].append("Fix exceptions.py format")
        
        return result
    
    def _validate_config_py(self, file_path: Path) -> Dict:
        """Validate config.py file"""
        result = {"valid": True, "issues": [], "recommendations": []}
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Check for environment variable usage
            if "os.getenv" not in content and "os.environ" not in content:
                result["valid"] = False
                result["score"] = 50
                result["issues"].append("No environment variable usage found")
                result["recommendations"].append("Add environment variable configuration")
            
        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"Error reading config.py: {e}")
            result["recommendations"].append("Fix config.py format")
        
        return result
    
    def _validate_logger_py(self, file_path: Path) -> Dict:
        """Validate logger.py file"""
        result = {"valid": True, "issues": [], "recommendations": []}
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Check for logging configuration
            if "logging" not in content or "getLogger" not in content:
                result["valid"] = False
                result["score"] = 50
                result["issues"].append("No logging configuration found")
                result["recommendations"].append("Add structured logging configuration")
            
        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"Error reading logger.py: {e}")
            result["recommendations"].append("Fix logger.py format")
        
        return result
    
    def _validate_github_workflows(self, dir_path: Path) -> Dict:
        """Validate GitHub workflows"""
        result = {"valid": True, "issues": [], "recommendations": []}
        
        if not dir_path.is_dir():
            return result
        
        # Check for workflow files
        workflow_files = list(dir_path.glob("*.yml")) + list(dir_path.glob("*.yaml"))
        if not workflow_files:
            result["valid"] = False
            result["score"] = 50
            result["issues"].append("No GitHub workflow files found")
            result["recommendations"].append("Add CI/CD workflow files")
        
        return result
    
    def _validate_dockerfile(self, file_path: Path) -> Dict:
        """Validate Dockerfile"""
        result = {"valid": True, "issues": [], "recommendations": []}
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Check for Docker basics
            if "FROM" not in content:
                result["valid"] = False
                result["score"] = 25
                result["issues"].append("Dockerfile missing FROM instruction")
                result["recommendations"].append("Add base image with FROM instruction")
            
        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"Error reading Dockerfile: {e}")
            result["recommendations"].append("Fix Dockerfile format")
        
        return result
    
    def _validate_dev_requirements(self, file_path: Path) -> Dict:
        """Validate requirements-dev.txt"""
        result = {"valid": True, "issues": [], "recommendations": []}
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Check for development dependencies
            if "pytest" not in content and "black" not in content:
                result["valid"] = False
                result["score"] = 50
                result["issues"].append("Missing common development dependencies")
                result["recommendations"].append("Add pytest, black, and other dev dependencies")
            
        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"Error reading requirements-dev.txt: {e}")
            result["recommendations"].append("Fix requirements-dev.txt format")
        
        return result
    
    def _get_requirement_category(self, requirement: StructureRequirement) -> str:
        """Get category for requirement"""
        if "src/" in requirement.path or "mcp_tools" in requirement.path:
            return "source_code"
        elif "config" in requirement.path or ".env" in requirement.path:
            return "configuration"
        elif "tests" in requirement.path:
            return "testing"
        elif "docs" in requirement.path:
            return "documentation"
        elif "pyproject.toml" in requirement.path or "README" in requirement.path:
            return "project_metadata"
        elif ".github" in requirement.path or "Dockerfile" in requirement.path:
            return "development_tools"
        else:
            return "other"
    
    def _generate_structure_recommendations(self, structure_results: Dict) -> List[str]:
        """Generate prioritized recommendations"""
        recommendations = []
        
        # High priority recommendations (REQUIRED level failures)
        for req_path, result in structure_results["requirement_results"].items():
            if not result["compliant"]:
                requirement = next((r for r in self.requirements if r.path == req_path), None)
                if requirement and requirement.level == "REQUIRED":
                    recommendations.extend([f"[HIGH] {rec}" for rec in result["recommendations"]])
        
        # Medium priority recommendations (RECOMMENDED level failures)
        for req_path, result in structure_results["requirement_results"].items():
            if not result["compliant"]:
                requirement = next((r for r in self.requirements if r.path == req_path), None)
                if requirement and requirement.level == "RECOMMENDED":
                    recommendations.extend([f"[MEDIUM] {rec}" for rec in result["recommendations"]])
        
        return recommendations
    
    def _analyze_current_structure(self) -> Dict:
        """Analyze current project structure"""
        structure = {
            "directories": [],
            "files": [],
            "missing_required": [],
            "missing_recommended": []
        }
        
        # Get all directories and files
        for item in self.project_path.rglob("*"):
            if item.is_dir():
                relative_path = str(item.relative_to(self.project_path))
                if not any(skip in relative_path for skip in ['.git', '__pycache__', '.venv', 'node_modules']):
                    structure["directories"].append(relative_path)
            elif item.is_file():
                relative_path = str(item.relative_to(self.project_path))
                if not any(skip in relative_path for skip in ['.git', '__pycache__', '.venv', 'node_modules']):
                    structure["files"].append(relative_path)
        
        # Identify missing items
        for requirement in self.requirements:
            full_path = self.project_path / requirement.path
            if not full_path.exists():
                if requirement.level == "REQUIRED":
                    structure["missing_required"].append(requirement.path)
                elif requirement.level == "RECOMMENDED":
                    structure["missing_recommended"].append(requirement.path)
        
        return structure
    
    def export_structure_report(self, output_path: str):
        """Export structure report to JSON"""
        import json
        
        report_data = {
            "project_path": str(self.project_path),
            "analysis_timestamp": str(Path(__file__).stat().st_mtime),
            "structure_results": self.structure_results,
            "requirement_details": [
                {
                    "path": req.path,
                    "title": req.description,
                    "level": req.level,
                    "is_directory": req.is_directory
                }
                for req in self.requirements
            ]
        }
        
        def default_serializer(obj):
            if isinstance(obj, Enum):
                return obj.value
            raise TypeError(f"Type {type(obj)} is not serializable")

        output_file = Path(output_path) / "mcp_structure_report.json"
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=default_serializer)
        
        print(f"📄 MCP structure report exported to: {output_file}")
    
    def generate_structure_badge(self) -> str:
        """Generate structure compliance badge for README"""
        score = self.structure_results.get("overall_score", 0)
        level = self.structure_results.get("compliance_level", StructureComplianceLevel.NON_COMPLIANT)
        
        if level == StructureComplianceLevel.COMPLIANT:
            color = "brightgreen"
            text = "MCP Structured"
        elif level == StructureComplianceLevel.PARTIAL:
            color = "yellow"
            text = "MCP Partial"
        else:
            color = "red"
            text = "MCP Unstructured"
        
        return f"![MCP Structure](https://img.shields.io/badge/{text}-{score}%25-{color})"
