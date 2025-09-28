import React from 'react';

const QuickActions: React.FC = () => {
  const actions = [
    {
      icon: '📅',
      title: 'Schedule Appointment',
      description: 'Book with your provider',
      action: () => console.log('Schedule appointment')
    },
    {
      icon: '💬',
      title: 'Message Provider',
      description: 'Ask a question',
      action: () => console.log('Message provider')
    },
    {
      icon: '💊',
      title: 'Refill Prescription',
      description: 'Request medication refill',
      action: () => console.log('Refill prescription')
    },
    {
      icon: '📋',
      title: 'View Records',
      description: 'Access health history',
      action: () => console.log('View records')
    }
  ];

  return (
    <section className="dashboard-section">
      <div className="section-header">
        <h2>Quick Actions</h2>
      </div>
      <div className="quick-actions-grid">
        {actions.map((action, index) => (
          <button
            key={index}
            className="quick-action-button"
            onClick={action.action}
          >
            <div className="action-icon">{action.icon}</div>
            <div className="action-content">
              <div className="action-title">{action.title}</div>
              <div className="action-description">{action.description}</div>
            </div>
          </button>
        ))}
      </div>
    </section>
  );
};

export default QuickActions;