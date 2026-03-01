"""
Findings Tracker - Systematic issue management with file/line context
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import json
from pathlib import Path

class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class Category(Enum):
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    RELIABILITY = "reliability"
    CONFIGURATION = "configuration"
    LOGGING = "logging"
    TESTING = "testing"

@dataclass
class FindingLocation:
    file_path: str
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    code_snippet: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "function_name": self.function_name,
            "code_snippet": self.code_snippet
        }

@dataclass
class Finding:
    id: str
    title: str
    description: str
    severity: Severity
    category: Category
    locations: List[FindingLocation] = field(default_factory=list)
    recommendation: str = ""
    effort_estimate: str = ""
    tags: List[str] = field(default_factory=list)
    false_positive: bool = False
    resolved: bool = False
    resolution_notes: str = ""
    
    def add_location(self, file_path: str, line: Optional[int] = None, 
                    function: Optional[str] = None, snippet: Optional[str] = None):
        self.locations.append(FindingLocation(file_path, line, function, snippet))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "category": self.category.value,
            "locations": [loc.to_dict() for loc in self.locations],
            "recommendation": self.recommendation,
            "effort_estimate": self.effort_estimate,
            "tags": self.tags,
            "false_positive": self.false_positive,
            "resolved": self.resolved,
            "resolution_notes": self.resolution_notes
        }

class FindingsTracker:
    def __init__(self):
        self.findings: Dict[str, Finding] = {}
        self._next_id = 1
    
    def add_finding(self, title: str, description: str, severity: Severity,
                   category: Category, recommendation: str = "",
                   effort_estimate: str = "", tags: List[str] = None) -> str:
        finding_id = f"FIND-{self._next_id:04d}"
        self._next_id += 1
        
        finding = Finding(
            id=finding_id,
            title=title,
            description=description,
            severity=severity,
            category=category,
            recommendation=recommendation,
            effort_estimate=effort_estimate,
            tags=tags or []
        )
        
        self.findings[finding_id] = finding
        return finding_id
    
    def get_by_severity(self, severity: Severity) -> List[Finding]:
        return [f for f in self.findings.values() if f.severity == severity and not f.resolved]
    
    def get_by_category(self, category: Category) -> List[Finding]:
        return [f for f in self.findings.values() if f.category == category and not f.resolved]
    
    def get_unresolved(self) -> List[Finding]:
        return [f for f in self.findings.values() if not f.resolved and not f.false_positive]
    
    def mark_resolved(self, finding_id: str, notes: str = ""):
        if finding_id in self.findings:
            self.findings[finding_id].resolved = True
            self.findings[finding_id].resolution_notes = notes
    
    def mark_false_positive(self, finding_id: str, notes: str = ""):
        if finding_id in self.findings:
            self.findings[finding_id].false_positive = True
            self.findings[finding_id].resolution_notes = notes
    
    def export_to_json(self, file_path: str):
        data = {
            "findings": [f.to_dict() for f in self.findings.values()],
            "summary": self._generate_summary()
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _generate_summary(self) -> Dict[str, Any]:
        unresolved = self.get_unresolved()
        return {
            "total_findings": len(self.findings),
            "unresolved": len(unresolved),
            "resolved": len([f for f in self.findings.values() if f.resolved]),
            "false_positives": len([f for f in self.findings.values() if f.false_positive]),
            "by_severity": {
                sev.value: len(self.get_by_severity(sev)) 
                for sev in Severity
            },
            "by_category": {
                cat.value: len(self.get_by_category(cat))
                for cat in Category
            }
        }
    
    def generate_roadmap(self) -> Dict[str, List[str]]:
        """Generate prioritized roadmap based on findings"""
        roadmap = {
            "Phase 1 - Critical Blockers": [],
            "Phase 2 - Architecture": [],
            "Phase 3 - Production Ready": [],
            "Phase 4 - Enhancement": []
        }
        
        critical = self.get_by_severity(Severity.CRITICAL)
        high = self.get_by_severity(Severity.HIGH)
        
        # Phase 1: All critical + high priority architectural issues
        for finding in critical:
            roadmap["Phase 1 - Critical Blockers"].append(f"{finding.id}: {finding.title}")
        
        # Phase 2: High severity architectural issues
        for finding in high:
            if finding.category in [Category.ARCHITECTURE, Category.MAINTAINABILITY]:
                roadmap["Phase 2 - Architecture"].append(f"{finding.id}: {finding.title}")
        
        # Phase 3: High severity production issues
        for finding in high:
            if finding.category in [Category.SECURITY, Category.RELIABILITY, Category.LOGGING]:
                roadmap["Phase 3 - Production Ready"].append(f"{finding.id}: {finding.title}")
        
        # Phase 4: Medium/Low severity issues
        medium = self.get_by_severity(Severity.MEDIUM)
        low = self.get_by_severity(Severity.LOW)
        
        for finding in medium + low:
            roadmap["Phase 4 - Enhancement"].append(f"{finding.id}: {finding.title}")
        
        return roadmap
