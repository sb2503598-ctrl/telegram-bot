import asyncio
import logging
import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession

logging.basicConfig(level=logging.INFO)

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION")
OWNER_ID = os.environ.get("OWNER_ID")
OWNER_ID_INT = int(os.environ.get("OWNER_ID_INT"))
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
        f"➡️ Antworten: /r {sender.id} Deine Antwort"
    )
    await client.send_message(OWNER_ID, forward_text)
    await event.reply("Deine Nachricht wurde weitergeleitet. ✅")

@client.on(events.NewMessage(incoming=True, pattern=r'^/r (\d+) (.+)$'))
async def reply_to_user(event):
    if event.sender_id == OWNER_ID_INT:
        target_id = int(event.pattern_match.group(1))
        reply_text = event.pattern_match.group(2)
        try:
            await client.send_message(target_id, reply_text)
            await event.respond("✅ Gesendet!")
        except Exception as e:
            await event.respond(f"❌ Fehler: {e}")

async def scheduler():
    await asyncio.sleep(30)
    dialogs = await client.get_dialogs()
    known_ids = {d.id for d in dialogs}
    logging.info(f"Bekannte Chats: {len(known_ids)}")
    
    while True:
        for group_id in GROUP_IDS:
            try:
                await client.send_message(group_id, POST_TEXT)
                logging.info(f"Gepostet in {group_id}")
            except Exception as e:
                logging.error(f"Fehler in {group_id}: {e}")
            await asyncio.sleep(2)
        await asyncio.sleep(INTERVAL)

async def run():
    await client.start()
    logging.info("Bot gestartet!")
    asyncio.ensure_future(scheduler())
    await client.run_until_disconnected()

asyncio.run(run())
