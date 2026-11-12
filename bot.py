
import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from google import genai

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
API_KEY = os.environ["GEMINI_API_KEY"]

ai = genai.Client(api_key=API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أهلاً بك في مساعد كيريو 🤖\n"
        "ابعت صورة السؤال أو اكتبه، وهساعدك تفهم الحل خطوة بخطوة."
    )

async def solve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ جاري فهم السؤال...")

    try:
        message = update.message

        if message.photo:
            photo = await message.photo[-1].get_file()
            image_bytes = await photo.download_as_bytearray()

            response = ai.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    "حلل سؤال كيريو الظاهر في الصورة واشرح الحل بالعربية خطوة بخطوة. لا تخمن إذا كانت الصورة غير واضحة.",
                    {"mime_type": "image/jpeg", "data": bytes(image_bytes)}
                ]
            )
        else:
            response = ai.models.generate_content(
                model="gemini-2.5-flash",
                contents="اشرح السؤال التالي وساعد الطالب في حله خطوة بخطوة بالعربية:\n" + message.text
            )

        answer = response.text or "لم أتمكن من استخراج إجابة."
        for i in range(0, len(answer), 4000):
            await message.reply_text(answer[i:i+4000])

    except Exception as e:
        logging.exception("Error while solving")
        await message.reply_text("حصل خطأ أثناء الحل. حاول مرة أخرى.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, solve))
    app.run_polling()

if __name__ == "__main__":
    main()
