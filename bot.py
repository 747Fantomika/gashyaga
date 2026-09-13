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
import database as db

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ============================================================
# УСЛУГИ (из скрина)
# ============================================================
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


# ============================================================
# FSM
# ============================================================
class Order(StatesGroup):
    choosing_region = State()
    choosing_percent = State()
    entering_contact = State()
    entering_comment = State()


# ============================================================
# КЛАВИАТУРЫ
# ============================================================
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🌍 Регион")],
        [KeyboardButton(text="💎 Доп. услуги")],
        [KeyboardButton(text="📋 Мои заказы")],
        [KeyboardButton(text="ℹ️ Помощь")],
    ],
    resize_keyboard=True
)

admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📥 Новые заявки")],
        [KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="⬅️ Выход")],
    ],
    resize_keyboard=True
)


def regions_kb():
    rows, row = [], []
    for name in SERVICES.keys():
        row.append(InlineKeyboardButton(text=name, callback_data=f"reg:{name}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def percent_kb(region):
    p = SERVICES[region]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"0–100%  — {p[0]}₽", callback_data=f"pct:{region}:0")],
        [InlineKeyboardButton(text=f"50–100% — {p[1]}₽", callback_data=f"pct:{region}:1")],
        [InlineKeyboardButton(text=f"85–100% — {p[2]}₽", callback_data=f"pct:{region}:2")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_regions")],
    ])


def extra_kb():
    rows = [
        [InlineKeyboardButton(text=f"{k} — {v}", callback_data=f"extra:{k}")]
        for k, v in EXTRA_SERVICES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def order_actions_kb(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Выполнено", callback_data=f"adm_done:{order_id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_reject:{order_id}")],
    ])


def is_admin(user_id):
    return user_id == ADMIN_ID


# ============================================================
# СИСТЕМНЫЕ КОМАНДЫ (регистрируем ПЕРВЫМИ!)
# ============================================================
@dp.message(Command("start"))
async def start(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        "👋 Добро пожаловать!\n"
        "Я помогу оформить заказ услуг Genshin Impact.\n\n"
        "Выберите категорию:",
        reply_markup=main_kb
    )


@dp.message(Command("cancel"))
async def cancel(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Действие отменено.", reply_markup=main_kb)


@dp.message(Command("myid"))
async def show_my_id(msg: Message):
    await msg.answer(
        f"Ваш ID: <code>{msg.from_user.id}</code>\n"
        f"ADMIN_ID из config: <code>{ADMIN_ID}</code>\n"
        f"Совпадает: <b>{msg.from_user.id == ADMIN_ID}</b>",
        parse_mode="HTML"
    )


@dp.message(Command("admin"))
async def admin_panel(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer("У вас нет доступа к админ-панели.")
        return
    await state.clear()
    await msg.answer("🔧 Админ-панель:", reply_markup=admin_kb)


# ============================================================
# АДМИН-КНОПКИ
# ============================================================
@dp.message(F.text == "⬅️ Выход")
async def admin_exit(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer("Вы вышли из админки.", reply_markup=main_kb)


@dp.message(F.text == "📊 Статистика")
async def admin_stats(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    s = await db.get_stats()
    await msg.answer(
        f"📊 <b>Статистика</b>\n\n"
        f"Всего заказов: <b>{s['total']}</b>\n"
        f"🕐 Новых: <b>{s['new']}</b>\n"
        f"✅ Выполнено: <b>{s['done']}</b>",
        parse_mode="HTML"
    )


@dp.message(F.text == "📥 Новые заявки")
async def admin_new_orders(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    orders = await db.get_new_orders()
    if not orders:
        await msg.answer("Новых заявок нет.")
        return
    for o in orders:
        text = (
            f"🔔 <b>Заказ #{o['id']}</b>\n\n"
            f"👤 {o['full_name']} (@{o['username'] or 'нет'})\n"
            f"🆔 <code>{o['user_id']}</code>\n"
            f"📦 {o['service']}\n"
            f"💰 {o['price']}₽\n"
            f"📞 {o['contact']}\n"
            f"💬 {o['comment']}\n"
            f"📅 {o['created_at']}"
        )
        await msg.answer(text, parse_mode="HTML",
                         reply_markup=order_actions_kb(o["id"]))


# ============================================================
# CALLBACK: ВЫПОЛНЕНО / ОТКЛОНИТЬ
# ============================================================
@dp.callback_query(F.data.startswith("adm_done:"))
async def adm_done(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("Нет доступа", show_alert=True)
        return
    order_id = int(cb.data.split(":")[1])
    order = await db.get_order(order_id)
    await db.set_status(order_id, "done")
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.answer(f"✅ Заказ #{order_id} выполнен.")
    if order:
        try:
            await bot.send_message(
                order["user_id"],
                f"✅ Ваш заказ <b>#{order_id}</b> ({order['service']}) выполнен!\n"
                f"Спасибо за обращение 💙",
                parse_mode="HTML"
            )
        except Exception as e:
            print("Не удалось уведомить клиента:", e)
    await cb.answer()


@dp.callback_query(F.data.startswith("adm_reject:"))
async def adm_reject(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("Нет доступа", show_alert=True)
        return
    order_id = int(cb.data.split(":")[1])
    order = await db.get_order(order_id)
    await db.set_status(order_id, "rejected")
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.answer(f"❌ Заказ #{order_id} отклонён.")
    if order:
        try:
            await bot.send_message(
                order["user_id"],
                f"❌ К сожалению, заказ <b>#{order_id}</b> отклонён.\n"
                f"Свяжитесь с оператором для деталей.",
                parse_mode="HTML"
            )
        except Exception as e:
            print("Не удалось уведомить клиента:", e)
    await cb.answer()


# ============================================================
# КЛИЕНТСКИЕ КНОПКИ
# ============================================================
@dp.message(F.text == "ℹ️ Помощь")
async def help_msg(msg: Message):
    await msg.answer(
        "Как оформить заказ:\n"
        "1. Нажмите «🌍 Регион» или «💎 Доп. услуги»\n"
        "2. Выберите услугу и процент\n"
        "3. Укажите контакт и комментарий\n"
        "4. Оператор свяжется с вами\n\n"
        "📋 «Мои заказы» — история и статусы."
    )


@dp.message(F.text == "📋 Мои заказы")
async def my_orders(msg: Message):
    orders = await db.get_user_orders(msg.from_user.id)
    if not orders:
        await msg.answer("У вас пока нет заказов.")
        return
    text = "📋 <b>Ваши последние заказы:</b>\n\n"
    for o in orders:
        status_emoji = {"new": "🕐", "done": "✅", "rejected": "❌"}.get(o["status"], "•")
        text += (
            f"{status_emoji} <b>#{o['id']}</b> — {o['service']}\n"
            f"💰 {o['price']}₽ | 📅 {o['created_at']}\n\n"
        )
    await msg.answer(text, parse_mode="HTML")


@dp.message(F.text == "🌍 Регион")
async def choose_region(msg: Message, state: FSMContext):
    await state.set_state(Order.choosing_region)
    await msg.answer("Выберите регион:", reply_markup=regions_kb())


@dp.message(F.text == "💎 Доп. услуги")
async def choose_extra(msg: Message, state: FSMContext):
    await msg.answer("Дополнительные услуги:", reply_markup=extra_kb())


# ============================================================
# CALLBACK: РЕГИОН / ПРОЦЕНТ / ДОП
# ============================================================
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
        f"Напишите ваш контакт (Telegram @username или телефон):",
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


# ============================================================
# FSM: КОНТАКТ / КОММЕНТАРИЙ
# ============================================================
@dp.message(Order.entering_contact)
async def enter_contact(msg: Message, state: FSMContext):
    await state.update_data(contact=msg.text)
    await state.set_state(Order.entering_comment)
    await msg.answer("Добавьте комментарий (UID аккаунта, пожелания) или напишите «нет»:")


@dp.message(Order.entering_comment)
async def enter_comment(msg: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    order_id = await db.add_order(
        user_id=msg.from_user.id,
        username=msg.from_user.username,
        full_name=msg.from_user.full_name,
        service=data["service"],
        price=str(data["price"]),
        contact=data["contact"],
        comment=msg.text
    )

    text_admin = (
        f"🔔 <b>НОВЫЙ ЗАКАЗ #{order_id}</b>\n\n"
        f"👤 {msg.from_user.full_name} (@{msg.from_user.username or 'нет'})\n"
        f"🆔 <code>{msg.from_user.id}</code>\n"
        f"📦 {data['service']}\n"
        f"💰 {data['price']}₽\n"
        f"📞 {data['contact']}\n"
        f"💬 {msg.text}"
    )
    try:
        await bot.send_message(ADMIN_ID, text_admin,
                               parse_mode="HTML",
                               reply_markup=order_actions_kb(order_id))
    except Exception as e:
        print("Не удалось отправить админу:", e)

    await msg.answer(
        f"✅ Заявка <b>#{order_id}</b> отправлена! Оператор свяжется с вами.",
        parse_mode="HTML",
        reply_markup=main_kb
    )


# ============================================================
# ЗАПУСК
# ============================================================
async def main():
    await db.init_db()
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())





