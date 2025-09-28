import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import './LoginPage.css';

const LoginPage: React.FC = () => {
  const { loginWithRedirect } = useAuth0();

  const handleLogin = () => {
    loginWithRedirect({
      appState: {
        returnTo: '/dashboard'
      }
    });
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <div className="logo">
            <div className="logo-icon">🏥</div>
            <h1>CareConnect</h1>
          </div>
          <p className="tagline">
            Connect with your healthcare providers seamlessly
          </p>
        </div>

        <div className="login-content">
          <h2>Welcome to Your Health Journey</h2>
          <p className="description">
            Access your appointments, communicate with providers, 
            and manage your healthcare all in one place.
          </p>

          <div className="features">
            <div className="feature">
              <span className="feature-icon">📅</span>
              <span>Easy Appointment Scheduling</span>
            </div>
            <div className="feature">
              <span className="feature-icon">💬</span>
              <span>Direct Provider Communication</span>
            </div>
            <div className="feature">
              <span className="feature-icon">📋</span>
              <span>Centralized Health Records</span>
            </div>
          </div>

          <button 
            onClick={handleLogin}
            className="login-button"
          >
            Sign In / Create Account
          </button>

          <p className="security-note">
            🔒 Your health data is encrypted and HIPAA compliant
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;