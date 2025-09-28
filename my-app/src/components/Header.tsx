import React, { useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import './Header.css';

interface HeaderProps {
  user: any;
}

const Header: React.FC<HeaderProps> = ({ user }) => {
  const { logout } = useAuth0();
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogout = () => {
    logout({ 
      logoutParams: { 
        returnTo: window.location.origin 
      } 
    });
  };

  return (
    <header className="dashboard-header">
      <div className="header-content">
        <div className="logo-section">
          <div className="logo-icon">🏥</div>
          <h1>CareFlow</h1>
        </div>

        <nav className="navigation">
          <a href="#dashboard" className="nav-link active">Dashboard</a>
          <a href="#appointments" className="nav-link">Appointments</a>
          <a href="#messages" className="nav-link">Messages</a>
          <a href="#records" className="nav-link">Records</a>
        </nav>

        <div className="user-section">
          <div 
            className="user-profile"
            onClick={() => setShowUserMenu(!showUserMenu)}
          >
            <img 
              src={user?.picture || '/default-avatar.png'} 
              alt="Profile"
              className="profile-image"
            />
            <span className="user-name">{user?.name}</span>
            <span className="dropdown-arrow">▼</span>
          </div>

          {showUserMenu && (
            <div className="user-menu">
              <div className="user-info">
                <p className="user-email">{user?.email}</p>
              </div>
              <hr />
              <button className="menu-item">Profile Settings</button>
              <button className="menu-item">Privacy & Security</button>
              <button className="menu-item">Help & Support</button>
              <hr />
              <button 
                className="menu-item logout"
                onClick={handleLogout}
              >
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;