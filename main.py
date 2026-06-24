import asyncio
import logging
import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession

logging.basicConfig(level=logging.INFO)

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION")
OWNER_ID = int(os.environ.get("OWNER_ID"))
GROUP_IDS = [int(x) for x in os.environ.get("GROUP_IDS", "").split(",")]
POST_TEXT = os.environ.get("POST_TEXT")
INTERVAL = int(os.environ.get("INTERVAL", "180"))

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

@client.on(events.NewMessage)
async def handle_all(event):
    logging.info(f"Nachricht empfangen: chat={event.chat_id} sender={event.sender_id} text={event.text}")
    if event.is_private and event.sender_id != OWNER_ID:
        sender = await event.get_sender()
        text = event.message.text or "[Kein Text]"
        forward_text = (
            f"📨 Neue Nachricht von:\n"
            f"Name: {sender.first_name} {sender.last_name or ''}\n"
            f"Username: @{sender.username or 'keiner'}\n"
            f"ID: {sender.id}\n\n"
            f"Nachricht:\n{text}\n\n"
            f"➡️ Antworten: /r {sender.id} Deine Antwort"
        )
        await client.send_message(OWNER_ID, forward_text)
    elif event.is_private and event.sender_id == OWNER_ID and event.text and event.text.startswith("/r "):
        parts = event.text.split(" ", 2)
        if len(parts) == 3:
            target_id = int(parts[1])
            reply_text = parts[2]
            try:
                await client.send_message(target_id, reply_text)
                await event.respond("✅ Gesendet!")
            except Exception as e:
                await event.respond(f"❌ Fehler: {e}")

async def scheduler():
    while True:
        for group_id in GROUP_IDS:
            try:
                await client.send_message(group_id, POST_TEXT)
                logging.info(f"Gepostet in {group_id}")
            except Exception as e:
                logging.error(f"Fehler: {e}")
        await asyncio.sleep(INTERVAL)

async def main():
    await client.start()
    logging.info("Bot gestartet!")
    await scheduler()

with client:
    client.loop.run_until_complete(main())
