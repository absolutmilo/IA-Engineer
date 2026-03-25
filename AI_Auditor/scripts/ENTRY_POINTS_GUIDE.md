# AI Engineering Guardian - Entry Points Guide

## 🚀 Recommended Usage

### **Primary Entry Point (Recommended)**
```bash
# GUI Interface
python run_auditor.py --gui

# CLI Interface  
python run_auditor.py /path/to/project
```

### **Specialized Analysis Tools**
```bash
# Static Code Analysis Only
python enhanced_audit.py /path/to/project

# Dependency Analysis Only
python dependency_audit.py /path/to/project

# MCP Structure Validation Only
python mcp_structure_audit.py /path/to/project

# Complete Integrated Audit (LLM + All Analysis)
python main.py /path/to/project
```

### **PowerShell Alternative**
```powershell
# Windows PowerShell launcher
.\audit.ps1 -TargetDir "/path/to/project"
```

## 📁 File Organization

### **Keep These (Core)**
- ✅ `run_auditor.py` - **Main launcher** (GUI + CLI)
- ✅ `main.py` - **Complete integrated audit**
- ✅ `enhanced_audit.py` - **Specialized static analysis**
- ✅ `dependency_audit.py` - **Specialized dependency analysis**
- ✅ `mcp_structure_audit.py` - **Specialized MCP analysis**
- ✅ `audit.ps1` - **PowerShell launcher**

### **Move to `scripts/` Folder**
- 📁 `scripts/standalone/`
  - `enhanced_audit.py`
  - `dependency_audit.py` 
  - `mcp_structure_audit.py`
  - `audit.ps1`

### **Keep in Root**
- 📄 `run_auditor.py` (main entry point)
- 📄 `main.py` (integrated audit)
- 📄 `README.md` (documentation)

## 🎯 Simplified User Experience

### **For Most Users:**
```bash
# Just use this one command
python run_auditor.py --gui    # or
python run_auditor.py /path/to/project
```

### **For Advanced Users:**
```bash
# Specialized tools
python scripts/standalone/enhanced_audit.py /path/to/project
python scripts/standalone/dependency_audit.py /path/to/project
python scripts/standalone/mcp_structure_audit.py /path/to/project
```

### **For Complete Analysis:**
```bash
python scripts/standalone/main.py /path/to/project
```
