import os
import psycopg2
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters


ROLE, SALES_TEAM, REQUESTS, CONTACT_INFO, PHONE, EMAIL, END_CONV = range(7)


DATABASE_URL = os.getenv("DATABASE_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")
KOYEB_APP_NAME = os.getenv("KOYEB_APP_NAME")

if not KOYEB_APP_NAME:
    raise ValueError("Переменная окружения KOYEB_APP_NAME не установлена. Убедитесь, что она задана на Koyeb.")

from psycopg2 import pool

db_pool = None

def initialize_database():
    global db_pool
    try:
        db_pool = psycopg2.pool.SimpleConnectionPool(
            1, 20, DATABASE_URL  # Минимум 1, максимум 20 соединений
        )
        conn = db_pool.getconn()
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id SERIAL PRIMARY KEY,
            role TEXT,
            sales_team TEXT,
            requests TEXT,
            name TEXT,
            phone TEXT,
            email TEXT
        );
        """)
        conn.commit()
        cursor.close()
        db_pool.putconn(conn)
    except Exception as e:
        print(f"Ошибка инициализации базы данных: {e}")
        exit(1)


# def initialize_database():
#     try:
#         conn = psycopg2.connect(DATABASE_URL)
#         cursor = conn.cursor()
#         cursor.execute("""
#         CREATE TABLE IF NOT EXISTS applications (
#             id SERIAL PRIMARY KEY,
#             role TEXT,
#             sales_team TEXT,
#             requests TEXT,
#             name TEXT,
#             phone TEXT,
#             email TEXT
#         );
#         """)
#         conn.commit()
#         cursor.close()
#         conn.close()
#     except Exception as e:
#         print(f"Ошибка инициализации базы данных: {e}")
#         exit(1)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Здравствуйте!\n\n"
        "Я - Евгений Шевченко, а это мой бот-ассистент. Я специализируюсь на создании сильных отделов продаж для Вашего бизнеса.\n"
        "А Вы, я так полагаю, тот самый собственник или руководитель, заинтересованный в росте Вашего бизнеса. Что ж, до нашей личной встречи, осталось совсем немного.\n\n"
        "Нажмите на кнопку «Участвовать», чтобы записаться на БЕСПЛАТНУЮ СЕССИЮ со мной.\n\n"
        "👇👇👇",
        reply_markup=ReplyKeyboardMarkup([["Участвовать"]], one_time_keyboard=True),
    )
    return ROLE

async def ask_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Прежде, чем мы встретимся, расскажите немного о себе!\n\n"
        "Какая Ваша роль в компании?",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["Собственник бизнеса", "Руководитель / ТОП менеджер"],
                ["Бизнес тренер /HR", "Иной сотрудник"],
            ],
            one_time_keyboard=True,
        ),
    )
    return SALES_TEAM

async def ask_sales_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["role"] = update.message.text
    await update.message.reply_text(
        "Сколько сотрудников работает в Вашем отделе продаж?",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["0 – 5 сотрудников", "5 – 10 сотрудников"],
                ["10 – 25 сотрудников", "25 – 50 сотрудников"],
                ["более 50 сотрудников"],
            ],
            one_time_keyboard=True,
        ),
    )
    return REQUESTS

async def ask_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["sales_team"] = update.message.text
    await update.message.reply_text(
        "Какие задачи / запросы для Вас сейчас максимально актуальны?",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["Хочу понять, как должен работать Отдел Продаж."],
                ["Запрос в создании отдела с нуля. Нужен РОП."],
                ["Запрос в создании системы продаж. Сейчас все работает хаотично."],
                ["Запрос в найме РОПа. Нужен сильный РОП для текущего отдела продаж."],
                ["Запрос в найме команды. Нужны сильные Продавцы."],
                ["Запрос в обучении. Нужно обучение продажам."],
                ["Другое"],
            ],
            one_time_keyboard=True,
        ),
    )
    return CONTACT_INFO

async def get_contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['requests'] = update.message.text
    await update.message.reply_text("Спасибо за Ваши ответы. Оставьте свои контактные данные.\n\n Ваше имя:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Укажите свой номер, зарегистрированный в WhatsApp или Telegram")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("Укажите свой e-mail")
    return END_CONV

async def end_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['email'] = update.message.text

    try:
        # Открываем новое подключение для записи данных
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO applications (role, sales_team, requests, name, phone, email) VALUES (%s, %s, %s, %s, %s, %s)",
            (
                context.user_data["role"],
                context.user_data["sales_team"],
                context.user_data["requests"],
                context.user_data["name"],
                context.user_data["phone"],
                context.user_data["email"],
            ),
        )
        conn.commit()
        cursor.close()
        conn.close()

        await update.message.reply_text(
            "Спасибо за заявку! В самое ближайшее время я свяжусь с Вами для согласования времени проведения Сессии. До скорой встречи!"
        )
    except Exception as e:
        print(f"Ошибка при сохранении данных: {e}")
        await update.message.reply_text("Произошла ошибка при сохранении данных. Пожалуйста, попробуйте ещё раз.")
    return ConversationHandler.END


def main():
    initialize_database()
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_role)],
            SALES_TEAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_sales_team)],
            REQUESTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_requests)],
            CONTACT_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact_info)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            END_CONV: [MessageHandler(filters.TEXT & ~filters.COMMAND, end_conv)],
        },
        fallbacks=[],
    )

    application.add_handler(conv_handler)

    PORT = int(os.environ.get("PORT", 8000))
    print(PORT, KOYEB_APP_NAME)
 
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url = f"http://{KOYEB_APP_NAME}.koyeb.app/{BOT_TOKEN}",
    )
    # application.run_polling()

if __name__ == "__main__":
    main()
