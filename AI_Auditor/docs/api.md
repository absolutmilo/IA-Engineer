# AI Auditor API Reference

## Overview

The AI Auditor provides MCP-compliant tools for comprehensive project analysis and code quality assessment.

## Tools

### analyze_project

Comprehensive project analysis for AI engineering best practices.

#### Input Schema

```json
{
  "type": "object",
  "properties": {
    "project_path": {
      "type": "string",
      "description": "Path to the project directory to analyze"
    },
    "analysis_types": {
      "type": "array",
      "description": "Types of analysis to perform",
      "items": {
        "type": "string",
        "enum": ["enhanced", "static", "dependency", "structure", "mcp_compliance"]
      }
    },
    "options": {
      "type": "object",
      "description": "Optional analysis parameters",
      "properties": {
        "max_files": {
          "type": "integer",
          "description": "Maximum number of files to analyze",
          "minimum": 1,
          "maximum": 1000
        }
      }
    }
  },
  "required": ["project_path", "analysis_types"]
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
    "project_path": {
      "type": "string",
      "description": "Validated absolute project path"
    },
    "analysis_types": {
      "type": "array",
      "description": "Analysis types that were performed"
    },
    "total_findings": {
      "type": "integer",
      "description": "Total number of findings across all analysis types"
    },
    "results": {
      "type": "object",
      "description": "Detailed results for each analysis type"
    },
    "metadata": {
      "type": "object",
      "properties": {
        "tool_version": {"type": "string"},
        "analysis_timestamp": {"type": "string"},
        "config": {"type": "object"}
      }
    }
  }
}
```

#### Error Responses

```json
{
  "status": "error",
  "error_code": "VALIDATION_ERROR_PROJECT_PATH",
  "message": "Project path does not exist: /nonexistent/path",
  "field": "project_path"
}
```

```json
{
  "status": "error", 
  "error_code": "ANALYSIS_ERROR_STATIC",
  "message": "Static analysis failed: permission denied",
  "analysis_type": "static"
}
```

## Usage Examples

### Basic Analysis

```python
from src.mcp_tools import analyze_project

result = analyze_project({
    "project_path": "/path/to/your/project",
    "analysis_types": ["enhanced"]
})

if result["status"] == "success":
    findings = result["total_findings"]
    print(f"Analysis complete: {findings} findings found")
else:
    print(f"Analysis failed: {result['error_code']}")
```

### Advanced Analysis with Options

```python
result = analyze_project({
    "project_path": "/path/to/your/project",
    "analysis_types": ["enhanced", "dependency", "structure"],
    "options": {
        "max_files": 500,
        "include_recommendations": True
    }
})
```

### Multiple Analysis Types

```python
result = analyze_project({
    "project_path": "/path/to/your/project",
    "analysis_types": ["enhanced", "static", "dependency", "structure"]
})
```

## Error Handling

### Validation Errors

```python
from src.mcp_tools.exceptions import ValidationError

try:
    result = analyze_project(request_data)
except ValidationError as e:
    print(f"Validation error: {e.message}")
    if e.field:
        print(f"Field: {e.field}")
```

### Analysis Errors

```python
from src.mcp_tools.exceptions import AnalysisError

try:
    result = analyze_project(request_data)
except AnalysisError as e:
    print(f"Analysis error: {e.message}")
    if e.analysis_type:
        print(f"Analysis type: {e.analysis_type}")
```

## Configuration

### Environment Variables

The tool supports the following environment variables:

- `AI_AUDITOR_LLM_MODEL`: LLM model name
- `AI_AUDITOR_LLM_API_BASE`: LLM API base URL
- `AI_AUDITOR_MAX_FILE_SIZE`: Maximum file size for analysis
- `AI_AUDITOR_LOG_LEVEL`: Logging level
- `AI_AUDITOR_ENABLE_MCP_VALIDATION`: Enable MCP structure validation

### Configuration File

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
# Edit .env with your values
```

## Integration

### MCP Integration

The tool follows MCP standards:

- **Structured input validation** with Pydantic schemas
- **Comprehensive error handling** with specific error codes
- **Structured logging** with JSON formatting
- **Environment-based configuration** management
- **Professional documentation** with examples

### AI System Integration

```python
# Import the tool
from src.mcp_tools import analyze_project, TOOL_METADATA

# Use in AI workflows
if TOOL_METADATA["capabilities"]["enhanced_analysis"]:
    result = analyze_project({
        "project_path": project_dir,
        "analysis_types": ["enhanced"]
    })
```

## Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_mcp_tools.py

# Run with coverage
python -m pytest --cov=src tests/
```

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run with debug logging
AI_AUDITOR_LOG_LEVEL=DEBUG python -m src.mcp_tools.audit_analyzer
```
