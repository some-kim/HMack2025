import React, { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import type { PatientProfile } from '../types/patient';
import AppointmentCard from './AppointmentCard';
import MessageThread from './MessageThread';
import HealthSummary from './HealthSummary';
import QuickActions from './QuickActions';
import Chat from './chat';
import './DashboardContent.css';

interface DashboardContentProps {
  patientProfile: PatientProfile | null;
}

interface Appointment {
  id: string;
  provider_name: string;
  date: string;
  time: string;
  type: string;
  status: 'upcoming' | 'completed' | 'cancelled';
  location: string;
}

interface Message {
  id: string;
  from: string;
  subject: string;
  preview: string;
  timestamp: string;
  unread: boolean;
  type: 'appointment' | 'results' | 'general';
}

const DashboardContent: React.FC<DashboardContentProps> = ({ patientProfile }) => {
  const { user, getAccessTokenSilently } = useAuth0();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);

  // Mock data for demo - replace with actual API calls
  useEffect(() => {
    const loadDashboardData = async () => {
      // Simulate API call delay
      setTimeout(() => {
        setAppointments([
          {
            id: '1',
            provider_name: 'Dr. Sarah Johnson',
            date: '2025-10-02',
            time: '2:30 PM',
            type: 'Annual Checkup',
            status: 'upcoming',
            location: 'Main Medical Center'
          },
          {
            id: '2',
            provider_name: 'Dr. Michael Chen',
            date: '2025-10-15',
            time: '10:00 AM',
            type: 'Cardiology Consultation',
            status: 'upcoming',
            location: 'Specialty Care Building'
          }
        ]);

        setMessages([
          {
            id: '1',
            from: 'Dr. Sarah Johnson',
            subject: 'Lab Results Available',
            preview: 'Your recent blood work results are now available for review...',
            timestamp: '2025-09-27T14:30:00Z',
            unread: true,
            type: 'results'
          },
          {
            id: '2',
            from: 'CareConnector System',
            subject: 'Appointment Reminder',
            preview: 'This is a reminder for your upcoming appointment on October 2nd...',
            timestamp: '2025-09-26T09:00:00Z',
            unread: false,
            type: 'appointment'
          },
          {
            id: '3',
            from: 'Dr. Michael Chen',
            subject: 'Pre-visit Instructions',
            preview: 'Please review these instructions before your cardiology consultation...',
            timestamp: '2025-09-25T16:45:00Z',
            unread: false,
            type: 'general'
          }
        ]);

        setLoading(false);
      }, 1000);
    };

    loadDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  const upcomingAppointments = appointments.filter(apt => apt.status === 'upcoming');
  const unreadMessages = messages.filter(msg => msg.unread);

  return (
    <div className="dashboard-content">
      <div className="dashboard-header-section">
        <div className="welcome-section">
          <h1>Welcome back, {user?.name?.split(' ')[0]}!</h1>
          <p className="dashboard-subtitle">
            Here's what's happening with your healthcare today
          </p>
        </div>
        <div className="dashboard-stats">
          <div className="stat-card">
            <div className="stat-number">{upcomingAppointments.length}</div>
            <div className="stat-label">Upcoming Appointments</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{unreadMessages.length}</div>
            <div className="stat-label">Unread Messages</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">3</div>
            <div className="stat-label">Active Prescriptions</div>
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="main-column">
          <section className="dashboard-section">
            <div className="section-header">
              <h2>Chat with AI Assistant</h2>
            </div>
            <div className="chat-container">
              <Chat />
            </div>
          </section>

          <section className="dashboard-section">
            <div className="section-header">
              <h2>Upcoming Appointments</h2>
              <button className="section-action">View All</button>
            </div>
            <div className="appointments-list">
              {upcomingAppointments.length > 0 ? (
                upcomingAppointments.map(appointment => (
                  <AppointmentCard 
                    key={appointment.id} 
                    appointment={appointment}
                  />
                ))
              ) : (
                <div className="empty-state">
                  <div className="empty-icon">📅</div>
                  <h3>No upcoming appointments</h3>
                  <p>Schedule your next appointment to stay on top of your health</p>
                  <button className="btn-primary">Schedule Appointment</button>
                </div>
              )}
            </div>
          </section>

          <section className="dashboard-section">
            <div className="section-header">
              <h2>Recent Messages</h2>
              <button className="section-action">View All</button>
            </div>
            <div className="messages-list">
              {messages.slice(0, 3).map(message => (
                <MessageThread key={message.id} message={message} />
              ))}
            </div>
          </section>
        </div>

        <div className="sidebar-column">
          <QuickActions />
          <HealthSummary patientProfile={patientProfile} />
          
          <section className="dashboard-section">
            <div className="section-header">
              <h2>Health Reminders</h2>
            </div>
            <div className="reminders-list">
              <div className="reminder-item">
                <div className="reminder-icon">💊</div>
                <div className="reminder-content">
                  <h4>Medication Refill</h4>
                  <p>Lisinopril prescription expires in 5 days</p>
                </div>
                <button className="reminder-action">Refill</button>
              </div>
              <div className="reminder-item">
                <div className="reminder-icon">🩺</div>
                <div className="reminder-content">
                  <h4>Annual Physical</h4>
                  <p>Due for annual checkup - last visit was 11 months ago</p>
                </div>
                <button className="reminder-action">Schedule</button>
              </div>
              <div className="reminder-item">
                <div className="reminder-icon">🧪</div>
                <div className="reminder-content">
                  <h4>Lab Work</h4>
                  <p>Cholesterol screening recommended</p>
                </div>
                <button className="reminder-action">Learn More</button>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export default DashboardContent;