# config.py
import os

# ✅ Render uchun Environment Variables dan olish
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Admin ID
ADMINS = [int(x) for x in os.environ.get("ADMIN_IDS", "123456789").split(",")]

# Bot sozlamalari
BOT_NAME = "MyAutoBot"
BOT_USERNAME = os.environ.get("BOT_USERNAME", "@my_auto_bot")

# Kanal (majburiy obuna)
CHANNELS = [
    {
        "id": int(os.environ.get("CHANNEL_ID", "-1001234567890")),
        "url": os.environ.get("CHANNEL_URL", "https://t.me/my_channel"),
        "name": os.environ.get("CHANNEL_NAME", "Asosiy Kanal"),
    },
]

# Ma'lumotlar bazasi
DB_NAME = "bot_database.db"

# Avtomatik javoblar
AUTO_REPLIES = {
    "salom": "Salom! 👋 Sizga qanday yordam bera olaman?",
    "narx": "💰 Narxlar ro'yxati:\n\n1. Asosiy — 50,000\n2. Premium — 100,000\n3. VIP — 200,000",
    "bog'lanish": "📞 Telefon: +998 90 123 45 67",
    "yordam": "❓ /start - Boshlash\n/help - Yordam",
}

WELCOME_MESSAGE = """
🎉 <b>Xush kelibsiz, {name}!</b>

🤖 Men — to'liq avtomatlashtirilgan botman.
Quyidagi tugmalardan foydalaning 👇
"""

GROUP_SETTINGS = {
    "anti_spam": True,
    "anti_flood": True,
    "max_warnings": 3,
    "flood_limit": 5,
    "welcome_new_members": True,
    "auto_delete_join_messages": True,
}
