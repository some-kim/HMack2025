import 'dotenv/config';
import fs from 'fs';
import path from 'path';
import { GoogleGenerativeAI } from '@google/generative-ai';

const systemInstruction = fs.readFileSync(
  path.join(__dirname, '..', 'prompts', 'system.md'),
  'utf8'
);

async function main() {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) throw new Error('Missing GEMINI_API_KEY in .env');

  const genAI = new GoogleGenerativeAI(apiKey);
  const model = genAI.getGenerativeModel({
    model: 'gemini-2.0-flash',
    systemInstruction
  });

  const resp = await model.generateContent('Suggest OTC options for a headache.');
  console.log(resp.response.text());
}
main().catch((e) => {
  console.error(e?.response?.error ?? e);
  process.exit(1);
});
