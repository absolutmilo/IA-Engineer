"""
reporter.py — Rich Markdown report generator.
Produces the 12-section format matching the target example report.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from llm.structure import AuditReport, SectionAudit  # type: ignore


VERDICT_EMOJI = {
    "CRITICAL":  "🔴 **CRITICAL**",
    "POOR":      "🔴 **POOR**",
    "WEAK":      "🟡 **WEAK**",
    "MIXED":     "🟡 **MIXED**",
    "GOOD":      "🟢 **GOOD**",
    "EXCELLENT": "🟢 **EXCELLENT**",
    "UNKNOWN":   "⚪ **UNAVAILABLE**",
}

GRADE_EMOJI = {
    "A+": "🏆", "A": "🥇", "B+": "🥈", "B": "🥈",
    "C": "🥉", "D+": "⚠️", "D": "⚠️", "F": "🚨", "N/A": "⚪",
}

SECTION_TITLES = {
    "architecture_analysis":  ("1️⃣",  "SYSTEM ARCHITECTURE ANALYSIS"),
    "llm_integration":        ("2️⃣",  "LLM INTEGRATION DESIGN"),
    "prompt_engineering":     ("3️⃣",  "PROMPT ENGINEERING DISCIPLINE"),
    "cost_performance":       ("4️⃣",  "COST & PERFORMANCE ANALYSIS"),
    "rag_data_pipeline":      ("5️⃣",  "RAG & DATA PIPELINE VALIDATION"),
    "mlops_deployment":       ("6️⃣",  "MLOPS & DEPLOYMENT READINESS"),
    "observability":          ("7️⃣",  "OBSERVABILITY & MONITORING"),
    "failure_resilience":     ("8️⃣",  "FAILURE MODES & RESILIENCE"),
    "security":               ("9️⃣",  "SECURITY ANALYSIS"),
    "scalability":            ("🔟",  "SCALABILITY & EXTENSIBILITY"),
    "technical_debt":         ("1️⃣1️⃣", "TECHNICAL DEBT FORECAST"),
    "final_verdict":          ("1️⃣2️⃣", "FINAL VERDICT"),
}


class Reporter:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ─── Format helpers ────────────────────────────────────────────────────

    def _format_section(self, field_name: str, section: SectionAudit,
                        is_final: bool = False) -> str:
        emoji, title = SECTION_TITLES.get(field_name, ("🔹", field_name.upper()))
        lines = [f"## {emoji} {title}", ""]

        if is_final:
            grade = section.verdict
            grade_e = GRADE_EMOJI.get(grade, "")
            lines += [f"**System Grade:** {grade_e} **{grade}**", ""]
        else:
            verdict_str = VERDICT_EMOJI.get(section.verdict, section.verdict)
            lines += [f"**Verdict:** {verdict_str}", ""]

        if section.findings:
            if is_final and len(section.findings) == 1:
                # Overall summary paragraph
                lines += [section.findings[0], ""]
            else:
                for f in section.findings:
                    if f:
                        lines.append(f"*   {f}")
                lines.append("")

        if section.recommendations:
            if is_final:
                lines += ["**Top 5 Critical Improvements:**"]
                for i, r in enumerate(section.recommendations[:5], 1):
                    lines.append(f"{i}.  {r}")
            else:
                lines += ["**Recommendations:**"]
                for r in section.recommendations:
                    if r:
                        lines.append(f"*   {r}")
            lines.append("")

        lines.append("---")
        lines.append("")
        return "\n".join(lines)

    # ─── Markdown ──────────────────────────────────────────────────────────

    def build_markdown(self, report: AuditReport,
                       context_summary: Dict[str, Any] = None,
                       mcp_results: Dict[str, Any] = None,
                       dependency_results: Dict[str, Any] = None) -> str:
        date_str = datetime.now().strftime("%Y-%m-%d")
        project = report.project_name or "Unknown"
        grade = report.grade or "N/A"
        grade_e = GRADE_EMOJI.get(grade, "")
        readiness = report.enterprise_readiness_pct

        md = [
            f"# Technical Audit: AI Engineering Guardian — `{project}`",
            "",
            f"**Date:** {date_str}  ",
            f"**Auditor:** Principal AI Systems Architect  ",
            f"**Target:** `{project}`  ",
            f"**Version Analyzed:** Local Snapshot  ",
            "",
            "---",
            "",
        ]

        # MCP Structure Analysis Section
        if mcp_results:
            md += [
                "## 🏗️ MCP Structure Analysis",
                "",
                f"| Metric | Value |",
                f"|--------|-------|",
                f"| Compliance Score | {mcp_results.get('overall_score', 'N/A')}% |",
                f"| Compliance Level | {mcp_results.get('compliance_level', 'N/A')} |",
                f"| Requirements Analyzed | {len(mcp_results.get('requirement_results', {}))} |",
                "",
            ]
            
            # Category breakdown
            if 'category_scores' in mcp_results:
                md.append("**Category Scores:**")
                for category, scores in mcp_results['category_scores'].items():
                    cat_score = int((scores["score"] / scores["max"]) * 100) if scores["max"] > 0 else 0
                    md.append(f"- {category.replace('_', ' ').title()}: {cat_score}%")
                md.append("")
            
            # Missing required items
            structure = mcp_results.get('structure_analysis', {})
            if structure.get('missing_required'):
                md.append("**❌ Missing Required Items:**")
                for item in structure['missing_required'][:10]:  # Limit to first 10
                    md.append(f"- {item}")
                md.append("")
            
            # Top recommendations
            if mcp_results.get('recommendations'):
                md.append("**🚨 Top MCP Recommendations:**")
                for rec in mcp_results['recommendations'][:5]:  # Limit to first 5
                    md.append(f"- {rec}")
                md.append("")
            
            md += ["---", ""]

        # Dependency Analysis Section
        if dependency_results:
            md += [
                "## 📦 Dependency Analysis",
                "",
                f"| Metric | Value |",
                f"|--------|-------|",
                f"| Files Analyzed | {dependency_results.get('summary', {}).get('total_files_analyzed', 'N/A')} |",
                f"| Total Imports | {dependency_results.get('summary', {}).get('total_imports', 'N/A')} |",
                f"| External Libraries | {dependency_results.get('summary', {}).get('external_libraries', 'N/A')} |",
                f"| Internal Modules | {dependency_results.get('summary', {}).get('internal_modules', 'N/A')} |",
                "",
            ]
            
            # Dependency issues
            if 'results' in dependency_results:
                total_issues = sum(len(findings) for findings in dependency_results['results'].values())
                if total_issues > 0:
                    md.append("**🚨 Dependency Issues Found:**")
                    for category, findings in dependency_results['results'].items():
                        if findings:
                            md.append(f"- {category.replace('_', ' ').title()}: {len(findings)}")
                    md.append("")
            
            # Most used libraries
            library_usage = dependency_results.get('library_usage', {})
            if library_usage.get('most_used'):
                md.append("**📚 Most Used Libraries:**")
                for lib, count in list(library_usage['most_used'].items())[:10]:
                    md.append(f"- {lib}: {count} imports")
                md.append("")
            
            # Cleanup candidates
            if library_usage.get('least_used'):
                md.append("**🧹 Potential Cleanup Candidates:**")
                least_used = library_usage['least_used']
                if isinstance(least_used, dict):
                    # Convert dict to list of tuples and sort
                    items = list(least_used.items())[:5]
                    for lib, count in items:
                        md.append(f"- {lib}: {count} imports")
                elif isinstance(least_used, list):
                    for item in least_used[:5]:
                        if isinstance(item, dict):
                            lib = item.get('lib', item.get('library', 'unknown'))
                            count = item.get('count', 0)
                            md.append(f"- {lib}: {count} imports")
                        else:
                            md.append(f"- {item}")
                md.append("")
            
            md += ["---", ""]

        # Static summary table (from context_summary if available)
        if context_summary:
            cq = context_summary.get("code_quality", {})
            ai = context_summary.get("ai_ml_profile", {})
            pf = context_summary.get("project_flags", {})
            md += [
                "## 📊 Static Analysis Summary",
                "",
                "| Metric | Value |",
                "|--------|-------|",
                f"| Total Python Files | {context_summary.get('total_python_files', 'N/A')} |",
                f"| Total LOC | {context_summary.get('total_loc', 'N/A')} |",
                f"| Hardcoded Secrets | {cq.get('total_hardcoded_secrets', 0)} |",
                f"| Broad Exceptions | {cq.get('total_broad_excepts', 0)} |",
                f"| Files Using `print()` | {cq.get('total_print_calls', 0)} total calls |",
                f"| Files Using Logging | {cq.get('files_using_logging', 0)} |",
                f"| Files with Retry Logic | {cq.get('files_with_retry', 0)} |",
                f"| Files with Timeout | {cq.get('files_with_timeout', 0)} |",
                f"| Circular Dependencies | {cq.get('circular_dependencies', 0)} |",
                f"| God-Mode Files | {len(cq.get('god_mode_files', []))} |",
                f"| Has Tests | {'✅' if pf.get('has_tests') else '❌'} |",
                f"| Has Dockerfile | {'✅' if pf.get('has_dockerfile') else '❌'} |",
                f"| Has CI/CD | {'✅' if pf.get('has_ci_config') else '❌'} |",
                f"| LLM Libraries | {', '.join(ai.get('llm_libraries', [])) or 'None'} |",
                f"| RAG Libraries | {', '.join(ai.get('rag_libraries', [])) or 'None'} |",
            ]

            if mcp_results:
                md.append(f"| MCP Compliance Score | {mcp_results.get('overall_score', 'N/A')}% |")
            if dependency_results:
                summary = dependency_results.get('summary', {})
                md.append(f"| External Dependencies | {summary.get('external_libraries', 'N/A')} |")

            md += [
                "",
                "---",
                "",
            ]

        # All 12 sections
        section_order = [
            "architecture_analysis", "llm_integration", "prompt_engineering",
            "cost_performance", "rag_data_pipeline", "mlops_deployment",
            "observability", "failure_resilience", "security",
            "scalability", "technical_debt",
        ]
        for field_name in section_order:
            section: SectionAudit = getattr(report, field_name, None)
            if section:
                md.append(self._format_section(field_name, section))

        # Final verdict section
        md.append(self._format_section("final_verdict", report.final_verdict, is_final=True))

        if report.overall_summary:
            md += [
                "## 💬 Overall Summary",
                "",
                report.overall_summary,
                "",
                "---",
                "",
            ]

        md += [
            f"**Enterprise Suitability:** {readiness}%  ",
            f"**Overall Grade:** {grade_e} **{grade}**  ",
            "",
            "*Generated by AI Engineering Guardian — Juan Gato*",
        ]

        return "\n".join(md)

    # ─── Savers ────────────────────────────────────────────────────────────

    def save_markdown(self, report: AuditReport, filename: str,
                      context_summary: Dict[str, Any] = None,
                      mcp_results: Dict[str, Any] = None,
                      dependency_results: Dict[str, Any] = None) -> Path:
        content = self.build_markdown(report, context_summary, mcp_results, dependency_results)
        out = self.output_dir / filename
        out.write_text(content, encoding="utf-8")
        return out

    def save_json(self, report: AuditReport, filename: str) -> Path:
        out = self.output_dir / filename
        out.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        return out
