import os
import aiohttp
import asyncio
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

TELEGRAM_TOKEN = "8203109703:AAFZJUv9vYIv19F1qQAZoBKxCuBswWyvc3c"
OPENROUTER_API_KEY = "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"

async def get_ai_response(user_message):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}"
    }
    data = {
        "model": "google/gemini-pro:free", 
        "messages": [{"role": "user", "content": user_message}],
        "stream": False
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content']
                else:
                    return "Бот думает над ответом... Попробуйте еще раз"
    except Exception as e:
        return "Привет! Я PUV AI - помощник для владельцев питомцев 🐾"

def handle_message(update: Update, context: CallbackContext):
    user_message = update.message.text
    
    async def send_response():
        response = await get_ai_response(user_message)
        await update.message.reply_text(f"🐾 PUV AI:\n\n{response}")
    
    asyncio.run(send_response())

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    print("✅ PUV AI бот запущен!")
    print("🤖 Бот готов к работе...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
