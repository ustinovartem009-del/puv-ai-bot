import logging
import asyncio
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = "8203109703:AAFZJUv9vYIv19F1qQAZoBKxCuBswWyvc3c"
DEEPSEEK_API_KEY = "sk-1bc290e93b3145d7932f1b1925c609c2"

session = None

async def get_session():
    global session
    if session is None:
        session = aiohttp.ClientSession()
    return session

async def close_session():
    global session
    if session:
        await session.close()
        session = None

async def ask_deepseek(question):
    try:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system", 
                    "content": "Ты профессиональный ветеринарный ассистент PetVel AI. Отвечай на русском языке. Консультируй по здоровью животных, давай рекомендации по питанию, уходу и лечению. Всегда уточняй, что при серьезных симптомах нужно срочно обращаться к ветеринару. Будь точным, профессиональным, но при этом дружелюбным. Если вопрос не связан с животными, вежливо сообщи об этом."
                },
                {
                    "role": "user", 
                    "content": question
                }
            ],
            "max_tokens": 1500,
            "temperature": 0.7,
            "stream": False
        }
        
        current_session = await get_session()
        
        async with current_session.post(url, headers=headers, json=data, timeout=30) as response:
            if response.status == 200:
                result = await response.json()
                return result['choices'][0]['message']['content']
            else:
                error_text = await response.text()
                logger.error(f"DeepSeek API error: {response.status} - {error_text}")
                return "Извините, возникла проблема с обработкой вашего запроса. Пожалуйста, попробуйте позже."
                
    except asyncio.TimeoutError:
        logger.error("DeepSeek API timeout")
        return "Время ожидания ответа истекло. Пожалуйста, попробуйте еще раз."
    except Exception as e:
        logger.error(f"DeepSeek connection error: {str(e)}")
        return f"Ошибка соединения: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
🐾 Добро пожаловать в PetVel AI! 

Я ваш AI-ветеринар на базе DeepSeek.

🤖 Просто опишите проблему питомца:

Примеры:
• "У собаки рвота 2 дня"
• "Котенок не ест, вялый" 
• "Чем кормить кошку 1 год"
• "Поведение собаки изменилось"

⚠️ Важно: 
• При серьезных симптомах срочно обращайтесь к ветеринару!
• Я не заменяю очный осмотр специалиста
• В экстренных случаях звоните в ветклинику

Для начала просто напишите ваш вопрос о здоровье питомца!
"""
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📖 Доступные команды:

/start - Начать работу с ботом
/help - Получить справку
/info - О боте

💡 Как пользоваться:
Просто напишите вопрос о вашем питомце, и я постараюсь помочь!

🐕 Примеры вопросов:
• "Собака чешется, что делать?"
• "Кот не пьет воду"
• "Щенок вялый после прививки"
• "Чем можно кормить кошку?"

⚠️ Помните: При острых состояниях немедленно обращайтесь к ветеринару!
"""
    await update.message.reply_text(help_text)

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info_text = """
🤖 PetVel AI Bot

Версия: 1.0
Платформа: DeepSeek AI
Назначение: Ветеринарный помощник

Возможности:
• Консультации по здоровью животных
• Рекомендации по питанию и уходу
• Советы по поведению питомцев
• Первая помощь при неотложных состояниях

🔒 Конфиденциальность: Ваши вопросы обрабатываются безопасно.
"""
    await update.message.reply_text(info_text)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.effective_user.id
    
    if user_message.startswith('/'):
        return
    
    logger.info(f"User {user_id} asked: {user_message}")
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        ai_response = await ask_deepseek(user_message)
        response_text = f"🐾 PetVel AI отвечает:\n\n{ai_response}"
        await update.message.reply_text(response_text)
        
    except Exception as e:
        logger.error(f"Error handling message from user {user_id}: {str(e)}")
        error_text = "Произошла непредвиденная ошибка. Пожалуйста, попробуйте еще раз позже."
        await update.message.reply_text(error_text)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.message:
        try:
            await update.message.reply_text("Произошла непредвиденная ошибка. Мы уже работаем над её устранением.")
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")

def main():
    try:
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("info", info_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        
        application.add_error_handler(error_handler)

        print("✅ PetVel AI бот запущен!")
        print("🚀 DeepSeek API подключен")
        print("📱 Бот готов к приему сообщений...")
        print("⚡ Для остановки нажмите Ctrl+C")

        application.run_polling()

    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    finally:
        asyncio.run(close_session())

if __name__ == "__main__":
    main()
