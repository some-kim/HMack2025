import React from 'react';
import type { PatientProfile } from '../types/patient';

interface HealthSummaryProps {
  patientProfile: PatientProfile | null;
}

const HealthSummary: React.FC<HealthSummaryProps> = ({ patientProfile }) => {
  if (!patientProfile) return null;

  const { medical_info } = patientProfile;

  return (
    <section className="dashboard-section">
      <div className="section-header">
        <h2>Health Summary</h2>
        <button className="section-action">Edit</button>
      </div>
      
      <div className="health-summary-content">
        <div className="summary-item">
          <div className="summary-label">Current Medications</div>
          <div className="summary-value">
            {medical_info.medications.length > 0 ? (
              <ul className="medications-list">
                {medical_info.medications.slice(0, 3).map((med, index) => (
                  <li key={index}>{med}</li>
                ))}
                {medical_info.medications.length > 3 && (
                  <li>+{medical_info.medications.length - 3} more</li>
                )}
              </ul>
            ) : (
              <span className="empty-value">No medications listed</span>
            )}
          </div>
        </div>

        <div className="summary-item">
          <div className="summary-label">Allergies</div>
          <div className="summary-value">
            {medical_info.allergies.length > 0 ? (
              medical_info.allergies.join(', ')
            ) : (
              <span className="empty-value">No known allergies</span>
            )}
          </div>
        </div>

        <div className="summary-item">
          <div className="summary-label">Insurance</div>
          <div className="summary-value">{medical_info.insurance.provider}</div>
        </div>

        <div className="summary-item">
          <div className="summary-label">Emergency Contact</div>
          <div className="summary-value">
            {patientProfile.personal_info.emergency_contact.name} 
            ({patientProfile.personal_info.emergency_contact.relationship})
          </div>
        </div>
      </div>
    </section>
  );
};

export default HealthSummary;