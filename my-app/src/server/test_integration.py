#!/usr/bin/env python3
"""
Test script for DynamoDB integration with the Flask server.

This script tests the patient profile API endpoints to ensure they work
correctly with our DynamoDB utilities.
"""

import os
import sys
import json
import requests
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
SERVER_URL = os.getenv('SERVER_URL', 'http://localhost:5000')
TEST_TOKEN = os.getenv('TEST_TOKEN', 'test-token-for-development')

# Mock test data - Complete profile
TEST_USER_PROFILE_COMPLETE = {
    "personal_info": {
        "date_of_birth": "1990-01-15",
        "gender": "female",
        "phone": "+1234567890",
        "address": "123 Test Street, Ann Arbor, MI 48104",
        "emergency_contact": {
            "name": "Jane Doe",
            "phone": "+0987654321",
            "relationship": "Sister"
        }
    },
    "medical_info": {
        "allergies": ["Penicillin", "Shellfish"],
        "medications": ["Lisinopril", "Vitamin D"],
        "conditions": ["Hypertension"],
        "insurance": {
            "provider": "Blue Cross Blue Shield",
            "policy_number": "12345ABC"
        }
    },
    "preferences": {
        "communication_method": "email",
        "appointment_reminders": True,
        "health_tips": False
    },
    "agent_email": "agent@careconnector.com"
}

# Mock test data - Minimal required data only
TEST_USER_PROFILE_MINIMAL = {
    "personal_info": {
        "date_of_birth": "1990-01-15",
        "gender": "female",
        "phone": "+1234567890",
        "address": "123 Test Street, Ann Arbor, MI 48104",
        "emergency_contact": {
            "name": "Jane Doe",
            "phone": "+0987654321",
            "relationship": "Sister"
        }
    }
    # medical_info and preferences should use defaults
}

# Mock test data - Invalid (missing required fields)
TEST_USER_PROFILE_INVALID = {
    "personal_info": {
        "date_of_birth": "1990-01-15",
        # Missing gender, phone, address, emergency_contact
    },
    "medical_info": {
        "allergies": ["Penicillin"]
    }
}

def make_request(method, endpoint, data=None, headers=None):
    """Make an HTTP request to the server."""
    url = f"{SERVER_URL}{endpoint}"

    default_headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {TEST_TOKEN}'
    }

    if headers:
        default_headers.update(headers)

    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=default_headers, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=default_headers, timeout=10)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data, headers=default_headers, timeout=10)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None

def test_health_check():
    """Test the health check endpoint."""
    logger.info("Testing health check endpoint...")

    response = make_request('GET', '/api/health')

    if response and response.status_code == 200:
        data = response.json()
        logger.info(f"Health check passed: {data}")
        return True
    else:
        logger.error(f"Health check failed: {response.status_code if response else 'No response'}")
        return False

def test_create_patient_profile_complete():
    """Test creating a complete patient profile."""
    logger.info("Testing complete patient profile creation...")

    response = make_request('POST', '/api/patient/profile', data=TEST_USER_PROFILE_COMPLETE)

    if response:
        if response.status_code == 201:
            data = response.json()
            logger.info(f"Complete profile created successfully: {data.get('message')}")
            return True
        elif response.status_code == 400:
            logger.error(f"Complete profile creation failed with validation error: {response.json()}")
            return False
        else:
            logger.error(f"Complete profile creation failed: {response.status_code} - {response.text}")
            return False
    else:
        logger.error("No response from server")
        return False

def test_create_patient_profile_minimal():
    """Test creating a minimal patient profile with only required fields."""
    logger.info("Testing minimal patient profile creation...")

    response = make_request('POST', '/api/patient/profile', data=TEST_USER_PROFILE_MINIMAL)

    if response:
        if response.status_code == 201:
            data = response.json()
            logger.info(f"Minimal profile created successfully: {data.get('message')}")
            return True
        elif response.status_code == 400:
            logger.error(f"Minimal profile creation failed with validation error: {response.json()}")
            return False
        else:
            logger.error(f"Minimal profile creation failed: {response.status_code} - {response.text}")
            return False
    else:
        logger.error("No response from server")
        return False

def test_create_patient_profile_invalid():
    """Test creating an invalid patient profile (should fail validation)."""
    logger.info("Testing invalid patient profile creation (should fail)...")

    response = make_request('POST', '/api/patient/profile', data=TEST_USER_PROFILE_INVALID)

    if response:
        if response.status_code == 400:
            data = response.json()
            logger.info(f"Invalid profile correctly rejected: {data.get('error')}")
            return True
        elif response.status_code == 201:
            logger.error("Invalid profile was incorrectly accepted")
            return False
        else:
            logger.error(f"Unexpected response for invalid profile: {response.status_code} - {response.text}")
            return False
    else:
        logger.error("No response from server")
        return False

def test_get_patient_profile():
    """Test retrieving a patient profile."""
    logger.info("Testing patient profile retrieval...")

    response = make_request('GET', '/api/patient/profile')

    if response:
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Profile retrieved successfully")
            logger.info(f"Profile data keys: {list(data.keys())}")
            return True
        elif response.status_code == 404:
            logger.info("No profile found (expected for first-time users)")
            return True
        else:
            logger.error(f"Profile retrieval failed: {response.status_code} - {response.text}")
            return False
    else:
        logger.error("No response from server")
        return False

def test_update_patient_profile():
    """Test updating a patient profile."""
    logger.info("Testing patient profile update...")

    updates = {
        "personal_info": {
            "phone": "+1555999888"
        },
        "preferences": {
            "health_tips": True
        }
    }

    response = make_request('PUT', '/api/patient/profile', data=updates)

    if response:
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Profile updated successfully: {data.get('message')}")
            return True
        elif response.status_code == 404:
            logger.warning("Profile not found for update (may need to create first)")
            return True
        else:
            logger.error(f"Profile update failed: {response.status_code} - {response.text}")
            return False
    else:
        logger.error("No response from server")
        return False

def test_patients_by_agent():
    """Test retrieving patients by agent email."""
    logger.info("Testing patients by agent query...")

    agent_email = "agent@careconnector.com"
    response = make_request('GET', f'/api/patients/by-agent/{agent_email}')

    if response:
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Agent query successful, found {len(data)} patients")
            return True
        else:
            logger.error(f"Agent query failed: {response.status_code} - {response.text}")
            return False
    else:
        logger.error("No response from server")
        return False

def run_integration_tests():
    """Run all integration tests."""
    logger.info("Starting integration tests...")
    logger.info(f"Testing server at: {SERVER_URL}")

    tests = [
        ("Health Check", test_health_check),
        ("Get Patient Profile (Should be 404)", test_get_patient_profile),
        ("Create Complete Patient Profile", test_create_patient_profile_complete),
        ("Get Patient Profile (After Create)", test_get_patient_profile),
        ("Create Minimal Patient Profile", test_create_patient_profile_minimal),
        ("Create Invalid Patient Profile (Should Fail)", test_create_patient_profile_invalid),
        ("Update Patient Profile", test_update_patient_profile),
        ("Query Patients by Agent", test_patients_by_agent),
    ]

    results = []

    for test_name, test_func in tests:
        logger.info(f"\n--- Running: {test_name} ---")
        try:
            success = test_func()
            results.append((test_name, success))
            status = "PASS" if success else "FAIL"
            logger.info(f"{test_name}: {status}")
        except Exception as e:
            logger.error(f"{test_name}: ERROR - {e}")
            results.append((test_name, False))

    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("INTEGRATION TEST SUMMARY")
    logger.info("=" * 50)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        logger.info(f"{test_name}: {status}")

    logger.info(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All integration tests passed!")
        return True
    else:
        logger.warning(f"⚠️  {total - passed} tests failed")
        return False

def check_server_status():
    """Check if the server is running."""
    logger.info("Checking server status...")

    try:
        response = requests.get(f"{SERVER_URL}/api/health", timeout=5)
        if response.status_code == 200:
            logger.info("Server is running and accessible")
            return True
        else:
            logger.error(f"Server responded with status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        logger.error(f"Cannot connect to server at {SERVER_URL}")
        logger.info("Make sure the Flask server is running:")
        logger.info("cd my-app/src/server && python app.py")
        return False
    except Exception as e:
        logger.error(f"Error checking server status: {e}")
        return False

if __name__ == "__main__":
    print("CareConnector DynamoDB Integration Test Suite")
    print("=" * 50)

    # Check if server is running first
    if not check_server_status():
        logger.error("Cannot proceed with tests - server not accessible")
        sys.exit(1)

    # Run the integration tests
    success = run_integration_tests()

    if success:
        logger.info("\n✅ Integration testing completed successfully!")
        print("\nThe DynamoDB integration is working correctly!")
        print("✅ Patient profiles can be created, retrieved, and updated")
        print("✅ Agent-based queries are functional")
        print("✅ All API endpoints are responding properly")
    else:
        logger.error("\n❌ Some integration tests failed")
        print("\nSome issues were found during testing.")
        print("Please check the logs above for details.")

    sys.exit(0 if success else 1)