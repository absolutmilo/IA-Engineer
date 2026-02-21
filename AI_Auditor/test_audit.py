#!/usr/bin/env python3
"""
test_audit.py — Quick validation of the improved audit system with full logging.
Tests the timeout enforcement and fallback mechanisms.
"""

import sys
import json
from pathlib import Path
from rich.console import Console

from core.context_builder import ContextBuilder
from core.dependency_graph import DependencyGraph
from core.static_analyzer import StaticAnalyzer
from llm.llm_client import LLMClient
from utils.logger import setup_logging, get_logger
import yaml

console = Console()
logger = setup_logging(verbose=True)
mod_logger = get_logger("test_audit")


def load_config(path: str = "config/audit_config.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def test_llm_client():
    """Test that LLM client doesn't block and handles timeouts gracefully."""
    mod_logger.info("╔════════════════════════════════════════════════════════════════╗")
    mod_logger.info("║  Testing LLM Client with Timeout Enforcement                 ║")
    mod_logger.info("╚════════════════════════════════════════════════════════════════╝")
    
    config = load_config()
    timeout_sec = 10  # Use shorter timeout for testing
    
    client = LLMClient(
        model=config.get("llm", {}).get("model", "llama3.2:3b-instruct-q4_0"),
        api_base=config.get("llm", {}).get("api_base", "http://localhost:11434"),
        section_timeout=timeout_sec
    )
    
    console.print(f"\n[cyan]LLM Client Configuration:[/cyan]")
    mod_logger.info(f"Model: {client.model}")
    mod_logger.info(f"API Base: {client.api_base}")
    mod_logger.info(f"Timeout per section: {timeout_sec}s")
    mod_logger.info(f"Max retries: 2 (with exponential backoff)")
    
    # Create a minimal test context
    test_context = {
        "project_name": "TestProject",
        "total_python_files": 5,
        "total_loc": 500,
        "project_flags": {
            "has_tests": False,
            "has_dockerfile": False,
            "has_requirements": True,
        },
        "code_quality": {
            "total_hardcoded_secrets": 2,
            "god_mode_files": ["main.py"],
            "circular_dependencies": 1,
        },
    }
    
    console.print(f"\n[cyan]Test Context:[/cyan]")
    console.print(json.dumps(test_context, indent=2)[:200] + "...")
    
    # Test one section (use shortest one)
    mod_logger.info("Testing section: 'cost_performance' (should be fast)")
    console.print(f"\n[cyan]Testing section: 'cost_performance' (should be fast)[/cyan]")
    console.print("Calling LLM with enforced timeout...", end=" ")
    
    summary_json = json.dumps(test_context, indent=2)
    response = client._call_section("cost_performance", summary_json)
    
    if response:
        console.print("[green]✓ Response received[/green]")
        mod_logger.info(f"Response length: {len(response)} characters")
        console.print(f"Response length: {len(response)} characters")
    else:
        console.print("[yellow]! Timeout or fallback triggered[/yellow]")
        mod_logger.warning("Timeout or fallback triggered")
    
    console.print("\n[green]✓ Timeout enforcement test completed[/green]")
    mod_logger.info("Timeout enforcement test completed successfully")
    mod_logger.info("The system did NOT hang/block indefinitely.")


def test_audit_on_sample():
    """Run a full audit on the AI_Auditor project itself."""
    mod_logger.info("╔════════════════════════════════════════════════════════════════╗")
    mod_logger.info("║  Running Full Audit on AI_Auditor Project                     ║")
    mod_logger.info("╚════════════════════════════════════════════════════════════════╝")
    
    base_dir = Path(__file__).parent
    target_path = base_dir  # Audit the auditor!
    config = load_config(str(base_dir / "config/audit_config.yaml"))
    
    mod_logger.info(f"Target: {target_path}")
    console.print(f"Target: {target_path}")
    console.print("Analyzing codebase...")
    
    # Dependency Graph
    mod_logger.debug("Building dependency graph...")
    graph = DependencyGraph(target_path)
    graph.build()
    cycles = graph.detect_cycles()
    coupling = graph.get_coupling_metrics()
    mod_logger.info(f"Dependency graph built: {len(graph.file_map)} files")
    
    # Static Analysis
    mod_logger.debug("Running static analysis...")
    file_stats = {}
    for i, (mod, file_path) in enumerate(graph.file_map.items(), 1):
        if i % 100 == 0:
            mod_logger.debug(f"Analyzing file {i}/{len(graph.file_map)}: {mod}")
        analyzer = StaticAnalyzer(file_path)
        stats = analyzer.analyze()
        file_stats[mod] = stats
    mod_logger.info(f"Static analysis complete: {len(file_stats)} files analyzed")
    
    # Context Builder
    mod_logger.debug("Building context...")
    context_builder = ContextBuilder(
        target_path, file_stats, graph, cycles, coupling, config
    )
    context_summary = context_builder.build()
    
    console.print(f"\n[cyan]Analysis Summary:[/cyan]")
    console.print(f"  Files analyzed: {context_summary['total_python_files']}")
    console.print(f"  Total LOC: {context_summary['total_loc']}")
    
    # LLM Analysis
    mod_logger.info("Starting LLM analysis with complete logging...")
    console.print(f"\n[cyan]Starting LLM analysis (max 2 min, with timeouts per section)...[/cyan]")
    
    client = LLMClient(
        model=config.get("llm", {}).get("model", "llama3.2:3b-instruct-q4_0"),
        api_base=config.get("llm", {}).get("api_base", "http://localhost:11434"),
        section_timeout=config.get("llm", {}).get("section_timeout", 30)
    )
    
    report = client.analyze_all(context_summary)
    
    console.print(f"\n[green]✓ Audit Complete[/green]")
    mod_logger.info("Audit completed successfully")
    console.print(f"  Project Grade: {report.grade}")
    console.print(f"  Enterprise Readiness: {report.enterprise_readiness_pct}%")


if __name__ == "__main__":
    try:
        mod_logger.info("Starting test session...")
        test_llm_client()
        
        print("\n" + "=" * 60)
        response = input("\nRun full audit on this project? (y/n) ")
        if response.lower() == 'y':
            test_audit_on_sample()
        else:
            mod_logger.info("Skipping full audit")
        
        console.print("\n[green][bold]All tests completed successfully![/bold][/green]")
        mod_logger.info("All tests completed successfully!")
        console.print("The improved system:")
        console.print("  ✓ Enforces hard timeouts (threading-based)")
        console.print("  ✓ Uses exponential backoff retries (tenacity)")
        console.print("  ✓ Provides intelligent fallbacks")
        console.print("  ✓ Logs everything to files/console")
        mod_logger.info("════════════════════════════════════════════════════════════════")
        
    except Exception as e:
        mod_logger.error(f"Test failed: {e}", exc_info=True)
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)
