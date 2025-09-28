import Chat from './components/chat';

export default function App() {
  return (
    <main style={{ maxWidth: 900, margin: '0 auto', padding: 16 }}>
      <h1>AgentMail + Gemini Demo</h1>
      <p style={{ color: '#555' }}>Ask something like: “Suggest an OTC option for a headache.”</p>
      <Chat />
    </main>
  );
}
