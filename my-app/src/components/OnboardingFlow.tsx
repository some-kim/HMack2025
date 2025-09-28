import React, { useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import type { PatientProfile } from '../types/patient';
import { createPatientProfile } from '../services/api';
import './OnboardingFlow.css';

interface OnboardingFlowProps {
  onComplete: (profile: PatientProfile) => void;
}

const OnboardingFlow: React.FC<OnboardingFlowProps> = ({ onComplete }) => {
  const { getAccessTokenSilently } = useAuth0();
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    dateOfBirth: '',
    gender: '',
    phone: '',
    address: '',
    emergencyContact: {
      name: '',
      phone: '',
      relationship: ''
    },
    insurance: {
      provider: '',
      policyNumber: ''
    },
    allergies: [] as string[],
    medications: [] as string[],
    medicalConditions: [] as string[],
    communicationPreferences: {
      method: 'email' as 'email' | 'sms' | 'both',
      appointmentReminders: true,
      healthTips: false
    }
  });

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleNestedChange = (parent: string, field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [parent]: { ...(prev as any)[parent], [field]: value }
    }));
  };

  const handleSubmit = async () => {
    try {
      const token = await getAccessTokenSilently();
      const profile = await createPatientProfile(token, formData);
      onComplete(profile);
    } catch (error) {
      console.error('Error creating profile:', error);
      alert('Error creating your profile. Please try again.');
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="onboarding-step">
            <h2>Welcome! Let's set up your profile</h2>
            <p>We need some basic information to get you started</p>
            
            <div className="form-group">
              <label>Date of Birth</label>
              <input 
                type="date"
                value={formData.dateOfBirth}
                onChange={(e) => handleInputChange('dateOfBirth', e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Gender</label>
              <select 
                value={formData.gender}
                onChange={(e) => handleInputChange('gender', e.target.value)}
              >
                <option value="">Select...</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="non-binary">Non-binary</option>
                <option value="prefer-not-to-say">Prefer not to say</option>
              </select>
            </div>

            <div className="form-group">
              <label>Phone Number</label>
              <input 
                type="tel"
                value={formData.phone}
                onChange={(e) => handleInputChange('phone', e.target.value)}
                placeholder="(555) 123-4567"
              />
            </div>
          </div>
        );

      case 2:
        return (
          <div className="onboarding-step">
            <h2>Contact & Emergency Information</h2>
            
            <div className="form-group">
              <label>Home Address</label>
              <textarea 
                value={formData.address}
                onChange={(e) => handleInputChange('address', e.target.value)}
                placeholder="123 Main St, Ann Arbor, MI 48104"
                rows={3}
              />
            </div>

            <h3>Emergency Contact</h3>
            <div className="form-row">
              <div className="form-group">
                <label>Name</label>
                <input 
                  type="text"
                  value={formData.emergencyContact.name}
                  onChange={(e) => handleNestedChange('emergencyContact', 'name', e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>Relationship</label>
                <input 
                  type="text"
                  value={formData.emergencyContact.relationship}
                  onChange={(e) => handleNestedChange('emergencyContact', 'relationship', e.target.value)}
                  placeholder="Spouse, Parent, etc."
                />
              </div>
            </div>
            <div className="form-group">
              <label>Phone</label>
              <input 
                type="tel"
                value={formData.emergencyContact.phone}
                onChange={(e) => handleNestedChange('emergencyContact', 'phone', e.target.value)}
              />
            </div>
          </div>
        );

      case 3:
        return (
          <div className="onboarding-step">
            <h2>Medical Information</h2>
            <p>This helps us provide better care coordination</p>

            <div className="form-group">
              <label>Insurance Provider</label>
              <input 
                type="text"
                value={formData.insurance.provider}
                onChange={(e) => handleNestedChange('insurance', 'provider', e.target.value)}
                placeholder="Blue Cross Blue Shield, Aetna, etc."
              />
            </div>

            <div className="form-group">
              <label>Policy Number (Optional)</label>
              <input 
                type="text"
                value={formData.insurance.policyNumber}
                onChange={(e) => handleNestedChange('insurance', 'policyNumber', e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Known Allergies (Optional)</label>
              <input 
                type="text"
                placeholder="Penicillin, Shellfish, etc. (comma separated)"
                onChange={(e) => handleInputChange('allergies', e.target.value.split(',').map(s => s.trim()).filter(s => s))}
              />
            </div>

            <div className="form-group">
              <label>Current Medications (Optional)</label>
              <input 
                type="text"
                placeholder="Lisinopril, Advil, etc. (comma separated)"
                onChange={(e) => handleInputChange('medications', e.target.value.split(',').map(s => s.trim()).filter(s => s))}
              />
            </div>
          </div>
        );

      case 4:
        return (
          <div className="onboarding-step">
            <h2>Communication Preferences</h2>
            
            <div className="form-group">
              <label>How would you like to receive updates?</label>
              <div className="radio-group">
                <label className="radio-option">
                  <input 
                    type="radio"
                    value="email"
                    checked={formData.communicationPreferences.method === 'email'}
                    onChange={(e) => handleNestedChange('communicationPreferences', 'method', e.target.value)}
                  />
                  Email only
                </label>
                <label className="radio-option">
                  <input 
                    type="radio"
                    value="sms"
                    checked={formData.communicationPreferences.method === 'sms'}
                    onChange={(e) => handleNestedChange('communicationPreferences', 'method', e.target.value)}
                  />
                  SMS only
                </label>
                <label className="radio-option">
                  <input 
                    type="radio"
                    value="both"
                    checked={formData.communicationPreferences.method === 'both'}
                    onChange={(e) => handleNestedChange('communicationPreferences', 'method', e.target.value)}
                  />
                  Both email and SMS
                </label>
              </div>
            </div>

            <div className="checkbox-group">
              <label className="checkbox-option">
                <input 
                  type="checkbox"
                  checked={formData.communicationPreferences.appointmentReminders}
                  onChange={(e) => handleNestedChange('communicationPreferences', 'appointmentReminders', e.target.checked)}
                />
                Send appointment reminders
              </label>
              <label className="checkbox-option">
                <input 
                  type="checkbox"
                  checked={formData.communicationPreferences.healthTips}
                  onChange={(e) => handleNestedChange('communicationPreferences', 'healthTips', e.target.checked)}
                />
                Receive health tips and wellness content
              </label>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="onboarding-container">
      <div className="onboarding-progress">
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ width: `${(currentStep / 4) * 100}%` }}
          />
        </div>
        <span className="progress-text">Step {currentStep} of 4</span>
      </div>

      <div className="onboarding-content">
        {renderStep()}
      </div>

      <div className="onboarding-actions">
        {currentStep > 1 && (
          <button 
            className="btn-secondary"
            onClick={() => setCurrentStep(currentStep - 1)}
          >
            Back
          </button>
        )}
        {currentStep < 4 ? (
          <button 
            className="btn-primary"
            onClick={() => setCurrentStep(currentStep + 1)}
          >
            Next
          </button>
        ) : (
          <button 
            className="btn-primary"
            onClick={handleSubmit}
          >
            Complete Setup
          </button>
        )}
      </div>
    </div>
  );
};

export default OnboardingFlow;