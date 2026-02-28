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
                       context_summary: Dict[str, Any] = None) -> str:
        date_str = datetime.now().strftime("%Y-%m-%d")
        project = report.project_name or "Unknown"
        grade = report.grade or "N/A"
        grade_e = GRADE_EMOJI.get(grade, "")
        readiness = report.enterprise_readiness_pct

        md = [
            f"# Technical Audit: AI Engineering Guardian — `{project}`",
            "",
            f"**Date:** {date_str}  ",
            f"**Auditor:** Principal AI Systems Architect (Antigravity)  ",
            f"**Target:** `{project}`  ",
            f"**Version Analyzed:** Local Snapshot  ",
            "",
            "---",
            "",
        ]

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
                      context_summary: Dict[str, Any] = None) -> Path:
        content = self.build_markdown(report, context_summary)
        out = self.output_dir / filename
        out.write_text(content, encoding="utf-8")
        return out

    def save_json(self, report: AuditReport, filename: str) -> Path:
        out = self.output_dir / filename
        out.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        return out
