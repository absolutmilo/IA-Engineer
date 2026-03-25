#!/usr/bin/env python3
"""
Enhanced Audit - Systematic finding capture with file/line tracking
"""

import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import json

from core.audit_analyzer import AuditAnalyzer
from utils.logger import setup_logging, get_logger
from core.findings_tracker import Severity

def main():
    parser = argparse.ArgumentParser(description="Enhanced AI Engineering Audit")
    parser.add_argument("project_path", help="Path to project to audit")
    parser.add_argument("--output", "-o", default="enhanced_findings", help="Output directory")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(verbose=args.debug)
    logger = get_logger(__name__)
    
    console = Console()
    
    console.print(Panel.fit(
        "[bold blue]🔍 Enhanced AI Engineering Audit[/bold blue]\n"
        "[dim]Systematic finding capture with precise file/line tracking[/dim]"
    ))
    
    # Initialize analyzer
    analyzer = AuditAnalyzer(args.project_path)
    
    console.print(f"\n[bold]Analyzing project:[/bold] {args.project_path}")
    console.print(f"[dim]Found {len(analyzer.python_files)} Python files[/dim]")
    
    # Run analysis
    console.print("\n[bold yellow]🔍 Running Analysis...[/bold yellow]")
    
    results = analyzer.run_full_analysis()
    
    # Display results
    console.print("\n[bold green]📊 Analysis Results:[/bold green]")
    
    table = Table(title="Findings Summary")
    table.add_column("Category", style="cyan")
    table.add_column("Count", justify="right", style="bold")
    
    for category, finding_ids in results.items():
        table.add_row(category.replace("_", " ").title(), str(len(finding_ids)))
    
    console.print(table)
    
    # Show top findings
    console.print("\n[bold red]🚨 Critical Findings:[/bold red]")
    
    critical_findings = analyzer.tracker.get_by_severity(Severity.CRITICAL)
    if critical_findings:
        for finding in critical_findings[:5]:  # Show top 5
            console.print(f"\n[bold]{finding.id}:[/bold] {finding.title}")
            console.print(f"[dim]📍 {finding.locations[0].file_path}:{finding.locations[0].line_number}[/dim]")
            console.print(f"[dim]💡 {finding.recommendation}[/dim]")
    else:
        console.print("[green]✅ No critical findings found![/green]")
    
    # Export findings
    console.print(f"\n[bold]📁 Exporting findings to:[/bold] {args.output}")
    analyzer.export_findings(args.output)
    
    # Show roadmap
    roadmap = analyzer.tracker.generate_roadmap()
    console.print("\n[bold blue]🗺️  Implementation Roadmap:[/bold blue]")
    
    for phase, items in roadmap.items():
        if items:
            console.print(f"\n[bold]{phase}:[/bold]")
            for item in items[:3]:  # Show top 3 per phase
                console.print(f"  • {item}")
            if len(items) > 3:
                console.print(f"  [dim]... and {len(items) - 3} more[/dim]")
    
    console.print(f"\n[bold green]✅ Enhanced audit complete![/bold green]")
    console.print(f"[dim]Check {args.output}/findings.json for detailed results[/dim]")

if __name__ == "__main__":
    main()
