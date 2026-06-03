// send.js — Envia mensagem para o grupo via Baileys
// Reutiliza a auth_info do trump_bot (já autenticado)
//
// Uso:
//   node send.js --text "mensagem"
//   node send.js --text "mensagem" --gif /caminho/arquivo.gif

const baileys = require('@whiskeysockets/baileys');
const makeWASocket = baileys.default;
const { useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion } = baileys;
const { Boom } = require('@hapi/boom');
const pino = require('pino');
const fs = require('fs');
const path = require('path');

// ── Configuração ──────────────────────────────────────────────
const GROUP_NAME = 'Previsão Clima por IA';

// Usa a auth_info do trump_bot — já autenticada, não precisa QR
const AUTH_FOLDER = '/homeassistant/trump_bot/auth_info';

const TIMEOUT_MS = 60000;

// ── Lê argumentos ─────────────────────────────────────────────
const args = process.argv.slice(2);
const textIdx = args.indexOf('--text');
const gifIdx = args.indexOf('--gif');
const messageText = textIdx !== -1 ? args[textIdx + 1] : null;
const gifPath = gifIdx !== -1 ? args[gifIdx + 1] : null;

if (!messageText) {
  console.error('Uso: node send.js --text "mensagem" [--gif /caminho/arquivo.gif]');
  process.exit(1);
}

// ── Main ──────────────────────────────────────────────────────
async function main() {
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_FOLDER);
  const { version } = await fetchLatestBaileysVersion();
  const logger = pino({ level: 'silent' });

  const sock = makeWASocket({
    version,
    logger,
    auth: state,
    printQRInTerminal: false,
    browser: ['Trump Monitor Bot', 'Chrome', '120.0.0'],
    connectTimeoutMs: TIMEOUT_MS,
  });

  sock.ev.on('creds.update', saveCreds);

  const timeout = setTimeout(() => {
    console.error('Timeout — não foi possível conectar.');
    process.exit(1);
  }, TIMEOUT_MS);

  sock.ev.on('connection.update', async (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      console.error('QR code apareceu — sessão do trump_bot expirou.');
      process.exit(1);
    }

    if (connection === 'close') {
      clearTimeout(timeout);
      const reason = new Boom(lastDisconnect?.error)?.output?.statusCode;
      console.error(`Desconectado (${reason}).`);
      process.exit(1);
    }

    if (connection === 'open') {
      clearTimeout(timeout);
      console.log('Conectado.');

      try {
        const groups = await sock.groupFetchAllParticipating();
        let groupJid = null;

        for (const [jid, group] of Object.entries(groups)) {
          if (group.subject === GROUP_NAME) {
            groupJid = jid;
            break;
          }
        }

        if (!groupJid) {
          console.error(`Grupo "${GROUP_NAME}" não encontrado.`);
          console.log('Grupos disponíveis:');
          for (const [, g] of Object.entries(groups)) {
            console.log(`  -> "${g.subject}"`);
          }
          process.exit(1);
        }

        console.log(`Enviando para "${GROUP_NAME}"...`);

        if (gifPath && fs.existsSync(gifPath)) {
          const gifBuffer = fs.readFileSync(gifPath);
          await sock.sendMessage(groupJid, {
            video: gifBuffer,
            gifPlayback: true,
            caption: messageText,
            mimetype: 'video/mp4',
          });
          console.log('GIF + mensagem enviados.');
        } else {
          await sock.sendMessage(groupJid, { text: messageText });
          console.log('Mensagem enviada.');
        }

        await new Promise(r => setTimeout(r, 2000));
        process.exit(0);

      } catch (err) {
        console.error('Erro ao enviar:', err.message);
        process.exit(1);
      }
    }
  });
}

main().catch(err => {
  console.error('Erro fatal:', err.message);
  process.exit(1);
});
