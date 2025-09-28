import React from 'react';

interface Message {
  id: string;
  from: string;
  subject: string;
  preview: string;
  timestamp: string;
  unread: boolean;
  type: 'appointment' | 'results' | 'general';
}

interface MessageThreadProps {
  message: Message;
}

const MessageThread: React.FC<MessageThreadProps> = ({ message }) => {
  const getMessageIcon = (type: string) => {
    switch (type) {
      case 'appointment':
        return '📅';
      case 'results':
        return '📊';
      case 'general':
        return '💬';
      default:
        return '📧';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = Math.abs(now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 24) {
      return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    } else {
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
      });
    }
  };

  return (
    <div className={`message-thread ${message.unread ? 'unread' : ''}`}>
      <div className="message-icon">
        {getMessageIcon(message.type)}
      </div>
      
      <div className="message-content">
        <div className="message-header">
          <span className="message-from">{message.from}</span>
          <span className="message-time">{formatTimestamp(message.timestamp)}</span>
        </div>
        <div className="message-subject">{message.subject}</div>
        <div className="message-preview">{message.preview}</div>
      </div>

      {message.unread && <div className="unread-indicator"></div>}
    </div>
  );
};

export default MessageThread;