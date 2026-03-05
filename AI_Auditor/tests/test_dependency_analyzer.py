"""
Test suite for DependencyAnalyzer - Advanced dependency analysis
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.dependency_analyzer import DependencyAnalyzer


class TestDependencyAnalyzer:
    """Test dependency analysis functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = DependencyAnalyzer(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, filename: str, content: str):
        """Helper to create test files"""
        file_path = Path(self.temp_dir) / filename
        file_path.write_text(content)
        return file_path
    
    def test_unused_imports_detected(self):
        """Test detection of unused imports"""
        test_content = '''
import os  # Used
import sys  # Unused
import json  # Used
import requests  # Unused

def load_config():
    with open(os.path.join("config", "app.json"), 'r') as f:
        return json.load(f)
'''
        self.create_test_file("test_unused_imports.py", test_content)
        
        results = self.analyzer.analyze_imports_and_usage()
        unused_imports = results.get("unused_imports", [])
        
        # Should detect unused sys and requests imports
        assert len(unused_imports) >= 2, f"Expected at least 2 unused imports, got {len(unused_imports)}"
    
    def test_all_imports_used(self):
        """Test that used imports are not flagged"""
        test_content = '''
import os
import json
from pathlib import Path

def load_config():
    config_path = Path("config") / "app.json"
    with open(config_path, 'r') as f:
        return json.load(f)
'''
        self.create_test_file("test_all_used.py", test_content)
        
        results = self.analyzer.analyze_imports_and_usage()
        unused_imports = results.get("unused_imports", [])
        
        # Should not detect any unused imports
        assert len(unused_imports) == 0, f"Expected 0 unused imports, got {len(unused_imports)}"
    
    def test_dependency_report_generation(self):
        """Test dependency report generation"""
        test_content = '''
import os
import json
import sys
import requests
from pathlib import Path

def main():
    data = {"key": "value"}
    print(json.dumps(data))
'''
        self.create_test_file("test_report.py", test_content)
        
        report = self.analyzer.generate_dependency_report()
        
        # Verify report structure
        assert "summary" in report
        assert "library_usage" in report
        assert "import_frequency" in report
        assert "dependency_graph" in report
        
        # Verify summary data
        summary = report["summary"]
        assert summary["total_files_analyzed"] == 1
        assert summary["total_imports"] >= 4  # os, json, sys, requests, Path


if __name__ == "__main__":
    # Run tests if this file is executed directly
    pytest.main([__file__])
