"""
MCP Audit Analyzer Tool - Main audit functionality for MCP integration
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from .schemas import AuditRequest, TOOL_SCHEMAS
from .validators import validate_project_path, validate_analysis_types
from .exceptions import AnalysisError, ValidationError
from .config import get_analysis_config, get_logging_config
from .logger import get_logger

# Import the actual audit analyzer from the core module
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from core.audit_analyzer import AuditAnalyzer
from core.dependency_analyzer import DependencyAnalyzer

logger = get_logger(__name__)


def analyze_project(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze project with proper validation and error handling
    
    Args:
        request_data: Dictionary containing analysis request
        
    Returns:
        Dictionary with analysis results
        
    Raises:
        ValidationError: If input data is invalid
        AnalysisError: If analysis fails
    """
    try:
        # Validate input using schema
        request = AuditRequest(**request_data)
        
        logger.info(
            "Starting project analysis",
            extra={
                "request_id": id(request_data),
                "project_path": request.project_path,
                "analysis_types": request.analysis_types,
                "options": request.options
            }
        )
        
        # Validate project path
        validated_path = validate_project_path(request.project_path)
        
        # Initialize analyzer
        analyzer = AuditAnalyzer(validated_path)
        
        # Run requested analysis types
        results = {}
        
        if "enhanced" in request.analysis_types:
            logger.info("Running enhanced analysis")
            enhanced_results = analyzer.run_full_analysis()
            results["enhanced"] = enhanced_results
        
        if "static" in request.analysis_types:
            logger.info("Running static analysis")
            from core.static_analyzer import StaticAnalyzer
            static_analyzer = StaticAnalyzer(validated_path)
            static_results = static_analyzer.analyze()
            results["static"] = static_results
        
        if "dependency" in request.analysis_types:
            logger.info("Running dependency analysis")
            dep_analyzer = DependencyAnalyzer(validated_path)
            dep_results = dep_analyzer.analyze_imports_and_usage()
            results["dependency"] = dep_results
        
        if "structure" in request.analysis_types:
            logger.info("Running MCP structure analysis")
            from core.mcp_structure_validator import MCPStructureValidator
            structure_validator = MCPStructureValidator(validated_path)
            structure_results = structure_validator.validate_structure()
            results["structure"] = structure_results
        
        # Generate summary
        total_findings = sum(
            len(findings) if isinstance(findings, list) else 0
            for findings in results.values()
            if isinstance(findings, dict)
        )
        
        analysis_result = {
            "status": "success",
            "project_path": validated_path,
            "analysis_types": request.analysis_types,
            "total_findings": total_findings,
            "results": results,
            "metadata": {
                "tool_version": "1.0.0",
                "analysis_timestamp": datetime.now().isoformat(),
                "config": get_analysis_config()
            }
        }
        
        logger.info(
            "Analysis completed successfully",
            extra={
                "request_id": id(request_data),
                "total_findings": total_findings,
                "analysis_types": list(results.keys())
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
        
    except AnalysisError as e:
        logger.error(
            "Analysis failed",
            extra={
                "request_id": id(request_data),
                "error": e.message,
                "analysis_type": e.analysis_type
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
        raise AnalysisError(f"Analysis failed: {e}", "general")


# Tool metadata for MCP discovery
TOOL_METADATA = {
    "name": "analyze_project",
    "description": "Comprehensive project analysis for AI engineering best practices",
    "schema": "AuditRequest",
    "version": "1.0.0",
    "author": "AI Auditor Team",
    "tags": ["analysis", "audit", "code-quality", "mcp-compliance"],
    "capabilities": [
        "enhanced_analysis",
        "static_analysis", 
        "dependency_analysis",
        "structure_validation"
    ]
}
