# 🚀 AI Engineering Guardian

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code Quality](https://img.shields.io/badge/code_quality-A+-brightgreen.svg)](https://github.com/your-org/ai-engineering-guardian)

> **Enterprise-grade AI code auditing platform** - Comprehensive analysis, MCP validation, dependency auditing, and LLM-powered insights for production-ready AI engineering.

---

## 🎯 What It Does

AI Engineering Guardian is a **comprehensive auditing platform** that transforms how AI engineering teams ensure code quality, architectural compliance, and production readiness. It combines static analysis, dependency auditing, MCP structure validation, and LLM-powered insights into one unified system.

### 🔍 Core Capabilities

- **🏗️ MCP Structure Validation** - Ensures Model Context Protocol compliance
- **📦 Dependency Analysis** - Identifies unused imports, circular dependencies, and bloat
- **🔍 Static Code Analysis** - Detects hardcoded paths, broad exceptions, print statements
- **🧠 LLM-Powered Auditing** - AI-driven architectural analysis and recommendations
- **📊 Integrated Reporting** - Unified reports with executive summaries and roadmaps
- **🖥️ Dual Interface** - Both GUI and CLI interfaces for different workflows

---

## 🚀 Quick Start

### Option 1: GUI Interface (Recommended)
```bash
# Clone and run the GUI
git clone https://github.com/your-org/ai-engineering-guardian.git
cd ai-engineering-guardian
python run_auditor.py --gui
```

### Option 2: CLI Interface
```bash
# Audit a project directly
python run_auditor.py --cli /path/to/your/project

# With debug logging
python run_auditor.py --cli /path/to/your/project --debug
```

### Option 3: Direct CLI (Advanced)
```bash
# Use main CLI directly
python main.py /path/to/project --debug
```

---

## 📋 Requirements

### System Requirements
- **Python 3.11+** - Modern Python features and performance
- **8GB+ RAM** - For large project analysis
- **2GB+ Disk Space** - For dependencies and reports

### Dependencies
```bash
# Core dependencies
pip install -r requirements.txt

# GUI dependencies (optional)
pip install tk  # Usually comes with Python

# Development dependencies
pip install -r requirements-dev.txt
```

### LLM Backend (Optional)
- **Ollama** (Recommended) - Local LLM inference
- **OpenAI API** - Cloud-based LLM access
- **Custom LLM** - Any OpenAI-compatible endpoint

---

## 🎯 What It Detects

### 🔴 Critical Issues (Deployment Blockers)
- **Hardcoded Absolute Paths** - `C:\Users\name\...` or `/usr/local/bin`
- **Security Vulnerabilities** - Hardcoded secrets, injection risks
- **Major Architectural Flaws** - Missing abstractions, tight coupling

### 🟡 High Priority Issues
- **LLM Integration Problems** - Direct client usage, no abstraction
- **Circular Dependencies** - Import cycles and coupling issues
- **Broad Exception Handlers** - `except:` or `except Exception:`

### 🟢 Medium Priority Issues
- **Print Statements** - Using `print()` instead of structured logging
- **Dependency Bloat** - Unused imports and oversized requirements
- **MCP Structure Violations** - Non-compliant project organization

---

## 📊 Output & Reports

### Audit Structure
```
audit_reports/
├── audit_project_name.json          # Complete audit data
├── audit_project_name.md           # Human-readable report
├── enhanced_findings/              # Detailed static analysis
│   ├── findings.json
│   ├── roadmap.json
│   └── summary.json
├── mcp_analysis/                 # MCP validation results
│   └── mcp_structure_report.json
├── dependency_analysis/            # Dependency audit results
│   ├── dependency_findings.json
│   └── dependency_report.json
└── logs/                        # Detailed execution logs
    ├── audit_YYYYMMDD_HHMMSS.log
    └── audit_YYYYMMDD_HHMMSS.jsonl
```

### Report Features
- **Executive Summary** - High-level overview and key metrics
- **Technical Details** - File/line specific findings
- **Prioritized Roadmap** - Phase-based improvement plan
- **Visual Dashboard** - GUI with real-time progress tracking
- **Export Options** - JSON, Markdown, PDF formats

---

## 🖥️ Interface Options

### GUI Dashboard
- **📊 Real-time Progress** - Live analysis updates
- **📑 Tabbed Results** - Organized by analysis type
- **⚙️ Configurable Options** - Enable/disable specific analyses
- **📤 Export Functions** - Multiple format support
- **🔍 Search & Filter** - Find specific issues quickly

### CLI Interface
- **⚡ Fast Execution** - Optimized for CI/CD pipelines
- **📈 Rich Output** - Colored console output with progress
- **🔧 Flexible Configuration** - Command-line options for all features
- **📋 Structured Logs** - Detailed debugging information

---

## 🔧 Configuration

### Basic Configuration
```yaml
# config/audit_config.yaml
llm:
  model: "llama3.2:3b-instruct-q4_0"
  api_base: "http://localhost:11434"
  section_timeout: 120

analysis:
  max_file_size_mb: 10
  exclude_patterns: [".venv", "__pycache__", ".git"]
  include_tests: false

output:
  format: "json"
  save_intermediate: true
```

### Advanced Configuration
```yaml
# MCP validation settings
mcp_validation:
  enabled: true
  strict_mode: false
  custom_requirements: []

# Dependency analysis settings
dependency_analysis:
  enabled: true
  check_licenses: true
  max_dependency_depth: 5

# Static analysis settings
static_analysis:
  enabled: true
  severity_threshold: "medium"
  custom_patterns: []
```

---

## 🔄 CI/CD Integration

### GitHub Actions
```yaml
name: AI Engineering Guardian Audit
on: [push, pull_request]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run AI Audit
        run: |
          python run_auditor.py --cli . --debug
      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: audit-results
          path: audit_reports/
```

### Quality Gates
```bash
#!/bin/bash
# Fail on critical issues
python run_auditor.py --cli . --output audit_results

critical_count=$(jq '.critical_issues_count' audit_results/summary.json)

if [ $critical_count -gt 0 ]; then
  echo "❌ Found $critical_count critical issues!"
  exit 1
else
  echo "✅ No critical issues found"
  exit 0
fi
```

---

## 📚 Documentation

### User Guides
- **[📖 Enhanced Audit Manual](docs/ENHANCED_AUDIT_MANUAL.md)** - Complete usage guide
- **[🔍 Logging Guide](docs/LOGGING_GUIDE.md)** - Debugging and troubleshooting
- **[🏗️ MCP Structure Guide](docs/MCP_STRUCTURE_GUIDE.md)** - MCP compliance details
- **[📦 Dependency Analysis Guide](docs/DEPENDENCY_ANALYSIS_GUIDE.md)** - Dependency management

### Technical Documentation
- **[🏢 Corporate Transformation Roadmap](docs/corporate_transformation_roadmap.md)** - Enterprise roadmap
- **[🔧 Configuration Reference](docs/CONFIG_REFERENCE.md)** - All configuration options
- **[🧪 Testing Guide](docs/TESTING_GUIDE.md)** - Running and writing tests

---

## 🏗️ Architecture

### Core Components
```
AI Engineering Guardian/
├── core/                          # Analysis engines
│   ├── audit_analyzer.py           # Main audit coordinator
│   ├── static_analyzer.py          # Static code analysis
│   ├── dependency_analyzer.py      # Dependency analysis
│   ├── mcp_structure_validator.py   # MCP validation
│   ├── dependency_graph.py         # Import graph analysis
│   └── findings_tracker.py         # Issue tracking
├── llm/                          # LLM integration
│   ├── llm_client.py              # LLM client abstraction
│   ├── prompts.py                 # Analysis prompts
│   └── structure.py               # Result structures
├── utils/                         # Utilities
│   ├── reporter.py                 # Report generation
│   └── logger.py                 # Logging system
├── integrated_auditor_gui.py       # GUI interface
├── main.py                       # CLI interface
└── run_auditor.py               # Unified launcher
```

### Data Flow
1. **Project Discovery** - Scan and analyze project structure
2. **Multi-Modal Analysis** - Run static, dependency, MCP, and LLM analysis
3. **Result Integration** - Combine findings from all analyzers
4. **Report Generation** - Create unified reports and roadmaps
5. **Export & Display** - Present results via GUI or CLI

---

## 🧪 Development

### Setup Development Environment
```bash
# Clone repository
git clone https://github.com/your-org/ai-engineering-guardian.git
cd ai-engineering-guardian

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v
```

### Running Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific test file
pytest tests/test_audit_analyzer.py -v
```

### Code Style
```bash
# Check code style
flake8 core/ llm/ utils/

# Type checking
mypy core/

# Security scanning
bandit -r core/
```

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### How to Contribute
1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Contribution Areas
- **🔍 New Analysis Types** - Add new detection patterns
- **🌐 LLM Integration** - Support for new LLM providers
- **📊 Report Formats** - Add new export formats
- **🖥️ GUI Improvements** - Enhance user experience
- **📚 Documentation** - Improve guides and examples

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **NetworkX** - Dependency graph analysis
- **Rich** - Beautiful terminal output
- **Pydantic** - Data validation and serialization
- **FastAPI** - API framework (for future web interface)
- **Ollama** - Local LLM inference support

---

## 📞 Support

### Getting Help
- **📖 Documentation** - Check the [docs/](docs/) folder first
- **🐛 Issues** - [Open an issue](https://github.com/your-org/ai-engineering-guardian/issues)
- **💬 Discussions** - [GitHub Discussions](https://github.com/your-org/ai-engineering-guardian/discussions)
- **📧 Email** - support@yourcompany.com (enterprise support)

### Common Issues
- **Import Errors** - Ensure all dependencies are installed
- **LLM Connection** - Check Ollama is running and accessible
- **Memory Issues** - Increase RAM or reduce analysis scope
- **Permission Errors** - Ensure read access to target project

---

## 🎉 What's Next?

### Upcoming Features
- **🌐 Web Interface** - Browser-based dashboard
- **🔌 Plugin System** - Custom analysis plugins
- **📱 Mobile App** - On-the-go audit results
- **🤖 Auto-Fix** - Automated issue resolution
- **📈 Team Analytics** - Organization-wide insights

### Roadmap
See our [Corporate Transformation Roadmap](docs/corporate_transformation_roadmap.md) for detailed plans.

---

<div align="center">

**🚀 Transform your AI engineering with confidence!**

[⭐ Star this repo](https://github.com/your-org/ai-engineering-guardian) | 
[🐛 Report issues](https://github.com/your-org/ai-engineering-guardian/issues) | 
[💬 Start discussion](https://github.com/your-org/ai-engineering-guardian/discussions)

</div>
