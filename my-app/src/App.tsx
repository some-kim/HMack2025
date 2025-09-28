import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import LoginPage from './components/LoginPage';
import Dashboard from './components/Dashboard';
import Loading from './components/Loading';
import './App.css';

const App: React.FC = () => {
  const { isLoading, isAuthenticated } = useAuth0();

  if (isLoading) {
    return <Loading />;
  }

  return (
    <div className="App">
      {isAuthenticated ? <Dashboard /> : <LoginPage />}
    </div>
  );
};

export default App;