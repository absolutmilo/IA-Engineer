#!/usr/bin/env python3
"""
Integrated Auditor - Comprehensive project analysis with GUI
Combines code analysis, MCP validation, and dependency auditing
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import queue
import time

# Core imports
from core.findings_tracker import Severity, Category
from core.audit_analyzer import AuditAnalyzer
from core.dependency_analyzer import DependencyAnalyzer
from core.mcp_structure_validator import MCPStructureValidator
from core.dependency_graph import DependencyGraph
from core.static_analyzer import StaticAnalyzer
from core.context_builder import ContextBuilder
from llm.llm_client import LLMClient
from llm.structure import AuditReport
from utils.reporter import Reporter
from utils.logger import setup_logging


class IntegratedAuditorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Engineering Guardian - Integrated Auditor")
        self.root.geometry("1400x900")
        
        # State management
        self.project_path = None
        self.analysis_results = {}
        self.analysis_queue = queue.Queue()
        self.is_analyzing = False
        
        # Setup GUI
        self.setup_gui()
        self.setup_logging()
        
    def setup_gui(self):
        """Initialize the GUI components"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Project selection frame
        self.create_project_frame(main_frame)
        
        # Analysis options frame
        self.create_options_frame(main_frame)
        
        # Results display frame
        self.create_results_frame(main_frame)
        
        # Status bar
        self.create_status_bar(main_frame)
        
    def create_project_frame(self, parent):
        """Create project selection frame"""
        frame = ttk.LabelFrame(parent, text="Project Selection", padding="10")
        frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        frame.columnconfigure(1, weight=1)
        
        ttk.Label(frame, text="Project Path:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.path_var = tk.StringVar()
        path_entry = ttk.Entry(frame, textvariable=self.path_var, width=60)
        path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(frame, text="Browse...", command=self.browse_project).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(frame, text="Analyze", command=self.start_analysis).grid(row=0, column=3)
        
    def create_options_frame(self, parent):
        """Create analysis options frame"""
        frame = ttk.LabelFrame(parent, text="Analysis Options", padding="10")
        frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Analysis options
        self.include_mcp = tk.BooleanVar(value=True)
        self.include_dependency = tk.BooleanVar(value=True)
        self.include_llm = tk.BooleanVar(value=True)
        self.include_static = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(frame, text="MCP Structure Validation", variable=self.include_mcp).grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        ttk.Checkbutton(frame, text="Dependency Analysis", variable=self.include_dependency).grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        ttk.Checkbutton(frame, text="LLM Audit Analysis", variable=self.include_llm).grid(row=0, column=2, sticky=tk.W, padx=(0, 20))
        ttk.Checkbutton(frame, text="Static Code Analysis", variable=self.include_static).grid(row=0, column=3, sticky=tk.W)
        
    def create_results_frame(self, parent):
        """Create results display frame"""
        # Create notebook for tabbed results
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Overview tab
        self.overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.overview_frame, text="Overview")
        self.create_overview_tab()
        
        # MCP Structure tab
        self.mcp_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.mcp_frame, text="MCP Structure")
        self.create_mcp_tab()
        
        # Dependency Analysis tab
        self.dep_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dep_frame, text="Dependencies")
        self.create_dependency_tab()
        
        # Code Quality tab
        self.code_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.code_frame, text="Code Quality")
        self.create_code_tab()
        
        # LLM Analysis tab
        self.llm_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.llm_frame, text="LLM Analysis")
        self.create_llm_tab()
        
        # Raw Logs tab
        self.logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.logs_frame, text="Logs")
        self.create_logs_tab()
        
    def create_overview_tab(self):
        """Create overview results tab"""
        # Summary frame
        summary_frame = ttk.LabelFrame(self.overview_frame, text="Analysis Summary", padding="10")
        summary_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Summary text widget
        self.overview_text = scrolledtext.ScrolledText(summary_frame, height=20, width=80)
        self.overview_text.pack(fill=tk.BOTH, expand=True)
        
        # Export buttons frame
        button_frame = ttk.Frame(self.overview_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="Export Full Report", command=self.export_report).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Export JSON", command=self.export_json).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Clear Results", command=self.clear_results).pack(side=tk.LEFT)
        
    def create_mcp_tab(self):
        """Create MCP structure results tab"""
        # MCP results frame
        mcp_results_frame = ttk.LabelFrame(self.mcp_frame, text="MCP Structure Analysis", padding="10")
        mcp_results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # MCP results text
        self.mcp_text = scrolledtext.ScrolledText(mcp_results_frame, height=25, width=80)
        self.mcp_text.pack(fill=tk.BOTH, expand=True)
        
    def create_dependency_tab(self):
        """Create dependency analysis results tab"""
        # Dependency results frame
        dep_results_frame = ttk.LabelFrame(self.dep_frame, text="Dependency Analysis", padding="10")
        dep_results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Dependency results text
        self.dep_text = scrolledtext.ScrolledText(dep_results_frame, height=25, width=80)
        self.dep_text.pack(fill=tk.BOTH, expand=True)
        
    def create_code_tab(self):
        """Create code quality results tab"""
        # Code quality frame
        code_results_frame = ttk.LabelFrame(self.code_frame, text="Code Quality Analysis", padding="10")
        code_results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Code quality results text
        self.code_text = scrolledtext.ScrolledText(code_results_frame, height=25, width=80)
        self.code_text.pack(fill=tk.BOTH, expand=True)
        
    def create_llm_tab(self):
        """Create LLM analysis results tab"""
        # LLM results frame
        llm_results_frame = ttk.LabelFrame(self.llm_frame, text="LLM Analysis Report", padding="10")
        llm_results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # LLM results text
        self.llm_text = scrolledtext.ScrolledText(llm_results_frame, height=25, width=80)
        self.llm_text.pack(fill=tk.BOTH, expand=True)
        
    def create_logs_tab(self):
        """Create logs tab"""
        # Logs frame
        logs_frame = ttk.LabelFrame(self.logs_frame, text="Analysis Logs", padding="10")
        logs_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Logs text
        self.logs_text = scrolledtext.ScrolledText(logs_frame, height=25, width=80)
        self.logs_text.pack(fill=tk.BOTH, expand=True)
        
    def create_status_bar(self, parent):
        """Create status bar"""
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Progress bar
        self.progress = ttk.Progressbar(parent, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
    def setup_logging(self):
        """Setup logging for the GUI"""
        self.logger = setup_logging(verbose=True)
        
    def browse_project(self):
        """Browse for project directory"""
        directory = filedialog.askdirectory()
        if directory:
            self.path_var.set(directory)
            
    def log_message(self, message: str):
        """Log message to GUI and console"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        # Update logs tab
        self.logs_text.insert(tk.END, formatted_message)
        self.logs_text.see(tk.END)
        
        # Update status
        self.status_var.set(message)
        
        # Also log to file
        if hasattr(self, 'logger'):
            self.logger.info(message)
            
    def start_analysis(self):
        """Start the analysis process"""
        if self.is_analyzing:
            messagebox.showwarning("Analysis in Progress", "Analysis is already running. Please wait.")
            return
            
        project_path = self.path_var.get().strip()
        if not project_path:
            messagebox.showerror("No Project", "Please select a project path.")
            return
            
        if not Path(project_path).exists():
            messagebox.showerror("Invalid Path", "The selected project path does not exist.")
            return
            
        self.project_path = Path(project_path)
        self.is_analyzing = True
        self.clear_results()
        
        # Start progress indicator
        self.progress.start()
        self.log_message(f"Starting analysis of: {project_path}")
        
        # Start analysis in separate thread
        analysis_thread = threading.Thread(target=self.run_analysis, daemon=True)
        analysis_thread.start()
        
    def run_analysis(self):
        """Run the comprehensive analysis"""
        try:
            self.analysis_results = {}
            
            # Initialize basic analyzers
            self.log_message("Initializing analyzers...")
            
            # 1. Static Code Analysis (always included)
            if self.include_static.get():
                self.log_message("Running static code analysis...")
                self.run_static_analysis()
                
            # 2. MCP Structure Validation
            if self.include_mcp.get():
                self.log_message("Running MCP structure validation...")
                self.run_mcp_analysis()
                
            # 3. Dependency Analysis
            if self.include_dependency.get():
                self.log_message("Running dependency analysis...")
                self.run_dependency_analysis()
                
            # 4. LLM Analysis
            if self.include_llm.get():
                self.log_message("Running LLM analysis...")
                self.run_llm_analysis()
                
            # Generate integrated report
            self.log_message("Generating integrated report...")
            self.generate_integrated_report()
            
            self.log_message("Analysis completed successfully!")
            
        except Exception as e:
            self.log_message(f"Analysis failed: {str(e)}")
            messagebox.showerror("Analysis Error", f"Analysis failed: {str(e)}")
        finally:
            self.is_analyzing = False
            self.progress.stop()
            self.status_var.set("Ready")
            
    def run_static_analysis(self):
        """Run static code analysis"""
        try:
            # Enhanced audit analysis
            enhanced_analyzer = AuditAnalyzer(str(self.project_path))
            enhanced_results = enhanced_analyzer.run_full_analysis()
            
            # Dependency graph
            graph = DependencyGraph(self.project_path)
            graph.build()
            cycles = graph.detect_cycles()
            coupling = graph.get_coupling_metrics()
            
            # Static analysis
            file_stats = {}
            for mod, file_path in graph.file_map.items():
                analyzer = StaticAnalyzer(file_path)
                stats = analyzer.analyze()
                file_stats[mod] = stats
                
            # Store results
            self.analysis_results['static'] = {
                'enhanced_results': enhanced_results,
                'graph_info': {
                    'files_count': len(graph.file_map),
                    'cycles': cycles,
                    'coupling': coupling
                },
                'file_stats': file_stats,
                'tracker': enhanced_analyzer.tracker
            }
            
            # Update GUI
            self.root.after(0, self.update_static_results)
            
        except Exception as e:
            self.log_message(f"Static analysis error: {str(e)}")
            
    def run_mcp_analysis(self):
        """Run MCP structure validation"""
        try:
            validator = MCPStructureValidator(str(self.project_path))
            results = validator.validate_structure()
            
            self.analysis_results['mcp'] = {
                'validator': validator,
                'results': results
            }
            
            # Update GUI
            self.root.after(0, self.update_mcp_results)
            
        except Exception as e:
            self.log_message(f"MCP analysis error: {str(e)}")
            
    def run_dependency_analysis(self):
        """Run dependency analysis"""
        try:
            analyzer = DependencyAnalyzer(str(self.project_path))
            results = analyzer.analyze_imports_and_usage()
            report = analyzer.generate_dependency_report()
            
            self.analysis_results['dependency'] = {
                'analyzer': analyzer,
                'results': results,
                'report': report
            }
            
            # Update GUI
            self.root.after(0, self.update_dependency_results)
            
        except Exception as e:
            self.log_message(f"Dependency analysis error: {str(e)}")
            
    def run_llm_analysis(self):
        """Run LLM analysis"""
        try:
            # Build context from static analysis if available
            context_summary = {}
            if 'static' in self.analysis_results:
                # Build context from static analysis results
                builder = ContextBuilder(
                    root_path=self.project_path,
                    file_stats=self.analysis_results['static']['file_stats'],
                    graph=None,  # Would need to rebuild or store
                    cycles=self.analysis_results['static']['graph_info']['cycles'],
                    coupling=self.analysis_results['static']['graph_info']['coupling'],
                    config={}  # Default config
                )
                context_summary = builder.build()
                
            # Run LLM analysis
            llm_client = LLMClient()  # Use default config
            report = llm_client.analyze_all(context_summary)
            
            self.analysis_results['llm'] = {
                'report': report,
                'context': context_summary
            }
            
            # Update GUI
            self.root.after(0, self.update_llm_results)
            
        except Exception as e:
            self.log_message(f"LLM analysis error: {str(e)}")
            
    def update_static_results(self):
        """Update static analysis results in GUI"""
        if 'static' not in self.analysis_results:
            return
            
        static_data = self.analysis_results['static']
        enhanced_results = static_data['enhanced_results']
        tracker = static_data['tracker']
        
        # Clear and update code quality tab
        self.code_text.delete(1.0, tk.END)
        
        # Summary
        total_findings = sum(len(findings) for findings in enhanced_results.values())
        self.code_text.insert(tk.END, f"📊 Static Code Analysis Results\n")
        self.code_text.insert(tk.END, f"{'='*50}\n\n")
        self.code_text.insert(tk.END, f"Total Findings: {total_findings}\n\n")
        
        # Category breakdown
        category_counts = {
            "Hardcoded Paths": len(enhanced_results.get("hardcoded_paths", [])),
            "Print Statements": len(enhanced_results.get("print_statements", [])),
            "Broad Exceptions": len(enhanced_results.get("broad_exceptions", [])),
            "LLM Integration": len(enhanced_results.get("llm_integration", [])),
            "Dependencies": len(enhanced_results.get("dependencies", [])),
            "MCP Structure": len(enhanced_results.get("mcp_structure", []))
        }
        
        self.code_text.insert(tk.END, "Findings by Category:\n")
        for category, count in category_counts.items():
            if count > 0:
                self.code_text.insert(tk.END, f"  • {category}: {count}\n")
                
        # Critical findings
        critical_count = len(tracker.get_by_severity(Severity.CRITICAL))
        if critical_count > 0:
            self.code_text.insert(tk.END, f"\n🚨 Critical Issues: {critical_count}\n")
            
        # Graph info
        graph_info = static_data['graph_info']
        self.code_text.insert(tk.END, f"\nDependency Graph:\n")
        self.code_text.insert(tk.END, f"  • Files analyzed: {graph_info['files_count']}\n")
        self.code_text.insert(tk.END, f"  • Circular dependencies: {len(graph_info['cycles'])}\n")
        
    def update_mcp_results(self):
        """Update MCP analysis results in GUI"""
        if 'mcp' not in self.analysis_results:
            return
            
        mcp_data = self.analysis_results['mcp']
        results = mcp_data['results']
        
        # Clear and update MCP tab
        self.mcp_text.delete(1.0, tk.END)
        
        # Summary
        self.mcp_text.insert(tk.END, f"🏗️ MCP Structure Analysis Results\n")
        self.mcp_text.insert(tk.END, f"{'='*50}\n\n")
        
        score = results["overall_score"]
        level = results["compliance_level"]
        
        self.mcp_text.insert(tk.END, f"Overall Score: {score}%\n")
        self.mcp_text.insert(tk.END, f"Compliance Level: {level.value}\n\n")
        
        # Category scores
        self.mcp_text.insert(tk.END, "Category Scores:\n")
        for category, scores in results["category_scores"].items():
            cat_score = int((scores["score"] / scores["max"]) * 100) if scores["max"] > 0 else 0
            self.mcp_text.insert(tk.END, f"  • {category.replace('_', ' ').title()}: {cat_score}%\n")
            
        # Missing items
        structure = results["structure_analysis"]
        if structure["missing_required"]:
            self.mcp_text.insert(tk.END, f"\n❌ Missing Required:\n")
            for item in structure["missing_required"]:
                self.mcp_text.insert(tk.END, f"  • {item}\n")
                
        # Recommendations
        if results["recommendations"]:
            self.mcp_text.insert(tk.END, f"\n🚨 Recommendations:\n")
            for rec in results["recommendations"][:10]:  # Limit to first 10
                self.mcp_text.insert(tk.END, f"  • {rec}\n")
                
    def update_dependency_results(self):
        """Update dependency analysis results in GUI"""
        if 'dependency' not in self.analysis_results:
            return
            
        dep_data = self.analysis_results['dependency']
        results = dep_data['results']
        report = dep_data['report']
        
        # Clear and update dependency tab
        self.dep_text.delete(1.0, tk.END)
        
        # Summary
        self.dep_text.insert(tk.END, f"📦 Dependency Analysis Results\n")
        self.dep_text.insert(tk.END, f"{'='*50}\n\n")
        
        summary = report['summary']
        self.dep_text.insert(tk.END, f"Project Summary:\n")
        self.dep_text.insert(tk.END, f"  • Files analyzed: {summary['total_files_analyzed']}\n")
        self.dep_text.insert(tk.END, f"  • Total imports: {summary['total_imports']}\n")
        self.dep_text.insert(tk.END, f"  • External libraries: {summary['external_libraries']}\n")
        self.dep_text.insert(tk.END, f"  • Internal modules: {summary['internal_modules']}\n\n")
        
        # Findings
        self.dep_text.insert(tk.END, "Findings:\n")
        for category, finding_ids in results.items():
            if finding_ids:  # Only show categories with findings
                self.dep_text.insert(tk.END, f"  • {category.replace('_', ' ').title()}: {len(finding_ids)}\n")
                
        # Most used libraries
        usage_data = report['library_usage']
        if usage_data['most_used']:
            self.dep_text.insert(tk.END, f"\n📚 Most Used Libraries:\n")
            for lib, count in list(usage_data['most_used'].items())[:10]:
                self.dep_text.insert(tk.END, f"  • {lib}: {count} imports\n")
                
        # Least used (cleanup candidates)
        if usage_data['least_used']:
            self.dep_text.insert(tk.END, f"\n🧹 Least Used Libraries (cleanup candidates):\n")
            for lib, count in usage_data['least_used'][:5]:
                self.dep_text.insert(tk.END, f"  • {lib}: {count} imports\n")
                
    def update_llm_results(self):
        """Update LLM analysis results in GUI"""
        if 'llm' not in self.analysis_results:
            return
            
        llm_data = self.analysis_results['llm']
        report = llm_data['report']
        
        # Clear and update LLM tab
        self.llm_text.delete(1.0, tk.END)
        
        # Summary
        self.llm_text.insert(tk.END, f"🧠 LLM Analysis Results\n")
        self.llm_text.insert(tk.END, f"{'='*50}\n\n")
        
        self.llm_text.insert(tk.END, f"Project: {report.project_name}\n")
        self.llm_text.insert(tk.END, f"Overall Grade: {report.grade}\n")
        self.llm_text.insert(tk.END, f"Enterprise Readiness: {report.enterprise_readiness_pct}%\n\n")
        
        # Section verdicts
        sections = [
            ("Architecture", report.architecture_analysis),
            ("LLM Integration", report.llm_integration),
            ("Security", report.security),
            ("MLOps/Deployment", report.mlops_deployment),
            ("Observability", report.observability),
        ]
        
        self.llm_text.insert(tk.END, "Section Verdicts:\n")
        for name, analysis in sections:
            self.llm_text.insert(tk.END, f"  • {name}: {analysis.verdict}\n")
            
        # Critical improvements
        if report.top_critical_improvements:
            self.llm_text.insert(tk.END, f"\n🚨 Critical Improvements:\n")
            for i, item in enumerate(report.top_critical_improvements[:10], 1):
                self.llm_text.insert(tk.END, f"  {i}. {item}\n")
                
    def generate_integrated_report(self):
        """Generate integrated overview report"""
        # Clear and update overview tab
        self.overview_text.delete(1.0, tk.END)
        
        self.overview_text.insert(tk.END, f"🎯 Integrated Audit Report\n")
        self.overview_text.insert(tk.END, f"{'='*60}\n\n")
        self.overview_text.insert(tk.END, f"Project: {self.project_path.name}\n")
        self.overview_text.insert(tk.END, f"Path: {self.project_path}\n")
        self.overview_text.insert(tk.END, f"Analysis Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Analysis summary
        self.overview_text.insert(tk.END, f"📊 Analysis Summary\n")
        self.overview_text.insert(tk.END, f"{'-'*30}\n")
        
        completed_analyses = []
        if 'static' in self.analysis_results:
            completed_analyses.append("✅ Static Code Analysis")
        if 'mcp' in self.analysis_results:
            completed_analyses.append("✅ MCP Structure Validation")
        if 'dependency' in self.analysis_results:
            completed_analyses.append("✅ Dependency Analysis")
        if 'llm' in self.analysis_results:
            completed_analyses.append("✅ LLM Analysis")
            
        for analysis in completed_analyses:
            self.overview_text.insert(tk.END, f"{analysis}\n")
            
        # Key metrics
        self.overview_text.insert(tk.END, f"\n🔍 Key Metrics\n")
        self.overview_text.insert(tk.END, f"{'-'*30}\n")
        
        # Static analysis metrics
        if 'static' in self.analysis_results:
            static_data = self.analysis_results['static']
            enhanced_results = static_data['enhanced_results']
            total_findings = sum(len(findings) for findings in enhanced_results.values())
            critical_count = len(static_data['tracker'].get_by_severity(Severity.CRITICAL))
            
            self.overview_text.insert(tk.END, f"Code Issues Found: {total_findings}\n")
            self.overview_text.insert(tk.END, f"Critical Issues: {critical_count}\n")
            
        # MCP metrics
        if 'mcp' in self.analysis_results:
            mcp_data = self.analysis_results['mcp']
            results = mcp_data['results']
            self.overview_text.insert(tk.END, f"MCP Compliance Score: {results['overall_score']}%\n")
            
        # Dependency metrics
        if 'dependency' in self.analysis_results:
            dep_data = self.analysis_results['dependency']
            report = dep_data['report']
            summary = report['summary']
            self.overview_text.insert(tk.END, f"External Dependencies: {summary['external_libraries']}\n")
            
            # Count dependency issues
            total_dep_issues = sum(len(findings) for findings in dep_data['results'].values())
            if total_dep_issues > 0:
                self.overview_text.insert(tk.END, f"Dependency Issues: {total_dep_issues}\n")
                
        # LLM metrics
        if 'llm' in self.analysis_results:
            llm_data = self.analysis_results['llm']
            report = llm_data['report']
            self.overview_text.insert(tk.END, f"Overall Grade: {report.grade}\n")
            self.overview_text.insert(tk.END, f"Enterprise Readiness: {report.enterprise_readiness_pct}%\n")
            
        # Overall assessment
        self.overview_text.insert(tk.END, f"\n🎯 Overall Assessment\n")
        self.overview_text.insert(tk.END, f"{'-'*30}\n")
        
        # Calculate overall health score
        health_score = self.calculate_overall_health()
        self.overview_text.insert(tk.END, f"Overall Health Score: {health_score}%\n")
        
        if health_score >= 80:
            self.overview_text.insert(tk.END, "Status: 🟢 Excellent\n")
        elif health_score >= 60:
            self.overview_text.insert(tk.END, "Status: 🟡 Good\n")
        elif health_score >= 40:
            self.overview_text.insert(tk.END, "Status: 🟠 Needs Improvement\n")
        else:
            self.overview_text.insert(tk.END, "Status: 🔴 Critical Issues\n")
            
        # Top recommendations
        self.overview_text.insert(tk.END, f"\n💡 Top Recommendations\n")
        self.overview_text.insert(tk.END, f"{'-'*30}\n")
        
        recommendations = self.generate_top_recommendations()
        for i, rec in enumerate(recommendations[:5], 1):
            self.overview_text.insert(tk.END, f"{i}. {rec}\n")
            
    def calculate_overall_health(self) -> int:
        """Calculate overall project health score"""
        scores = []
        
        # Static analysis score (inverse of issues found)
        if 'static' in self.analysis_results:
            static_data = self.analysis_results['static']
            enhanced_results = static_data['enhanced_results']
            total_findings = sum(len(findings) for findings in enhanced_results.values())
            # Score based on few issues = higher score
            static_score = max(0, 100 - (total_findings * 2))  # Each issue reduces score by 2 points
            scores.append(min(100, static_score))
            
        # MCP compliance score
        if 'mcp' in self.analysis_results:
            mcp_data = self.analysis_results['mcp']
            scores.append(mcp_data['results']['overall_score'])
            
        # Dependency health score
        if 'dependency' in self.analysis_results:
            dep_data = self.analysis_results['dependency']
            total_dep_issues = sum(len(findings) for findings in dep_data['results'].values())
            dep_score = max(0, 100 - (total_dep_issues * 3))  # Each dependency issue reduces score by 3 points
            scores.append(min(100, dep_score))
            
        # LLM enterprise readiness
        if 'llm' in self.analysis_results:
            llm_data = self.analysis_results['llm']
            scores.append(llm_data['report'].enterprise_readiness_pct)
            
        return int(sum(scores) / len(scores)) if scores else 0
        
    def generate_top_recommendations(self) -> list:
        """Generate top recommendations across all analyses"""
        recommendations = []
        
        # Critical code issues
        if 'static' in self.analysis_results:
            static_data = self.analysis_results['static']
            critical_count = len(static_data['tracker'].get_by_severity(Severity.CRITICAL))
            if critical_count > 0:
                recommendations.append(f"Address {critical_count} critical code issues immediately")
                
        # MCP compliance
        if 'mcp' in self.analysis_results:
            mcp_data = self.analysis_results['mcp']
            results = mcp_data['results']
            if results['overall_score'] < 80:
                recommendations.append("Improve MCP structure compliance for better project organization")
                
        # Dependency cleanup
        if 'dependency' in self.analysis_results:
            dep_data = self.analysis_results['dependency']
            if 'unused_imports' in dep_data['results'] and dep_data['results']['unused_imports']:
                count = len(dep_data['results']['unused_imports'])
                recommendations.append(f"Remove {count} unused imports to clean up code")
                
        # LLM improvements
        if 'llm' in self.analysis_results:
            llm_data = self.analysis_results['llm']
            if llm_data['report'].top_critical_improvements:
                recommendations.append(llm_data['report'].top_critical_improvements[0])
                
        return recommendations
        
    def clear_results(self):
        """Clear all results"""
        self.overview_text.delete(1.0, tk.END)
        self.mcp_text.delete(1.0, tk.END)
        self.dep_text.delete(1.0, tk.END)
        self.code_text.delete(1.0, tk.END)
        self.llm_text.delete(1.0, tk.END)
        self.logs_text.delete(1.0, tk.END)
        self.analysis_results = {}
        
    def export_report(self):
        """Export comprehensive report"""
        if not self.analysis_results:
            messagebox.showwarning("No Results", "No analysis results to export.")
            return
            
        # Choose save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.generate_markdown_report(file_path)
                messagebox.showinfo("Export Complete", f"Report exported to: {file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export report: {str(e)}")
                
    def export_json(self):
        """Export results as JSON"""
        if not self.analysis_results:
            messagebox.showwarning("No Results", "No analysis results to export.")
            return
            
        # Choose save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                # Prepare JSON data
                json_data = {
                    'project_path': str(self.project_path),
                    'analysis_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'overall_health': self.calculate_overall_health(),
                    'results': {}
                }
                
                # Convert results to JSON-serializable format
                for key, value in self.analysis_results.items():
                    if key == 'static':
                        json_data['results'][key] = {
                            'enhanced_results': value['enhanced_results'],
                            'graph_info': value['graph_info'],
                            'total_findings': sum(len(f) for f in value['enhanced_results'].values())
                        }
                    elif key == 'mcp':
                        json_data['results'][key] = value['results']
                    elif key == 'dependency':
                        json_data['results'][key] = {
                            'results': value['results'],
                            'report': value['report']
                        }
                    elif key == 'llm':
                        json_data['results'][key] = {
                            'grade': value['report'].grade,
                            'enterprise_readiness_pct': value['report'].enterprise_readiness_pct,
                            'top_critical_improvements': value['report'].top_critical_improvements
                        }
                        
                with open(file_path, 'w') as f:
                    json.dump(json_data, f, indent=2, default=str)
                    
                messagebox.showinfo("Export Complete", f"JSON data exported to: {file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export JSON: {str(e)}")
                
    def generate_markdown_report(self, file_path: str):
        """Generate comprehensive markdown report"""
        with open(file_path, 'w') as f:
            f.write("# AI Engineering Guardian - Integrated Audit Report\n\n")
            f.write(f"**Project:** {self.project_path.name}\n")
            f.write(f"**Path:** {self.project_path}\n")
            f.write(f"**Analysis Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Overall health
            health_score = self.calculate_overall_health()
            f.write(f"## Overall Health Score: {health_score}%\n\n")
            
            # Analysis sections
            if 'static' in self.analysis_results:
                f.write("## Static Code Analysis\n\n")
                static_data = self.analysis_results['static']
                enhanced_results = static_data['enhanced_results']
                total_findings = sum(len(findings) for findings in enhanced_results.values())
                f.write(f"- **Total Issues Found:** {total_findings}\n")
                
                # Category breakdown
                for category, findings in enhanced_results.items():
                    if findings:
                        f.write(f"- **{category.replace('_', ' ').title()}:** {len(findings)}\n")
                f.write("\n")
                
            if 'mcp' in self.analysis_results:
                f.write("## MCP Structure Validation\n\n")
                mcp_data = self.analysis_results['mcp']
                results = mcp_data['results']
                f.write(f"- **Compliance Score:** {results['overall_score']}%\n")
                f.write(f"- **Compliance Level:** {results['compliance_level'].value}\n\n")
                
            if 'dependency' in self.analysis_results:
                f.write("## Dependency Analysis\n\n")
                dep_data = self.analysis_results['dependency']
                report = dep_data['report']
                summary = report['summary']
                f.write(f"- **Files Analyzed:** {summary['total_files_analyzed']}\n")
                f.write(f"- **External Libraries:** {summary['external_libraries']}\n")
                f.write(f"- **Total Import Issues:** {sum(len(f) for f in dep_data['results'].values())}\n\n")
                
            if 'llm' in self.analysis_results:
                f.write("## LLM Analysis\n\n")
                llm_data = self.analysis_results['llm']
                report = llm_data['report']
                f.write(f"- **Overall Grade:** {report.grade}\n")
                f.write(f"- **Enterprise Readiness:** {report.enterprise_readiness_pct}%\n\n")
                
            # Recommendations
            f.write("## Top Recommendations\n\n")
            recommendations = self.generate_top_recommendations()
            for i, rec in enumerate(recommendations, 1):
                f.write(f"{i}. {rec}\n")
                

def main():
    """Main entry point for the GUI"""
    root = tk.Tk()
    app = IntegratedAuditorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
