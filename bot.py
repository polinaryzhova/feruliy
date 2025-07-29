import logging
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

logging.basicConfig(level=logging.INFO)

participants = {}

class Form(StatesGroup):
    nickname = State()
    characters = State()
    style = State()
    anon_chat = State()

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME}")
    )
    await message.answer(
        "Привет! Для участия нужно подписаться на канал организатора✨",
        reply_markup=kb
    )
    await message.answer("Напиши любое сообщение после подписки, чтобы продолжить.")

@dp.message_handler(lambda message: True, state='*')
async def check_subscription(message: types.Message):
    user = await bot.get_chat_member(f"@{CHANNEL_USERNAME}", message.from_user.id)
    if user.status in ['member', 'creator', 'administrator']:
        await message.answer(
            "Спасибо за подписку! Теперь, чтобы принять участие, нужно заполнить анкету

"
            "1) Укажи свой ник в социальных сетя🙌🏻"
        )
        await Form.nickname.set()
    else:
        await message.answer("Пожалуйста, сначала подпишись на канал!")

@dp.message_handler(state=Form.nickname)
async def process_nickname(message: types.Message, state: FSMContext):
    await state.update_data(nickname=message.text)
    await message.answer("2) Расскажи о своих любимых персонажах или поставь прочерк, если это не имеет значения!")
    await Form.characters.set()

@dp.message_handler(state=Form.characters)
async def process_characters(message: types.Message, state: FSMContext):
    await state.update_data(characters=message.text)
    await message.answer("3) Как ты считаешь, в чём главная изюминка твоего стиля?🎨")
    await Form.style.set()

@dp.message_handler(state=Form.style)
async def process_style(message: types.Message, state: FSMContext):
    await state.update_data(style=message.text)
    await message.answer("4) Отправь ссылку на свой анонимный чат (ее можно получить в этом боте: https://t.me/voprosy)")
    await Form.anon_chat.set()

@dp.message_handler(state=Form.anon_chat)
async def process_anon_chat(message: types.Message, state: FSMContext):
    await state.update_data(anon_chat=message.text)
    data = await state.get_data()
    participants[message.from_user.id] = data

    await message.answer("Спасибо! Ты добавлен в список участников 🎉")
    await state.finish()

@dp.message_handler(commands=['draw'])
async def draw_handler(message: types.Message):
    if message.from_user.username != ADMIN_USERNAME:
        await message.reply("Только админ может запускать жеребьёвку.")
        return

    users = list(participants.items())
    if len(users) < 2:
        await message.reply("Недостаточно участников для жеребьёвки.")
        return

    shuffled = users[:]
    import random
    random.shuffle(shuffled)

    for (uid, data), (_, receiver_data) in zip(users, shuffled[1:] + shuffled[:1]):
        text = (
            f"Твой участник:

"
            f"Ник: {receiver_data['nickname']}
"
            f"Персонажи: {receiver_data['characters']}
"
            f"Изюминка: {receiver_data['style']}
"
            f"Анонимный чат: {receiver_data['anon_chat']}"
        )
        try:
            await bot.send_message(uid, text)
        except:
            continue

    await message.reply("Жеребьёвка проведена!")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
