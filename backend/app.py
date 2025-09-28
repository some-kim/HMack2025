# app.py

from flask import Flask, jsonify
from flask_cors import CORS
from agentmail_tool import create_inbox

app = Flask(__name__)
CORS(app)

#AgentMail
@app.route('/api/create-inbox', methods=['POST'])
def create_inbox_route():
    try:
        inbox_data = create_inbox()
        return jsonify({"status": "success", "inbox": inbox_data}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
