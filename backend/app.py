from flask import Flask, jsonify, request
from flask_cors import CORS
from agentmail_tool import create_inbox, send_new_message, reply_message, get_message, get_thread_context, get_all_threads, autoReply, webhookSetup
import logging

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

app.secret_key = "something"

@app.route('/api/create-inbox', methods=['POST'])
def create_inbox_route():
    data = request.get_json()
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    user_id = data.get("user_id")

    if not all([first_name, last_name, user_id]):
        return jsonify({"error": "Missing first_name, last_name, or user_id"}), 400

    try:
        inbox_data = create_inbox(first_name, last_name, user_id)
        return jsonify({"status": "success", "inbox": inbox_data}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/send-new-message', methods=['POST'])
def send_new_message_route():
    data = request.get_json()
    agent_email = data.get("agent_email")
    recipient_email = data.get("recipient_email")
    subject = data.get("subject")
    text = data.get("text")

    if not all([agent_email, recipient_email, subject, text]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        result = send_new_message(agent_email, recipient_email, subject, text)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reply-message', methods=['POST'])
def reply_message_route():
    data = request.get_json()
    agent_email = data.get("agent_email")
    message_id = data.get("message_id")
    text = data.get("text")

    if not all([agent_email, message_id, text]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        result = reply_message(agent_email, message_id, text)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get-message', methods=['POST'])
def get_message_route():
    data = request.get_json()
    agent_email = data.get("agent_email")
    message_id = data.get("message_id")

    if not all([agent_email, message_id]):
        return jsonify({"error": "Missing agent_email or message_id"}), 400

    try:
        message = get_message(agent_email, message_id)
        return jsonify({"status": "success", "message": message}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get-thread-context', methods=['POST'])
def get_thread_context_route():
    data = request.get_json()
    agent_email = data.get("agent_email")
    thread_id = data.get("thread_id")

    if not all([agent_email, thread_id]):
        return jsonify({"error": "Missing agent_email or thread_id"}), 400

    try:
        response = get_thread_context(agent_email, thread_id)
        return jsonify({"status": "success", "context": response}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get-all-threads', methods=['POST'])
def get_all_threads_route():
    data = request.get_json()
    agent_email = data.get("agent_email")

    if not agent_email:
        return jsonify({"error": "Missing agent_email"}), 400

    try:
        threads_data = get_all_threads(agent_email)
        return jsonify(threads_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    if 'thread_id' not in data['message']:
        logging.error('Missing required fields in the webhook payload')
        return jsonify({'error': 'Missing required fields: thread_id'}), 400

    message = data['message']
    thread_id = message.get('thread_id')

    if not thread_id:
        logging.error(f"Invalid email or thread_id: {thread_id}")
        return jsonify({'error': 'Missing valid agent_email or thread_id'}), 400

    try:
        autoReply(thread_id)
        logging.info(f"Auto-reply triggered for thread_id: {thread_id}")
        return jsonify({'status': 'success', 'message': 'Auto-reply triggered successfully'}), 200
    except Exception as e:
        logging.error(f"Error in autoReply: {e}")
        return jsonify({'error': str(e)}), 500
    
if __name__ == "__main__":
    webhookSetup()
    app.run(debug=True, port=5002)
