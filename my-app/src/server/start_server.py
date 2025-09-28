#!/usr/bin/env python3
"""
Startup script for the CareConnector Flask server.
This script helps diagnose and start the server properly.
"""

import os
import sys
import time
import subprocess
import requests
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are available."""
    print("Checking dependencies...")

    try:
        import flask
        print(f"  Flask: {flask.__version__}")
    except ImportError:
        print("  Flask: NOT INSTALLED")
        return False

    try:
        import flask_cors
        print(f"  Flask-CORS: {flask_cors.__version__}")
    except ImportError:
        print("  Flask-CORS: NOT INSTALLED")
        return False

    try:
        import boto3
        print(f"  Boto3: {boto3.__version__}")
    except ImportError:
        print("  Boto3: NOT INSTALLED")
        return False

    try:
        import jose
        print("  Python-JOSE: Available")
    except ImportError:
        print("  Python-JOSE: NOT INSTALLED")
        return False

    return True

def check_environment():
    """Check environment configuration."""
    print("\nChecking environment...")

    required_env = {
        'AUTH0_DOMAIN': os.getenv('AUTH0_DOMAIN'),
        'AUTH0_AUDIENCE': os.getenv('AUTH0_AUDIENCE'),
    }

    optional_env = {
        'AWS_DEFAULT_REGION': os.getenv('AWS_DEFAULT_REGION', 'us-east-2'),
        'PATIENTS_TABLE_NAME': os.getenv('PATIENTS_TABLE_NAME', 'careconnector-main'),
        'FLASK_DEBUG': os.getenv('FLASK_DEBUG', 'False'),
        'PORT': os.getenv('PORT', '5000'),
    }

    print("  Required:")
    for key, value in required_env.items():
        status = "SET" if value else "NOT SET"
        print(f"    {key}: {status}")

    print("  Optional:")
    for key, value in optional_env.items():
        print(f"    {key}: {value}")

    return all(required_env.values())

def install_dependencies():
    """Install missing dependencies."""
    print("\nInstalling dependencies...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False

def test_server_connectivity(port=5000, timeout=30):
    """Test if the server is responding."""
    print(f"\nTesting server connectivity on port {port}...")

    url = f"http://localhost:{port}/api/health"
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print(f"  Server is responding! Status: {response.status_code}")
                print(f"  Response: {response.json()}")
                return True
        except requests.exceptions.ConnectionError:
            pass
        except requests.exceptions.Timeout:
            pass

        time.sleep(1)

    print(f"  Server not responding after {timeout} seconds")
    return False

def start_server():
    """Start the Flask server."""
    print("\nStarting Flask server...")

    # Check if app.py exists
    if not os.path.exists('app.py'):
        print("ERROR: app.py not found in current directory")
        print("Make sure you're in the my-app/src/server directory")
        return False

    try:
        # Start the server
        print("Running: python app.py")
        print("Press Ctrl+C to stop the server")
        print("-" * 50)

        subprocess.run([sys.executable, 'app.py'])
        return True

    except KeyboardInterrupt:
        print("\nServer stopped by user")
        return True
    except Exception as e:
        print(f"Failed to start server: {e}")
        return False

def main():
    """Main startup routine."""
    print("CareConnector Flask Server Startup")
    print("=" * 40)

    # Check current directory
    cwd = os.getcwd()
    print(f"Current directory: {cwd}")

    if not cwd.endswith(os.path.join('my-app', 'src', 'server')):
        print("\nWARNING: You should run this from the my-app/src/server directory")
        print("Expected path ending: my-app/src/server")
        print("Current path ending:", os.path.sep.join(Path(cwd).parts[-3:]))

    # Check dependencies
    if not check_dependencies():
        print("\nMissing dependencies. Attempting to install...")
        if not install_dependencies():
            print("FAILED: Could not install dependencies")
            print("Please run: pip install -r requirements.txt")
            return False

    # Check environment
    env_ok = check_environment()
    if not env_ok:
        print("\nWARNING: Missing required environment variables")
        print("The server will run in development mode")
        print("Set AUTH0_DOMAIN and AUTH0_AUDIENCE for full functionality")

    # Check if server is already running
    if test_server_connectivity(timeout=3):
        print("\nServer appears to already be running!")
        choice = input("Start anyway? (y/N): ").lower()
        if choice != 'y':
            return True

    # Start the server
    return start_server()

if __name__ == "__main__":
    success = main()
    if not success:
        print("\nStartup failed. Please check the errors above.")
        sys.exit(1)