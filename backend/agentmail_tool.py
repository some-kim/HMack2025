import os
from dotenv import load_dotenv
from agentmail import AgentMail

# Load the API key from the .env file
load_dotenv()
api_key = os.getenv("AGENTMAIL_API_KEY")

# Initialize the client
client = AgentMail(api_key=api_key)

def create_inbox(first_Name, last_Name, user_ID):
    username = f'{first_Name}{last_Name}.CareConnector.{user_ID}'
    inbox = client.inboxes.create(username=username)

def send_new_message(agent_email, recipient_email, subject, text):
    sent_message = client.inboxes.messages.send(
        inbox_id=agent_email,
        to=recipient_email,
        subject=subject,
        text=text,
    )
    return {
        "message_id": sent_message.message_id,
        "status": "sent"
    }

def reply_message(agent_email, message_id, text):
    reply = client.inboxes.messages.reply(
        inbox_id=agent_email,
        message_id=message_id,
        text=text,
    )

    client.messages.update(
        inbox_id=agent_email,
        message_id=message_id,
        add_labels=["replied"],
        remove_labels=["unreplied"]
    )   
    return {
        "message_id": reply.message_id,
        "status": "replied"
    }

def get_message(agent_email, message_id):
    message = client.inboxes.messages.get(
        inbox_id=agent_email,
        message_id=message_id
    )
    return {
        "subject": message.subject,
        "from": message.from_,
        "to": message.to,
        "text": message.text,
        "sent_at": message.sent_at
    }

