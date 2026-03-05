"""
Basic usage example for AI Auditor MCP tools
"""

from pathlib import Path
import sys

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.mcp_tools import analyze_project
from src.mcp_tools.exceptions import ValidationError, AnalysisError


def main():
    """Example of basic AI Auditor tool usage"""
    
    # Example 1: Basic enhanced analysis
    print("=== Example 1: Basic Enhanced Analysis ===")
    
    try:
        result = analyze_project({
            "project_path": str(Path(__file__).parent.parent.parent),
            "analysis_types": ["enhanced"]
        })
        
        if result["status"] == "success":
            findings = result["total_findings"]
            print(f"✅ Analysis complete: {findings} findings found")
            
            # Show breakdown by category
            if "results" in result and "enhanced" in result["results"]:
                enhanced = result["results"]["enhanced"]
                print(f"📊 Enhanced Analysis Results:")
                for category, finding_ids in enhanced.items():
                    if finding_ids:
                        print(f"  • {category}: {len(finding_ids)} findings")
        else:
            print(f"❌ Analysis failed: {result.get('error_code', 'Unknown error')}")
            
    except ValidationError as e:
        print(f"❌ Validation error: {e.message}")
        if e.field:
            print(f"   Field: {e.field}")
    except AnalysisError as e:
        print(f"❌ Analysis error: {e.message}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print()
    
    # Example 2: Analysis with options
    print("=== Example 2: Analysis with Options ===")
    
    try:
        result = analyze_project({
            "project_path": str(Path(__file__).parent.parent.parent),
            "analysis_types": ["enhanced", "dependency"],
            "options": {
                "max_files": 100,
                "include_recommendations": True
            }
        })
        
        if result["status"] == "success":
            total_findings = result["total_findings"]
            print(f"✅ Analysis complete: {total_findings} findings found")
            
            # Show analysis types performed
            if "analysis_types" in result:
                performed_types = result["analysis_types"]
                print(f"📋 Analysis types: {', '.join(performed_types)}")
        else:
            print(f"❌ Analysis failed: {result.get('error_code', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Example 3: Multiple analysis types
    print("=== Example 3: Multiple Analysis Types ===")
    
    try:
        result = analyze_project({
            "project_path": str(Path(__file__).parent.parent.parent),
            "analysis_types": ["enhanced", "structure", "dependency"]
        })
        
        if result["status"] == "success":
            print(f"✅ Comprehensive analysis complete")
            
            # Show results summary
            if "results" in result:
                for analysis_type, analysis_result in result["results"].items():
                    if isinstance(analysis_result, dict) and "total_findings" in analysis_result:
                        print(f"📊 {analysis_type.title()}: {analysis_result['total_findings']} findings")
                    elif isinstance(analysis_result, dict):
                        print(f"📊 {analysis_type.title()}: Analysis completed")
        else:
            print(f"❌ Analysis failed: {result.get('error_code', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    # Example 4: Error handling demonstration
    print("=== Example 4: Error Handling ===")
    
    # Demonstrate validation error
    try:
        result = analyze_project({
            "project_path": "",  # Empty path should fail validation
            "analysis_types": ["enhanced"]
        })
    except ValidationError as e:
        print(f"✅ Caught validation error as expected:")
        print(f"   Message: {e.message}")
        print(f"   Error Code: {e.error_code}")
        if e.field:
            print(f"   Field: {e.field}")
    
    # Demonstrate analysis error
    try:
        result = analyze_project({
            "project_path": "/nonexistent/path",  # Nonexistent path should fail
            "analysis_types": ["enhanced"]
        })
    except AnalysisError as e:
        print(f"✅ Caught analysis error as expected:")
        print(f"   Message: {e.message}")
        print(f"   Error Code: {e.error_code}")
        if hasattr(e, 'analysis_type'):
            print(f"   Analysis Type: {e.analysis_type}")


if __name__ == "__main__":
    main()
