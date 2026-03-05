#!/usr/bin/env python3
"""
Dependency Audit - Advanced dependency analysis
Identifies unused imports, decomposable libraries, and dependency bloat
"""

import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import json

from core.dependency_analyzer import DependencyAnalyzer
from utils.logger import setup_logging, get_logger

def main():
    parser = argparse.ArgumentParser(description="Advanced Dependency Analysis")
    parser.add_argument("project_path", help="Path to project to analyze")
    parser.add_argument("--output", "-o", default="dependency_analysis", help="Output directory")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(verbose=args.debug)
    logger = get_logger(__name__)
    
    console = Console()
    
    console.print(Panel.fit(
        "[bold blue]📦 Advanced Dependency Analysis[/bold blue]\n"
        "[dim]Identify unused imports, decomposable libraries, and dependency bloat[/dim]"
    ))
    
    # Initialize analyzer
    analyzer = DependencyAnalyzer(args.project_path)
    
    console.print(f"\n[bold]Analyzing project:[/bold] {args.project_path}")
    
    # Run analysis
    console.print("\n[bold yellow]🔍 Analyzing Dependencies...[/bold yellow]")
    
    try:
        results = analyzer.analyze_imports_and_usage()
        report = analyzer.generate_dependency_report()
        
        # Display results
        console.print("\n[bold green]📊 Analysis Results:[/bold green]")
        
        # Summary table
        summary_table = Table(title="Project Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Count", justify="right", style="bold")
        
        summary = report['summary']
        summary_table.add_row("Files Analyzed", str(summary['total_files_analyzed']))
        summary_table.add_row("Total Imports", str(summary['total_imports']))
        summary_table.add_row("External Libraries", str(summary['external_libraries']))
        summary_table.add_row("Internal Modules", str(summary['internal_modules']))
        summary_table.add_row("Defined Functions", str(summary['defined_functions']))
        summary_table.add_row("Defined Classes", str(summary['defined_classes']))
        
        console.print(summary_table)
        
        # Findings breakdown
        console.print("\n[bold red]🚨 Findings Breakdown:[/bold red]")
        
        findings_table = Table()
        findings_table.add_column("Category", style="cyan")
        findings_table.add_column("Count", justify="right", style="bold")
        
        for category, finding_ids in results.items():
            findings_table.add_row(category.replace("_", " ").title(), str(len(finding_ids)))
        
        console.print(findings_table)
        
        # Most used libraries
        if report['library_usage']['most_used']:
            console.print("\n[bold cyan]📚 Most Used Libraries:[/bold cyan]")
            for lib, count in list(report['library_usage']['most_used'].items())[:5]:
                console.print(f"  • {lib}: {count} imports")
        
        # Dependency details
        console.print("\n[bold blue]📈 Library Usage Analysis:[/bold blue]")
        
        usage_data = report['library_usage']
        console.print(f"  Total unique libraries: {usage_data['total_unique_libraries']}")
        
        if usage_data['least_used']:
            console.print("\n[dim]Least used libraries (potential cleanup candidates):[/dim]")
            for lib, count in usage_data['least_used'][:3]:
                console.print(f"  • {lib}: {count} imports")
        
        # Files with most imports
        if report['dependency_graph']['files_with_most_imports']:
            console.print("\n[bold yellow]📁 Files with Most Imports:[/bold yellow]")
            for file_path, count in report['dependency_graph']['files_with_most_imports'][:3]:
                console.print(f"  • {file_path}: {count} imports")
        
        # Export results
        output_path = Path(args.output)
        output_path.mkdir(exist_ok=True)
        
        # Export detailed findings
        with open(output_path / "dependency_findings.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        # Export full report
        with open(output_path / "dependency_report.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        console.print(f"\n[bold]📁 Results exported to:[/bold] {output_path}")
        console.print(f"[dim]• dependency_findings.json - Detailed findings[/dim]")
        console.print(f"[dim]• dependency_report.json - Full analysis report[/dim]")
        
        # Show top recommendations
        console.print("\n[bold green]💡 Top Recommendations:[/bold green]")
        
        unused_count = len(results.get("unused_imports", []))
        decomposable_count = len(results.get("decomposable_libraries", []))
        unused_deps_count = len(results.get("unused_dependencies", []))
        
        if unused_count > 0:
            console.print(f"  🧹 Remove {unused_count} unused imports to clean up code")
        
        if decomposable_count > 0:
            console.print(f"  ⚖️  Review {decomposable_count} libraries for potential optimization")
        
        if unused_deps_count > 0:
            console.print(f"  📦 Remove {unused_deps_count} unused dependencies from requirements.txt")
        
        if unused_count == 0 and decomposable_count == 0 and unused_deps_count == 0:
            console.print("  ✅ No dependency issues found - well maintained!")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Analysis failed:[/bold red] {e}")
        if args.debug:
            import traceback
            console.print(traceback.format_exc())

if __name__ == "__main__":
    main()
