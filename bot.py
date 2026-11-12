
import os
import logging
from io import BytesIO
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from google import genai

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
API_KEY = os.environ["GEMINI_API_KEY"]
PORT = int(os.environ.get("PORT", "10000"))
URL = os.environ["RENDER_EXTERNAL_URL"]

ai = genai.Client(api_key=API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أهلاً بك في مساعد كيريو 🤖\n"
        "أرسل صورة السؤال أو اكتبه وسأساعدك في فهم الحل."
    )

async def solve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    status = await msg.reply_text("⏳ جاري تحليل السؤال...")

    try:
        if msg.photo:
            photo = await msg.photo[-1].get_file()
            image_bytes = await photo.download_as_bytearray()

            content = [
                "حل سؤال كيريو واشرح الحل بالعربية خطوة بخطوة. "
                "إذا كانت الصورة غير واضحة اطلب صورة أوضح.",
                {
                    "mime_type": "image/jpeg",
                    "data": bytes(image_bytes)
                }
            ]
        else:
            content = (
                "ساعد الطالب في فهم وحل السؤال التالي بالعربية "
                "مع شرح الخطوات:\n" + msg.text
            )

        response = ai.models.generate_content(
            model="gemini-2.5-flash",
            contents=content
        )

        answer = response.text or "لم أتمكن من استخراج إجابة."
        for i in range(0, len(answer), 4000):
            await msg.reply_text(answer[i:i+4000])

        await status.delete()

    except Exception:
        logging.exception("Solve error")
        await status.edit_text("حصل خطأ، حاول مرة أخرى.")

async def post_init(app):
    await app.bot.set_webhook(
        url=f"{URL}/{TOKEN}",
        allowed_updates=Update.ALL_TYPES
    )

def main():
    app = (
        Application.builder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(
            filters.PHOTO | (filters.TEXT & ~filters.COMMAND),
            solve
        )
    )

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{URL}/{TOKEN}",
        secret_token=TOKEN[:40],
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == "__main__":
    main()
