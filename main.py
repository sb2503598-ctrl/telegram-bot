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

@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def forward_to_owner(event):
    sender = await event.get_sender()
    text = event.message.text or "[Kein Text]"
    forward_text = (
        f"📨 Neue Nachricht von:\n"
        f"Name: {sender.first_name} {sender.last_name or ''}\n"
        f"Username: @{sender.username or 'keiner'}\n"
        f"ID: {sender.id}\n\n"
        f"Nachricht:\n{text}\n\n"
        f"➡️ Antworten mit: /r {sender.id} Deine Antwort hier"
    )
    await client.send_message(OWNER_ID, forward_text)
    await event.reply("Deine Nachricht wurde weitergeleitet. ✅")

@client.on(events.NewMessage(outgoing=True, func=lambda e: e.is_private and e.text and e.text.startswith("/r ")))
async def reply_to_user(event):
    try:
        parts = event.text.split(" ", 2)
        target_id = int(parts[1])
        reply_text = parts[2]
        await client.send_message(target_id, reply_text)
        await event.edit(f"✅ Gesendet an {target_id}:\n{reply_text}")
    except Exception as e:
        await event.edit(f"❌ Fehler beim Senden: {e}")

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
