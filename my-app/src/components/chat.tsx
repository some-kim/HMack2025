import React, { useState } from 'react';


type Role = 'user' | 'assistant';
type Msg = { role: Role; content: string };


export default function Chat() {
 const [history, setHistory] = useState<Msg[]>([]);
 const [input, setInput] = useState('');
 const [loading, setLoading] = useState(false);


 const send = async () => {
   const message = input.trim();
   if (!message) return;


   setInput('');
   const nextHistory: Msg[] = [...history, { role: 'user', content: message }];
   setHistory(nextHistory);
   setLoading(true);


   try {
     const resp = await fetch('/api/chat', {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ message, history: nextHistory })
     });
     const data = await resp.json();
     setHistory(h => [...h, { role: 'assistant', content: data.text ?? '(no response)' }]);
   } catch (e) {
     console.error(e);
     setHistory(h => [...h, { role: 'assistant', content: 'Error contacting AI.' }]);
   } finally {
     setLoading(false);
   }
 };


 const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
   if (e.key === 'Enter' && !e.shiftKey) send();
 };


 return (
   <div style={{ display: 'grid', gap: 12 }}>
     <div style={{ border: '1px solid #ddd', borderRadius: 8, padding: 12, height: 360, overflowY: 'auto', background: '#fff' }}>
       {history.map((m, i) => (
         <div key={i} style={{ marginBottom: 8, textAlign: m.role === 'user' ? 'right' : 'left' }}>
           <span style={{ display: 'inline-block', padding: '8px 12px', borderRadius: 12, background: m.role === 'user' ? '#e6f0ff' : '#f2f3f5' }}>
             {m.content}
           </span>
         </div>
       ))}
       {loading && <div style={{ color: '#666' }}>Thinking…</div>}
     </div>


     <div style={{ display: 'flex', gap: 8 }}>
       <input
         style={{ flex: 1, padding: '10px 12px', borderRadius: 8, border: '1px solid #ddd' }}
         placeholder="Type a message…"
         value={input}
         onChange={e => setInput(e.target.value)}
         onKeyDown={onKeyDown}
       />
       <button
         style={{ padding: '10px 14px', borderRadius: 8, color: '#fff', background: '#111', border: 'none' }}
         onClick={send}
         disabled={loading}
       >
         Send
       </button>
     </div>
   </div>
 );
}
