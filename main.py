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

pending_replies = {}

@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def forward_to_owner(event):
    sender = await event.get_sender()
    text = event.message.text or "[Kein Text]"
    forward_text = (
        f"📨 Neue Nachricht von:\n"
        f"Name: {sender.first_name} {sender.last_name or ''}\n"
        f"Username: @{sender.username or 'keiner'}\n"
        f"ID: {sender.id}\n\n"
        f"Nachricht:\n{text}"
    )
    sent = await client.send_message(OWNER_ID, forward_text)
    pending_replies[sent.id] = sender.id
    await event.reply("Deine Nachricht wurde weitergeleitet. ✅")

@client.on(events.NewMessage(outgoing=True, func=lambda e: e.is_private))
async def handle_owner_reply(event):
    if event.reply_to_msg_id and event.reply_to_msg_id in pending_replies:
        target_id = pending_replies[event.reply_to_msg_id]
        try:
            await client.send_message(target_id, event.text)
            await event.edit(f"✅ Gesendet!\n\n{event.text}")
        except Exception as e:
            logging.error(f"Fehler beim Antworten: {e}")

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
