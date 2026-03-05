"""
Test suite for AuditAnalyzer - Enhanced code analysis functionality
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.audit_analyzer import AuditAnalyzer
from core.findings_tracker import Severity, Category


class TestHardcodedPathDetection:
    """Test hardcoded path detection with various scenarios"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = AuditAnalyzer(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, filename: str, content: str):
        """Helper to create test files"""
        file_path = Path(self.temp_dir) / filename
        file_path.write_text(content)
        return file_path
    
    def test_real_hardcoded_paths_detected(self):
        """Test that real hardcoded paths are detected"""
        test_content = '''
import os

def load_config():
    config_path = "/etc/myapp/production.yaml"
    with open(config_path, 'r') as f:
        return f.read()

data_dir = "C:\\Users\\myuser\\Documents\\app\\data"
log_file = "/var/log/myapp/application.log"
'''
        self.create_test_file("test_real_paths.py", test_content)
        
        results = self.analyzer.analyze_hardcoded_paths()
        
        # Should detect the real hardcoded paths
        assert len(results) >= 3, f"Expected at least 3 findings, got {len(results)}"
        
        # Check specific findings
        finding_descriptions = [self.analyzer.tracker.findings[fid].description for fid in results]
        
        assert any("production.yaml" in desc for desc in finding_descriptions), "Should detect /etc/myapp/production.yaml"
        assert any("Documents\\app\\data" in desc for desc in finding_descriptions), "Should detect C:\\Users\\myuser\\Documents\\app\\data"
        assert any("application.log" in desc for desc in finding_descriptions), "Should detect /var/log/myapp/application.log"
    
    def test_rich_console_formatting_ignored(self):
        """Test that Rich console formatting tags are ignored"""
        test_content = '''
from rich.console import Console

console = Console()
console.print(f"[bold]Analyzing project:[/bold] {project_name}")
console.print("[red]Error:[/red] Something went wrong")
console.print("[orange1]Warning:[/orange1] Check this")
console.print("[bold green]Success:[/bold green] Operation completed")
'''
        self.create_test_file("test_rich_formatting.py", test_content)
        
        results = self.analyzer.analyze_hardcoded_paths()
        
        # Should not detect any hardcoded paths from Rich formatting
        assert len(results) == 0, f"Expected 0 findings from Rich formatting, got {len(results)}"
    
    def test_comments_and_docstrings_ignored(self):
        """Test that paths in comments and docstrings are ignored"""
        test_content = '''
#!/usr/bin/env python3
"""
Example usage:
    config_path = "/etc/myapp/config.yaml"
    data_dir = "/usr/local/bin/myapp"
"""

# This should be ignored
# config_path = "/etc/myapp/config.yaml"

def example_function():
    """Docstring with path example:
       path = "/var/log/myapp.log"
    """
    pass

# TODO: Change this from C:\\Users\\name\\config to use env vars
'''
        self.create_test_file("test_comments_docstrings.py", test_content)
        
        results = self.analyzer.analyze_hardcoded_paths()
        
        # Should not detect any hardcoded paths from comments/docstrings
        assert len(results) == 0, f"Expected 0 findings from comments/docstrings, got {len(results)}"
    
    def test_urls_and_examples_ignored(self):
        """Test that URLs and example paths are ignored"""
        test_content = '''
# URLs should be ignored
api_url = "https://example.com/api/v1/data"
docs_url = "http://localhost:8080/docs"

# Example paths should be ignored
example_path = "/path/to/your/file"
sample_dir = "/example/directory/structure"
demo_config = "/demo/configuration/file.yaml"

# Placeholder patterns
path_to_file = "/path/to/your/file"
folder_path = "/some/folder/directory"
'''
        self.create_test_file("test_urls_examples.py", test_content)
        
        results = self.analyzer.analyze_hardcoded_paths()
        
        # Should not detect any hardcoded paths from URLs/examples
        assert len(results) == 0, f"Expected 0 findings from URLs/examples, got {len(results)}"
    
    def test_system_paths_ignored(self):
        """Test that common system paths are ignored"""
        test_content = '''
# System paths should be ignored
python_path = "C:\\Python311\\python.exe"
program_files = "C:\\Program Files\\MyApp"
unix_bin = "/usr/bin/python"
local_bin = "/usr/local/bin"
system_config = "/etc/system/config"
var_log = "/var/log/system"
'''
        self.create_test_file("test_system_paths.py", test_content)
        
        results = self.analyzer.analyze_hardcoded_paths()
        
        # Should not detect system paths
        assert len(results) == 0, f"Expected 0 findings from system paths, got {len(results)}"
    
    def test_mixed_scenarios(self):
        """Test mixed scenarios with both real and false positives"""
        test_content = '''
#!/usr/bin/env python3
"""
Module for testing path detection
"""

from rich.console import Console

# This should be ignored (comment)
# config_path = "/etc/myapp/config.yaml"

# This should be detected (real hardcoded path)
def get_config():
    config_file = "/etc/myapp/production.yaml"
    return config_file

# This should be ignored (Rich formatting)
console.print(f"[bold]Loading config:[/bold] {config_file}")

# This should be detected (another real path)
data_directory = "C:\\Users\\myuser\\Documents\\app\\data"

# This should be ignored (URL)
api_endpoint = "https://api.example.com/v1"

# This should be detected (real path)
log_location = "/var/log/myapp/application.log"
'''
        self.create_test_file("test_mixed.py", test_content)
        
        results = self.analyzer.analyze_hardcoded_paths()
        
        # Should detect exactly 3 real hardcoded paths
        assert len(results) == 3, f"Expected exactly 3 findings, got {len(results)}"
        
        # Verify the correct paths were detected
        finding_descriptions = [self.analyzer.tracker.findings[fid].description for fid in results]
        
        assert any("production.yaml" in desc for desc in finding_descriptions), "Should detect /etc/myapp/production.yaml"
        assert any("Documents\\app\\data" in desc for desc in finding_descriptions), "Should detect C:\\Users\\myuser\\Documents\\app\\data"
        assert any("application.log" in desc for desc in finding_descriptions), "Should detect /var/log/myapp/application.log"


class TestPrintStatementDetection:
    """Test print statement detection"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = AuditAnalyzer(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, filename: str, content: str):
        """Helper to create test files"""
        file_path = Path(self.temp_dir) / filename
        file_path.write_text(content)
        return file_path
    
    def test_print_statements_detected(self):
        """Test that print statements are detected"""
        test_content = '''
def process_data():
    print("Processing data...")
    print(f"Processed {count} items")
    print("Done")
'''
        self.create_test_file("test_prints.py", test_content)
        
        results = self.analyzer.analyze_print_statements()
        
        # Should detect all 3 print statements
        assert len(results) == 3, f"Expected 3 print statements, got {len(results)}"
    
    def test_prints_in_comments_ignored(self):
        """Test that print statements in comments are ignored"""
        test_content = '''
# print("This should be ignored")
# print(f"This too: {var}")
'''
        self.create_test_file("test_print_comments.py", test_content)
        
        results = self.analyzer.analyze_print_statements()
        
        # Should not detect any print statements
        assert len(results) == 0, f"Expected 0 findings from comments, got {len(results)}"


if __name__ == "__main__":
    # Run tests if this file is executed directly
    pytest.main([__file__])
