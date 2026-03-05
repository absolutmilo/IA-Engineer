"""
MCP Tool Validators - Input validation functions for AI Auditor tools
"""

import re
import html
import os
from pathlib import Path
from typing import Dict, Any, List, Optional


def sanitize_input(user_input: str) -> str:
    """Sanitize user input for security"""
    if not isinstance(user_input, str):
        raise TypeError("Input must be a string")
    
    # HTML escape to prevent XSS
    sanitized = html.escape(user_input)
    
    # Remove control characters except newlines and tabs
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
    
    # Limit length
    max_length = 10000
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "...[truncated]"
    
    return sanitized


def validate_project_path(project_path: str) -> str:
    """Validate project path for security and accessibility"""
    if not isinstance(project_path, str):
        raise TypeError("Project path must be a string")
    
    if not project_path.strip():
        raise ValueError("Project path cannot be empty")
    
    path = Path(project_path)
    
    # Check for path traversal attempts
    dangerous_patterns = ['..', '~/', '/etc/', '/var/', '/usr/', '/sys/', '/proc/']
    if any(pattern in str(path) for pattern in dangerous_patterns):
        raise ValueError(f"Potentially dangerous path detected: {project_path}")
    
    # Convert to absolute path
    abs_path = path.absolute()
    
    # Check if path exists
    if not abs_path.exists():
        raise ValueError(f"Project path does not exist: {abs_path}")
    
    # Check if it's a directory
    if not abs_path.is_dir():
        raise ValueError(f"Project path must be a directory: {abs_path}")
    
    return str(abs_path)


def validate_analysis_types(analysis_types: List[str]) -> List[str]:
    """Validate analysis types for audit requests"""
    if not isinstance(analysis_types, list):
        raise TypeError("Analysis types must be a list")
    
    allowed_types = ["enhanced", "static", "llm", "dependency", "structure", "mcp_compliance"]
    invalid_types = [t for t in analysis_types if t not in allowed_types]
    
    if invalid_types:
        raise ValueError(f"Invalid analysis types: {invalid_types}. Allowed: {allowed_types}")
    
    return analysis_types


def validate_json_structure(data: Dict[str, Any]) -> bool:
    """Validate JSON structure for common patterns"""
    if not isinstance(data, dict):
        return False
    
    # Check for nested depth (prevent DoS)
    max_depth = 10
    def get_depth(obj, current_depth=0):
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(get_depth(v, current_depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(get_depth(item, current_depth + 1) for item in obj)
        else:
            return current_depth
    
    return get_depth(data) <= max_depth


def validate_file_path(file_path: str) -> bool:
    """Validate file path for security"""
    if not isinstance(file_path, str):
        return False
    
    # Prevent path traversal
    dangerous_patterns = ['..', '~/', '/etc/', '/var/', '/usr/']
    if any(pattern in file_path for pattern in dangerous_patterns):
        return False
    
    # Check for allowed extensions
    allowed_extensions = ['.txt', '.json', '.csv', '.py', '.md', '.yaml', '.yml', '.toml']
    if not any(file_path.endswith(ext) for ext in allowed_extensions):
        return False
    
    return True


def validate_log_level(log_level: str) -> str:
    """Validate log level"""
    if not isinstance(log_level, str):
        raise TypeError("Log level must be a string")
    
    allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    normalized_level = log_level.upper()
    
    if normalized_level not in allowed_levels:
        raise ValueError(f"Invalid log level: {log_level}. Allowed: {allowed_levels}")
    
    return normalized_level


def validate_timeout(timeout: int) -> int:
    """Validate timeout value"""
    if not isinstance(timeout, int):
        raise TypeError("Timeout must be an integer")
    
    if timeout < 1:
        raise ValueError("Timeout must be at least 1 second")
    
    if timeout > 600:  # 10 minutes max
        raise ValueError("Timeout cannot exceed 600 seconds (10 minutes)")
    
    return timeout


def validate_severity(severity: str) -> str:
    """Validate severity level"""
    if not isinstance(severity, str):
        raise TypeError("Severity must be a string")
    
    allowed_severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    normalized_severity = severity.upper()
    
    if normalized_severity not in allowed_severities:
        raise ValueError(f"Invalid severity: {severity}. Allowed: {allowed_severities}")
    
    return normalized_severity


def validate_category(category: str) -> str:
    """Validate finding category"""
    if not isinstance(category, str):
        raise TypeError("Category must be a string")
    
    allowed_categories = [
        "ARCHITECTURE", "SECURITY", "PERFORMANCE", "MAINTAINABILITY",
        "RELIABILITY", "CONFIGURATION", "LOGGING", "TESTING"
    ]
    normalized_category = category.upper()
    
    if normalized_category not in allowed_categories:
        raise ValueError(f"Invalid category: {category}. Allowed: {allowed_categories}")
    
    return normalized_category
