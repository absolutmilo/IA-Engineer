"""
llm_client.py — Section-by-section LLM analyzer.

Strategy:
  1. Receive a compact metadata JSON summary (< 3k tokens)
  2. For each of 12 sections, send a focused prompt with a 30s timeout
  3. Parse plain-text output into SectionAudit objects
  4. Never block forever — timeout or error yields a graceful fallback
  5. Use threading to enforce hard timeouts + tenacity for retries
  6. Extensive logging for debugging and observability
"""

import re
import json
import ollama
import threading
import time
from queue import Queue, Empty
from typing import Optional, Dict, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .structure import AuditReport, SectionAudit
from .prompts import SECTION_PROMPTS
from utils.logger import get_logger, log_event

console = Console()
logger = get_logger("llm_client")

# Maps section key -> AuditReport field name (same here, just for clarity)
SECTION_ORDER = [
    "architecture",
    "llm_integration",
    "prompt_engineering",
    "cost_performance",
    "rag_data_pipeline",
    "mlops_deployment",
    "observability",
    "failure_resilience",
    "security",
    "scalability",
    "technical_debt",
    "final_verdict",
]

SECTION_DISPLAY_NAMES = {
    "architecture":        "1️⃣  System Architecture",
    "llm_integration":     "2️⃣  LLM Integration Design",
    "prompt_engineering":  "3️⃣  Prompt Engineering Discipline",
    "cost_performance":    "4️⃣  Cost & Performance",
    "rag_data_pipeline":   "5️⃣  RAG & Data Pipeline",
    "mlops_deployment":    "6️⃣  MLOps & Deployment Readiness",
    "observability":       "7️⃣  Observability & Monitoring",
    "failure_resilience":  "8️⃣  Failure Modes & Resilience",
    "security":            "9️⃣  Security Analysis",
    "scalability":         "🔟  Scalability & Extensibility",
    "technical_debt":      "1️⃣1️⃣ Technical Debt Forecast",
    "final_verdict":       "1️⃣2️⃣ Final Verdict",
}

VERDICT_TO_RISK = {
    "CRITICAL":   "Critical",
    "POOR":       "High",
    "WEAK":       "High",
    "MIXED":      "Medium",
    "GOOD":       "Low",
    "EXCELLENT":  "Low",
    "UNKNOWN":    "Medium",
}

VERDICT_TO_SCORE = {
    "CRITICAL":   1,
    "POOR":       3,
    "WEAK":       4,
    "MIXED":      6,
    "GOOD":       8,
    "EXCELLENT":  10,
    "UNKNOWN":    5,
}


class LLMClient:
    def __init__(self, model: str = "llama3.2:3b-instruct-q4_0",
                 api_base: str = "http://localhost:11434",
                 section_timeout: int = 120):
        self.model = model
        self.section_timeout = section_timeout
        self.api_base = api_base
        self.client = ollama.Client(host=api_base)
        
        logger.info(f"LLMClient initialized")
        logger.info(f"  Model: {self.model}")
        logger.info(f"  API Base: {self.api_base}")
        logger.info(f"  Section timeout: {self.section_timeout}s")
        logger.info(f"  Retry strategy: 2 attempts with exponential backoff (2-10s)")

    # ─── Retry decorator with exponential backoff ───────────────────────────

    @staticmethod
    def _call_ollama_with_retry(client, model: str, messages: list, options: dict) -> str:
        """Calls ollama.Client.chat with exponential backoff retry."""
        @retry(
            stop=stop_after_attempt(2),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((ConnectionError, TimeoutError, Exception)),
            reraise=True
        )
        def _attempt():
            response = client.chat(
                model=model,
                messages=messages,
                options=options,
            )
            msg = response.get("message", {}) if isinstance(response, dict) else response["message"]
            return msg.get("content", "") if isinstance(msg, dict) else msg.content

        return _attempt()

    # ─── Thread-enforced timeout ───────────────────────────────────────────

    @staticmethod
    def _cap_text(text: str, max_chars: int) -> str:
        if len(text) <= max_chars:
            return text
        return text[:max_chars]

    def _build_section_summary(self, section_key: str, context_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Build a smaller, section-focused summary for local models."""
        base: Dict[str, Any] = {
            "project_name": context_summary.get("project_name"),
            "total_python_files": context_summary.get("total_python_files"),
            "total_loc": context_summary.get("total_loc"),
            "project_flags": context_summary.get("project_flags", {}),
            "code_quality": context_summary.get("code_quality", {}),
            "ai_ml_profile": context_summary.get("ai_ml_profile", {}),
        }

        files = context_summary.get("files", []) or []

        # Choose how many file entries to include depending on the section.
        # Keep it conservative for local models.
        per_section_file_caps = {
            "architecture": 8,
            "llm_integration": 5,
            "prompt_engineering": 5,
            "cost_performance": 5,
            "rag_data_pipeline": 6,
            "mlops_deployment": 5,
            "observability": 5,
            "failure_resilience": 5,
            "security": 5,
            "scalability": 5,
            "technical_debt": 6,
            "final_verdict": 10,
        }
        cap = per_section_file_caps.get(section_key, 20)

        # Always take highest-LOC first; ContextBuilder already sorts by LOC desc.
        base["files"] = files[:cap]

        # Extra focus per section (adds small hints, not full data dumps)
        if section_key in ("architecture", "scalability"):
            cq = base.get("code_quality", {})
            base["focus"] = (
                f"God-mode files: {len(cq.get('god_mode_files', []))}. "
                f"Circular deps: {len(cq.get('circular_dependency_examples', []))}."
            )
        elif section_key in ("mlops_deployment", "security"):
            cq = base.get("code_quality", {})
            base["focus"] = (
                f"Hardcoded paths: {len(cq.get('sample_hardcoded_paths', []))}. "
                f"Secrets: {cq.get('total_hardcoded_secrets', 0)}."
            )
        elif section_key in ("observability", "failure_resilience"):
            cq = base.get("code_quality", {})
            base["focus"] = (
                f"Logging files: {cq.get('files_using_logging', 0)}. "
                f"Retry files: {cq.get('files_with_retry', 0)}. "
                f"Timeout files: {cq.get('files_with_timeout', 0)}. "
                f"Broad excepts: {cq.get('total_broad_excepts', 0)}."
            )
        elif section_key in ("llm_integration", "prompt_engineering"):
            ai = base.get("ai_ml_profile", {})
            libs = ai.get("llm_libraries", [])
            base["focus"] = (
                f"LLM libs: {libs}. "
                f"Direct LLM calls files: {len(ai.get('files_with_direct_llm_calls', []))}. "
                f"Prompt strings: {ai.get('total_prompt_strings_detected', 0)}."
            )

        return base

    def _build_section_summary_json(self, section_key: str, context_summary: Dict[str, Any]) -> str:
        # Budget in characters (proxy for tokens). Tuned for small local models.
        max_chars = 3000 if section_key != "final_verdict" else 5000
        data = self._build_section_summary(section_key, context_summary)
        s = json.dumps(data, indent=2)
        return self._cap_text(s, max_chars)

    def _call_section_with_timeout(self, section_key: str, summary_json: str) -> str:
        """
        Calls the LLM with a hard timeout enforced by threading.
        Returns response or empty string if timeout occurs.
        """
        logger.debug(f"[SECTION] Starting: {section_key}")
        
        if section_key not in SECTION_PROMPTS:
            logger.error(f"[SECTION] Unknown section key: {section_key}")
            return ""

        prompt = SECTION_PROMPTS[section_key].format(summary=summary_json)
        
        logger.debug(f"[SECTION] Prompt for '{section_key}':")
        logger.debug(f"  Prompt length: {len(prompt)} characters")
        logger.debug(f"  First 300 chars: {prompt[:300]}...")

        log_event(
            logger,
            "llm_section_prompt_built",
            section_key=section_key,
            summary_chars=len(summary_json),
            prompt_chars=len(prompt),
        )
        
        result_queue: Queue = Queue()
        thread_id = threading.current_thread().ident

        def _worker():
            worker_thread_id = threading.current_thread().ident
            logger.debug(f"[WORKER] Started for section '{section_key}' (thread: {worker_thread_id})")
            start_time = time.time()
            
            try:
                logger.debug(f"[WORKER] Calling ollama.chat() with retry...")
                response = self._call_ollama_with_retry(
                    self.client,
                    self.model,
                    [{"role": "user", "content": prompt}],
                    {
                        "temperature": 0.1,
                        "num_predict": 512,   # hard cap on output tokens per section
                    }
                )
                elapsed = time.time() - start_time
                logger.info(f"[WORKER] SUCCESS '{section_key}': Got response ({len(response)} chars) in {elapsed:.1f}s")
                logger.debug(f"[WORKER] Response preview: {response[:200]}...")
                result_queue.put(("success", response))
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"[WORKER] ERROR '{section_key}': {e} (after {elapsed:.1f}s)", exc_info=True)
                result_queue.put(("error", str(e)))

        # Start the thread as a daemon so it doesn't block the entire program
        thread = threading.Thread(target=_worker, daemon=True, name=f"LLM-{section_key}")
        logger.debug(f"[SECTION] Spawning worker thread for {section_key}")
        thread.start()

        # Wait for result with a hard timeout
        logger.debug(f"[SECTION] Waiting for result (timeout: {self.section_timeout}s)...")
        try:
            status, result = result_queue.get(timeout=self.section_timeout)
            if status == "success":
                logger.info(f"[SECTION] '{section_key}' completed successfully")
                return result
            else:
                logger.warning(f"[SECTION] '{section_key}' failed: {result}")
                console.print(f"    [yellow]⚠ Section '{section_key}' failed: {result}[/yellow]")
                return ""
        except Empty:
            logger.error(f"[SECTION] '{section_key}' TIMEOUT after {self.section_timeout}s")
            logger.error(f"[SECTION] Worker thread still running; will be terminated as daemon")
            console.print(f"    [red]✗ Section '{section_key}' TIMEOUT after {self.section_timeout}s[/red]")
            return ""

    # ─── Single Section ────────────────────────────────────────────────────

    def _call_section(self, section_key: str, summary_json: str) -> str:
        """
        Calls the LLM for a single audit section.
        Returns raw text response, or empty string on failure.
        Uses thread-enforced timeout to prevent blocking indefinitely.
        """
        return self._call_section_with_timeout(section_key, summary_json)

    # ─── Parsing ───────────────────────────────────────────────────────────

    def _parse_section(self, raw: str, section_key: str) -> SectionAudit:
        """Parse the structured plain-text response into a SectionAudit."""
        section = SectionAudit(raw_analysis=raw)

        if not raw.strip():
            section.verdict = "UNKNOWN"
            section.findings = ["LLM analysis unavailable for this section."]
            section.recommendations = ["Re-run the audit when the LLM is responsive."]
            return section

        # Verdict
        m = re.search(r"VERDICT\s*:\s*([A-Z]+)", raw, re.IGNORECASE)
        if m:
            section.verdict = m.group(1).strip().upper()

        # Score (optional — only LLM Integration asks for it)
        m = re.search(r"SCORE\s*:\s*(\d+)\s*/\s*10", raw)
        if m:
            section.score = min(int(m.group(1)), 10)
        else:
            section.score = VERDICT_TO_SCORE.get(section.verdict, 5)

        section.risk_level = VERDICT_TO_RISK.get(section.verdict, "Medium")

        # Findings
        f_block = re.search(r"FINDINGS\s*:(.*?)(?:RECOMMENDATIONS|GRADE|$)", raw, re.DOTALL | re.IGNORECASE)
        if f_block:
            lines = [l.strip().lstrip("-• *").strip()
                     for l in f_block.group(1).splitlines()
                     if l.strip() and not l.strip().startswith("#")]
            section.findings = [l for l in lines if l and len(l) > 5]
        
        # Ensure we have at least one finding
        if not section.findings:
            section.findings = ["Analysis indicates potential improvements needed. Review findings in audit context."]

        # Recommendations
        r_block = re.search(r"RECOMMENDATIONS\s*:(.*?)(?:VENDOR|GRADE|$)", raw, re.DOTALL | re.IGNORECASE)
        if r_block:
            lines = [l.strip().lstrip("-• *").strip()
                     for l in r_block.group(1).splitlines()
                     if l.strip() and not l.strip().startswith("#")]
            section.recommendations = [l for l in lines if l and len(l) > 5]
        
        # Ensure we have at least one recommendation
        if not section.recommendations:
            section.recommendations = ["Schedule a comprehensive code review to identify improvement areas."]

        return section

    def _parse_final_verdict(self, raw: str) -> SectionAudit:
        """Parse the final verdict section to extract grade, readiness, top improvements."""
        section = SectionAudit(raw_analysis=raw)
        section.score = 0

        if not raw.strip():
            section.verdict = "UNKNOWN"
            return section

        section.verdict = "FINAL"

        # Grade
        m = re.search(r"GRADE\s*:\s*([A-F][+\-]?)", raw, re.IGNORECASE)
        if m:
            section.verdict = m.group(1).strip()

        # Summary (overall)
        m = re.search(r"SUMMARY\s*:(.*?)(?:TOP 5|IMPROVEMENTS|$)", raw, re.DOTALL | re.IGNORECASE)
        if m:
            section.findings = [m.group(1).strip()]

        # Top 5 improvements (try different patterns)
        improvements = []
        
        # Pattern 1: numbered list with dots
        m = re.search(r"TOP 5 IMPROVEMENTS\s*:(.*?)$", raw, re.DOTALL | re.IGNORECASE)
        if m:
            lines = re.findall(r"\d+\.\s*(.+?)(?:\n|$)", m.group(1))
            improvements = [l.strip() for l in lines if l.strip() and len(l.strip()) > 5]
        
        # Pattern 2: simpler pattern without numbers
        if not improvements:
            m = re.search(r"IMPROVEMENTS?\s*:(.*?)$", raw, re.DOTALL | re.IGNORECASE)
            if m:
                lines = [l.strip().lstrip("-• *").strip()
                         for l in m.group(1).splitlines()
                         if l.strip() and not l.strip().startswith("#")]
                improvements = [l for l in lines if l and len(l) > 5]

        # Ensure we have 5 improvements (pad with generic if needed)
        default_improvements = [
            "Implement proper configuration management with environment variables.",
            "Replace print() logging with structured logging framework.",
            "Abstract LLM and external service integrations.",
            "Add comprehensive error handling and retry mechanisms.",
            "Implement security hardening (secrets management, input validation).",
        ]
        
        section.recommendations = improvements[:5] if improvements else default_improvements

        return section

    # ─── Full Audit ────────────────────────────────────────────────────────

    def analyze_all(self, context_summary: Dict[str, Any]) -> AuditReport:
        """
        Run all 12 audit sections sequentially, with a per-section timeout.
        Returns a fully assembled AuditReport.
        """
        logger.info("=" * 70)
        logger.info("STARTING FULL AUDIT ANALYSIS (12 SECTIONS)")
        logger.info("=" * 70)
        
        project_name = context_summary.get("project_name", "Unknown")
        
        logger.info(f"Project: {project_name}")
        full_summary_json = json.dumps(context_summary, indent=2)
        logger.info(f"Context summary size: {len(full_summary_json)} bytes")
        logger.debug(f"Context summary (first 500 chars):\n{full_summary_json[:500]}")

        log_event(
            logger,
            "context_summary_ready",
            project_name=project_name,
            summary_chars=len(full_summary_json),
        )
        
        report = AuditReport(project_name=project_name)

        section_map = {
            "architecture":        "architecture_analysis",
            "llm_integration":     "llm_integration",
            "prompt_engineering":  "prompt_engineering",
            "cost_performance":    "cost_performance",
            "rag_data_pipeline":   "rag_data_pipeline",
            "mlops_deployment":    "mlops_deployment",
            "observability":       "observability",
            "failure_resilience":  "failure_resilience",
            "security":            "security",
            "scalability":         "scalability",
            "technical_debt":      "technical_debt",
            "final_verdict":       "final_verdict",
        }

        total_start = time.time()
        
        for idx, section_key in enumerate(SECTION_ORDER, 1):
            display = SECTION_DISPLAY_NAMES.get(section_key, section_key)
            section_start = time.time()
            
            logger.info(f"[{idx}/12] Processing: {section_key}")
            console.print(f"  [bold cyan]{display}[/bold cyan]...", end=" ")

            section_summary_json = self._build_section_summary_json(section_key, context_summary)
            raw = self._call_section(section_key, section_summary_json)
            section_elapsed = time.time() - section_start
            logger.info(f"[{idx}/12] Section '{section_key}' completed in {section_elapsed:.1f}s (response: {len(raw)} bytes)")

            log_event(
                logger,
                "llm_section_completed",
                section_key=section_key,
                elapsed_s=round(section_elapsed, 3),
                response_chars=len(raw),
            )

            if section_key == "final_verdict":
                logger.debug("Parsing final verdict...")
                section = self._parse_final_verdict(raw)
                report.grade = section.verdict
                report.overall_summary = section.findings[0] if section.findings else ""
                report.top_critical_improvements = section.recommendations
                
                logger.info(f"[FINAL] Grade: {report.grade}")
                logger.info(f"[FINAL] Enterprise Readiness: {report.enterprise_readiness_pct}%")
                logger.info(f"[FINAL] Top improvements: {len(report.top_critical_improvements)}")

                # Parse enterprise readiness %
                m = re.search(r"ENTERPRISE_READINESS\s*:\s*(\d+)", raw)
                if m:
                    report.enterprise_readiness_pct = int(m.group(1))
            else:
                logger.debug(f"Parsing section '{section_key}'...")
                section = self._parse_section(raw, section_key)
                logger.debug(f"  Verdict: {section.verdict}")
                logger.debug(f"  Findings: {len(section.findings)}")
                logger.debug(f"  Recommendations: {len(section.recommendations)}")

            field_name = section_map.get(section_key)
            if field_name:
                setattr(report, field_name, section)

            # Show verdict inline
            verdict_colors = {
                "CRITICAL": "red", "POOR": "red", "WEAK": "yellow",
                "MIXED": "yellow", "GOOD": "green", "EXCELLENT": "bright_green",
            }
            color = verdict_colors.get(section.verdict, "white")
            console.print(f"[{color}]{section.verdict}[/{color}]")

        total_elapsed = time.time() - total_start
        logger.info("=" * 70)
        logger.info(f"AUDIT ANALYSIS COMPLETE in {total_elapsed:.1f}s")
        logger.info(f"Final Grade: {report.grade} | Enterprise Readiness: {report.enterprise_readiness_pct}%")
        logger.info("=" * 70)

        return report
