#!/usr/bin/env python3
"""
Simple fix for jose package conflicts without Unicode characters.
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and show results."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("SUCCESS")
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"FAILED: {e}")
        if e.stdout:
            print(f"Stdout: {e.stdout}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return False

def main():
    """Simple fix routine."""
    print("JOSE PACKAGE FIX")
    print("=" * 30)

    # Step 1: Force remove ALL jose packages
    print("\n1. Removing ALL jose packages...")
    jose_packages = ['jose', 'python-jose', 'python-jose[cryptography]']

    for pkg in jose_packages:
        run_command([sys.executable, '-m', 'pip', 'uninstall', '-y', pkg],
                   f"Uninstalling {pkg}")

    # Step 2: Clear pip cache
    print("\n2. Clearing pip cache...")
    run_command([sys.executable, '-m', 'pip', 'cache', 'purge'],
               "Clearing pip cache")

    # Step 3: Install the correct package
    print("\n3. Installing correct python-jose...")
    if not run_command([sys.executable, '-m', 'pip', 'install', 'python-jose==3.3.0'],
                      "Installing python-jose==3.3.0"):
        print("Trying alternative installation...")
        run_command([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', 'python-jose'],
                   "Installing python-jose (no cache)")

    # Step 4: Test import
    print("\n4. Testing import...")
    try:
        from jose import jwt as jose_jwt
        print("SUCCESS: jose import working!")

        # Test a simple operation
        token = jose_jwt.encode({'test': 'data'}, 'secret', algorithm='HS256')
        decoded = jose_jwt.decode(token, 'secret', algorithms=['HS256'])
        print(f"SUCCESS: jose operations working: {decoded}")

    except Exception as e:
        print(f"FAILED: Import test failed: {e}")
        return False

    print("\nSUCCESS! Try running 'python app.py' now.")
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted by user")
        sys.exit(1)