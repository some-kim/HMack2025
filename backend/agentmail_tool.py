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
        "thread_id": sent_message.thread_id,
        "status": "sent"
    }

def reply_message(agent_email, message_id, text):
    reply = client.inboxes.messages.reply(
        inbox_id=agent_email,
        message_id=message_id,
        text=text,
    )

    client.inboxes.messages.update(
        inbox_id=agent_email,
        message_id=message_id,
        add_labels=["read"],
        remove_labels=["unread"]
    )   
    return {
        "message_id": reply.message_id,
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

def get_thread_context(agent_email, thread_id):
    thread = client.inboxes.threads.get(inbox_id=agent_email, thread_id=thread_id)

    messages = []
    for msg in thread.messages:
        messages.append({
            "message_id": msg.message_id,
            "from": msg.from_,
            "to": msg.to,
            "labels": msg.labels,
            "subject": msg.subject,
            "text": msg.text,
            "sent_at": msg.timestamp
        })

    return {
        "last_message_id": thread.last_message_id,
        "context_messages": messages
    }