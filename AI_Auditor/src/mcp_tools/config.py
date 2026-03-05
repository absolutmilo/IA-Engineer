"""
MCP Tool Configuration - Environment-based configuration management for AI Auditor
"""

import os
from typing import Optional, List
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """AI Auditor settings with environment variable support"""
    
    # LLM Configuration
    llm_model: str = "llama3.2:3b-instruct-q4_0"
    llm_api_base: str = "http://localhost:11434"
    llm_timeout: int = 120
    llm_section_timeout: int = 60
    
    # Analysis Configuration
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    max_python_files: int = 1000
    exclude_patterns: List[str] = [".venv", "__pycache__", ".git", "node_modules"]
    
    # Output Configuration
    output_directory: str = "audit_reports"
    log_directory: str = "logs"
    enable_json_output: bool = True
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json"
    enable_console_output: bool = True
    log_file: Optional[str] = None
    
    # Security Configuration
    enable_secret_detection: bool = True
    max_path_length: int = 200
    allow_test_paths: bool = False
    
    # Performance Configuration
    enable_parallel_processing: bool = True
    max_workers: int = 4
    memory_limit_mb: int = 1024  # 1GB
    
    # MCP Configuration
    enable_mcp_validation: bool = True
    mcp_compliance_level: str = "PARTIAL"  # COMPLIANT, PARTIAL, NON_COMPLIANT
    require_mcp_structure: bool = True
    
    class Config:
        env_file = ".env"
        env_prefix = "AI_AUDITOR_"
    
    @validator('llm_api_base')
    def validate_llm_api_base(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('LLM API base must start with http:// or https://')
        return v
    
    @validator('llm_timeout')
    def validate_llm_timeout(cls, v):
        if v < 10 or v > 600:
            raise ValueError('LLM timeout must be between 10 and 600 seconds')
        return v
    
    @validator('max_file_size')
    def validate_max_file_size(cls, v):
        if v < 1024:  # Minimum 1KB
            raise ValueError('max_file_size must be at least 1024 bytes')
        return v
    
    @validator('max_workers')
    def validate_max_workers(cls, v):
        if v < 1 or v > 16:
            raise ValueError('max_workers must be between 1 and 16')
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f'log_level must be one of: {allowed_levels}')
        return v.upper()
    
    @validator('mcp_compliance_level')
    def validate_mcp_compliance_level(cls, v):
        allowed_levels = ["COMPLIANT", "PARTIAL", "NON_COMPLIANT"]
        if v.upper() not in allowed_levels:
            raise ValueError(f'mcp_compliance_level must be one of: {allowed_levels}')
        return v.upper()


# Global settings instance
settings = Settings()


def get_llm_config() -> dict:
    """Get LLM configuration dictionary"""
    return {
        "model": settings.llm_model,
        "api_base": settings.llm_api_base,
        "timeout": settings.llm_timeout,
        "section_timeout": settings.llm_section_timeout
    }


def get_analysis_config() -> dict:
    """Get analysis configuration dictionary"""
    return {
        "max_file_size": settings.max_file_size,
        "max_python_files": settings.max_python_files,
        "exclude_patterns": settings.exclude_patterns,
        "output_directory": settings.output_directory
    }


def get_logging_config() -> dict:
    """Get logging configuration dictionary"""
    return {
        "level": settings.log_level,
        "format": settings.log_format,
        "enable_console": settings.enable_console_output,
        "log_file": settings.log_file
    }


def get_mcp_config() -> dict:
    """Get MCP configuration dictionary"""
    return {
        "enable_validation": settings.enable_mcp_validation,
        "compliance_level": settings.mcp_compliance_level,
        "require_structure": settings.require_mcp_structure
    }
