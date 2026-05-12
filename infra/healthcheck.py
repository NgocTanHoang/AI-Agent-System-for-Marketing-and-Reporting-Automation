#!/usr/bin/env python3
"""
Health check script for AI Marketing Agent System Docker container.
"""

import os
import sys
import json
from pathlib import Path
import subprocess
from datetime import datetime

def check_file_exists(filepath):
    """Check if a file exists."""
    return Path(filepath).exists()

def check_directory_exists(dirpath):
    """Check if a directory exists."""
    return Path(dirpath).exists() and Path(dirpath).is_dir()

def check_docker_container_status():
    """Check if Docker container is running."""
    try:
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=ai-marketing-agent', '--format', '{{.Status}}'],
            capture_output=True, text=True, timeout=10
        )
        return 'Up' in result.stdout
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_python_availability():
    """Check if Python is available."""
    try:
        result = subprocess.run(
            ['python', '--version'],
            capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_required_directories():
    """Check if required directories exist and are writable."""
    required_dirs = [
        'data/raw/marketing_content',
        'data/processed',
        'logs'
    ]

    for dir_path in required_dirs:
        if not check_directory_exists(dir_path):
            return False, f"Directory {dir_path} does not exist"

        # Check if writable
        test_file = Path(dir_path) / '.write_test'
        try:
            test_file.touch()
            test_file.unlink()
        except (PermissionError, OSError):
            return False, f"Directory {dir_path} is not writable"

    return True, "All directories exist and are writable"

def check_import_modules():
    """Check if required Python modules can be imported."""
    required_modules = [
        'crewai',
        'litellm',
        'pydantic',
        'python_dotenv',
        'pandas',
        'duckduckgo_search',
        'sentence_transformers',
        'matplotlib',
        'fastapi',
        'uvicorn',
        'markdown',
        'chromadb'
    ]

    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)

    return len(missing_modules) == 0, missing_modules

def main():
    """Main health check function."""
    print(f"[{datetime.now().isoformat()}] Performing health check...")

    checks = []

    # Check 1: Docker container status
    if 'DOCKER_CONTAINER' in os.environ:
        docker_status = check_docker_container_status()
        checks.append(('Docker Container Status', docker_status))
        if not docker_status:
            print("ERROR: Docker container is not running properly")

    # Check 2: Python availability
    python_status = check_python_availability()
    checks.append(('Python Availability', python_status))
    if not python_status:
        print("ERROR: Python is not available")

    # Check 3: Required directories
    dirs_status, dirs_msg = check_required_directories()
    checks.append(('Required Directories', dirs_status))
    if not dirs_status:
        print(f"ERROR: {dirs_msg}")

    # Check 4: Required Python modules
    modules_status, modules_msg = check_import_modules()
    checks.append(('Required Python Modules', modules_status))
    if not modules_status:
        print(f"ERROR: Missing Python modules: {modules_msg}")

    # Summary
    passed_checks = sum(1 for _, status in checks if status)
    total_checks = len(checks)

    print(f"Health check completed: {passed_checks}/{total_checks} checks passed")

    if passed_checks == total_checks:
        print("STATUS: HEALTHY")
        sys.exit(0)
    else:
        print("STATUS: UNHEALTHY")
        sys.exit(1)

if __name__ == '__main__':
    main()