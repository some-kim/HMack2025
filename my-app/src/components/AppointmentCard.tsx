import React from 'react';

interface Appointment {
  id: string;
  provider_name: string;
  date: string;
  time: string;
  type: string;
  status: 'upcoming' | 'completed' | 'cancelled';
  location: string;
}

interface AppointmentCardProps {
  appointment: Appointment;
}

const AppointmentCard: React.FC<AppointmentCardProps> = ({ appointment }) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    });
  };

  const getTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'annual checkup':
        return '🩺';
      case 'cardiology consultation':
        return '❤️';
      case 'dental':
        return '🦷';
      case 'dermatology':
        return '🧴';
      default:
        return '📋';
    }
  };

  return (
    <div className="appointment-card">
      <div className="appointment-date">
        <div className="date-day">{formatDate(appointment.date)}</div>
        <div className="date-time">{appointment.time}</div>
      </div>
      
      <div className="appointment-details">
        <div className="appointment-type">
          <span className="type-icon">{getTypeIcon(appointment.type)}</span>
          <span className="type-text">{appointment.type}</span>
        </div>
        <div className="provider-name">{appointment.provider_name}</div>
        <div className="appointment-location">📍 {appointment.location}</div>
      </div>

      <div className="appointment-actions">
        <button className="btn-secondary btn-sm">Reschedule</button>
        <button className="btn-primary btn-sm">Join Video Call</button>
      </div>
    </div>
  );
};

export default AppointmentCard;