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
from jose import jwt as jose_jwt
from botocore.exceptions import ClientError
from werkzeug.exceptions import BadRequest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the backend directory to the Python path to import agentmail_tool and dynamodb_utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))
try:
    from agentmail_tool import create_inbox
    from dynamodb_utils import get_db_client, PatientRecord
except ImportError as e:
    logging.warning(f"Could not import backend tools: {e}")
    create_inbox = None
    get_db_client = None
    PatientRecord = None


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
CARECONNECTOR_TABLE = os.getenv('PATIENTS_TABLE_NAME', 'careconnector-main')

# AgentMail Configuration
AGENTMAIL_API_KEY = os.getenv('AGENTMAIL_API_KEY')
AGENTMAIL_BASE_URL = os.getenv('AGENTMAIL_BASE_URL', 'https://api.agentmail.com')

# Initialize DynamoDB with our sophisticated utilities
try:
    if get_db_client and PatientRecord:
        db_client = get_db_client(table_name=CARECONNECTOR_TABLE, region_name=AWS_REGION)
        patient_ops = PatientRecord(db_client)
        logger.info(f"Initialized DynamoDB utilities for table: {CARECONNECTOR_TABLE}")
    else:
        db_client = None
        patient_ops = None
        logger.warning("DynamoDB utilities not available - using fallback mode")

    # Fallback for legacy code compatibility
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    patients_table = dynamodb.Table(CARECONNECTOR_TABLE)
except Exception as e:
    logger.error(f"Failed to initialize DynamoDB: {e}")
    db_client = None
    patient_ops = None
    patients_table = None

# In-memory storage for development when DynamoDB is not available
dev_patient_profiles = {}
dev_appointments = {}
dev_messages = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log configuration on startup
logger.info(f"[Startup] Auth0 Domain: {AUTH0_DOMAIN}")
logger.info(f"[Startup] Auth0 Audience: {AUTH0_AUDIENCE}")
logger.info(f"[Startup] AWS Region: {AWS_REGION}")
logger.info(f"[Startup] DynamoDB Table: {CARECONNECTOR_TABLE}")
logger.info(f"[Startup] AgentMail API Key configured: {bool(AGENTMAIL_API_KEY)}")
logger.info(f"[Startup] DynamoDB utilities available: {bool(db_client and patient_ops)}")
logger.info(f"[Startup] Legacy table available: {bool(patients_table)}")

# Auth0 JWT Token Validation
class AuthError(Exception):
    """Custom Auth Error Exception"""
    def __init__(self, error: Dict[str, str], status_code: int):
        self.error = error
        self.status_code = status_code

def get_token_auth_header() -> str:
    """Obtains the Access Token from the Authorization Header"""
    logger.info(f"[Auth] All request headers: {dict(request.headers)}")
    auth_header = request.headers.get('Authorization', None)
    logger.info(f"[Auth] Authorization header: {auth_header}")

    if not auth_header:
        logger.error("[Auth] Authorization header missing!")
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
        
        unverified_header = jose_jwt.get_unverified_header(token)
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

        payload = jose_jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=AUTH0_AUDIENCE,
            issuer=f'https://{AUTH0_DOMAIN}/'
        )

        return payload

    except jose_jwt.ExpiredSignatureError:
        raise AuthError({
            'code': 'token_expired',
            'description': 'Token expired.'
        }, 401)

    except jose_jwt.JWTClaimsError:
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
            logger.info(f"[Auth] Processing authentication for {request.endpoint}")
            token = get_token_auth_header()
            logger.info(f"[Auth] Token extracted, length: {len(token) if token else 0}")

            payload = verify_decode_jwt(token)
            logger.info(f"[Auth] Token decoded successfully, user: {payload.get('sub', 'unknown')}")
            request.current_user = payload
        except AuthError as auth_error:
            logger.error(f"[Auth] Auth error: {auth_error.error}")
            return jsonify(auth_error.error), auth_error.status_code
        except Exception as e:
            logger.error(f"[Auth] Authentication error: {e}")
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

# User Initialization Route
@app.route('/api/patient/initialize', methods=['POST'])
@requires_auth
def initialize_patient():
    """Initialize a basic patient record for a new user"""
    user_id = get_current_user_id()
    user_email = request.current_user.get('email', '')
    user_name = request.current_user.get('name', 'User')

    logger.info(f"[Initialize] Creating initial record for user: {user_id}")

    try:
        # Check if user already exists
        if patient_ops:
            existing = patient_ops.get_patient(user_id)
            if existing:
                logger.info(f"[Initialize] User {user_id} already exists")
                return jsonify({'message': 'User already initialized', 'profile': serialize_dynamodb_item(existing)})
        elif patients_table:
            response = patients_table.get_item(Key={'user_id': user_id})
            if 'Item' in response:
                logger.info(f"[Initialize] User {user_id} already exists (legacy)")
                return jsonify({'message': 'User already initialized', 'profile': serialize_dynamodb_item(response['Item'])})
        else:
            if user_id in dev_patient_profiles:
                logger.info(f"[Initialize] User {user_id} already exists (dev)")
                return jsonify({'message': 'User already initialized', 'profile': dev_patient_profiles[user_id]})

        # Create minimal initial profile
        initial_data = {
            'user_id': user_id,
            'email': user_email,
            'name': user_name,
            'initialization_complete': True,
            'profile_complete': False,
            'personal_info': {},
            'medical_info': {
                'allergies': [],
                'medications': [],
                'conditions': [],
                'insurance': {'provider': '', 'policy_number': ''}
            },
            'preferences': {
                'communication_method': 'email',
                'appointment_reminders': True,
                'health_tips': False
            },
            'agent_email': ''
        }

        if patient_ops:
            # Use sophisticated patient operations
            result = patient_ops.create_patient(user_id, initial_data)
            created_profile = result['item']
        elif patients_table:
            # Fallback to legacy table access
            initial_data.update({
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            })
            patients_table.put_item(Item=initial_data)
            created_profile = initial_data
        else:
            # Development mode
            initial_data.update({
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            })
            dev_patient_profiles[user_id] = initial_data
            created_profile = initial_data

        logger.info(f"[Initialize] Successfully created initial record for {user_id}")
        return jsonify({
            'message': 'User initialized successfully',
            'profile': serialize_dynamodb_item(created_profile)
        }), 201

    except Exception as e:
        logger.error(f"[Initialize] Error initializing user {user_id}: {e}")
        return jsonify({'error': 'Failed to initialize user'}), 500

# Patient Profile Routes
@app.route('/api/patient/profile', methods=['GET'])
@requires_auth
def get_patient_profile():
    """Get patient profile using sophisticated DynamoDB utilities"""
    user_id = get_current_user_id()
    logger.info(f"[Profile GET] Request for user_id: {user_id}")
    logger.info(f"[Profile GET] patient_ops available: {patient_ops is not None}")
    logger.info(f"[Profile GET] patients_table available: {patients_table is not None}")

    try:
        if patient_ops:
            # Use our sophisticated patient operations
            logger.info(f"[Profile GET] Using patient_ops to get profile for {user_id}")
            profile = patient_ops.get_patient(user_id)
            if profile:
                logger.info(f"[Profile GET] Profile found for {user_id}")
                return jsonify(serialize_dynamodb_item(profile))
            else:
                logger.info(f"[Profile GET] No profile found for {user_id} - returning 404")
                return jsonify({'message': 'Patient profile not found'}), 404

        elif patients_table:
            # Fallback to legacy table access
            logger.info(f"[Profile GET] Using legacy table access for {user_id}")
            response = patients_table.get_item(Key={'user_id': user_id})
            if 'Item' not in response:
                logger.info(f"[Profile GET] No legacy profile found for {user_id} - returning 404")
                return jsonify({'message': 'Patient profile not found'}), 404
            return jsonify(serialize_dynamodb_item(response['Item']))

        else:
            # Development mode with in-memory storage
            logger.info(f"[Profile GET] Using dev storage for {user_id}")
            logger.info(f"[Profile GET] Dev profiles available: {list(dev_patient_profiles.keys())}")
            if user_id in dev_patient_profiles:
                logger.info(f"[Profile GET] Dev profile found for {user_id}")
                return jsonify(dev_patient_profiles[user_id])
            else:
                logger.info(f"[Profile GET] No dev profile found for {user_id} - returning 404")
                return jsonify({'message': 'Patient profile not found'}), 404

    except Exception as e:
        logger.error(f"[Profile GET] Error retrieving patient profile for {user_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/patient/profile', methods=['POST'])
@requires_auth
def create_patient_profile():
    """Create new patient profile using sophisticated DynamoDB utilities"""
    user_id = get_current_user_id()

    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No data provided")

        # Validate required personal info fields
        if 'personal_info' not in data:
            return jsonify({'error': 'Personal information is required'}), 400

        personal_info = data['personal_info']
        required_personal_fields = ['date_of_birth', 'gender', 'phone', 'address']
        missing_fields = []

        for field in required_personal_fields:
            if field not in personal_info or not personal_info[field]:
                missing_fields.append(field)

        if missing_fields:
            return jsonify({'error': f'Missing required personal information: {", ".join(missing_fields)}'}), 400

        # Validate emergency contact if provided
        if 'emergency_contact' in personal_info:
            emergency_contact = personal_info['emergency_contact']
            required_emergency_fields = ['name', 'phone', 'relationship']
            missing_emergency_fields = []

            for field in required_emergency_fields:
                if field not in emergency_contact or not emergency_contact[field]:
                    missing_emergency_fields.append(field)

            if missing_emergency_fields:
                return jsonify({'error': f'Missing required emergency contact information: {", ".join(missing_emergency_fields)}'}), 400

        # Default structures for optional sections
        default_medical_info = {
            'allergies': [],
            'medications': [],
            'conditions': [],
            'insurance': {
                'provider': '',
                'policy_number': ''
            }
        }

        default_preferences = {
            'communication_method': 'email',
            'appointment_reminders': True,
            'health_tips': False
        }

        # Use provided personal info as-is (already validated)
        # Merge optional sections with defaults
        medical_info = {**default_medical_info, **data.get('medical_info', {})}
        if 'insurance' in data.get('medical_info', {}):
            medical_info['insurance'] = {
                **default_medical_info['insurance'],
                **data['medical_info']['insurance']
            }

        preferences = {**default_preferences, **data.get('preferences', {})}

        # Prepare patient data with proper structure for our utilities
        patient_data = {
            'user_id': user_id,
            'personal_info': personal_info,
            'medical_info': medical_info,
            'preferences': preferences,
            'agent_email': data.get('agent_email', ''),  # For GSI querying
        }

        logger.info(f"[Profile POST] Prepared patient data for {user_id}: {list(patient_data.keys())}")

        if patient_ops:
            # Use our sophisticated patient operations
            result = patient_ops.create_patient(user_id, patient_data)
            created_profile = result['item']

            # Set up GSI fields for agent-based queries if agent_email is provided
            if data.get('agent_email'):
                # Update with GSI fields for agent queries
                db_client.update_item(
                    pk=f'PATIENT#{user_id}',
                    sk='PROFILE',
                    updates={
                        'GSI1PK': f'AGENT#{data["agent_email"]}',
                        'GSI1SK': f'PATIENT#{user_id}'
                    }
                )

        elif patients_table:
            # Fallback to legacy table access
            profile_data = {
                'user_id': user_id,
                'personal_info': data['personal_info'],
                'medical_info': data['medical_info'],
                'preferences': data['preferences'],
                'agent_email': data.get('agent_email', ''),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            patients_table.put_item(Item=profile_data)
            created_profile = profile_data

        else:
            # Development mode with in-memory storage
            profile_data = {
                'user_id': user_id,
                'personal_info': data['personal_info'],
                'medical_info': data['medical_info'],
                'preferences': data['preferences'],
                'agent_email': data.get('agent_email', ''),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            dev_patient_profiles[user_id] = profile_data
            created_profile = profile_data

        # Create AgentMail inbox for the patient if create_inbox is available
        if create_inbox:
            try:
                user_email = request.current_user.get('email', '')
                user_name = request.current_user.get('name', 'Patient')
                first_name = user_name.split(' ')[0] if user_name else 'Patient'
                last_name = user_name.split(' ')[-1] if ' ' in user_name else 'User'

                inbox_result = create_inbox(first_name, last_name, user_id)
                logger.info(f"Created AgentMail inbox for user {user_id}: {inbox_result}")

                # Update patient profile with inbox information
                if patient_ops:
                    patient_ops.update_patient(user_id, {
                        'agentmail_inbox': inbox_result
                    })

            except Exception as e:
                logger.error(f"Failed to create AgentMail inbox: {e}")
                # Don't fail the profile creation if inbox creation fails

        # Send welcome email via AgentMail
        user_email = request.current_user.get('email')
        if user_email:
            send_agentmail_message(
                to_email=user_email,
                subject='Welcome to CareConnector!',
                content=f'Welcome to CareConnector! Your health profile has been successfully created. You can now schedule appointments, communicate with providers, and manage your healthcare all in one place.',
                template_id='welcome_template'
            )

        return jsonify({
            'message': 'Profile created successfully',
            'profile': serialize_dynamodb_item(created_profile)
        }), 201

    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating patient profile: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/patient/profile', methods=['PUT'])
@requires_auth
def update_patient_profile():
    """Update patient profile using sophisticated DynamoDB utilities"""
    user_id = get_current_user_id()

    try:
        updates = request.get_json()
        if not updates:
            raise BadRequest("No update data provided")

        # Remove user_id from updates if present
        updates.pop('user_id', None)

        if patient_ops:
            # Use our sophisticated patient operations
            updated_profile = patient_ops.update_patient(user_id, updates)

            # Handle agent_email GSI updates
            if 'agent_email' in updates:
                db_client.update_item(
                    pk=f'PATIENT#{user_id}',
                    sk='PROFILE',
                    updates={
                        'GSI1PK': f'AGENT#{updates["agent_email"]}' if updates["agent_email"] else '',
                        'GSI1SK': f'PATIENT#{user_id}' if updates["agent_email"] else ''
                    }
                )

            return jsonify({
                'message': 'Profile updated successfully',
                'profile': serialize_dynamodb_item(updated_profile)
            })

        elif patients_table:
            # Fallback to legacy table access
            updates['updated_at'] = datetime.utcnow().isoformat()

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

        else:
            # Development mode with in-memory storage
            if user_id in dev_patient_profiles:
                dev_patient_profiles[user_id].update(updates)
                dev_patient_profiles[user_id]['updated_at'] = datetime.utcnow().isoformat()
                return jsonify({'message': 'Profile updated successfully'})
            else:
                return jsonify({'error': 'Profile not found'}), 404

    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating patient profile: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Patient by Agent Email Route (using GSI)
@app.route('/api/patients/by-agent/<agent_email>', methods=['GET'])
@requires_auth
def get_patients_by_agent(agent_email):
    """Get patients assigned to a specific agent using sophisticated DynamoDB utilities with GSI"""
    try:
        if db_client:
            # Use our sophisticated DynamoDB utilities with GSI1
            patients = db_client.query_items(
                pk=f'AGENT#{agent_email}',
                index_name='GSI1'
            )

            # Transform the results to match expected frontend format
            patient_profiles = []
            for patient_item in patients:
                if patient_item.get('EntityType') == 'Patient':
                    patient_profiles.append(serialize_dynamodb_item(patient_item))

            return jsonify(patient_profiles)

        elif patients_table:
            # Fallback to legacy table access with GSI
            try:
                response = patients_table.query(
                    IndexName='agent-email-index',
                    KeyConditionExpression='agent_email = :agent_email',
                    ExpressionAttributeValues={':agent_email': agent_email}
                )
                patients = [serialize_dynamodb_item(item) for item in response.get('Items', [])]
                return jsonify(patients)
            except ClientError as e:
                if 'ResourceNotFoundException' in str(e):
                    logger.warning(f"GSI 'agent-email-index' not found, returning empty list")
                    return jsonify([])
                raise

        else:
            # Development mode with in-memory storage
            agent_patients = []
            for user_id, profile in dev_patient_profiles.items():
                if profile.get('agent_email') == agent_email:
                    agent_patients.append(profile)
            return jsonify(agent_patients)

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