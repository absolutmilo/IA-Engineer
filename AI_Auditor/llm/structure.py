from pydantic import BaseModel, Field
from typing import List, Optional


class SectionAudit(BaseModel):
    verdict: str = "UNKNOWN"           # CRITICAL / POOR / WEAK / MIXED / GOOD / EXCELLENT
    score: int = Field(default=0, ge=0, le=10, description="Score from 0 to 10")
    risk_level: str = "Medium"         # Low / Medium / High / Critical
    findings: List[str] = []
    recommendations: List[str] = []
    raw_analysis: str = ""             # Full LLM plain-text response


class AuditReport(BaseModel):
    project_name: str = ""
    architecture_analysis: SectionAudit = SectionAudit()
    llm_integration: SectionAudit = SectionAudit()
    prompt_engineering: SectionAudit = SectionAudit()
    cost_performance: SectionAudit = SectionAudit()
    rag_data_pipeline: SectionAudit = SectionAudit()
    mlops_deployment: SectionAudit = SectionAudit()
    observability: SectionAudit = SectionAudit()
    failure_resilience: SectionAudit = SectionAudit()
    security: SectionAudit = SectionAudit()
    scalability: SectionAudit = SectionAudit()
    technical_debt: SectionAudit = SectionAudit()
    final_verdict: SectionAudit = SectionAudit()

    overall_summary: str = ""
    top_critical_improvements: List[str] = []
    enterprise_readiness_pct: int = 0
    grade: str = "N/A"
