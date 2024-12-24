from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup
import schedule
import time
import threading
from datetime import datetime

# Данные бота
BOT_TOKEN = "7903049524:AAGAtPir0J3VsNtWud7yZKsKR5TVmbhh-Rs"
API_ID = 24375354
API_HASH = "bc3f6910f4ba395f0396e68287d3e99c"

# Идентификаторы пользователей
USER_IDS = {
    "vanya": 1026996176,  # ID Вани
    "olesya": 1083949994  # ID Олеси
}

# Дни рождения
BIRTHDAYS = {
    "vanya": datetime(2003, 4, 4),
    "olesya": datetime(2005, 7, 27)
}

# Напоминания для Нового года
NEW_YEAR = datetime(datetime.now().year, 12, 31)

# Хранилище желаний
wishlists = {
    "vanya": [],
    "olesya": []
}

# Состояние пользователей (для отслеживания действий)
user_states = {}

# Тексты кнопок, которые нельзя добавлять в желания
INVALID_WISH_TEXTS = [
    "🎁 Добавить желание",
    "💌 Смотреть вишлист Олеси",
    "💌 Смотреть вишлист Вани",
    "❌ Удалить желание",
    "🗑 Очистить вишлист",
    "ℹ️ Помощь"
]

# Создаем клиента для бота
app = Client(
    "wishlist_bot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH
)


# Команда /start
@app.on_message(filters.command("start"))
def start(client, message):
    user_id = message.from_user.id
    if user_id in USER_IDS.values():
        message.reply_text(
            "Привет! 👋 Выберите действие на панели ниже:\n\n"
            "Для помощи нажмите кнопку ℹ️ Помощь.",
            reply_markup=ReplyKeyboardMarkup(
                [
                    ["🎁 Добавить желание"],
                    ["💌 Смотреть вишлист Олеси", "💌 Смотреть вишлист Вани"],
                    ["❌ Удалить желание", "🗑 Очистить вишлист"],
                    ["ℹ️ Помощь"]
                ],
                resize_keyboard=True
            )
        )
    else:
        message.reply_text("Извините, этот бот доступен только для Вани и Олеси.")


# Команда /help
@app.on_message(filters.command("help"))
def help_command(client, message):
    send_help_message(message)


# Кнопка ℹ️ Помощь
@app.on_message(filters.text & filters.private & filters.regex(r"ℹ️ Помощь"))
def help_button(client, message):
    send_help_message(message)


def send_help_message(message):
    message.reply_text(
        "📜 Инструкция по использованию:\n\n"
        "1. 🎁 Добавить желание — добавляет новые желания в ваш вишлист.\n"
        "2. 💌 Смотреть вишлист Олеси/Вани — позволяет посмотреть вишлист другого пользователя.\n"
        "3. ❌ Удалить желание — удаляет одно или несколько желаний по их номерам.\n"
        "4. 🗑 Очистить вишлист — удаляет все желания из вашего списка.\n"
        "5. ℹ️ Помощь — показывает эту инструкцию.\n\n"
        "👉 Пример удаления нескольких желаний: 1 3 5\n"
        "👉 Если есть вопросы, обращайтесь!"
    )


# Обработка всех сообщений
@app.on_message(filters.text & filters.private)
def handle_message(client, message):
    user_id = message.from_user.id
    text = message.text.strip()

    # Проверка доступа
    if user_id not in USER_IDS.values():
        message.reply_text("У вас нет доступа к этому боту.")
        return

    # Проверяем, находится ли пользователь в каком-то состоянии
    if user_id in user_states:
        state = user_states[user_id]

        if state == "adding_wish":
            add_wish(client, user_id, message)
        elif state == "deleting_wish":
            delete_wish(client, user_id, message)
        return

    # Обработка кнопок
    if text == "🎁 Добавить желание":
        user_states[user_id] = "adding_wish"
        message.reply_text("Введите ваши желания (каждое с новой строки):")
    elif text == "💌 Смотреть вишлист Олеси":
        view_wishlist(message, "olesya")
    elif text == "💌 Смотреть вишлист Вани":
        view_wishlist(message, "vanya")
    elif text == "❌ Удалить желание":
        if not wishlists[get_user_key(user_id)]:
            message.reply_text("Ваш вишлист пуст. Нечего удалять.")
        else:
            user_states[user_id] = "deleting_wish"
            message.reply_text("Введите номера желаний для удаления (например, 1 3 5):")
    elif text == "🗑 Очистить вишлист":
        clear_wishlist(message, user_id)
    else:
        message.reply_text("Команда не распознана. Нажмите ℹ️ Помощь для получения инструкции.")


# Функция добавления желания
def add_wish(client, user_id, message):
    wishlist_key = get_user_key(user_id)

    # Разделяем текст на строки (каждое желание - новая строка)
    wishes = [wish.strip() for wish in message.text.splitlines() if wish.strip()]
    if not wishes:
        message.reply_text("Пожалуйста, введите хотя бы одно желание.")
        return

    # Проверяем, чтобы желания не содержали команд или повторяющиеся строки
    filtered_wishes = []
    for wish in wishes:
        if wish in INVALID_WISH_TEXTS or wish in filtered_wishes or wish in wishlists[wishlist_key]:
            continue
        filtered_wishes.append(wish)

    if not filtered_wishes:
        message.reply_text("Вы ввели дублирующиеся или некорректные желания. Попробуйте снова.")
        return

    wishlists[wishlist_key].extend(filtered_wishes)

    message.reply_text("🎉 Успешно добавлено:")
    message.reply_text("\n".join([f"{i+1}. {wish}" for i, wish in enumerate(filtered_wishes)]))

    # Уведомить партнёра
    partner_id = USER_IDS["olesya"] if wishlist_key == "vanya" else USER_IDS["vanya"]
    client.send_message(
        partner_id,
        f"🔔 Ваш партнёр добавил новые желания:\n" + "\n".join([f"- {wish}" for wish in filtered_wishes])
    )

    # Сброс состояния пользователя
    user_states.pop(user_id, None)


# Функция просмотра вишлиста
def view_wishlist(message, partner_key):
    wishlist = wishlists[partner_key]
    if wishlist:
        text = "\n".join([f"{i+1}. {item}" for i, item in enumerate(wishlist)])
    else:
        text = "Вишлист пока пуст."

    message.reply_text(f"🎁 Вишлист:\n\n{text}")


# Функция удаления желаний
def delete_wish(client, user_id, message):
    wishlist_key = get_user_key(user_id)
    numbers = message.text.split()

    try:
        indices = sorted([int(num) - 1 for num in numbers], reverse=True)
        deleted_items = []
        for index in indices:
            if 0 <= index < len(wishlists[wishlist_key]):
                deleted_items.append(wishlists[wishlist_key].pop(index))

        if deleted_items:
            message.reply_text(f"❌ Удалено:\n" + "\n".join([f"- {item}" for item in deleted_items]))
        else:
            message.reply_text("Некорректные номера. Попробуйте снова.")
    except ValueError:
        message.reply_text("Введите номера желаний через пробел (например, 1 2 3).")

    # Сброс состояния пользователя
    user_states.pop(user_id, None)


# Функция очистки вишлиста
def clear_wishlist(message, user_id):
    wishlist_key = get_user_key(user_id)
    if wishlists[wishlist_key]:
        wishlists[wishlist_key].clear()
        message.reply_text("🗑 Ваш вишлист успешно очищен!")
    else:
        message.reply_text("Ваш вишлист уже пуст.")


# Вспомогательная функция для определения ключа пользователя
def get_user_key(user_id):
    return "vanya" if user_id == USER_IDS["vanya"] else "olesya"


# Запуск бота
if __name__ == "__main__":
    app.run()
