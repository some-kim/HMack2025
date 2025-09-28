# app.py
import os
import sys
import json
import boto3
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Dict, Any, List

import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import jose
from botocore.exceptions import ClientError
from werkzeug.exceptions import BadRequest

# Add the backend directory to the Python path to import agentmail_tool
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))
try:
    from agentmail_tool import create_inbox
except ImportError as e:
    logging.warning(f"Could not import agentmail_tool: {e}")
    create_inbox = None


# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# CORS configuration
CORS(app, origins=os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(','))

# Auth0 Configuration
AUTH0_DOMAIN = os.getenv('AUTH0_DOMAIN')
AUTH0_AUDIENCE = os.getenv('AUTH0_AUDIENCE')
ALGORITHMS = ['RS256']

# AWS Configuration
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-2')

# DynamoDB Table Names
PATIENTS_TABLE = os.getenv('PATIENTS_TABLE_NAME', 'careconnector-patients')

# AgentMail Configuration
AGENTMAIL_API_KEY = os.getenv('AGENTMAIL_API_KEY')
AGENTMAIL_BASE_URL = os.getenv('AGENTMAIL_BASE_URL', 'https://api.agentmail.com')

# Initialize DynamoDB
try:
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    patients_table = dynamodb.Table(PATIENTS_TABLE)
except Exception as e:
    app.logger.error(f"Failed to initialize DynamoDB: {e}")
    # For local development, you might want to use mock tables
    patients_table = None

# In-memory storage for development when DynamoDB is not available
dev_patient_profiles = {}
dev_appointments = {}
dev_messages = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Auth0 JWT Token Validation
class AuthError(Exception):
    """Custom Auth Error Exception"""
    def __init__(self, error: Dict[str, str], status_code: int):
        self.error = error
        self.status_code = status_code

def get_token_auth_header() -> str:
    """Obtains the Access Token from the Authorization Header"""
    auth_header = request.headers.get('Authorization', None)
    
    if not auth_header:
        raise AuthError({
            'code': 'authorization_header_missing',
            'description': 'Authorization header is expected.'
        }, 401)

    parts = auth_header.split()

    if parts[0].lower() != 'bearer':
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must start with "Bearer".'
        }, 401)

    if len(parts) == 1:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Token not found.'
        }, 401)

    if len(parts) > 2:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must be bearer token.'
        }, 401)

    return parts[1]

def verify_decode_jwt(token: str) -> Dict[str, Any]:
    """Verifies and decodes the JWT token"""
    try:
        # Get the public key from Auth0
        jsonurl = requests.get(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
        jwks = jsonurl.json()
        
        unverified_header = jose.jwt.get_unverified_header(token)
        rsa_key = {}
        
        if 'kid' not in unverified_header:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Authorization malformed.'
            }, 401)

        for key in jwks['keys']:
            if key['kid'] == unverified_header['kid']:
                rsa_key = {
                    'kty': key['kty'],
                    'kid': key['kid'],
                    'use': key['use'],
                    'n': key['n'],
                    'e': key['e']
                }
                break

        if not rsa_key:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to find appropriate key.'
            }, 401)

        payload = jose.jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=AUTH0_AUDIENCE,
            issuer=f'https://{AUTH0_DOMAIN}/'
        )

        return payload

    except jose.jwt.ExpiredSignatureError:
        raise AuthError({
            'code': 'token_expired',
            'description': 'Token expired.'
        }, 401)

    except jose.jwt.JWTClaimsError:
        raise AuthError({
            'code': 'invalid_claims',
            'description': 'Incorrect claims. Please, check the audience and issuer.'
        }, 401)

    except Exception:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Unable to parse authentication token.'
        }, 400)

def requires_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            request.current_user = payload
        except AuthError as auth_error:
            return jsonify(auth_error.error), auth_error.status_code
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return jsonify({
                'code': 'invalid_token',
                'description': 'Unable to validate token.'
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated

# Error Handlers
@app.errorhandler(AuthError)
def handle_auth_error(ex: AuthError):
    return jsonify(ex.error), ex.status_code

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Resource not found'
    }), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request'
    }), 400

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

# Utility Functions
def get_current_user_id() -> str:
    """Get the current authenticated user's ID"""
    return request.current_user['sub']

def serialize_dynamodb_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Convert DynamoDB item to JSON serializable format"""
    if not item:
        return {}
    
    # Handle datetime objects
    for key, value in item.items():
        if isinstance(value, datetime):
            item[key] = value.isoformat()
    
    return item

def generate_id() -> str:
    """Generate a unique ID"""
    import uuid
    return str(uuid.uuid4())

# AgentMail Integration Functions
def send_agentmail_message(to_email: str, subject: str, content: str, template_id: Optional[str] = None) -> bool:
    """Send email via AgentMail API"""
    if not AGENTMAIL_API_KEY:
        logger.warning("AgentMail API key not configured")
        return False
    
    try:
        headers = {
            'Authorization': f'Bearer {AGENTMAIL_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'to': to_email,
            'subject': subject,
            'content': content,
            'template_id': template_id
        }
        
        response = requests.post(
            f'{AGENTMAIL_BASE_URL}/v1/messages',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info(f"Email sent successfully to {to_email}")
            return True
        else:
            logger.error(f"Failed to send email: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"AgentMail error: {e}")
        return False

# API Routes

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

# Patient Profile Routes
@app.route('/api/patient/profile', methods=['GET'])
@requires_auth
def get_patient_profile():
    """Get patient profile from DynamoDB"""
    user_id = get_current_user_id()
    
    try:
        if not patients_table:
            # In development mode, check in-memory storage
            if user_id in dev_patient_profiles:
                return jsonify(dev_patient_profiles[user_id])
            else:
                return jsonify({'message': 'Patient profile not found'}), 404
        
        response = patients_table.get_item(Key={'user_id': user_id})
        
        if 'Item' not in response:
            return jsonify({'message': 'Patient profile not found'}), 404
        
        return jsonify(serialize_dynamodb_item(response['Item']))
    
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        logger.error(f"Error retrieving patient profile: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/patient/profile', methods=['POST'])
@requires_auth
def create_patient_profile():
    """Create new patient profile in DynamoDB"""
    user_id = get_current_user_id()
    
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No data provided")
        
        # Validate required fields
        required_fields = ['personal_info', 'medical_info', 'preferences']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create patient profile with agent_email support
        profile_data = {
            'user_id': user_id,
            'personal_info': data['personal_info'],
            'medical_info': data['medical_info'],
            'preferences': data['preferences'],
            'agent_email': data.get('agent_email', ''),  # Support for agent email as GSI
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        if patients_table:
            patients_table.put_item(Item=profile_data)
        else:
            # Store in development memory for testing
            dev_patient_profiles[user_id] = profile_data
        
        # Send welcome email via AgentMail
        user_email = request.current_user.get('email')
        if user_email:
            send_agentmail_message(
                to_email=user_email,
                subject='Welcome to CareFlow!',
                content=f'Welcome to CareFlow! Your health profile has been successfully created. You can now schedule appointments, communicate with providers, and manage your healthcare all in one place.',
                template_id='welcome_template'
            )
        
        return jsonify({
            'message': 'Profile created successfully',
            'profile': serialize_dynamodb_item(profile_data)
        }), 201
    
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        logger.error(f"Error creating patient profile: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/patient/profile', methods=['PUT'])
@requires_auth
def update_patient_profile():
    """Update patient profile in DynamoDB"""
    user_id = get_current_user_id()
    
    try:
        updates = request.get_json()
        if not updates:
            raise BadRequest("No update data provided")
        
        # Remove user_id from updates if present
        updates.pop('user_id', None)
        updates['updated_at'] = datetime.utcnow().isoformat()
        
        if patients_table:
            # Build update expression
            update_expression = "SET "
            expression_values = {}
            
            for key, value in updates.items():
                update_expression += f"#{key} = :{key}, "
                expression_values[f":{key}"] = value
            
            update_expression = update_expression.rstrip(', ')
            expression_names = {f"#{key}": key for key in updates.keys()}
            
            patients_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ExpressionAttributeNames=expression_names
            )
        
        return jsonify({'message': 'Profile updated successfully'})
    
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        logger.error(f"Error updating patient profile: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Patient by Agent Email Route (using GSI)
@app.route('/api/patients/by-agent/<agent_email>', methods=['GET'])
@requires_auth
def get_patients_by_agent(agent_email):
    """Get patients assigned to a specific agent using the GSI"""
    try:
        if not patients_table:
            # Return mock data for development
            return jsonify([])

        response = patients_table.query(
            IndexName='agent-email-index',
            KeyConditionExpression='agent_email = :agent_email',
            ExpressionAttributeValues={':agent_email': agent_email}
        )

        patients = [serialize_dynamodb_item(item) for item in response.get('Items', [])]
        return jsonify(patients)

    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        logger.error(f"Error retrieving patients by agent: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Appointments Routes (simplified - mock data only)
@app.route('/api/appointments', methods=['GET'])
@requires_auth
def get_appointments():
    """Get user's appointments (mock data - not stored in patients table)"""
    user_id = get_current_user_id()

    try:
        # Return mock data - appointments could be stored elsewhere or in a separate system
        return jsonify([
            {
                'id': '1',
                'provider_name': 'Dr. Sarah Johnson',
                'date': '2025-10-02',
                'time': '2:30 PM',
                'type': 'Annual Checkup',
                'status': 'upcoming',
                'location': 'Main Medical Center',
                'provider_id': 'provider-1'
            },
            {
                'id': '2',
                'provider_name': 'Dr. Michael Chen',
                'date': '2025-10-15',
                'time': '10:00 AM',
                'type': 'Cardiology Consultation',
                'status': 'upcoming',
                'location': 'Specialty Care Building',
                'provider_id': 'provider-2'
            }
        ])

    except Exception as e:
        logger.error(f"Error retrieving appointments: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/appointments', methods=['POST'])
@requires_auth
def create_appointment():
    """Create a new appointment (mock implementation)"""
    user_id = get_current_user_id()

    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No appointment data provided")

        # Validate required fields
        required_fields = ['provider_id', 'date', 'time', 'type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        appointment_id = generate_id()
        appointment_data = {
            'appointment_id': appointment_id,
            'patient_id': user_id,
            'provider_id': data['provider_id'],
            'date': data['date'],
            'time': data['time'],
            'type': data['type'],
            'status': 'upcoming',
            'location': data.get('location', ''),
            'notes': data.get('notes', ''),
            'created_at': datetime.utcnow().isoformat()
        }

        # Send confirmation email via AgentMail
        user_email = request.current_user.get('email')
        if user_email:
            send_agentmail_message(
                to_email=user_email,
                subject='Appointment Confirmation',
                content=f'Your appointment for {data["type"]} on {data["date"]} at {data["time"]} has been confirmed.',
                template_id='appointment_confirmation'
            )

        return jsonify({
            'message': 'Appointment created successfully',
            'appointment': appointment_data
        }), 201

    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating appointment: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Messages Routes (simplified - mock data only)
@app.route('/api/messages', methods=['GET'])
@requires_auth
def get_messages():
    """Get user's messages (mock data - not stored in patients table)"""
    user_id = get_current_user_id()

    try:
        # Return mock data - messages could be stored elsewhere or in a separate system
        return jsonify([
            {
                'id': '1',
                'from': 'Dr. Sarah Johnson',
                'subject': 'Lab Results Available',
                'preview': 'Your recent blood work results are now available for review...',
                'timestamp': '2025-09-27T14:30:00Z',
                'unread': True,
                'type': 'results'
            },
            {
                'id': '2',
                'from': 'CareFlow System',
                'subject': 'Appointment Reminder',
                'preview': 'This is a reminder for your upcoming appointment on October 2nd...',
                'timestamp': '2025-09-26T09:00:00Z',
                'unread': False,
                'type': 'appointment'
            }
        ])

    except Exception as e:
        logger.error(f"Error retrieving messages: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/messages', methods=['POST'])
@requires_auth
def send_message():
    """Send a message to provider (mock implementation)"""
    user_id = get_current_user_id()

    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No message data provided")

        # Validate required fields
        required_fields = ['to', 'subject', 'content']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        message_id = generate_id()
        timestamp = datetime.utcnow().isoformat()

        message_data = {
            'message_id': message_id,
            'patient_id': user_id,
            'provider_id': data['to'],
            'timestamp': timestamp,
            'subject': data['subject'],
            'content': data['content'],
            'from': 'patient',
            'type': data.get('type', 'general'),
            'created_at': timestamp
        }

        # Send notification email via AgentMail to provider
        provider_email = data.get('provider_email')
        if provider_email:
            send_agentmail_message(
                to_email=provider_email,
                subject=f'New message from patient: {data["subject"]}',
                content=f'You have received a new message from a patient.\n\nSubject: {data["subject"]}\n\nMessage: {data["content"]}',
                template_id='provider_notification'
            )

        return jsonify({
            'message': 'Message sent successfully',
            'message_data': message_data
        }), 201

    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Providers Routes (simplified - mock data only)
@app.route('/api/providers', methods=['GET'])
@requires_auth
def get_providers():
    """Get available providers (mock data - not stored in patients table)"""
    try:
        location = request.args.get('location')
        specialty = request.args.get('specialty')

        # Return mock data - providers could be stored elsewhere or in a separate system
        providers = [
            {
                'provider_id': 'provider-1',
                'name': 'Dr. Sarah Johnson',
                'specialty': 'Family Medicine',
                'location': 'Ann Arbor, MI',
                'rating': 4.8,
                'available_times': ['9:00 AM', '2:30 PM', '4:00 PM'],
                'bio': 'Board-certified family physician with 15 years of experience.'
            },
            {
                'provider_id': 'provider-2',
                'name': 'Dr. Michael Chen',
                'specialty': 'Cardiology',
                'location': 'Ann Arbor, MI',
                'rating': 4.9,
                'available_times': ['10:00 AM', '1:00 PM', '3:30 PM'],
                'bio': 'Cardiologist specializing in preventive heart care.'
            }
        ]

        # Simple filtering for demo purposes
        if location:
            providers = [p for p in providers if location.lower() in p['location'].lower()]
        if specialty:
            providers = [p for p in providers if specialty.lower() in p['specialty'].lower()]

        return jsonify(providers)

    except Exception as e:
        logger.error(f"Error retrieving providers: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Dashboard Analytics Routes
@app.route('/api/dashboard/stats', methods=['GET'])
@requires_auth
def get_dashboard_stats():
    """Get dashboard statistics for the user"""
    user_id = get_current_user_id()
    
    try:
        # Mock data for development
        stats = {
            'upcoming_appointments': 2,
            'unread_messages': 1,
            'active_prescriptions': 3,
            'last_visit': '2025-08-15',
            'next_appointment': '2025-10-02'
        }
        
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Error retrieving dashboard stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# AgentMail Integration Routes
@app.route('/api/notifications/send', methods=['POST'])
@requires_auth
def send_notification():
    """Send notification via AgentMail"""
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No notification data provided")
        
        required_fields = ['type', 'recipient']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        user_email = request.current_user.get('email')
        notification_type = data['type']
        
        # Template-based notifications
        templates = {
            'appointment_reminder': {
                'subject': 'Appointment Reminder - CareFlow',
                'template_id': 'appointment_reminder'
            },
            'test_results': {
                'subject': 'Test Results Available - CareFlow',
                'template_id': 'test_results'
            },
            'prescription_refill': {
                'subject': 'Prescription Refill Reminder - CareFlow',
                'template_id': 'prescription_refill'
            }
        }
        
        template = templates.get(notification_type)
        if not template:
            return jsonify({'error': 'Invalid notification type'}), 400
        
        success = send_agentmail_message(
            to_email=user_email,
            subject=template['subject'],
            content=data.get('content', ''),
            template_id=template['template_id']
        )
        
        if success:
            return jsonify({'message': 'Notification sent successfully'})
        else:
            return jsonify({'error': 'Failed to send notification'}), 500
    
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Development server
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=app.config['DEBUG']
    )