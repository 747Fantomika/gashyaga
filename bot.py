import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command

from config import BOT_TOKEN, ADMIN_ID

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

SERVICES = {
    "Снежная":            (3199, 2699, 1599),
    "Нод Край":           (4999, 4199, 2899),
    "Луна":               (2399, 1999, 1399),
    "Натлан":             (4999, 4199, 2999),
    "Священная гора":     (1799, 1499, 999),
    "Фонтейн":            (4799, 3999, 2799),
    "Море древности":     (1699, 1399, 999),
    "Джунгли":            (3899, 3499, 2499),
    "Пустыня":            (4499, 3999, 2899),
    "Инадзума":           (3999, 3399, 2199),
    "Энканомия":          (1799, 1499, 999),
    "Ли Юэ":              (3599, 3199, 1799),
    "Чень Юй":            (2599, 2199, 1499),
    "Разлом":             (1699, 1399, 999),
    "Драконий хребет":    (1599, 1299, 999),
    "Асмодей":            (2199, 1799, 1299),
    "Монд":               (2299, 1899, 1399),
}

EXTRA_SERVICES = {
    "Фул карта":   "от 40 000",
    "100 круток":  "13 500",
    "100k гемов":  "80 000",
}

class Order(StatesGroup):
    choosing_type = State()      
    choosing_region = State()
    choosing_percent = State()
    entering_contact = State()
    entering_comment = State()

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🌍 Регион")],
        [KeyboardButton(text="💎 Доп. услуги")],
        [KeyboardButton(text="ℹ️ Помощь")],
    ],
    resize_keyboard=True
)

def regions_kb():
    rows = []
    row = []
    for name in SERVICES.keys():
        row.append(InlineKeyboardButton(text=name, callback_data=f"reg:{name}"))
        if len(row) == 2:
            rows.append(row); row = []
    if row: rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)

def percent_kb(region: str):
    p = SERVICES[region]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"0–100%  — {p[0]}₽",  callback_data=f"pct:{region}:0")],
        [InlineKeyboardButton(text=f"50–100% — {p[1]}₽",  callback_data=f"pct:{region}:1")],
        [InlineKeyboardButton(text=f"85–100% — {p[2]}₽",  callback_data=f"pct:{region}:2")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_regions")],
    ])

def extra_kb():
    rows = [[InlineKeyboardButton(text=f"{k} — {v}", callback_data=f"extra:{k}")]
            for k, v in EXTRA_SERVICES.items()]
    return InlineKeyboardMarkup(inline_keyboard=rows)

@dp.message(F.text == "/start")
async def start(msg: Message):
    await msg.answer(
        "👋 Добро пожаловать!\n"
        "Я помогу оформить заказ услуг Genshin Impact.\n\n"
        "Выберите категорию:",
        reply_markup=main_kb
    )

@dp.message(F.text == "ℹ️ Помощь")
async def help_msg(msg: Message):
    await msg.answer(
        "Как оформить заказ:\n"
        "1. Нажмите «🌍 Регион» или «💎 Доп. услуги»\n"
        "2. Выберите нужный пункт\n"
        "3. Укажите контакт для связи\n"
        "4. Дождитесь подтверждения от оператора"
    )

@dp.message(F.text == "🌍 Регион")
async def choose_region(msg: Message, state: FSMContext):
    await state.set_state(Order.choosing_region)
    await msg.answer("Выберите регион:", reply_markup=regions_kb())

@dp.message(F.text == "💎 Доп. услуги")
async def choose_extra(msg: Message, state: FSMContext):
    await state.set_state(Order.choosing_type)
    await msg.answer("Дополнительные услуги:", reply_markup=extra_kb())

@dp.callback_query(F.data.startswith("reg:"))
async def region_selected(cb: CallbackQuery, state: FSMContext):
    region = cb.data.split(":", 1)[1]
    await state.update_data(region=region)
    await state.set_state(Order.choosing_percent)
    await cb.message.edit_text(
        f"Регион: <b>{region}</b>\nВыберите процент исследования:",
        parse_mode="HTML",
        reply_markup=percent_kb(region)
    )
    await cb.answer()

@dp.callback_query(F.data == "back_regions")
async def back_regions(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Order.choosing_region)
    await cb.message.edit_text("Выберите регион:", reply_markup=regions_kb())
    await cb.answer()

@dp.callback_query(F.data.startswith("pct:"))
async def percent_selected(cb: CallbackQuery, state: FSMContext):
    _, region, idx = cb.data.split(":")
    idx = int(idx)
    percent_label = ["0–100%", "50–100%", "85–100%"][idx]
    price = SERVICES[region][idx]
    await state.update_data(service=f"{region} ({percent_label})", price=price)
    await state.set_state(Order.entering_contact)
    await cb.message.edit_text(
        f"✅ Услуга: <b>{region} — {percent_label}</b>\n"
        f"💰 Цена: <b>{price}₽</b>\n\n"
        f"Напишите ваш контакт для связи (Telegram @username или телефон):",
        parse_mode="HTML"
    )
    await cb.answer()

@dp.callback_query(F.data.startswith("extra:"))
async def extra_selected(cb: CallbackQuery, state: FSMContext):
    name = cb.data.split(":", 1)[1]
    price = EXTRA_SERVICES[name]
    await state.update_data(service=name, price=price)
    await state.set_state(Order.entering_contact)
    await cb.message.edit_text(
        f"✅ Услуга: <b>{name}</b>\n"
        f"💰 Цена: <b>{price}₽</b>\n\n"
        f"Напишите ваш контакт для связи:",
        parse_mode="HTML"
    )
    await cb.answer()

@dp.message(Order.entering_contact)
async def enter_contact(msg: Message, state: FSMContext):
    await state.update_data(contact=msg.text)
    await state.set_state(Order.entering_comment)
    await msg.answer("Добавьте комментарий (UID аккаунта, пожелания) или напишите «нет»:")

@dp.message(Order.entering_comment)
async def enter_comment(msg: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    text_admin = (
        "🔔 <b>НОВЫЙ ЗАКАЗ</b>\n\n"
        f"👤 Клиент: {msg.from_user.full_name} (@{msg.from_user.username or 'нет'})\n"
        f"🆔 ID: <code>{msg.from_user.id}</code>\n"
        f"📦 Услуга: <b>{data['service']}</b>\n"
        f"💰 Цена: <b>{data['price']}₽</b>\n"
        f"📞 Контакт: {data['contact']}\n"
        f"💬 Комментарий: {msg.text}"
    )
    try:
        await bot.send_message(ADMIN_ID, text_admin, parse_mode="HTML")
    except Exception as e:
        print("Не удалось отправить админу:", e)

    await msg.answer(
        "✅ Заявка отправлена! Оператор свяжется с вами в ближайшее время.",
        reply_markup=main_kb
        
    )
@dp.message(Command("myid"))
async def show_my_id(msg: Message):
    await msg.answer(
        f"Ваш ID: <code>{msg.from_user.id}</code>\n"
        f"ADMIN_ID в config: <code>{ADMIN_ID}</code>\n"
        f"Совпадает: <b>{msg.from_user.id == ADMIN_ID}</b>",
        parse_mode="HTML"
    )
    
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
