import requests
from datetime import datetime
from telegram import (
    Update, ReplyKeyboardMarkup,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler, CallbackQueryHandler
)
from database import init_db, add_user, add_order, get_user_orders, add_reservation

# Стейти
(
    CHOOSING_PIZZA, CHOOSING_SIZE, CONFIRM_ORDER,
    ASKING_CITY, ASKING_CONVERT, ASKING_ZODIAC,
    RES_CITY, RES_TABLE, RES_PEOPLE, RES_TIME, RES_CONFIRM
) = range(11)

main_menu = [
    ["Замовити піцу", "Мої замовлення"],
    ["Каталог", "Бронювання"],
    ["Прогноз погоди", "Обмін валют"],
    ["Гороскоп", "Контакти", "Про нас"]
]

pizza_menu = [["Маргарита", "Пепероні"], ["Гавайська", "4 Сири"], ["Назад"]]
size_menu = [["Мала", "Середня", "Велика"], ["Назад"]]

# Каталог товарів
CATALOG = {
    "Маргарита": {"price": 150, "desc": "Класична піца з сиром та томатами."},
    "Пепероні": {"price": 170, "desc": "Гостра піца з салямі пепероні."},
    "Гавайська": {"price": 165, "desc": "Піца з ананасами та куркою."},
    "4 Сири": {"price": 180, "desc": "Сирна піца з моцарелою, дорблю, чеддером та пармезаном."},
}

ZODIAC_SIGNS = {
    "Овен": "aries", "Телець": "taurus", "Близнюки": "gemini",
    "Рак": "cancer", "Лев": "leo", "Діва": "virgo",
    "Терези": "libra", "Скорпіон": "scorpio", "Стрілець": "sagittarius",
    "Козеріг": "capricorn", "Водолій": "aquarius", "Риби": "pisces"
}

# /start

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username, user.first_name)
    await update.message.reply_text(
        f"👋 Привіт, {user.first_name}!\n"
        f"Я — *PizzaBot*, твій цифровий асистент піцерії.\n"
        f"Усі команди можете дізнатися /help або оберіть дію нижче:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
    )

# /help

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📘 *Доступні команди:*\n"
        "/start — перезапустити бота\n"
        "/help — список команд\n"
        "/today — гороскоп на сьогодні\n"
        "/catalog — каталог товарів\n"
        "/reserve — бронювання столика\n"
        "/weather — прогноз погоди\n"
        "/convert — обмін валют\n",
        parse_mode="Markdown"
    )


# /catalog — inline кнопки

async def catalog_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for item in CATALOG:
        keyboard.append([InlineKeyboardButton(item, callback_data=f"cat_{item}")])

    await update.message.reply_text(
        "📦 *Каталог товарів:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def catalog_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    item = query.data.replace("cat_", "")
    data = CATALOG.get(item)
    if not data:
        await query.edit_message_text("Товар не знайдено.")
        return

    text = (
        f"🍕 *{item}*\n"
        f"💰 Ціна: {data['price']} грн\n"
        f"ℹ️ Опис: {data['desc']}"
    )

    await query.edit_message_text(text, parse_mode="Markdown")


# Повернення з меню

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "Замовити піцу":
        await update.message.reply_text("Обери піцу:", reply_markup=ReplyKeyboardMarkup(pizza_menu, resize_keyboard=True))
        return CHOOSING_PIZZA

    elif text == "Каталог":
        await catalog_command(update, context)
        return ConversationHandler.END

    elif text == "Бронювання":
        return await reserve_start(update, context)

    elif text == "Мої замовлення":
        await show_order_history(update, context)
        return ConversationHandler.END

    elif text == "Прогноз погоди":
        return await start_weather(update, context)

    elif text == "Обмін валют":
        return await start_convert(update, context)

    elif text == "Гороскоп":
        return await choose_zodiac(update, context)

    elif text == "Контакти":
        await update.message.reply_text("вул. Смачна, 10\n +380 99 999 9999")
        return ConversationHandler.END

    elif text == "Про нас":
        await update.message.reply_text("Ми доставляємо найсмачнішу піцу у місті!")
        return ConversationHandler.END

    else:
        return ConversationHandler.END


# Показ історії замовлень

async def show_order_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    orders = get_user_orders(user.id)

    if not orders:
        await update.message.reply_text("У вас ще немає замовлень.",
                                        reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))
        return

    text = "*Ваші замовлення:*\n\n"
    for o in orders:
        text += f" #{o[0]} |  {o[1]} ({o[2]}) — Статус: {o[3]}\n"

    await update.message.reply_text(text, parse_mode="Markdown",
                                    reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))


# Замовлення піци

async def choose_pizza(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pizza = update.message.text
    if pizza == "Назад":
        await update.message.reply_text("Меню:", reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))
        return ConversationHandler.END

    context.user_data["pizza"] = pizza
    await update.message.reply_text("Обери розмір:", reply_markup=ReplyKeyboardMarkup(size_menu, resize_keyboard=True))
    return CHOOSING_SIZE

async def choose_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    size = update.message.text
    if size == "Назад":
        await update.message.reply_text("Обери піцу:", reply_markup=ReplyKeyboardMarkup(pizza_menu, resize_keyboard=True))
        return CHOOSING_PIZZA

    context.user_data["size"] = size
    pizza = context.user_data["pizza"]

    await update.message.reply_text(
        f"Замовити '{pizza}', розмір — {size}?",
        reply_markup=ReplyKeyboardMarkup([["Так", "Ні"]], resize_keyboard=True)
    )
    return CONFIRM_ORDER

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    user = update.effective_user

    if choice == "Так":
        add_order(user.id, context.user_data["pizza"], context.user_data["size"])
        await update.message.reply_text("Замовлення прийнято!", reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))
    else:
        await update.message.reply_text("Скасовано.", reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))

    return ConversationHandler.END


# Погода — роздільні стартові функції

async def start_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # надсилаємо запит на введення міста та повертаємо стан ASKING_CITY
    await update.message.reply_text("Введіть місто:", reply_markup=ReplyKeyboardMarkup([["Назад"]], resize_keyboard=True))
    return ASKING_CITY

async def get_weather_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text.strip()
    if city == "Назад":
        await update.message.reply_text("Меню:", reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))
        return ConversationHandler.END

    API_KEY = "42af3687b2d5c1f8f5ef7e16a8b4908c"
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&units=metric&lang=uk&appid={API_KEY}"

    try:
        resp = requests.get(url)
        data = resp.json()
        if resp.status_code != 200 or "city" not in data:
            raise Exception("Неправильна назва міста або помилка API")

        city_name = data["city"]["name"]

        forecast = {}
        for item in data["list"]:
            date_str = item["dt_txt"].split()[0]
            forecast.setdefault(date_str, {"temp": [], "wind": [], "desc": []})
            forecast[date_str]["temp"].append(item["main"]["temp"])
            forecast[date_str]["wind"].append(item["wind"]["speed"])
            forecast[date_str]["desc"].append(item["weather"][0]["description"].capitalize())

        days = list(forecast.keys())[:5]
        text = f"Прогноз погоди в {city_name}:\n\n"
        for d in days:
            avg_temp = sum(forecast[d]["temp"]) / len(forecast[d]["temp"])
            avg_wind = sum(forecast[d]["wind"]) / len(forecast[d]["wind"])
            desc = max(set(forecast[d]["desc"]), key=forecast[d]["desc"].count)
            date_fmt = datetime.strptime(d, "%Y-%m-%d").strftime("%d.%m")
            text += f"{date_fmt}: {desc}, {avg_temp:.1f}°C, вітер {avg_wind:.1f} м/с\n"

        await update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))

    except Exception:
        await update.message.reply_text("Помилка отримання прогнозу. Перевірте назву міста.", reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))

    return ConversationHandler.END


# Валюти — старт і обробка

async def start_convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Введіть суму та валюти у форматі: `100 USD в EUR`",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([["Назад"]], resize_keyboard=True)
    )
    return ASKING_CONVERT

async def currency_convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "Назад":
        await update.message.reply_text("Меню:", reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))
        return ConversationHandler.END

    try:
        parts = text.upper().replace("В", "IN").split()
        if len(parts) != 4 or not parts[0].replace('.', '', 1).isdigit():
            raise ValueError("format")
        amount = float(parts[0])
        from_curr = parts[1]
        to_curr = parts[3]

        API_KEY = "01b93b09b4959a96b9585523ee9573b1"
        url = f"https://api.currencylayer.com/live?access_key={API_KEY}&currencies={to_curr}&source={from_curr}"

        resp = requests.get(url).json()
        if not resp.get("success", True):
            raise Exception("Помилка API валют")
        rate = resp["quotes"][f"{from_curr}{to_curr}"]
        converted = rate * amount

        await update.message.reply_text(
            f"💱 {amount:.2f} {from_curr} = {converted:.2f} {to_curr}\nКурс: 1 {from_curr} = {rate:.4f} {to_curr}",
            reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
        )

    except ValueError:
        await update.message.reply_text("Введіть у форматі: 100 USD в EUR", reply_markup=ReplyKeyboardMarkup([["Назад"]], resize_keyboard=True))
    except Exception:
        await update.message.reply_text("Помилка при конвертації. Перевірте введені валюти.", reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))

    return ConversationHandler.END


# Гороскоп

async def choose_zodiac(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [list(ZODIAC_SIGNS.keys())[i:i + 3] for i in range(0, 12, 3)]
    keyboard.append(["Назад"])

    await update.message.reply_text(
        "Оберіть знак зодіаку:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return ASKING_ZODIAC

async def get_horoscope(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sign_name = update.message.text
    if sign_name == "Назад":
        await update.message.reply_text("Меню.", reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))
        return ConversationHandler.END

    if sign_name not in ZODIAC_SIGNS:
        await update.message.reply_text("Невірно. Спробуйте ще.")
        return ASKING_ZODIAC

    sign = ZODIAC_SIGNS[sign_name]
    context.user_data["zodiac"] = sign_name

    API_KEY = "fvy0NmxiJxdVSuhSlUKMsg==HzdsT9AI9kaoZtmk"
    url = f"https://api.api-ninjas.com/v1/horoscope?zodiac={sign}"

    try:
        resp = requests.get(url, headers={"X-Api-Key": API_KEY})
        if resp.status_code != 200:
            raise Exception("API error")
        data = resp.json()
        text = f"Гороскоп для *{sign_name}*:\n\n{data.get('horoscope','')}"
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))

    except Exception:
        await update.message.reply_text("Помилка гороскопу.", reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))

    return ConversationHandler.END


# /today

async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    last_sign = context.user_data.get("zodiac")
    if not last_sign:
        return await choose_zodiac(update, context)

    # передамо знак як якщо б користувач надіслав текст
    update.message.text = last_sign
    return await get_horoscope(update, context)


# Бронювання столика

async def reserve_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "У якому місті бронюємо?",
        reply_markup=ReplyKeyboardMarkup([["Назад"]], resize_keyboard=True)
    )
    return RES_CITY

async def reserve_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text
    if city == "Назад":
        await update.message.reply_text("Меню.", reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))
        return ConversationHandler.END

    context.user_data["res_city"] = city
    await update.message.reply_text("Введіть номер столика (1–20):")
    return RES_TABLE

async def reserve_table(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit():
        await update.message.reply_text("Введіть число.")
        return RES_TABLE

    table = int(update.message.text)
    context.user_data["res_table"] = table

    await update.message.reply_text("На скільки людей?")
    return RES_PEOPLE

async def reserve_people(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit():
        await update.message.reply_text("Числом, будь ласка.")
        return RES_PEOPLE

    people = int(update.message.text)
    context.user_data["res_people"] = people

    await update.message.reply_text("На яку годину? (наприклад 19:00)")
    return RES_TIME

async def reserve_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    time = update.message.text
    context.user_data["res_time"] = time

    city = context.user_data["res_city"]
    table = context.user_data["res_table"]
    people = context.user_data["res_people"]

    await update.message.reply_text(
        f"Підтверджуєте бронювання?\n\n"
        f"Місто: {city}\n"
        f"Стіл: {table}\n"
        f"Людей: {people}\n"
        f"Час: {time}",
        reply_markup=ReplyKeyboardMarkup([["Так", "Ні"]], resize_keyboard=True)
    )
    return RES_CONFIRM

async def reserve_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    user = update.effective_user

    if choice == "Так":
        add_reservation(
            user.id,
            context.user_data["res_city"],
            context.user_data["res_table"],
            context.user_data["res_people"],
            context.user_data["res_time"]
        )
        await update.message.reply_text("Столик заброньовано!", reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))
    else:
        await update.message.reply_text("Бронювання скасовано.", reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True))

    return ConversationHandler.END


# MAIN

def main():
    init_db()
    TOKEN = "8578959960:AAENh7GmeGyX0RijoJlCkn9TZi45ZAxz9bY"

    app = Application.builder().token(TOKEN).build()

    # --- Handlers ---

    # Бронювання
    conv_reserve = ConversationHandler(
        entry_points=[CommandHandler("reserve", reserve_start),
                      MessageHandler(filters.Regex("^Бронювання$"), reserve_start)],
        states={
            RES_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, reserve_city)],
            RES_TABLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reserve_table)],
            RES_PEOPLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reserve_people)],
            RES_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reserve_time)],
            RES_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, reserve_confirm)],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )

    # Замовлення піци
    conv_order = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Замовити піцу$"), main_menu_handler)],
        states={
            CHOOSING_PIZZA: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_pizza)],
            CHOOSING_SIZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_size)],
            CONFIRM_ORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_order)],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )

    # Погода
    conv_weather = ConversationHandler(
        entry_points=[CommandHandler("weather", start_weather),
                      MessageHandler(filters.Regex("^Прогноз погоди$"), main_menu_handler)],
        states={ASKING_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_weather_forecast)]},
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )

    # Валюта
    conv_currency = ConversationHandler(
        entry_points=[CommandHandler("convert", start_convert),
                      MessageHandler(filters.Regex("^Обмін валют$"), main_menu_handler)],
        states={ASKING_CONVERT: [MessageHandler(filters.TEXT & ~filters.COMMAND, currency_convert)]},
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )

    # Гороскоп
    conv_horoscope = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Гороскоп$"), main_menu_handler)],
        states={ASKING_ZODIAC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_horoscope)]},
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )

    # Реєстрація хендлерів
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("today", today_command))
    app.add_handler(CommandHandler("catalog", catalog_command))
    app.add_handler(CallbackQueryHandler(catalog_callback))

    app.add_handler(conv_order)
    app.add_handler(conv_weather)
    app.add_handler(conv_currency)
    app.add_handler(conv_horoscope)
    app.add_handler(conv_reserve)

    # Замість широкого catch-all — тільки кнопки головного меню,
    # щоб не перехоплювати повідомлення, які мають обробляти ConversationHandler
    main_menu_regex = "^(" + "|".join([
        "Замовити піцу", "Мої замовлення", "Каталог", "Бронювання",
        "Прогноз погоди", "Обмін валют", "Гороскоп", "Контакти", "Про нас"
    ]) + ")$"
    app.add_handler(MessageHandler(filters.Regex(main_menu_regex), main_menu_handler))

    print("Бот запущено.")
    app.run_polling()

if __name__ == "__main__":
    main()
