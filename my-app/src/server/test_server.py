#!/usr/bin/env python3
"""
Minimal test server for CareConnector without authentication.
Use this to test if the basic server functionality works.
"""

import os
import sys
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=['http://localhost:3000'])

# In-memory storage for testing
test_profiles = {}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': 'test-1.0.0',
        'message': 'Test server running without authentication'
    })

@app.route('/api/patient/profile', methods=['GET'])
def get_patient_profile():
    """Get patient profile (test mode - no auth)"""
    # Use a test user ID
    user_id = 'test-user-123'

    if user_id in test_profiles:
        return jsonify(test_profiles[user_id])
    else:
        return jsonify({'message': 'Patient profile not found'}), 404

@app.route('/api/patient/profile', methods=['POST'])
def create_patient_profile():
    """Create patient profile (test mode - no auth)"""
    user_id = 'test-user-123'

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        print(f"[Test Server] Received profile data: {json.dumps(data, indent=2)}")

        # Validate required personal info
        if 'personal_info' not in data:
            return jsonify({'error': 'Personal information is required'}), 400

        personal_info = data['personal_info']
        required_fields = ['date_of_birth', 'gender', 'phone', 'address']
        missing_fields = []

        for field in required_fields:
            if field not in personal_info or not personal_info[field]:
                missing_fields.append(field)

        if missing_fields:
            return jsonify({'error': f'Missing required personal information: {", ".join(missing_fields)}'}), 400

        # Create profile with defaults
        profile_data = {
            'user_id': user_id,
            'personal_info': personal_info,
            'medical_info': data.get('medical_info', {
                'allergies': [],
                'medications': [],
                'conditions': [],
                'insurance': {'provider': '', 'policy_number': ''}
            }),
            'preferences': data.get('preferences', {
                'communication_method': 'email',
                'appointment_reminders': True,
                'health_tips': False
            }),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        # Store the profile
        test_profiles[user_id] = profile_data

        print(f"[Test Server] Created profile for {user_id}")

        return jsonify({
            'message': 'Profile created successfully',
            'profile': profile_data
        }), 201

    except Exception as e:
        print(f"[Test Server] Error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/patient/profile', methods=['PUT'])
def update_patient_profile():
    """Update patient profile (test mode - no auth)"""
    user_id = 'test-user-123'

    try:
        updates = request.get_json()
        if not updates:
            return jsonify({'error': 'No update data provided'}), 400

        if user_id in test_profiles:
            test_profiles[user_id].update(updates)
            test_profiles[user_id]['updated_at'] = datetime.utcnow().isoformat()
            return jsonify({'message': 'Profile updated successfully'})
        else:
            return jsonify({'error': 'Profile not found'}), 404

    except Exception as e:
        print(f"[Test Server] Error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/test/status', methods=['GET'])
def test_status():
    """Test endpoint to show server status"""
    return jsonify({
        'server': 'Test Server (No Auth)',
        'profiles_stored': len(test_profiles),
        'profiles': list(test_profiles.keys()),
        'endpoints': [
            'GET /api/health',
            'GET /api/patient/profile',
            'POST /api/patient/profile',
            'PUT /api/patient/profile',
            'GET /api/test/status'
        ]
    })

if __name__ == '__main__':
    print("=" * 50)
    print("CareConnector Test Server")
    print("=" * 50)
    print("This is a minimal server without authentication")
    print("Use this to test if your frontend can connect")
    print("")
    print("Available endpoints:")
    print("  GET  /api/health")
    print("  GET  /api/patient/profile")
    print("  POST /api/patient/profile")
    print("  PUT  /api/patient/profile")
    print("  GET  /api/test/status")
    print("")
    print("Frontend should connect to: http://localhost:5000")
    print("=" * 50)

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )