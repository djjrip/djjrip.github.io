const nodemailer = require('nodemailer');
const fs = require('fs');

const queue = JSON.parse(fs.readFileSync('C:/Users/Jayson Quindao/Desktop/Projects & Code/gaming-for-groceries/sponsor_outreach_queue.json', 'utf8'));

const transporter = nodemailer.createTransport({
    host: 'smtp.mail.me.com',
    port: 587,
    secure: false,
    auth: {
        user: 'jquindao1@icloud.com',
        pass: 'ziiv-nofz-vfvs-ehht'
    }
});

async function dispatchAll() {
    console.log("🔥 DISPATCHING DFW B2B TOURNAMENT SPONSORSHIP CANNON 🔥");
    console.log(`[+] Total Targets in Queue: ${queue.length}`);
    
    for (const item of queue) {
        try {
            console.log(`[>>] Pitching ${item.company} (${item.to})...`);
            await transporter.sendMail({
                from: '"Jayson Quindao | GG Loop" <jquindao1@icloud.com>',
                to: item.to,
                subject: item.subject,
                text: item.body
            });
            console.log(`[✅ DELIVERED] Pitch sent to ${item.company}`);
            await new Promise(r => setTimeout(r, 2500));
        } catch (err) {
            console.error(`[❌ ERROR] Failed to send to ${item.to}:`, err.message);
        }
    }
    
    console.log("🏆 ALL DFW SPONSORSHIP PITCHES DISPATCHED SUCCESSFULLY!");
}

dispatchAll();
