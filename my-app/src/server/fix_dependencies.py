#!/usr/bin/env python3
"""
Fix dependencies script for CareConnector server.
This script helps resolve common dependency conflicts.
"""

import subprocess
import sys
import os

def uninstall_conflicting_packages():
    """Remove conflicting jose packages."""
    print("Removing conflicting packages...")

    conflicting_packages = ['jose', 'python-jose[cryptography]']

    for package in conflicting_packages:
        try:
            print(f"  Uninstalling {package}...")
            subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', package],
                         capture_output=True, check=False)
        except Exception as e:
            print(f"    Warning: {e}")

def install_correct_packages():
    """Install the correct packages."""
    print("Installing correct packages...")

    packages = [
        'python-jose>=3.3.0',
        'flask>=2.3.0',
        'flask-cors>=4.0.0',
        'boto3>=1.26.0',
        'botocore>=1.29.0',
        'requests>=2.28.0',
        'python-dotenv>=1.0.0'
    ]

    for package in packages:
        try:
            print(f"  Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        except subprocess.CalledProcessError as e:
            print(f"    Error installing {package}: {e}")
            return False

    return True

def test_imports():
    """Test that imports work correctly."""
    print("Testing imports...")

    try:
        from jose import jwt as jose_jwt
        print("  jose.jwt: OK")
    except ImportError as e:
        print(f"  jose.jwt: FAILED - {e}")
        return False

    try:
        import flask
        print(f"  flask: OK ({flask.__version__})")
    except ImportError as e:
        print(f"  flask: FAILED - {e}")
        return False

    try:
        import flask_cors
        print(f"  flask_cors: OK")
    except ImportError as e:
        print(f"  flask_cors: FAILED - {e}")
        return False

    try:
        import boto3
        print(f"  boto3: OK ({boto3.__version__})")
    except ImportError as e:
        print(f"  boto3: FAILED - {e}")
        return False

    return True

def main():
    """Main fix routine."""
    print("CareConnector Dependencies Fix")
    print("=" * 30)

    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")

    # Step 1: Remove conflicting packages
    uninstall_conflicting_packages()

    # Step 2: Install correct packages
    if not install_correct_packages():
        print("FAILED: Could not install packages")
        return False

    # Step 3: Test imports
    if not test_imports():
        print("FAILED: Import test failed")
        return False

    print("\nSUCCESS: Dependencies fixed!")
    print("You can now run: python app.py")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\nFix failed. You may need to:")
        print("1. Update pip: python -m pip install --upgrade pip")
        print("2. Use a virtual environment")
        print("3. Check Python version compatibility")
        sys.exit(1)