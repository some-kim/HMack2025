import os
import json
from dotenv import load_dotenv
from agentmail import AgentMail
from google import genai
from datetime import datetime
import re
import logging


# Load the API key from the .env file
load_dotenv()
api_key = os.getenv("AGENTMAIL_API_KEY")
gemini = os.getenv("GEMINI_API")
# Initialize the client
client = AgentMail(api_key=api_key)
client_genai = genai.Client(api_key=gemini)

def create_inbox(first_Name, last_Name, user_ID):
    username = f'{first_Name}{last_Name}.CareConnector.{user_ID}'
    inbox = client.inboxes.create(username=username)
    return {
        "inbox_id": inbox.inbox_id,
        "username": username,
        "email": inbox.email,
        "created_at": inbox.created_at
    }

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

def get_all_threads(agent_email):
    all_threads = []

    threads = client.inboxes.threads.list(inbox_id=agent_email)
    for thread in threads.threads:
        thread_full = client.inboxes.threads.get(inbox_id=agent_email, thread_id=thread.thread_id)
        thread_data = {
            "thread_id": thread_full.thread_id,
            "subject": thread_full.subject,
            "messages": [
                {
                    "from": msg.from_,
                    "to": msg.to,
                    "text": msg.text,
                    "timestamp": msg.timestamp,
                    "message_id": msg.message_id,
                }
                for msg in thread_full.messages
            ]
        }

        all_threads.append(thread_data)

    return all_threads


# Set up basic logging configuration without timestamps
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')
def is_valid_email(email):
    # Regex pattern to match a valid email address format
    pattern = r"^(?!\.)(?!.*\.\.)([A-Za-z0-9_'+\-\.]*)[A-Za-z0-9_+-]@([A-Za-z0-9][A-Za-z0-9\-]*\.)+[A-Za-z]{2,}$"
    return re.match(pattern, email) is not None

def autoReply(thread_id):
    agent_email = client.threads.get(thread_id=thread_id).inbox_id

    prompt = """You are a healthcare assistant drafting an email on behalf of the sender (the person requesting information or action).

Read the email chain below and write a clear, professional, and action-oriented reply addressed to healthcare staff (such as doctors, nurses, or medical secretaries). Your reply should:

1. Provide or request the information needed to move the task forward.
   - If all necessary details are present, confirm the next step or supply the requested information.
     Example: "I would like to schedule a follow-up appointment with Dr. Kim next week. Could you let me know if Wednesday afternoon is available?"
     Example: "Following Dr. Patel’s instructions, I’m confirming that the lab order has been completed and the results are attached for review."

   - If details are missing or unclear, politely ask focused questions to obtain what is needed.
     Example: "Could you advise which imaging center would be best for the MRI referral?"
     Example: "Would you confirm whether a prescription refill requires a new consultation?"

2. Keep the message concise, courteous, and professional.
   - Be direct and solution-focused so the recipient knows exactly how to respond or what to do next.
   - Write as if you are the sender themselves (use "I" or "we," not third-person references).

Your goal is to either complete the request (such as scheduling an appointment, confirming instructions, or forwarding results) or gather the precise details required to complete it.

Here is the email chain to respond to:
\n\n"""
    
    # Get thread context once and store the result
    context = get_thread_context(agent_email=agent_email, thread_id=thread_id)
    message_id = context["last_message_id"]
    
    # Convert context messages to a human-readable format (instead of JSON string)
    messages = ""
    for msg in context["context_messages"]:
        messages += f"From: {msg['from']}\nTo: {msg['to']}\nSubject: {msg['subject']}\nMessage: {msg['text']}\n\n"
    
    # Combine prompt with email thread context
    full_prompt = prompt + messages

    # Generate the response based on the prompt and context
    response = client_genai.models.generate_content(
        contents=full_prompt,
        model="gemini-2.5-flash",
    )
    
    # Send the generated response as a reply
    reply_message(agent_email=agent_email, message_id=message_id, text=response.text)
    
    return

def webhookSetup():
    client.webhooks.create(
        url="https://kindra-cressiest-bernardine.ngrok-free.dev/webhook",
        event_types=["message.received"]  # Specify which events to listen to
    )
