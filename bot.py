# bot.py

import logging
import os
import asyncio
from threading import Thread
from flask import Flask, request

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)
from config import BOT_TOKEN, ADMINS
from database import db

# Handlers
from handlers.start import start_command, check_subscription_callback
from handlers.user import (
    handle_services, handle_prices, handle_profile,
    handle_statistics, handle_referral, handle_contact,
    handle_help, handle_settings, handle_my_orders,
    start_order, order_product, order_quantity,
    order_confirm_callback, service_callback, back_callback,
    ORDER_PRODUCT, ORDER_QUANTITY, ORDER_CONFIRM,
)
from handlers.admin import (
    admin_panel, admin_statistics, admin_users_list,
    start_broadcast, broadcast_message, broadcast_confirm_callback,
    start_ban, ban_user_id, admin_action_callback,
    manage_auto_replies, start_add_auto_reply,
    add_auto_reply_trigger, add_auto_reply_response,
    export_data, back_to_main,
    BROADCAST_MESSAGE, BAN_USER_ID,
    ADD_AUTO_REPLY_TRIGGER, ADD_AUTO_REPLY_RESPONSE,
)
from handlers.auto_reply import (
    auto_reply_handler, handle_new_member, handle_left_member,
    handle_photo, handle_document, handle_video,
    handle_voice, handle_contact as handle_contact_msg,
    handle_location,
)

# ============ LOGGING ============
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ============ FLASK (RENDER UCHUN KEEP ALIVE) ============
app = Flask(__name__)

@app.route("/")
def home():
    return "🤖 Bot ishlayapti!", 200

@app.route("/health")
def health():
    return "OK", 200

def run_flask():
    """Flask serverni ishga tushirish"""
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


# ============ BOT FUNKSIYALARI ============

async def post_init(application: Application):
    """Bot ishga tushganda"""
    await db.create_tables()

    commands = [
        BotCommand("start", "Botni ishga tushirish"),
        BotCommand("help", "Yordam"),
        BotCommand("profile", "Profil"),
        BotCommand("services", "Xizmatlar"),
        BotCommand("prices", "Narxlar"),
        BotCommand("order", "Buyurtma berish"),
        BotCommand("referral", "Referal tizimi"),
        BotCommand("contact", "Bog'lanish"),
        BotCommand("settings", "Sozlamalar"),
    ]
    await application.bot.set_my_commands(commands)

    for admin_id in ADMINS:
        try:
            await application.bot.send_message(
                admin_id,
                "🟢 <b>Bot Render serverda ishga tushdi!</b>",
                parse_mode="HTML"
            )
        except Exception:
            pass

    logger.info("✅ Bot muvaffaqiyatli ishga tushdi!")


async def error_handler(update: Update, context):
    """Xatoliklarni qayta ishlash"""
    logger.error(f"Xatolik: {context.error}")
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Xatolik yuz berdi. Qayta urinib ko'ring."
            )
        except Exception:
            pass


def main():
    """Asosiy funksiya"""

    # ✅ Flask ni alohida threadda ishga tushirish (Render uchun)
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("🌐 Flask server ishga tushdi")

    # Bot yaratish
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # ============ CONVERSATION HANDLERS ============

    order_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🛒 Buyurtma berish$"), start_order),
            CommandHandler("order", start_order),
        ],
        states={
            ORDER_PRODUCT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, order_product)
            ],
            ORDER_QUANTITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, order_quantity)
            ],
            ORDER_CONFIRM: [
                CallbackQueryHandler(
                    order_confirm_callback, pattern="^(confirm_order_|cancel_order)"
                )
            ],
        },
        fallbacks=[CommandHandler("start", start_command)],
    )

    broadcast_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📢 Xabar tarqatish$"), start_broadcast),
        ],
        states={
            BROADCAST_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message)
            ],
        },
        fallbacks=[CommandHandler("start", start_command)],
    )

    ban_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🚫 Ban/Unban$"), start_ban),
        ],
        states={
            BAN_USER_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ban_user_id)
            ],
        },
        fallbacks=[CommandHandler("start", start_command)],
    )

    auto_reply_conv = ConversationHandler(
        entry_points=[
            CommandHandler("add_reply", start_add_auto_reply),
        ],
        states={
            ADD_AUTO_REPLY_TRIGGER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_auto_reply_trigger)
            ],
            ADD_AUTO_REPLY_RESPONSE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_auto_reply_response)
            ],
        },
        fallbacks=[CommandHandler("start", start_command)],
    )

    # ============ HANDLERS QO'SHISH ============

    # Conversations
    application.add_handler(order_conv)
    application.add_handler(broadcast_conv)
    application.add_handler(ban_conv)
    application.add_handler(auto_reply_conv)

    # Commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", handle_help))
    application.add_handler(CommandHandler("profile", handle_profile))
    application.add_handler(CommandHandler("services", handle_services))
    application.add_handler(CommandHandler("prices", handle_prices))
    application.add_handler(CommandHandler("referral", handle_referral))
    application.add_handler(CommandHandler("contact", handle_contact))
    application.add_handler(CommandHandler("settings", handle_settings))
    application.add_handler(CommandHandler("admin", admin_panel))

    # Admin text handlers
    application.add_handler(MessageHandler(
        filters.Regex("^📊 Bot statistikasi$"), admin_statistics))
    application.add_handler(MessageHandler(
        filters.Regex("^👥 Foydalanuvchilar$"), admin_users_list))
    application.add_handler(MessageHandler(
        filters.Regex("^🤖 Avtomatik javoblar$"), manage_auto_replies))
    application.add_handler(MessageHandler(
        filters.Regex("^📥 Export data$"), export_data))
    application.add_handler(MessageHandler(
        filters.Regex("^⚙️ Bot sozlamalari$"), admin_panel))
    application.add_handler(MessageHandler(
        filters.Regex("^🔙 Asosiy menyu$"), back_to_main))

    # User text handlers
    application.add_handler(MessageHandler(
        filters.Regex("^📋 Xizmatlar$"), handle_services))
    application.add_handler(MessageHandler(
        filters.Regex("^💰 Narxlar$"), handle_prices))
    application.add_handler(MessageHandler(
        filters.Regex("^👤 Profil$"), handle_profile))
    application.add_handler(MessageHandler(
        filters.Regex("^📊 Statistika$"), handle_statistics))
    application.add_handler(MessageHandler(
        filters.Regex("^🔗 Referal$"), handle_referral))
    application.add_handler(MessageHandler(
        filters.Regex("^📞 Bog'lanish$"), handle_contact))
    application.add_handler(MessageHandler(
        filters.Regex("^❓ Yordam$"), handle_help))
    application.add_handler(MessageHandler(
        filters.Regex("^⚙️ Sozlamalar$"), handle_settings))
    application.add_handler(MessageHandler(
        filters.Regex("^📦 Buyurtmalarim$"), handle_my_orders))

    # Callbacks
    application.add_handler(CallbackQueryHandler(
        check_subscription_callback, pattern="^check_subscription$"))
    application.add_handler(CallbackQueryHandler(
        service_callback, pattern="^service_"))
    application.add_handler(CallbackQueryHandler(
        back_callback, pattern="^back_"))
    application.add_handler(CallbackQueryHandler(
        broadcast_confirm_callback, pattern="^broadcast_"))
    application.add_handler(CallbackQueryHandler(
        admin_action_callback, pattern="^admin_"))

    # Media handlers
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact_msg))
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))

    # Group events
    application.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_member))
    application.add_handler(MessageHandler(
        filters.StatusUpdate.LEFT_CHAT_MEMBER, handle_left_member))

    # Auto reply (eng oxirida!)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, auto_reply_handler))

    # Error handler
    application.add_error_handler(error_handler)

    # ✅ Botni ishga tushirish
    print("🤖 Bot Render serverda ishga tushmoqda...")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
