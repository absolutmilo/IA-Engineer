"""
MCP Tool Schemas - Input validation schemas for AI Auditor tools
"""

from pydantic import BaseModel, validator
from typing import Dict, List, Any, Optional
from pathlib import Path


class AuditRequest(BaseModel):
    """Schema for audit analysis requests"""
    project_path: str
    analysis_types: List[str] = ["enhanced", "static", "llm"]
    options: Optional[Dict[str, Any]] = {}
    
    @validator('project_path')
    def validate_project_path(cls, v):
        if not v.strip():
            raise ValueError('Project path cannot be empty')
        path = Path(v)
        if not path.exists():
            raise ValueError(f'Project path does not exist: {v}')
        return str(path.absolute())
    
    @validator('analysis_types')
    def validate_analysis_types(cls, v):
        allowed_types = ["enhanced", "static", "llm", "dependency", "structure"]
        invalid_types = [t for t in v if t not in allowed_types]
        if invalid_types:
            raise ValueError(f'Invalid analysis types: {invalid_types}')
        return v


class StructureAnalysisRequest(BaseModel):
    """Schema for MCP structure analysis requests"""
    project_path: str
    compliance_level: Optional[str] = None
    include_recommendations: bool = True
    
    @validator('project_path')
    def validate_project_path(cls, v):
        if not v.strip():
            raise ValueError('Project path cannot be empty')
        return v


class DependencyAnalysisRequest(BaseModel):
    """Schema for dependency analysis requests"""
    project_path: str
    include_unused: bool = True
    include_decomposable: bool = True
    
    @validator('project_path')
    def validate_project_path(cls, v):
        if not v.strip():
            raise ValueError('Project path cannot be empty')
        return v


# Tool schema exports for MCP integration
TOOL_SCHEMAS = {
    "audit": AuditRequest,
    "structure_analysis": StructureAnalysisRequest,
    "dependency_analysis": DependencyAnalysisRequest,
}
