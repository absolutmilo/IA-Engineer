import argparse
import sys
import time
from pathlib import Path
from rich.console import Console
from rich.table import Table
import yaml

# Core
from core.static_analyzer import StaticAnalyzer, FileStats
from core.dependency_graph import DependencyGraph
from core.context_builder import ContextBuilder

# LLM
from llm.llm_client import LLMClient
from llm.structure import AuditReport
from utils.reporter import Reporter
from utils.logger import setup_logging, get_logger

console = Console()
logger = None  # Will be initialized in main()


def load_config(path: str = "config/audit_config.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def render_scorecard(report: AuditReport, context_summary: dict) -> None:
    grade = report.grade or "N/A"
    readiness = report.enterprise_readiness_pct

    GRADE_COLOR = {
        "A+": "bright_green", "A": "green", "B+": "green", "B": "cyan",
        "C": "yellow", "D+": "yellow", "D": "red", "F": "bright_red", "N/A": "white",
    }
    color = GRADE_COLOR.get(grade, "white")

    table = Table(title=f"[bold]Audit Scorecard: {report.project_name}[/bold]",
                  show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Result", style="white")

    table.add_row("Overall Grade", f"[{color}]{grade}[/{color}]")
    table.add_row("Enterprise Readiness", f"{readiness}%")

    cq = context_summary.get("code_quality", {})
    table.add_row("Hardcoded Secrets", str(cq.get("total_hardcoded_secrets", 0)))
    table.add_row("Circular Dependencies", str(cq.get("circular_dependencies", 0)))
    table.add_row("God-Mode Files", str(len(cq.get("god_mode_files", []))))

    section_verdicts = [
        ("Architecture", report.architecture_analysis.verdict),
        ("LLM Integration", report.llm_integration.verdict),
        ("Security", report.security.verdict),
        ("MLOps/Deployment", report.mlops_deployment.verdict),
        ("Observability", report.observability.verdict),
    ]
    for name, verdict in section_verdicts:
        VERDICT_COLOR = {
            "CRITICAL": "red", "POOR": "red", "WEAK": "yellow",
            "MIXED": "yellow", "GOOD": "green", "EXCELLENT": "bright_green",
        }
        vc = VERDICT_COLOR.get(verdict, "white")
        table.add_row(name, f"[{vc}]{verdict}[/{vc}]")

    console.print()
    console.print(table)
    console.print()

    if report.top_critical_improvements:
        console.print("[bold red]Top Critical Improvements:[/bold red]")
        for i, item in enumerate(report.top_critical_improvements[:5], 1):
            console.print(f"  {i}. {item}")
        console.print()


def main():
    global logger
    
    # Initialize logging
    verbose = "--debug" in sys.argv
    logger = setup_logging(verbose=verbose)
    
    logger.info("╔════════════════════════════════════════════════════════════════╗")
    logger.info("║          AI ENGINEERING GUARDIAN — AUDIT SYSTEM START          ║")
    logger.info("╚════════════════════════════════════════════════════════════════╝")
    
    parser = argparse.ArgumentParser(
        description="AI Engineering Guardian — Principal Architect Audit"
    )
    parser.add_argument("path", help="Path to the project directory to audit")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    target_path = Path(args.path).resolve()
    if not target_path.exists():
        logger.error(f"Target path does not exist: {target_path}")
        console.print(f"[red]Error: Path '{target_path}' does not exist.[/red]")
        sys.exit(1)

    project_name = target_path.name
    logger.info(f"Target project: {project_name}")
    logger.info(f"Target path: {target_path}")
    console.print(f"\n[bold green]🔍 Starting Audit: {project_name}[/bold green]")
    console.print(f"   Target: {target_path}\n")

    # ── Config ─────────────────────────────────────────────────────────────
    logger.debug("Loading configuration...")
    base_dir = Path(__file__).parent
    try:
        config = load_config(str(base_dir / "config/audit_config.yaml"))
        logger.info(f"Configuration loaded successfully")
        logger.debug(f"LLM model: {config.get('llm', {}).get('model')}")
        logger.debug(f"LLM timeout per section: {config.get('llm', {}).get('section_timeout')}s")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}", exc_info=True)
        raise

    # ── Dependency Graph ───────────────────────────────────────────────────
    logger.info("Starting dependency graph analysis...")
    console.print("[blue][*] Building Dependency Graph...[/blue]")
    try:
        graph = DependencyGraph(target_path)
        logger.debug("DependencyGraph initialized")
        
        graph.build()
        logger.info(f"Dependency graph built with {len(graph.file_map)} files")
        
        cycles = graph.detect_cycles()
        logger.info(f"Circular dependency detection: {len(cycles)} cycle(s) found")
        if cycles:
            for i, cycle in enumerate(cycles[:5], 1):
                logger.debug(f"  Cycle {i}: {' -> '.join(cycle)}")
        
        coupling = graph.get_coupling_metrics()
        logger.debug(f"Coupling metrics calculated for {len(coupling)} modules")

        if cycles:
            console.print(f"   [yellow]⚠ {len(cycles)} circular dependency(ies) detected[/yellow]")
        else:
            console.print("   [green]✓ No circular dependencies[/green]")
    except Exception as e:
        logger.error(f"Dependency graph analysis failed: {e}", exc_info=True)
        raise

    # ── Static Analysis ────────────────────────────────────────────────────
    logger.info("Starting static analysis...")
    console.print("[blue][*] Running Static Analysis...[/blue]")
    try:
        file_stats: dict[str, FileStats] = {}
        for i, (mod, file_path) in enumerate(graph.file_map.items(), 1):
            logger.debug(f"Analyzing file {i}/{len(graph.file_map)}: {mod}")
            analyzer = StaticAnalyzer(file_path)
            stats = analyzer.analyze()
            file_stats[mod] = stats
            logger.debug(f"  LOC: {stats.loc}, Functions: {len(stats.functions)}, Classes: {len(stats.classes)}")

        logger.info(f"Static analysis complete: {len(file_stats)} Python files analyzed")
        console.print(f"   [green]✓ Analyzed {len(file_stats)} Python files[/green]")
    except Exception as e:
        logger.error(f"Static analysis failed: {e}", exc_info=True)
        raise

    # ── Context Builder ────────────────────────────────────────────────────
    logger.info("Building metadata summary...")
    console.print("[blue][*] Building Metadata Summary...[/blue]")
    try:
        builder = ContextBuilder(
            root_path=target_path,
            file_stats=file_stats,
            graph=graph,
            cycles=cycles,
            coupling=coupling,
            config=config,
        )
        logger.debug("ContextBuilder initialized")
        
        context_summary = builder.build()
        logger.info("Context summary built successfully")
        
        total_loc = context_summary.get("total_loc", 0)
        total_files = context_summary.get("total_python_files", 0)
        logger.debug(f"Summary: {total_loc} LOC, {total_files} files")
        logger.debug(f"Code quality flags: {context_summary.get('code_quality', {})}")
        logger.debug(f"AI/ML profile: {context_summary.get('ai_ml_profile', {})}")
        
        console.print(f"   [green]✓ Summary ready ({total_loc} LOC across {total_files} files)[/green]")
    except Exception as e:
        logger.error(f"Context building failed: {e}", exc_info=True)
        raise

    # ── LLM Analysis — Section by Section ──────────────────────────────────
    llm_cfg = config.get("llm", {})
    model = llm_cfg.get("model", "llama3.2:3b-instruct-q4_0")
    api_base = llm_cfg.get("api_base", "http://localhost:11434")
    section_timeout = llm_cfg.get("section_timeout", 30)
    
    logger.info(f"Initializing LLM client")
    logger.info(f"  Model: {model}")
    logger.info(f"  API Base: {api_base}")
    logger.info(f"  Section timeout: {section_timeout}s")
    
    console.print(
        f"\n[bold purple][*] Consulting Principal Architect (LLM: {model})...[/bold purple]\n"
    )
    
    try:
        llm_client = LLMClient(
            model=model,
            api_base=api_base,
            section_timeout=section_timeout,
        )
        logger.debug("LLMClient initialized successfully")
        logger.info("Starting full audit analysis (12 sections)...")
        
        start_time = time.time()
        report = llm_client.analyze_all(context_summary)
        elapsed = time.time() - start_time
        
        logger.info(f"LLM analysis complete in {elapsed:.1f}s")
        logger.info(f"Final grade: {report.grade}")
        logger.info(f"Enterprise readiness: {report.enterprise_readiness_pct}%")
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}", exc_info=True)
        raise

    # ── Scorecard ──────────────────────────────────────────────────────────
    logger.debug("Rendering scorecard...")
    render_scorecard(report, context_summary)

    # ── Reports ────────────────────────────────────────────────────────────
    logger.info("Generating and saving reports...")
    console.print("[blue][*] Generating Reports...[/blue]")
    try:
        reporter = Reporter(target_path / "audit_reports")
        logger.debug(f"Reporter initialized with output dir: {target_path / 'audit_reports'}")

        safe_name = project_name.replace(" ", "_")
        json_path = reporter.save_json(report, f"audit_{safe_name}.json")
        logger.info(f"JSON report saved: {json_path}")
        
        md_path = reporter.save_markdown(report, f"audit_{safe_name}.md", context_summary)
        logger.info(f"Markdown report saved: {md_path}")

        console.print(f"\n[bold green]✅ Audit Complete![/bold green]")
        console.print(f"   📄 Markdown Report: {md_path}")
        console.print(f"   📦 JSON Data:       {json_path}\n")
        
        logger.info("═" * 70)
        logger.info("AUDIT COMPLETED SUCCESSFULLY")
        logger.info(f"Reports saved to: {target_path / 'audit_reports'}")
        logger.info("═" * 70)
    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
