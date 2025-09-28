#!/usr/bin/env python3
"""
Emergency fix for jose package conflicts.
This completely removes all jose packages and reinstalls the correct one.
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
        print("✓ Success")
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed: {e}")
        if e.stdout:
            print(f"Stdout: {e.stdout}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return False

def main():
    """Emergency fix routine."""
    print("EMERGENCY JOSE PACKAGE FIX")
    print("=" * 30)

    # Step 1: Show current packages
    print("\n1. Current jose-related packages:")
    subprocess.run([sys.executable, '-m', 'pip', 'list'], capture_output=False)

    # Step 2: Force remove ALL jose packages
    print("\n2. Removing ALL jose packages...")
    jose_packages = ['jose', 'python-jose', 'python-jose[cryptography]']

    for pkg in jose_packages:
        run_command([sys.executable, '-m', 'pip', 'uninstall', '-y', pkg],
                   f"Uninstalling {pkg}")

    # Step 3: Clear pip cache
    print("\n3. Clearing pip cache...")
    run_command([sys.executable, '-m', 'pip', 'cache', 'purge'],
               "Clearing pip cache")

    # Step 4: Install the correct package
    print("\n4. Installing correct python-jose...")
    if not run_command([sys.executable, '-m', 'pip', 'install', 'python-jose==3.3.0'],
                      "Installing python-jose==3.3.0"):
        print("Trying alternative installation...")
        run_command([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', 'python-jose'],
                   "Installing python-jose (no cache)")

    # Step 5: Install other requirements
    print("\n5. Installing other requirements...")
    other_packages = [
        'flask>=2.3.0',
        'flask-cors>=4.0.0',
        'boto3>=1.26.0',
        'requests>=2.28.0',
        'python-dotenv>=1.0.0'
    ]

    for pkg in other_packages:
        run_command([sys.executable, '-m', 'pip', 'install', pkg],
                   f"Installing {pkg}")

    # Step 6: Test import
    print("\n6. Testing import...")
    try:
        from jose import jwt as jose_jwt
        print("✓ jose import successful!")

        # Test a simple operation
        token = jose_jwt.encode({'test': 'data'}, 'secret', algorithm='HS256')
        decoded = jose_jwt.decode(token, 'secret', algorithms=['HS256'])
        print(f"✓ jose operations working: {decoded}")

    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False

    print("\n7. Final package list:")
    subprocess.run([sys.executable, '-m', 'pip', 'list', '|', 'grep', 'jose'],
                  shell=True, capture_output=False)

    print("\nSUCCESS! Try running 'python app.py' now.")
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted by user")
        sys.exit(1)