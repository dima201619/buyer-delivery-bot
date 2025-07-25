import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
DATA_FILE = os.getenv("DATA_FILE", "catalog.json")

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

def load_catalog():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_catalog(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class AddProduct(StatesGroup):
    category = State()
    name = State()
    description = State()
    price = State()
    size = State()

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    catalog = load_catalog()
    kb = InlineKeyboardMarkup(row_width=2)
    for cat in catalog:
        kb.add(InlineKeyboardButton(text=cat, callback_data=f"cat_{cat}"))
    await message.answer(
        "👋 Ласкаво просимо до Buyer Delivery!\n\n"
        "🛍 Оберіть категорію товарів для перегляду:",
        reply_markup=kb
    )

@dp.callback_query_handler(lambda c: c.data.startswith("cat_"))
async def show_category(callback: types.CallbackQuery):
    catalog = load_catalog()
    cat = callback.data.replace("cat_", "")
    items = catalog.get(cat, [])
    if not items:
        await callback.message.answer("❗️ Товарів у цій категорії немає.")
        return
    for item in items:
        text = (
            f"<b>{item['name']}</b>\n"
            f"💰 {item['price']} грн\n"
            f"📏 {item['size']}\n"
            f"📝 {item['description']}"
        )
        await callback.message.answer(text)

@dp.message_handler(commands=["add"])
async def add_item(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("⛔️ Вибач, але ти не маєш доступу до додавання товарів.")
        return
    await message.answer("🗂 Введіть категорію товару:")
    await AddProduct.category.set()

@dp.message_handler(state=AddProduct.category)
async def set_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer("✏️ Введіть назву товару:")
    await AddProduct.next()

@dp.message_handler(state=AddProduct.name)
async def set_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📝 Введіть опис товару:")
    await AddProduct.next()

@dp.message_handler(state=AddProduct.description)
async def set_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("💰 Введіть ціну товару (наприклад: 499):")
    await AddProduct.next()

@dp.message_handler(state=AddProduct.price)
async def set_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("📏 Введіть розмір товару:")
    await AddProduct.next()

@dp.message_handler(state=AddProduct.size)
async def set_size(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    catalog = load_catalog()
    cat = user_data["category"]
    item = {
        "name": user_data["name"],
        "description": user_data["description"],
        "price": user_data["price"],
        "size": message.text
    }
    catalog.setdefault(cat, []).append(item)
    save_catalog(catalog)
    await message.answer("✅ Товар додано!")
    await state.finish()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
