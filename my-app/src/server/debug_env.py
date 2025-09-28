#!/usr/bin/env python3
"""
Debug script to check environment configuration for the CareConnector app.
Run this to identify potential configuration issues with Auth0, DynamoDB, etc.
"""

import os
import sys
import logging

# Add backend path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_environment():
    """Check all environment variables and configurations."""
    print("CareConnector Environment Debug Check")
    print("=" * 50)

    # Auth0 Configuration
    print("\n1. Auth0 Configuration:")
    auth0_domain = os.getenv('AUTH0_DOMAIN')
    auth0_audience = os.getenv('AUTH0_AUDIENCE')

    print(f"   AUTH0_DOMAIN: {auth0_domain}")
    print(f"   AUTH0_AUDIENCE: {auth0_audience}")

    if not auth0_domain:
        print("   WARNING: AUTH0_DOMAIN not set")
    if not auth0_audience:
        print("   WARNING: AUTH0_AUDIENCE not set")

    # AWS Configuration
    print("\n2. AWS Configuration:")
    aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-2')
    table_name = os.getenv('PATIENTS_TABLE_NAME', 'careconnector-main')

    print(f"   AWS_DEFAULT_REGION: {aws_region}")
    print(f"   PATIENTS_TABLE_NAME: {table_name}")

    # AgentMail Configuration
    print("\n3. AgentMail Configuration:")
    agentmail_key = os.getenv('AGENTMAIL_API_KEY')
    agentmail_url = os.getenv('AGENTMAIL_BASE_URL', 'https://api.agentmail.com')

    print(f"   AGENTMAIL_API_KEY: {'[SET]' if agentmail_key else '[NOT SET]'}")
    print(f"   AGENTMAIL_BASE_URL: {agentmail_url}")

    # Flask Configuration
    print("\n4. Flask Configuration:")
    flask_debug = os.getenv('FLASK_DEBUG', 'False')
    port = os.getenv('PORT', '5000')
    cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000')

    print(f"   FLASK_DEBUG: {flask_debug}")
    print(f"   PORT: {port}")
    print(f"   CORS_ORIGINS: {cors_origins}")

    # Try to import and initialize components
    print("\n5. Component Availability:")

    try:
        from dynamodb_utils import get_db_client, PatientRecord
        print("   DynamoDB Utils: AVAILABLE")

        try:
            db_client = get_db_client(table_name=table_name, region_name=aws_region)
            patient_ops = PatientRecord(db_client)
            print("   DynamoDB Client: INITIALIZED")
        except Exception as e:
            print(f"   DynamoDB Client: ERROR - {e}")

    except ImportError as e:
        print(f"   DynamoDB Utils: IMPORT ERROR - {e}")

    try:
        from agentmail_tool import create_inbox
        print("   AgentMail Tool: AVAILABLE")
    except ImportError as e:
        print(f"   AgentMail Tool: IMPORT ERROR - {e}")

    # Check for common issues
    print("\n6. Common Issues Check:")

    issues = []

    if not auth0_domain or not auth0_audience:
        issues.append("Auth0 configuration missing - users cannot authenticate")

    if not agentmail_key:
        issues.append("AgentMail API key missing - email features will not work")

    if flask_debug.lower() == 'true':
        issues.append("Flask debug mode enabled - ensure this is intentional")

    if cors_origins == 'http://localhost:3000' and port != '5000':
        issues.append("CORS origins may not match frontend URL")

    if issues:
        print("   POTENTIAL ISSUES FOUND:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    else:
        print("   No obvious issues found")

    # Development recommendations
    print("\n7. Development Setup Recommendations:")
    print("   For local development, create a .env file with:")
    print("   - AUTH0_DOMAIN=your-auth0-domain.auth0.com")
    print("   - AUTH0_AUDIENCE=your-api-identifier")
    print("   - AGENTMAIL_API_KEY=your-agentmail-key")
    print("   - FLASK_DEBUG=True")
    print("   - AWS credentials configured (aws configure or IAM role)")

    print("\n8. Quick Server Test:")
    try:
        import requests
        import time

        print("   Starting server test in 2 seconds...")
        time.sleep(2)

        # Try to hit the health endpoint
        try:
            response = requests.get(f"http://localhost:{port}/api/health", timeout=5)
            if response.status_code == 200:
                print("   Server Health Check: PASS")
                data = response.json()
                print(f"   Server Response: {data}")
            else:
                print(f"   Server Health Check: FAIL (Status: {response.status_code})")
        except requests.exceptions.ConnectionError:
            print("   Server Health Check: NOT RUNNING")
            print("   Start the server with: python app.py")
        except Exception as e:
            print(f"   Server Health Check: ERROR - {e}")

    except ImportError:
        print("   Requests not available, skipping server test")

if __name__ == "__main__":
    check_environment()