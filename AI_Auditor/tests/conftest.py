"""
Pytest configuration and fixtures for AI Auditor tests
"""

import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_python_file(temp_project_dir):
    """Create a sample Python file for testing"""
    content = '''
import os
import json
from pathlib import Path

def load_config():
    """Load configuration from hardcoded path"""
    config_path = "/etc/myapp/production.yaml"
    with open(config_path, 'r') as f:
        return json.load(f)

def process_data():
    print("Processing data...")
    data = {"count": 10}
    print(f"Processed {data['count']} items")
    return data

if __name__ == "__main__":
    config = load_config()
    process_data()
'''
    file_path = temp_project_dir / "sample.py"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def requirements_file(temp_project_dir):
    """Create a sample requirements.txt file"""
    content = '''
pydantic>=2.0
networkx>=3.0
radon>=6.0
rich>=13.0
ollama>=0.1.0
pyyaml>=6.0
tenacity>=8.0
requests>=2.25.0
'''
    file_path = temp_project_dir / "requirements.txt"
    file_path.write_text(content)
    return file_path
