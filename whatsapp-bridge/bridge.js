const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');

const client = new Client({
    authStrategy: new LocalAuth()
});

client.on('qr', qr => {
    console.log('Scan this QR with WhatsApp');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('WhatsApp is ready!');
});

client.on('message', async message => {
    try {
        console.log("Incoming:", message.body);

        const response = await axios.post("http://localhost:8000/chat", {
            user_id: message.from,
            message: message.body
        });

        await message.reply(response.data.response);

    } catch (error) {
        console.error("Error:", error.message);
        await message.reply("Something went wrong.");
    }
});

client.initialize();