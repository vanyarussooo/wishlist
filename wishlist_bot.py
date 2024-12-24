from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import logging

logging.basicConfig(level=logging.INFO)

API_TOKEN = 'Ваш_ТОКЕН_ЗДЕСЬ'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# IDs пользователей
USERS = {
    "vanya": 1026996176,  # ID Вани
    "olesya": 1083949994  # ID Олеси
}

# Состояния и вишлисты
states = {}
wishlists = {
    USERS["vanya"]: [],
    USERS["olesya"]: []
}

# Клавиатура
main_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add(
    KeyboardButton("🎁 Добавить желание"),
    KeyboardButton("📄 Смотреть вишлист Олеси"),
    KeyboardButton("📄 Смотреть вишлист Вани"),
    KeyboardButton("🗑 Очистить вишлист")
)

# Хэндлер старт/команды
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    if message.from_user.id not in USERS.values():
        await message.reply("Извините, этот бот доступен только для Олеси и Вани.")
        return

    states[message.from_user.id] = None
    await message.reply("Привет! 👋 Выберите действие:", reply_markup=main_kb)

# Хэндлер добавления желания
@dp.message_handler(lambda message: message.text == "🎁 Добавить желание")
async def add_wishlist(message: types.Message):
    if message.from_user.id not in USERS.values():
        return

    states[message.from_user.id] = "adding_wish"
    await message.reply("Введите ваши желания (каждое желание с новой строки):")

@dp.message_handler(lambda message: states.get(message.from_user.id) == "adding_wish")
async def process_wishlist(message: types.Message):
    if message.from_user.id not in USERS.values():
        return

    wishes = message.text.split("\n")
    if any(wish.strip() == "" for wish in wishes):
        await message.reply("Вы ввели некорректные желания. Попробуйте снова.")
        return

    wishlists[message.from_user.id].extend(wishes)
    states[message.from_user.id] = None  # Сбрасываем состояние
    await message.reply("Ваши желания успешно добавлены! 🎉")

# Хэндлер очистки вишлиста
@dp.message_handler(lambda message: message.text == "🗑 Очистить вишлист")
async def clear_wishlist(message: types.Message):
    if message.from_user.id not in USERS.values():
        return

    wishlists[message.from_user.id] = []
    states[message.from_user.id] = None  # Сбрасываем состояние
    await message.reply("Ваш вишлист успешно очищен! 🗑")

# Хэндлеры просмотра вишлистов
@dp.message_handler(lambda message: message.text == "📄 Смотреть вишлист Олеси")
async def show_olesya_wishlist(message: types.Message):
    if message.from_user.id not in USERS.values():
        return

    wishlist = wishlists[USERS["olesya"]]
    response = "🎁 Вишлист Олеси:\n" + "\n".join(
        f"{i + 1}. {item}" for i, item in enumerate(wishlist)
    ) if wishlist else "Вишлист пока пуст."
    states[message.from_user.id] = None  # Сбрасываем состояние
    await message.reply(response)

@dp.message_handler(lambda message: message.text == "📄 Смотреть вишлист Вани")
async def show_vanya_wishlist(message: types.Message):
    if message.from_user.id not in USERS.values():
        return

    wishlist = wishlists[USERS["vanya"]]
    response = "🎁 Вишлист Вани:\n" + "\n".join(
        f"{i + 1}. {item}" for i, item in enumerate(wishlist)
    ) if wishlist else "Вишлист пока пуст."
    states[message.from_user.id] = None  # Сбрасываем состояние
    await message.reply(response)

# Хэндлер всех остальных сообщений
@dp.message_handler()
async def fallback_handler(message: types.Message):
    if message.from_user.id not in USERS.values():
        return

    await message.reply("Я не понимаю эту команду. Пожалуйста, выберите действие из меню.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
