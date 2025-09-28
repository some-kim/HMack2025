<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
import Chat from './components/chat';
>>>>>>> Stashed changes

export default function App() {
  return (
<<<<<<< Updated upstream
    <div className="App">
      {isAuthenticated ? <Dashboard /> : <LoginPage />}
    </div>
  );
};

export default App;
=======
=======
import Chat from './components/chat';

export default function App() {
  return (
>>>>>>> Stashed changes
    <main style={{ maxWidth: 900, margin: '0 auto', padding: 16 }}>
      <h1>AgentMail + Gemini Demo</h1>
      <p style={{ color: '#555' }}>Ask something like: “Suggest an OTC option for a headache.”</p>
      <Chat />
    </main>
  );
<<<<<<< Updated upstream
}
>>>>>>> Stashed changes
=======
}
>>>>>>> Stashed changes
