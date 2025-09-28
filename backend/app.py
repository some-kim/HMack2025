# app.py

from flask import Flask, jsonify, request
from flask_cors import CORS
from agentmail_tool import create_inbox, send_new_message, reply_message, get_message

app = Flask(__name__)
CORS(app)

#AgentMail
@app.route('/api/create-inbox', methods=['POST'])
def create_inbox_route():
    data = request.get_json()

    first_name = data.get("firstName")
    last_name = data.get("lastName")
    user_id = data.get("userID")

    if not first_name or not last_name or not user_id:
        return jsonify({"error": "Missing firstName, lastName, or userID"}), 400
    
    try:
        create_inbox(first_name, last_name, user_id)
        return jsonify({"status": "success"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/api/send-new-message', methods=['POST'])
def send_new_message_route():
    data = request.get_json()
    agent_email = data.get("agentEmail")
    recipient_email = data.get("recipientEmail")
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
    agent_email = data.get("agentEmail")
    message_id = data.get("messageID")
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
    agent_email = data.get("agentEmail")
    message_id = data.get("messageID")

    if not all([agent_email, message_id]):
        return jsonify({"error": "Missing agentEmail or messageID"}), 400

    try:
        message = get_message(agent_email, message_id)
        return jsonify({"status": "success", "message": message}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
