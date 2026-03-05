"""
Test suite for MCP Tools - Comprehensive testing for AI Auditor
"""

import pytest
import tempfile
import json
from pathlib import Path

from src.mcp_tools.schemas import AuditRequest, TOOL_SCHEMAS
from src.mcp_tools.validators import ValidationError, validate_project_path
from src.mcp_tools.exceptions import AnalysisError, ValidationError
from src.mcp_tools.audit_analyzer import analyze_project


class TestMCPTools:
    """Test cases for MCP tools functionality"""
    
    def test_audit_request_validation(self):
        """Test audit request validation"""
        # Valid request
        valid_request = {
            "project_path": str(Path(__file__).parent.parent.parent),
            "analysis_types": ["enhanced"],
            "options": {"max_files": 10}
        }
        
        try:
            request = AuditRequest(**valid_request)
            assert request.project_path == str(Path(__file__).parent.parent.parent)
            assert request.analysis_types == ["enhanced"]
        except ValidationError:
            pytest.fail("Valid request should not raise ValidationError")
        
        # Invalid request - empty project path
        invalid_request = {
            "project_path": "",
            "analysis_types": ["enhanced"]
        }
        
        with pytest.raises(ValidationError):
            AuditRequest(**invalid_request)
        
        # Invalid request - invalid analysis types
        invalid_request2 = {
            "project_path": str(Path(__file__).parent.parent.parent),
            "analysis_types": ["invalid_type"]
        }
        
        with pytest.raises(ValidationError):
            AuditRequest(**invalid_request2)
    
    def test_project_path_validation(self):
        """Test project path validation"""
        from src.mcp_tools.validators import validate_project_path
        
        # Valid path
        valid_path = str(Path(__file__).parent.parent.parent)
        result = validate_project_path(valid_path)
        assert result == str(Path(valid_path).absolute())
        
        # Invalid path - doesn't exist
        with pytest.raises(ValueError):
            validate_project_path("/nonexistent/path")
        
        # Invalid path - dangerous pattern
        with pytest.raises(ValueError):
            validate_project_path("/etc/passwd")
    
    def test_analyze_project_success(self):
        """Test successful project analysis"""
        request_data = {
            "project_path": str(Path(__file__).parent.parent.parent),
            "analysis_types": ["enhanced"],
            "options": {}
        }
        
        result = analyze_project(request_data)
        
        assert result["status"] == "success"
        assert "results" in result
        assert "metadata" in result
        assert result["total_findings"] >= 0
        assert "tool_version" in result["metadata"]
    
    def test_analyze_project_with_options(self):
        """Test project analysis with options"""
        request_data = {
            "project_path": str(Path(__file__).parent.parent.parent),
            "analysis_types": ["enhanced"],
            "options": {"max_files": 5}
        }
        
        result = analyze_project(request_data)
        
        assert result["status"] == "success"
        assert result["metadata"]["config"]["max_python_files"] == 1000  # Default value
    
    def test_analyze_project_multiple_types(self):
        """Test project analysis with multiple analysis types"""
        request_data = {
            "project_path": str(Path(__file__).parent.parent.parent),
            "analysis_types": ["enhanced", "dependency"],
            "options": {}
        }
        
        result = analyze_project(request_data)
        
        assert result["status"] == "success"
        assert "enhanced" in result["results"]
        assert "dependency" in result["results"]
        assert set(result["analysis_types"]) == {"enhanced", "dependency"}
    
    def test_analyze_project_validation_error(self):
        """Test project analysis with invalid input"""
        request_data = {
            "project_path": "/nonexistent/path",
            "analysis_types": ["enhanced"]
        }
        
        with pytest.raises(ValueError):
            analyze_project(request_data)
    
    def test_tool_metadata(self):
        """Test tool metadata is properly defined"""
        assert "name" in TOOL_METADATA["analyze_project"]
        assert "description" in TOOL_METADATA["analyze_project"]
        assert "schema" in TOOL_METADATA["analyze_project"]
        assert TOOL_METADATA["analyze_project"]["schema"] == "AuditRequest"
        assert "version" in TOOL_METADATA["analyze_project"]
        assert "capabilities" in TOOL_METADATA["analyze_project"]
        assert isinstance(TOOL_METADATA["analyze_project"]["capabilities"], list)
    
    def test_schema_exports(self):
        """Test that all schemas are properly exported"""
        from src.mcp_tools.schemas import TOOL_SCHEMAS
        
        assert "audit" in TOOL_SCHEMAS
        assert TOOL_SCHEMAS["audit"] == AuditRequest
        
        # Check that schemas are Pydantic models
        assert hasattr(TOOL_SCHEMAS["audit"], "__name__")
        assert hasattr(TOOL_SCHEMAS["audit"], "validate")
    
    def test_exception_hierarchy(self):
        """Test that exceptions inherit properly"""
        from src.mcp_tools.exceptions import (
            MCPToolError, ValidationError, AnalysisError
        )
        
        # Test inheritance
        assert issubclass(ValidationError, MCPToolError)
        assert issubclass(AnalysisError, MCPToolError)
        
        # Test instantiation
        base_error = MCPToolError("Base error")
        assert base_error.error_code == "TOOL_ERROR"
        assert base_error.message == "Base error"
        
        validation_error = ValidationError("Validation failed", field="test")
        assert validation_error.error_code == "VALIDATION_ERROR_TEST"
        assert validation_error.field == "test"
        
        analysis_error = AnalysisError("Analysis failed", analysis_type="static")
        assert analysis_error.error_code == "ANALYSIS_ERROR_STATIC"
        assert analysis_error.analysis_type == "static"


if __name__ == "__main__":
    pytest.main([__file__])
