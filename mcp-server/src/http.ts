import 'dotenv/config';
import fs from 'fs';
import path from 'path';
import express from 'express';
import cors from 'cors';
import { GoogleGenerativeAI } from '@google/generative-ai';

const app = express();
app.use(cors());                 // dev only; proxy makes this unnecessary but safe
app.use(express.json());

const systemInstruction = fs.readFileSync(
  path.join(__dirname, '..', 'prompts', 'system.md'),
  'utf8'
);

const apiKey = process.env.GEMINI_API_KEY;
if (!apiKey) throw new Error('Missing GEMINI_API_KEY in .env');

const genAI = new GoogleGenerativeAI(apiKey);
const model = genAI.getGenerativeModel({
  model: 'gemini-2.0-flash',
  systemInstruction
});

/**
 * POST /api/chat
 * body: { message: string, history?: Array<{role:'user'|'assistant', content:string}> }
 * returns: { text: string }
 *
 * Note: Google’s API expects roles 'user' and 'model'.
 * We map 'assistant' -> 'model' for you.
 */
app.post('/api/chat', async (req, res) => {
  try {
    const { message, history = [] } = req.body as {
      message: string;
      history?: Array<{ role: 'user' | 'assistant'; content: string }>;
    };

    if (!message || typeof message !== 'string') {
      return res.status(400).json({ error: 'message is required' });
    }

    // Transform our history to Gemini's "contents" format
    const contents = history.map((m) => ({
      role: m.role === 'assistant' ? 'model' : 'user',
      parts: [{ text: m.content }]
    }));

    // Append the new user message
    contents.push({ role: 'user', parts: [{ text: message }] });

    const resp = await model.generateContent({ contents });
    const text = resp.response.text();
    res.json({ text });
  } catch (e: any) {
    console.error(e?.response?.error ?? e);
    res.status(500).json({ error: 'chat_failed', details: e?.message ?? String(e) });
  }
});

const PORT = process.env.PORT ? Number(process.env.PORT) : 8787;
app.listen(PORT, () => {
  console.log(`Chat API listening on http://localhost:${PORT}`);
});
