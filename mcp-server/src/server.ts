import 'dotenv/config';
import { GoogleGenerativeAI } from '@google/generative-ai';
import readline from 'node:readline/promises';
import { stdin as input, stdout as output } from 'node:process';
import { buildSystemInstruction, loadUserProfile } from './context';

type Msg = { role: 'user' | 'assistant'; content: string };

const apiKey = process.env.GEMINI_API_KEY;
if (!apiKey) throw new Error('Missing GEMINI_API_KEY in .env');

const genAI = new GoogleGenerativeAI(apiKey);

const DEFAULT_USER = process.env.DEFAULT_USER_ID || 'demo';
const BACKEND = process.env.BACKEND_BASE_URL; // your Flask service
const AGENT_EMAIL = process.env.AGENTMAIL_AGENT || 'terriblemedicine23@agentmail.to';

function parseArg(flag: string, fallback?: string) {
  const i = process.argv.indexOf(flag);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}

async function sendEmailViaBackend(to: string, subject: string, text: string) {
  if (!BACKEND) {
    console.log('⚠️  BACKEND_BASE_URL not set; cannot send email.');
    return;
  }
  const resp = await fetch(`${BACKEND}/api/send-new-message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      agent_email: AGENT_EMAIL,
      recipientEmail: to,
      subject,
      text
    })
  });
  if (!resp.ok) {
    const err = await resp.text().catch(() => '');
    console.log(`❌ Email failed: ${resp.status} ${err}`);
    return;
  }
  console.log('✅ Email sent (forwarded by backend).');
}

async function main() {
  const userId = parseArg('--user', DEFAULT_USER);

  const systemInstruction = buildSystemInstruction(userId);
  const model = genAI.getGenerativeModel({
    model: 'gemini-2.0-flash',
    systemInstruction
  });

  const profile = loadUserProfile(userId);
  console.log(`\n👤 User: ${profile.name ?? userId}  |  Email: ${profile.email ?? 'N/A'}`);
  console.log('💬 Type a message. Commands:');
  console.log('   :mail "Subject" | Body text     (sends an email to user on file)');
  console.log('   :quit                            (exit)\n');

  const rl = readline.createInterface({ input, output });
  const history: Msg[] = [];

  while (true) {
    const q = (await rl.question('you> ')).trim();
    if (!q) continue;
    if (q === ':quit') break;

    // :mail "Subject" | body
    if (q.startsWith(':mail')) {
      if (!profile.email) {
        console.log('⚠️  No recipient email on file in profile.json for this user.');
        continue;
      }
      const m = q.match(/^:mail\s+"([^"]+)"\s*\|\s*(.+)$/);
      if (!m) {
        console.log('Usage: :mail "Subject" | Body text');
        continue;
      }
      const [, subject, body] = m;
      await sendEmailViaBackend(profile.email, subject, body);
      continue;
    }

    // chat
    const contents = [
      ...history.map(h => ({ role: h.role === 'assistant' ? 'model' : 'user', parts: [{ text: h.content }] })),
      { role: 'user', parts: [{ text: q }] }
    ];

    try {
      const resp = await model.generateContent({ contents });
      const text = resp.response.text();
      console.log(`\nai> ${text}\n`);
      history.push({ role: 'user', content: q });
      history.push({ role: 'assistant', content: text });
    } catch (e: any) {
      console.log('❌ chat_failed:', e?.message ?? String(e));
    }
  }

  rl.close();
  console.log('bye 👋');
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
