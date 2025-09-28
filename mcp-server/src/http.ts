// mcp-server/src/http.ts
import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import { GoogleGenerativeAI } from '@google/generative-ai';

import {
  buildSystemInstruction,
  loadUserProfile,
} from './context';

// ---------- Environment ----------
const PORT = Number(process.env.PORT ?? 8787);
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
const BACKEND_BASE_URL = process.env.BACKEND_BASE_URL; // e.g. http://127.0.0.1:5000
const AGENTMAIL_AGENT = process.env.AGENTMAIL_AGENT || 'terriblemedicine23@agentmail.to';

if (!GEMINI_API_KEY) {
  throw new Error('Missing GEMINI_API_KEY in .env');
}

const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);

// ---------- App ----------
const app = express();
app.use(cors());            // dev convenience; lock down in prod
app.use(express.json());

// Types
type Msg = { role: 'user' | 'assistant'; content: string };

// ---------- Routes ----------

// Health check
app.get('/api/health', (_req, res) => {
  res.json({ ok: true, service: 'mcp-http', time: new Date().toISOString() });
});

// Return a user's profile (from context/profile.json)
app.get('/api/profile/:userId', (req, res) => {
  const { userId } = req.params;
  const profile = loadUserProfile(userId || 'demo');
  res.json({ userId, profile });
});

// Chat with Gemini using per-user context
app.post('/api/chat', async (req, res) => {
  try {
    const {
      message,
      history = [] as Msg[],
      userId = 'demo',
      modelName = 'gemini-2.0-flash',
    } = req.body as {
      message: string;
      history?: Msg[];
      userId?: string;
      modelName?: string;
    };

    if (!message || typeof message !== 'string') {
      return res.status(400).json({ error: 'message is required (string)' });
    }

    // Build system instruction using profile + meds red flags
    const systemInstruction = buildSystemInstruction(userId);

    const model = genAI.getGenerativeModel({
      model: modelName,
      systemInstruction,
    });

    // Transform our history into Gemini "contents"
    const contents = [
      ...history.map(h => ({
        role: h.role === 'assistant' ? 'model' : 'user',
        parts: [{ text: h.content }],
      })),
      { role: 'user', parts: [{ text: message }] },
    ];

    const resp = await model.generateContent({ contents });
    const text = resp.response.text();

    res.json({ text });
  } catch (e: any) {
    console.error('chat_failed:', e?.response?.error ?? e);
    res.status(500).json({ error: 'chat_failed', details: e?.message ?? String(e) });
  }
});

// Forward an email request to your Flask service that talks to AgentMail
// Body: { to: string, subject: string, text: string, userId?: string }
app.post('/api/send-email', async (req, res) => {
  try {
    const { to, subject, text, userId = 'demo' } = req.body as {
      to: string;
      subject: string;
      text: string;
      userId?: string;
    };

    if (!BACKEND_BASE_URL) {
      return res.status(400).json({ error: 'BACKEND_BASE_URL not configured in .env' });
    }
    if (!to || !subject || !text) {
      return res.status(400).json({ error: 'to, subject, and text are required' });
    }

    // Optional: look up user (for demo/logging)
    const profile = loadUserProfile(userId);

    const resp = await fetch(`${BACKEND_BASE_URL}/api/send-new-message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agent_email: AGENTMAIL_AGENT,         // the AgentMail inbox you own
        recipientEmail: to,                   // destination
        subject,
        text,
        // You can pass additional metadata if your Flask endpoint accepts it
        meta: { userId, profileEmail: profile.email ?? null },
      }),
    });

    if (!resp.ok) {
      const errTxt = await resp.text().catch(() => '');
      console.error('send-email failed:', resp.status, errTxt);
      return res.status(502).json({ error: 'sender_bad_gateway', status: resp.status, body: errTxt });
    }

    const data = await resp.json().catch(() => ({}));
    res.json({ ok: true, forwarded: data });
  } catch (e: any) {
    console.error('send-email error:', e);
    res.status(500).json({ error: 'send_email_failed', details: e?.message ?? String(e) });
  }
});

// ---------- Start ----------
app.listen(PORT, () => {
  console.log(`Chat API listening on http://localhost:${PORT}`);
  if (BACKEND_BASE_URL) {
    console.log(`Email sender proxy -> ${BACKEND_BASE_URL}/api/send-new-message`);
  } else {
    console.log('Email sender proxy disabled (BACKEND_BASE_URL not set).');
  }
});

export default app;
