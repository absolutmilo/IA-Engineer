# 🏗️ MCP Project Structure Guide

## 📋 Overview

The **MCP Project Structure Validator** ensures your project follows **Model Context Protocol (MCP) organization standards** for professional tool development and seamless AI integration.

## 🎯 Why MCP Structure Matters

### **🤖 AI Integration Benefits**
- **Standardized tool organization** for better AI discovery
- **Consistent interfaces** across MCP tools
- **Professional packaging** for distribution
- **Clear separation** of concerns

### **🔧 Development Benefits**
- **Maintainable codebase** with logical organization
- **Easy testing** with standard test structure
- **Professional documentation** layout
- **Configuration management** best practices

## 📊 Structure Compliance Levels

### **🟢 COMPLIANT (90-100%)**
- All REQUIRED structure elements present
- Most RECOMMENDED elements implemented
- Professional MCP tool organization

### **🟡 PARTIAL (70-89%)**
- All REQUIRED elements present
- Some RECOMMENDED elements missing
- Good foundation, needs improvements

### **🔴 NON_COMPLIANT (0-69%)**
- Missing REQUIRED structure elements
- Significant reorganization needed
- Not ready for professional MCP development

## 📁 Ideal MCP Project Structure

```
my-mcp-tool/
├── pyproject.toml              # REQUIRED - Project configuration
├── README.md                   # REQUIRED - Project documentation
├── .env.example               # REQUIRED - Environment template
├── src/                       # REQUIRED - Source code directory
│   ├── __init__.py             # REQUIRED - Package initialization
│   └── mcp_tools/            # REQUIRED - MCP tools package
│       ├── __init__.py         # REQUIRED - Tool exports
│       ├── schemas.py           # REQUIRED - Input schemas
│       ├── validators.py        # RECOMMENDED - Input validation
│       ├── exceptions.py        # REQUIRED - Custom exceptions
│       ├── config.py           # RECOMMENDED - Configuration
│       ├── logger.py           # REQUIRED - Structured logging
│       └── tool_*.py          # REQUIRED - Tool implementations
├── tests/                      # REQUIRED - Test suite
│   ├── __init__.py             # RECOMMENDED - Test package
│   ├── test_mcp_tools.py    # RECOMMENDED - Tool tests
│   └── conftest.py          # OPTIONAL - Test configuration
├── config/                     # REQUIRED - Configuration files
├── docs/                       # RECOMMENDED - Documentation
│   ├── api.md               # RECOMMENDED - API reference
│   ├── examples/             # RECOMMENDED - Usage examples
│   └── integration.md        # OPTIONAL - Integration guide
├── .github/                    # OPTIONAL - Development tools
│   └── workflows/           # OPTIONAL - CI/CD workflows
├── Dockerfile                  # OPTIONAL - Containerization
├── requirements.txt            # OPTIONAL - Dependencies
└── requirements-dev.txt        # OPTIONAL - Development dependencies
```

## 📋 MCP Structure Requirements

### **🔧 REQUIRED Elements**

#### **pyproject.toml**
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-mcp-tool"
version = "1.0.0"
description = "MCP tool for AI integration"
authors = [{name = "Your Name", email = "your.email@example.com"}]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]

dependencies = [
    "pydantic>=2.0",
    "rich>=13.0",
    "mcp>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "black>=23.0",
    "mypy>=1.0",
    "pre-commit>=3.0",
]

[project.urls]
Homepage = "https://github.com/yourusername/my-mcp-tool"
Repository = "https://github.com/yourusername/my-mcp-tool.git"
Issues = "https://github.com/yourusername/my-mcp-tool/issues"

[project.scripts]
my-mcp-tool = "my_mcp_tool.cli:main"
```

#### **README.md**
```markdown
# My MCP Tool

A Model Context Protocol (MCP) tool for AI integration.

## Installation

```bash
pip install my-mcp-tool
```

## Usage

```python
from my_mcp_tool import process_data

result = process_data({
    "action": "analyze",
    "parameters": {"data": "example"}
})
```

## Configuration

Set environment variables:
- `API_KEY`: Your API key
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## MCP Integration

This tool follows MCP standards for:
- Structured error handling
- Input validation with Pydantic schemas
- Environment-based configuration
- Comprehensive logging

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with type checking
mypy src/

# Format code
black src/
```

## License

MIT License - see LICENSE file for details.
```

#### **src/mcp_tools/ Package Structure**
```python
# src/mcp_tools/__init__.py
"""
MCP Tools Package

This package provides MCP-compliant tools for AI integration.
"""

from .tool_analyzer import analyze_data
from .tool_processor import process_data

__all__ = [
    "analyze_data",
    "process_data",
]

__version__ = "1.0.0"
```

#### **schemas.py**
```python
# src/mcp_tools/schemas.py
"""
Input schemas for MCP tools using Pydantic validation
"""

from pydantic import BaseModel, validator
from typing import Dict, Any, Optional, List
from datetime import datetime

class AnalysisRequest(BaseModel):
    """Schema for data analysis requests"""
    data: str
    options: Optional[Dict[str, Any]] = {}
    max_results: int = 100
    
    @validator('data')
    def validate_data_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Data cannot be empty')
        return v
    
    @validator('max_results')
    def validate_max_results(cls, v):
        if v < 1 or v > 1000:
            raise ValueError('max_results must be between 1 and 1000')
        return v

class ProcessRequest(BaseModel):
    """Schema for data processing requests"""
    action: str
    parameters: Dict[str, Any]
    timestamp: Optional[datetime] = None
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = ['analyze', 'process', 'transform']
        if v not in allowed_actions:
            raise ValueError(f'Action must be one of: {allowed_actions}')
        return v

# Tool schema exports for MCP integration
TOOL_SCHEMAS = {
    "analyze": AnalysisRequest,
    "process": ProcessRequest,
}
```

#### **validators.py**
```python
# src/mcp_tools/validators.py
"""
Input validation functions for MCP tools
"""

import re
import html
from typing import Dict, Any, List

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
    allowed_extensions = ['.txt', '.json', '.csv', '.py', '.md']
    if not any(file_path.endswith(ext) for ext in allowed_extensions):
        return False
    
    return True
```

#### **exceptions.py**
```python
# src/mcp_tools/exceptions.py
"""
Custom exceptions for MCP tools with structured error codes
"""

class MCPToolError(Exception):
    """Base exception for MCP tool errors"""
    def __init__(self, message: str, error_code: str = "TOOL_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)

class ValidationError(MCPToolError):
    """Input validation errors"""
    def __init__(self, message: str, field: str = None):
        error_code = "VALIDATION_ERROR"
        if field:
            error_code = f"VALIDATION_ERROR_{field.upper()}"
        super().__init__(message, error_code)
        self.field = field

class ProcessingError(MCPToolError):
    """Data processing errors"""
    def __init__(self, message: str, step: str = None):
        error_code = "PROCESSING_ERROR"
        if step:
            error_code = f"PROCESSING_ERROR_{step.upper()}"
        super().__init__(message, error_code)
        self.step = step

class ConfigurationError(MCPToolError):
    """Configuration-related errors"""
    def __init__(self, message: str, config_key: str = None):
        error_code = "CONFIG_ERROR"
        if config_key:
            error_code = f"CONFIG_ERROR_{config_key.upper()}"
        super().__init__(message, error_code)
        self.config_key = config_key

class ExternalServiceError(MCPToolError):
    """External service integration errors"""
    def __init__(self, message: str, service: str = None, status_code: int = None):
        error_code = "EXTERNAL_ERROR"
        if service:
            error_code = f"EXTERNAL_ERROR_{service.upper()}"
        super().__init__(message, error_code)
        self.service = service
        self.status_code = status_code
```

#### **config.py**
```python
# src/mcp_tools/config.py
"""
Configuration management with environment variables and validation
"""

import os
from typing import Optional, List
from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    api_host: str = "localhost"
    api_port: int = 8000
    api_key: Optional[str] = None
    api_timeout: int = 30
    
    # Processing Configuration
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    max_concurrent_requests: int = 10
    default_log_level: str = "INFO"
    
    # Security Configuration
    allowed_origins: List[str] = ["http://localhost:3000"]
    enable_cors: bool = True
    rate_limit_per_minute: int = 100
    
    # Logging Configuration
    log_format: str = "json"
    log_file: Optional[str] = None
    enable_structured_logging: bool = True
    
    class Config:
        env_file = ".env"
        env_prefix = "MCP_TOOL_"
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if not v:
            raise ValueError('API_KEY environment variable is required')
        return v
    
    @validator('api_port')
    def validate_port(cls, v):
        if v < 1 or v > 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
    
    @validator('max_file_size')
    def validate_file_size(cls, v):
        if v < 1024:  # Minimum 1KB
            raise ValueError('max_file_size must be at least 1024 bytes')
        return v

# Global settings instance
settings = Settings()
```

#### **logger.py**
```python
# src/mcp_tools/logger.py
"""
Structured logging configuration for MCP tools
"""

import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for MCP tools"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        return json.dumps(log_entry, default=str)

def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    structured: bool = True
) -> logging.Logger:
    """Setup structured logging for MCP tools"""
    
    # Create logger
    logger = logging.getLogger("mcp_tools")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if structured:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(StructuredFormatter())
        logger.addHandler(file_handler)
    
    return logger

# Initialize logger
logger = setup_logging()
```

#### **Tool Implementation Example**
```python
# src/mcp_tools/tool_analyzer.py
"""
MCP-compliant data analysis tool
"""

import logging
from typing import Dict, Any
from .schemas import AnalysisRequest
from .validators import sanitize_input, validate_json_structure
from .exceptions import ValidationError, ProcessingError
from .config import settings

logger = logging.getLogger(__name__)

def analyze_data(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze data with proper validation and error handling
    
    Args:
        request_data: Dictionary containing analysis request
        
    Returns:
        Dictionary with analysis results
        
    Raises:
        ValidationError: If input data is invalid
        ProcessingError: If analysis fails
    """
    try:
        # Validate input using schema
        request = AnalysisRequest(**request_data)
        
        logger.info(
            "Starting data analysis",
            extra={
                "request_id": id(request_data),
                "data_length": len(request.data),
                "max_results": request.max_results
            }
        )
        
        # Sanitize input
        sanitized_data = sanitize_input(request.data)
        
        # Validate structure
        if not validate_json_structure({"data": sanitized_data}):
            raise ValidationError("Invalid JSON structure", "data")
        
        # Perform analysis
        analysis_result = {
            "status": "success",
            "data": {
                "length": len(sanitized_data),
                "word_count": len(sanitized_data.split()),
                "line_count": len(sanitized_data.split('\n')),
                "analysis_timestamp": datetime.now().isoformat()
            },
            "metadata": {
                "tool_version": "1.0.0",
                "processing_time_ms": 150  # Would calculate actual time
            }
        }
        
        logger.info(
            "Analysis completed successfully",
            extra={
                "request_id": id(request_data),
                "result_size": len(str(analysis_result))
            }
        )
        
        return analysis_result
        
    except ValidationError as e:
        logger.error(
            "Input validation failed",
            extra={
                "request_id": id(request_data),
                "error": e.message,
                "field": e.field
            }
        )
        raise
        
    except ProcessingError as e:
        logger.error(
            "Processing failed",
            extra={
                "request_id": id(request_data),
                "error": e.message,
                "step": e.step
            }
        )
        raise
        
    except Exception as e:
        logger.error(
            "Unexpected error during analysis",
            extra={
                "request_id": id(request_data),
                "error": str(e),
                "error_type": type(e).__name__
            }
        )
        raise ProcessingError(f"Analysis failed: {e}", "analysis")

# Tool metadata for MCP discovery
TOOL_METADATA = {
    "name": "analyze_data",
    "description": "Analyze text data for statistics and insights",
    "schema": "AnalysisRequest",
    "version": "1.0.0",
    "author": "MCP Tool Developer",
    "tags": ["analysis", "text", "statistics"]
}
```

### **🔧 RECOMMENDED Elements**

#### **tests/test_mcp_tools.py**
```python
# tests/test_mcp_tools.py
"""
Test suite for MCP tools
"""

import pytest
from pydantic import ValidationError
from src.mcp_tools.tool_analyzer import analyze_data
from src.mcp_tools.schemas import AnalysisRequest
from src.mcp_tools.exceptions import ValidationError, ProcessingError

class TestAnalyzeData:
    """Test cases for analyze_data function"""
    
    def test_valid_analysis_request(self):
        """Test analysis with valid request"""
        request_data = {
            "data": "Hello world! This is a test.",
            "max_results": 100
        }
        
        result = analyze_data(request_data)
        
        assert result["status"] == "success"
        assert "data" in result
        assert result["data"]["word_count"] == 6
        assert "metadata" in result
    
    def test_empty_data_validation(self):
        """Test validation with empty data"""
        request_data = {
            "data": "",
            "max_results": 100
        }
        
        with pytest.raises(ValidationError):
            analyze_data(request_data)
    
    def test_invalid_max_results(self):
        """Test validation with invalid max_results"""
        request_data = {
            "data": "Test data",
            "max_results": 2000  # Over limit
        }
        
        with pytest.raises(ValidationError):
            analyze_data(request_data)
    
    def test_sanitization(self):
        """Test input sanitization"""
        request_data = {
            "data": "<script>alert('xss')</script>",
            "max_results": 100
        }
        
        result = analyze_data(request_data)
        
        # Should be sanitized
        assert "<script>" not in result["data"]["original_data"]
    
    def test_structured_logging(self, caplog):
        """Test that structured logging is working"""
        request_data = {
            "data": "Test logging",
            "max_results": 100
        }
        
        analyze_data(request_data)
        
        # Check for structured log entries
        assert len(caplog.records) > 0
        log_record = caplog.records[0]
        assert hasattr(log_record, 'extra_fields')
```

#### **docs/api.md**
```markdown
# API Reference

## Overview

This MCP tool provides data analysis capabilities with structured input validation and error handling.

## Tools

### analyze_data

Analyzes text data for statistics and insights.

#### Input Schema

```json
{
  "type": "object",
  "properties": {
    "data": {
      "type": "string",
      "description": "Text data to analyze"
    },
    "options": {
      "type": "object",
      "description": "Optional analysis parameters",
      "properties": {
        "max_results": {
          "type": "integer",
          "description": "Maximum results to return",
          "minimum": 1,
          "maximum": 1000,
          "default": 100
        }
      }
    }
  },
  "required": ["data"]
}
```

#### Output Schema

```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["success", "error"]
    },
    "data": {
      "type": "object",
      "properties": {
        "length": {"type": "integer"},
        "word_count": {"type": "integer"},
        "line_count": {"type": "integer"},
        "analysis_timestamp": {"type": "string"}
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "tool_version": {"type": "string"},
        "processing_time_ms": {"type": "integer"}
      }
    }
  }
}
```

#### Error Responses

```json
{
  "status": "error",
  "error_code": "VALIDATION_ERROR",
  "message": "Data cannot be empty",
  "field": "data"
}
```

## Usage Examples

### Basic Analysis

```python
from my_mcp_tool import analyze_data

result = analyze_data({
    "data": "Hello world! This is a test.",
    "max_results": 100
})

print(result["data"]["word_count"])  # 6
```

### Advanced Analysis with Options

```python
result = analyze_data({
    "data": "This is a longer text with multiple sentences.",
    "options": {
        "max_results": 50,
        "include_metadata": True
    }
})
```

### Error Handling

```python
try:
    result = analyze_data(request_data)
    if result["status"] == "success":
        print("Analysis successful")
    else:
        print(f"Error: {result['error_code']}")
except ValidationError as e:
    print(f"Validation error: {e.message}")
except ProcessingError as e:
    print(f"Processing error: {e.message}")
```
```

#### **docs/examples/basic_usage.py**
```python
# docs/examples/basic_usage.py
"""
Basic usage example for MCP tool
"""

from my_mcp_tool import analyze_data

def main():
    """Example of basic tool usage"""
    
    # Simple analysis
    text = "Hello world! This is a basic example of the MCP tool."
    
    request = {
        "data": text,
        "max_results": 100
    }
    
    try:
        result = analyze_data(request)
        
        if result["status"] == "success":
            data = result["data"]
            print(f"Analysis Results:")
            print(f"  Character count: {data['length']}")
            print(f"  Word count: {data['word_count']}")
            print(f"  Line count: {data['line_count']}")
            print(f"  Timestamp: {data['analysis_timestamp']}")
        else:
            print(f"Analysis failed: {result['error_code']}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
```

## 🚀 Running Structure Analysis

### **Integrated Analysis**
```bash
# Run with enhanced audit (includes MCP structure)
python scripts/standalone/main.py "path/to/project" --debug
```

### **Standalone Analysis**
```bash
# MCP structure only
python mcp_structure_audit.py "path/to/project" --output mcp_structure

# With compliance badge generation
python mcp_structure_audit.py "path/to/project" --badge
```

### **Test Suite**
```bash
# Run structure tests
python -m pytest tests/test_mcp_structure.py -v
```

## 📊 Understanding Results

### **Structure Report Structure**
```json
{
  "project_path": "/path/to/project",
  "overall_score": 85,
  "compliance_level": "PARTIAL",
  "category_scores": {
    "source_code": {"score": 90, "max": 100},
    "configuration": {"score": 80, "max": 100},
    "testing": {"score": 70, "max": 100},
    "documentation": {"score": 60, "max": 100}
  },
  "requirement_results": {
    "src/mcp_tools/": {
      "compliant": true,
      "score": 100,
      "issues": [],
      "recommendations": []
    },
    "docs/": {
      "compliant": false,
      "score": 50,
      "issues": ["No documentation files found"],
      "recommendations": ["Add documentation files to docs/ directory"]
    }
  },
  "structure_analysis": {
    "directories": ["src", "tests", "config"],
    "files": ["pyproject.toml", "README.md"],
    "missing_required": ["docs/"],
    "missing_recommended": [".github/workflows/"]
  },
  "recommendations": [
    "[HIGH] Create docs/ directory",
    "[MEDIUM] Add comprehensive API documentation"
  ]
}
```

### **Structure Badge**
```markdown
![MCP Structure](https://img.shields.io/badge/MCP%20Structured-85%25-yellow)
```

## 🎯 Implementation Roadmap

### **Phase 1: REQUIRED Structure (Critical)**
1. **Create pyproject.toml** - Project configuration
2. **Setup src/mcp_tools/** - Tool package structure
3. **Add schemas.py** - Input validation schemas
4. **Create exceptions.py** - Custom error classes
5. **Setup logger.py** - Structured logging
6. **Add tests/** - Test suite structure
7. **Create README.md** - Project documentation
8. **Add .env.example** - Environment template

### **Phase 2: RECOMMENDED Structure (Enhancement)**
1. **Add validators.py** - Input validation functions
2. **Create config.py** - Configuration management
3. **Setup docs/** - Documentation directory
4. **Add API documentation** - docs/api.md
5. **Create examples/** - Usage examples
6. **Add comprehensive tests** - test_mcp_tools.py

### **Phase 3: OPTIONAL Structure (Optimization)**
1. **Add .github/workflows/** - CI/CD pipelines
2. **Create Dockerfile** - Containerization
3. **Add requirements-dev.txt** - Development dependencies
4. **Setup integration guides** - docs/integration.md

## 🔧 Best Practices

### **📝 Development Workflow**
1. **Run structure analysis** during development
2. **Fix REQUIRED issues** before committing
3. **Implement RECOMMENDED elements** incrementally
4. **Monitor structure score** over time
5. **Add structure checks** to CI/CD pipeline

### **🛡️ Security Considerations**
- **Validate all inputs** with Pydantic schemas
- **Sanitize user data** to prevent injection
- **Use environment variables** for secrets
- **Implement proper error handling** without information leakage
- **Follow principle of least privilege**

### **📈 Performance Optimization**
- **Use structured logging** for better debugging
- **Implement input validation** early in the pipeline
- **Create reusable schemas** for consistency
- **Add comprehensive tests** for reliability
- **Document all interfaces** for maintainability

## 🎉 Benefits of MCP Structure

### **🤖 AI Integration**
- **Standardized tool discovery** for AI systems
- **Consistent interfaces** across MCP tools
- **Professional packaging** for distribution
- **Clear documentation** for integration

### **🔧 Development Benefits**
- **Maintainable codebase** with logical organization
- **Easy testing** with standard structure
- **Professional documentation** layout
- **Configuration management** best practices

### **📊 Business Value**
- **Faster development** with proven patterns
- **Reduced onboarding time** for new developers
- **Better reliability** with standard structure
- **Easier maintenance** with clear organization

---

## 📞 Support

For MCP structure questions:
1. **Check this guide** for implementation examples
2. **Run structure analyzer** for specific recommendations
3. **Review test suite** for structure patterns
4. **Consult MCP documentation** for protocol details

**Remember**: MCP structure compliance ensures professional tool development and seamless AI integration! 🚀
