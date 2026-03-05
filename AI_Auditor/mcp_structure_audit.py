#!/usr/bin/env python3
"""
MCP Structure Audit - Validates Model Context Protocol project structure
Ensures projects follow MCP folder organization standards
"""

import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import json

from core.mcp_structure_validator import MCPStructureValidator, StructureComplianceLevel
from utils.logger import setup_logging, get_logger

def main():
    parser = argparse.ArgumentParser(description="MCP Project Structure Analysis")
    parser.add_argument("project_path", help="Path to project to analyze")
    parser.add_argument("--output", "-o", default="mcp_structure", help="Output directory")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--badge", action="store_true", help="Generate structure compliance badge")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(verbose=args.debug)
    logger = get_logger(__name__)
    
    console = Console()
    
    console.print(Panel.fit(
        "[bold bright_blue]🏗️ MCP Project Structure Analysis[/bold bright_blue]\n"
        "[dim]Validate Model Context Protocol project organization standards[/dim]"
    ))
    
    # Initialize validator
    validator = MCPStructureValidator(args.project_path)
    
    console.print(f"\n[bold]Analyzing project structure:[/bold] {args.project_path}")
    
    # Run analysis with progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing MCP structure...", total=None)
        
        try:
            results = validator.validate_structure()
            progress.update(task, description="Analysis complete!")
        except Exception as e:
            console.print(f"\n[bold red]❌ Analysis failed:[/bold red] {e}")
            if args.debug:
                import traceback
                console.print(traceback.format_exc())
            return
    
    # Display results
    console.print("\n[bold green]📊 MCP Structure Results:[/bold green]")
    
    # Overall compliance
    score = results["overall_score"]
    level = results["compliance_level"]
    
    # Color coding for compliance level
    level_colors = {
        StructureComplianceLevel.COMPLIANT: "bright_green",
        StructureComplianceLevel.PARTIAL: "yellow", 
        StructureComplianceLevel.NON_COMPLIANT: "red",
    }
    
    level_color = level_colors.get(level, "white")
    
    # Summary table
    summary_table = Table(title="Structure Compliance Overview")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Result", justify="right", style="bold")
    
    summary_table.add_row("Overall Score", f"{score}%")
    summary_table.add_row("Compliance Level", f"[{level_color}]{level.value}[/{level_color}]")
    summary_table.add_row("Requirements Analyzed", str(len(results["requirement_results"])))
    
    console.print(summary_table)
    
    # Category breakdown
    console.print("\n[bold cyan]📈 Compliance by Category:[/bold cyan]")
    
    category_table = Table()
    category_table.add_column("Category", style="cyan")
    category_table.add_column("Score", justify="right", style="bold")
    category_table.add_column("Status", justify="center")
    
    for category, scores in results["category_scores"].items():
        cat_score = int((scores["score"] / scores["max"]) * 100) if scores["max"] > 0 else 0
        
        if cat_score >= 90:
            status = "✅"
            status_style = "bright_green"
        elif cat_score >= 70:
            status = "⚠️"
            status_style = "yellow"
        else:
            status = "❌"
            status_style = "red"
        
        category_table.add_row(
            category.replace("_", " ").title(),
            f"{cat_score}%",
            f"[{status_style}]{status}[/{status_style}]"
        )
    
    console.print(category_table)
    
    # Requirement details
    console.print("\n[bold yellow]📋 Structure Requirements:[/bold yellow]")
    
    req_table = Table()
    req_table.add_column("Path", style="dim")
    req_table.add_column("Description", style="cyan")
    req_table.add_column("Level", justify="center")
    req_table.add_column("Status", justify="center")
    
    for req_path, result in results["requirement_results"].items():
        # Find requirement details
        requirement = next((r for r in validator.requirements if r.path == req_path), None)
        if not requirement:
            continue
        
        # Status icon
        if result["compliant"]:
            status = "✅"
            status_style = "bright_green"
        else:
            status = "❌"
            status_style = "red"
        
        # Level color
        level_colors = {
            "REQUIRED": "red",
            "RECOMMENDED": "yellow",
            "OPTIONAL": "dim"
        }
        level_color = level_colors.get(requirement.level, "white")
        
        req_table.add_row(
            req_path,
            requirement.description,
            f"[{level_color}]{requirement.level}[/{level_color}]",
            f"[{status_style}]{status}[/{status_style}]"
        )
    
    console.print(req_table)
    
    # Current structure analysis
    structure = results["structure_analysis"]
    console.print("\n[bold blue]📁 Current Project Structure:[/bold blue]")
    
    if structure["directories"]:
        console.print("\n[dim]Directories:[/dim]")
        for directory in sorted(structure["directories"]):
            console.print(f"  📁 {directory}")
    
    if structure["files"]:
        console.print("\n[dim]Files:[/dim]")
        for file in sorted(structure["files"]):
            console.print(f"  📄 {file}")
    
    # Missing items
    if structure["missing_required"]:
        console.print("\n[bold red]❌ Missing Required:[/bold red]")
        for item in structure["missing_required"]:
            console.print(f"  🚫 {item}")
    
    if structure["missing_recommended"]:
        console.print("\n[bold yellow]⚠️ Missing Recommended:[/bold yellow]")
        for item in structure["missing_recommended"]:
            console.print(f"  ⚠️ {item}")
    
    # Issues and recommendations
    if results["recommendations"]:
        console.print("\n[bold red]🚨 Priority Recommendations:[/bold red]")
        
        # Group by priority
        high_priority = [rec for rec in results["recommendations"] if "[HIGH]" in rec]
        medium_priority = [rec for rec in results["recommendations"] if "[MEDIUM]" in rec]
        
        if high_priority:
            console.print("\n[bold red]High Priority:[/bold red]")
            for rec in high_priority:
                console.print(f"  • {rec.replace('[HIGH] ', '')}")
        
        if medium_priority:
            console.print("\n[bold yellow]Medium Priority:[/bold yellow]")
            for rec in medium_priority:
                console.print(f"  • {rec.replace('[MEDIUM] ', '')}")
    
    # Export results
    output_path = Path(args.output)
    output_path.mkdir(exist_ok=True)
    
    # Export detailed report
    validator.export_structure_report(str(output_path))
    
    # Generate compliance badge if requested
    if args.badge:
        badge = validator.generate_structure_badge()
        badge_file = output_path / "mcp_structure_badge.md"
        with open(badge_file, 'w') as f:
            f.write(badge)
        console.print(f"\n[bold]🏷️ Structure compliance badge saved to:[/bold] {badge_file}")
    
    console.print(f"\n[bold]📁 Results exported to:[/bold] {output_path}")
    console.print(f"[dim]• mcp_structure_report.json - Detailed structure analysis[/dim]")
    
    # Structure guidance
    console.print("\n[bold blue]💡 MCP Structure Guidance:[/bold blue]")
    
    if level == StructureComplianceLevel.COMPLIANT:
        console.print("  ✅ Excellent! Your project follows MCP structure standards")
        console.print("  🎉 Ready for professional MCP tool development")
    elif level == StructureComplianceLevel.PARTIAL:
        console.print("  ⚠️ Good foundation! Address missing requirements")
        console.print("  📈 Focus on REQUIRED level structure elements first")
    else:
        console.print("  ❌ Significant restructuring needed for MCP compliance")
        console.print("  🔧 Start with REQUIRED level structure elements")
        console.print("  📚 Follow MCP project organization guidelines")
    
    console.print("\n[dim]MCP structure ensures:[/dim]")
    console.print("[dim]• Proper Python package organization[/dim]")
    console.print("[dim]• Clear separation of concerns[/dim]")
    console.print("[dim]• Standardized configuration management[/dim]")
    console.print("[dim]• Comprehensive testing structure[/dim]")
    console.print("[dim]• Professional documentation organization[/dim]")
    console.print("[dim]• Development tool integration[/dim]")
    
    # Show ideal structure example
    console.print("\n[bold magenta]📋 Ideal MCP Project Structure:[/bold magenta]")
    console.print("""
[dim]my-mcp-tool/
├── pyproject.toml              # Project configuration
├── README.md                   # Project documentation
├── .env.example               # Environment template
├── src/                       # Source code
│   ├── __init__.py
│   └── mcp_tools/            # MCP tools package
│       ├── __init__.py         # Tool exports
│       ├── schemas.py           # Input schemas
│       ├── validators.py        # Input validation
│       ├── exceptions.py        # Custom exceptions
│       ├── config.py           # Configuration
│       ├── logger.py           # Logging
│       └── tool_*.py          # Tool implementations
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_mcp_tools.py    # Tool tests
│   └── conftest.py          # Test configuration
├── config/                     # Configuration files
├── docs/                       # Documentation
│   ├── api.md               # API reference
│   ├── examples/             # Usage examples
│   └── integration.md        # Integration guide
├── .github/                    # Development tools
│   └── workflows/           # CI/CD workflows
├── Dockerfile                  # Containerization
├── requirements.txt            # Dependencies
└── requirements-dev.txt        # Development dependencies[/dim]""")

if __name__ == "__main__":
    main()
