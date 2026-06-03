// send.js — Envia mensagem/GIF para o grupo via Baileys
// Uso:
//   node send.js --text "mensagem"
//   node send.js --text "mensagem" --gif /caminho/para/arquivo.gif
//
// Na primeira execução mostra QR code para escanear.
// Sessão salva em ./auth_info — não precisa escanear de novo.

const baileys = require('@whiskeysockets/baileys');
const makeWASocket = baileys.default;
const { useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion } = baileys;
const { Boom } = require('@hapi/boom');
const qrcode = require('qrcode-terminal');
const pino = require('pino');
const fs = require('fs');
const path = require('path');

// ── Configuração ──────────────────────────────────────────────
const GROUP_NAME = 'Previsão Clima por IA';
const AUTH_FOLDER = path.join(__dirname, 'auth_info');
const TIMEOUT_MS = 60000;

// ── Lê argumentos da linha de comando ────────────────────────
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
  if (!fs.existsSync(AUTH_FOLDER)) fs.mkdirSync(AUTH_FOLDER, { recursive: true });

  const { state, saveCreds } = await useMultiFileAuthState(AUTH_FOLDER);
  const { version } = await fetchLatestBaileysVersion();
  const logger = pino({ level: 'silent' });

  const sock = makeWASocket({
    version,
    logger,
    auth: state,
    printQRInTerminal: false,
    browser: ['Meteologix Bot', 'Chrome', '120.0.0'],
    connectTimeoutMs: TIMEOUT_MS,
  });

  sock.ev.on('creds.update', saveCreds);

  // Timeout de segurança
  const timeout = setTimeout(() => {
    console.error('Timeout — não foi possível conectar.');
    process.exit(1);
  }, TIMEOUT_MS);

  sock.ev.on('connection.update', async (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      console.log('\n╔══════════════════════════════════════════╗');
      console.log('║  📱  ESCANEIE O QR CODE COM SEU WHATSAPP  ║');
      console.log('╚══════════════════════════════════════════╝\n');
      qrcode.generate(qr, { small: true });
      console.log('\n(WhatsApp > Configurações > Aparelhos conectados > Conectar)\n');
    }

    if (connection === 'close') {
      clearTimeout(timeout);
      const reason = new Boom(lastDisconnect?.error)?.output?.statusCode;
      if (reason === DisconnectReason.loggedOut) {
        console.error('Sessão expirada. Delete a pasta auth_info e rode novamente.');
      } else {
        console.error(`Desconectado (${reason}).`);
      }
      process.exit(1);
    }

    if (connection === 'open') {
      clearTimeout(timeout);
      console.log('✅ WhatsApp conectado.');

      try {
        // Busca o grupo pelo nome
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
            console.log(`  → "${g.subject}"`);
          }
          await sock.logout();
          process.exit(1);
        }

        console.log(`📤 Enviando para "${GROUP_NAME}"...`);

        // Envia GIF se fornecido
        if (gifPath && fs.existsSync(gifPath)) {
          const gifBuffer = fs.readFileSync(gifPath);
          await sock.sendMessage(groupJid, {
            video: gifBuffer,
            gifPlayback: true,
            caption: messageText,
            mimetype: 'video/mp4',
          });
          console.log('✅ GIF + mensagem enviados.');
        } else {
          // Só texto
          await sock.sendMessage(groupJid, { text: messageText });
          console.log('✅ Mensagem enviada.');
        }

        await sock.logout();
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
