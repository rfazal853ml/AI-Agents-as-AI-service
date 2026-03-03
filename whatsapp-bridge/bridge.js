// bridge.js

const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios  = require('axios');

const BACKEND = "http://localhost:8000/chat";
const DELAY_MS = 600; // small pause between multiple messages

const client = new Client({ authStrategy: new LocalAuth() });

// ── Helpers ───────────────────────────────────────────────────

const sleep = ms => new Promise(r => setTimeout(r, ms));

/**
 * Send a single reply unit.
 * shape: { text, image_url? }
 */
async function sendUnit(message, unit) {
    if (unit.image_url) {
        try {
            const media = await MessageMedia.fromUrl(unit.image_url, { unsafeMime: true });
            await message.reply(media, undefined, { caption: unit.text });
        } catch (err) {
            // Image failed — fall back to text only
            console.error("Image load failed:", err.message);
            await message.reply(unit.text);
        }
    } else {
        await message.reply(unit.text);
    }
}

/**
 * Handle the backend response which can be:
 *   { text }                        — single plain reply
 *   { text, image_url }             — single image reply
 *   { messages: [{text,image_url}] }— sequence of replies
 */
async function handleResponse(message, data) {
    if (data.messages && Array.isArray(data.messages)) {
        for (const unit of data.messages) {
            await sendUnit(message, unit);
            await sleep(DELAY_MS);
        }
    } else {
        await sendUnit(message, data);
    }
}

// ── WhatsApp events ───────────────────────────────────────────

client.on('qr', qr => {
    console.log('📱 Scan this QR with WhatsApp:');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('✅ WhatsApp client is ready!');
});

client.on('message', async message => {
    // Ignore group messages (optional)
    if (message.from.includes('@g.us')) return;

    console.log(`📩 [${message.from}]: ${message.body}`);

    try {
        const { data } = await axios.post(BACKEND, {
            user_id: message.from,
            message: message.body,
        });

        await handleResponse(message, data);

    } catch (err) {
        console.error("Backend error:", err.message);
        await message.reply("⚠️ Something went wrong. Please try again.");
    }
});

client.initialize();