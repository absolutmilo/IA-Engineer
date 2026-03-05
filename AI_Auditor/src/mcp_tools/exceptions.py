"""
MCP Tool Exceptions - Custom exception classes for AI Auditor tools
"""

from typing import Optional, Dict, Any


class MCPToolError(Exception):
    """Base exception for MCP tool errors"""
    def __init__(self, message: str, error_code: str = "TOOL_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class ValidationError(MCPToolError):
    """Input validation errors"""
    def __init__(self, message: str, field: str = None, value: Any = None):
        error_code = "VALIDATION_ERROR"
        if field:
            error_code = f"VALIDATION_ERROR_{field.upper()}"
        super().__init__(message, error_code, {"field": field, "value": value})
        self.field = field
        self.value = value


class AnalysisError(MCPToolError):
    """Analysis processing errors"""
    def __init__(self, message: str, analysis_type: str = None, step: str = None):
        error_code = "ANALYSIS_ERROR"
        if analysis_type:
            error_code = f"ANALYSIS_ERROR_{analysis_type.upper()}"
        if step:
            error_code = f"ANALYSIS_ERROR_{step.upper()}"
        super().__init__(message, error_code, {"analysis_type": analysis_type, "step": step})
        self.analysis_type = analysis_type
        self.step = step


class ConfigurationError(MCPToolError):
    """Configuration-related errors"""
    def __init__(self, message: str, config_key: str = None, config_file: str = None):
        error_code = "CONFIG_ERROR"
        if config_key:
            error_code = f"CONFIG_ERROR_{config_key.upper()}"
        super().__init__(message, error_code, {"config_key": config_key, "config_file": config_file})
        self.config_key = config_key
        self.config_file = config_file


class ExternalServiceError(MCPToolError):
    """External service integration errors"""
    def __init__(self, message: str, service: str = None, status_code: int = None, response: Optional[Dict[str, Any]] = None):
        error_code = "EXTERNAL_ERROR"
        if service:
            error_code = f"EXTERNAL_ERROR_{service.upper()}"
        super().__init__(message, error_code, {
            "service": service, 
            "status_code": status_code,
            "response": response
        })
        self.service = service
        self.status_code = status_code
        self.response = response


class FileSystemError(MCPToolError):
    """File system and I/O errors"""
    def __init__(self, message: str, file_path: str = None, operation: str = None):
        error_code = "FILESYSTEM_ERROR"
        if operation:
            error_code = f"FILESYSTEM_ERROR_{operation.upper()}"
        super().__init__(message, error_code, {"file_path": file_path, "operation": operation})
        self.file_path = file_path
        self.operation = operation


class ProjectStructureError(MCPToolError):
    """Project structure validation errors"""
    def __init__(self, message: str, requirement: str = None, path: str = None):
        error_code = "STRUCTURE_ERROR"
        if requirement:
            error_code = f"STRUCTURE_ERROR_{requirement.upper().replace(' ', '_')}"
        super().__init__(message, error_code, {"requirement": requirement, "path": path})
        self.requirement = requirement
        self.path = path
