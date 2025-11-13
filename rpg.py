"""Main entry point for the Eldrathia Telegram RPG bot.

The previous implementation bundled hundreds of lines of highly stateful
logic and contained many latent bugs.  The version below focuses on a
small but robust feature set that can be easily extended.
"""

from __future__ import annotations

import logging
import os
import random
from typing import Dict, List

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from battle_system import start_battle
from data.areas.areas_data import AREAS
from data.characters import CHARACTERS
from database import (
    add_item,
    add_player,
    create_tables,
    delete_player,
    get_inventory,
    get_player,
    get_shop_items,
    purchase_item,
    seed_shop_items,
    update_player,
)
from database_utils import prevent_if_has_character, require_player

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

MAIN_MENU = ReplyKeyboardMarkup(
    [["📜 Profile", "⚔️ Adventure"], ["🎒 Inventory", "🏪 Shop"], ["🔄 Reset"]],
    resize_keyboard=True,
)

CLASS_SELECTION = [
    [
        InlineKeyboardButton("⚔️ Fighter", callback_data="class|Fighter"),
        InlineKeyboardButton("🔮 Mage", callback_data="class|Mage"),
    ],
    [
        InlineKeyboardButton("🗡️ Assassin", callback_data="class|Assassin"),
        InlineKeyboardButton("✝️ Paladin", callback_data="class|Paladin"),
    ],
    [
        InlineKeyboardButton("🛡️ Tank", callback_data="class|Tank"),
        InlineKeyboardButton("🏹 Archer", callback_data="class|Archer"),
    ],
]


async def _show_main_menu(bot, chat_id: int, text: str) -> None:
    await bot.send_message(chat_id=chat_id, text=text, reply_markup=MAIN_MENU)


async def _send_class_selection(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    message = update.effective_message
    if message:
        await message.reply_text(
            "🎭 Pilih class karaktermu!",
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.reply_photo(
            photo="https://raw.githubusercontent.com/oflannahar-gif/Eldrathia/main/Eldrathia.jpg",
            caption="Pilih salah satu class di bawah ini.",
            reply_markup=InlineKeyboardMarkup(CLASS_SELECTION),
        )
        return

    chat = update.effective_chat
    if chat:
        await context.bot.send_photo(
            chat_id=chat.id,
            photo="https://raw.githubusercontent.com/oflannahar-gif/Eldrathia/main/Eldrathia.jpg",
            caption="Pilih salah satu class di bawah ini.",
            reply_markup=InlineKeyboardMarkup(CLASS_SELECTION),
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return

    player = await get_player(user.id)
    chat = update.effective_chat
    if player and chat:
        await _show_main_menu(
            context.bot,
            chat.id,
            "Selamat datang kembali di Eldrathia!",
        )
        return

    if update.message:
        await update.message.reply_text(
            "🌄 Selamat datang di dunia Eldrathia! Tekan tombol di bawah untuk memilih karaktermu.",
            reply_markup=ReplyKeyboardMarkup([["🎭 Pilih Karakter"]], resize_keyboard=True),
        )


@prevent_if_has_character
async def pilih_karakter_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    await _send_class_selection(update, context)


def _render_hero_keyboard(class_name: str, index: int) -> InlineKeyboardMarkup:
    heroes = CHARACTERS[class_name]
    hero = heroes[index]
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️",
                    callback_data=f"hero|prev|{class_name}|{index}",
                ),
                InlineKeyboardButton(
                    "➡️",
                    callback_data=f"hero|next|{class_name}|{index}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🗡️ Pilih Karakter Ini",
                    callback_data=f"hero|select|{class_name}|{hero['name']}",
                )
            ],
            [InlineKeyboardButton("🔙 Kembali", callback_data="hero|back")],
        ]
    )


def _hero_caption(class_name: str, index: int) -> str:
    hero = CHARACTERS[class_name][index]
    return (
        f"*{hero['name']}* — {hero['title']}\n"
        f"Class: {hero['class']}\n"
        f"HP: {hero['hp']}  ATK: {hero['atk']}  DEF: {hero['def']}\n\n"
        f"Skill: {hero['skill']} — {hero['skill_desc']}\n\n"
        f"_{hero['desc']}_"
    )


async def _show_hero(
    query, class_name: str, index: int, *, new_message: bool = False
) -> None:
    heroes = CHARACTERS[class_name]
    index %= len(heroes)
    hero = heroes[index]

    keyboard = _render_hero_keyboard(class_name, index)
    caption = _hero_caption(class_name, index)

    if new_message:
        await query.message.reply_photo(
            photo=hero["image"],
            caption=caption,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )
    else:
        media = InputMediaPhoto(media=hero["image"], caption=caption, parse_mode="Markdown")
        await query.edit_message_media(media=media, reply_markup=keyboard)


@prevent_if_has_character
async def class_selection_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()

    _, class_name = query.data.split("|", 1)
    context.user_data["hero_class"] = class_name
    context.user_data["hero_index"] = 0
    await _show_hero(query, class_name, 0, new_message=True)


@prevent_if_has_character
async def hero_navigation_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()

    _, action, class_name, index_str = query.data.split("|", 3)
    index = int(index_str)
    heroes = CHARACTERS[class_name]

    if action == "next":
        index = (index + 1) % len(heroes)
    elif action == "prev":
        index = (index - 1) % len(heroes)

    context.user_data["hero_class"] = class_name
    context.user_data["hero_index"] = index
    await _show_hero(query, class_name, index)


@prevent_if_has_character
async def hero_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    try:
        await query.message.delete()
    except Exception:
        await query.edit_message_text("Memuat daftar class...")
    await _send_class_selection(update, context)


@prevent_if_has_character
async def hero_confirm_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()

    _, _, class_name, hero_name = query.data.split("|", 3)
    user = query.from_user

    await add_player(user.id, user.username, user.first_name, class_name)
    # Starter items
    for _ in range(2):
        await add_item(user.id, "Potion", "Common")
    await add_item(user.id, "Iron Sword", "Uncommon")

    await query.edit_message_text(
        f"🎉 Kamu memilih *{hero_name}* dari class *{class_name}*!",
        parse_mode="Markdown",
    )

    chat = query.message.chat if query.message else update.effective_chat
    if chat:
        await _show_main_menu(context.bot, chat.id, "Petualangan dimulai!")


@require_player
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    player = await get_player(update.effective_user.id)  # type: ignore[arg-type]
    if not player:
        return

    await update.message.reply_text(
        "\n".join(
            [
                "📜 Profil",
                f"Nama: {player.first_name or '-'}",
                f"Username: @{player.username}" if player.username else "Username: -",
                f"Class: {player.class_name}",
                f"Level: {player.level}",
                f"EXP: {player.exp}/{player.max_exp}",
                f"Gold: 💰 {player.gold}",
            ]
        )
    )


@require_player
async def inventory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    items = await get_inventory(update.effective_user.id)  # type: ignore[arg-type]
    if not items:
        await update.message.reply_text("Tasmu kosong.")
        return

    lines = ["🎒 Inventory"]
    for name, rarity, qty in items:
        lines.append(f"• {name} ({rarity}) x{qty}")
    await update.message.reply_text("\n".join(lines))


@require_player
async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    items = await get_shop_items()
    lines = ["🏪 Shop Eldrathia", "Gunakan /buy <id> <jumlah> untuk membeli."]
    for item_id, name, rarity, price in items:
        lines.append(f"{item_id}. {name} [{rarity}] — 💰 {price}")
    await update.message.reply_text("\n".join(lines))


@require_player
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 2:
        await update.message.reply_text("Format: /buy <id> <jumlah>")
        return

    try:
        item_id = int(context.args[0])
        quantity = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Gunakan angka untuk id dan jumlah.")
        return

    if quantity <= 0:
        await update.message.reply_text("Jumlah minimal 1.")
        return

    items = await get_shop_items()
    try:
        item_id_index = next(i for i, item in enumerate(items) if item[0] == item_id)
    except StopIteration:
        await update.message.reply_text("Item tidak ditemukan.")
        return

    _, name, rarity, price = items[item_id_index]
    success = await purchase_item(
        update.effective_user.id,  # type: ignore[arg-type]
        item_name=name,
        rarity=rarity,
        price=price,
        quantity=quantity,
    )

    if success:
        await update.message.reply_text(
            f"Berhasil membeli {name} x{quantity}!"
        )
    else:
        await update.message.reply_text("Gold tidak cukup atau pemain tidak ditemukan.")


@require_player
async def adventure(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    player = await get_player(update.effective_user.id)  # type: ignore[arg-type]
    if not player:
        return

    exp_gain = random.randint(15, 35)
    gold_gain = random.randint(20, 45)
    new_exp = player.exp + exp_gain
    level = player.level
    max_exp = player.max_exp

    leveled_up = False
    while new_exp >= max_exp:
        new_exp -= max_exp
        level += 1
        max_exp = int(max_exp * 1.2)
        leveled_up = True

    await update_player(
        player.user_id,
        level=level,
        exp=new_exp,
        gold=player.gold + gold_gain,
        max_exp=max_exp,
    )

    lines = [
        "⚔️ Petualangan Berhasil!",
        f"✨ EXP +{exp_gain}",
        f"💰 Gold +{gold_gain}",
    ]
    if leveled_up:
        lines.append(f"🎉 Naik ke level {level}!")

    await update.message.reply_text("\n".join(lines))


@require_player
async def resetme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await delete_player(update.effective_user.id)  # type: ignore[arg-type]
    await update.message.reply_text(
        "Data kamu sudah dihapus. Gunakan /start untuk memulai ulang."
    )


@require_player
async def explore_padang_latihan(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()

    area = AREAS["PadangLatihan"]
    monsters = [monster["name"] for monster in area["monsters"]]
    chosen = random.choice(monsters)

    player = await get_player(query.from_user.id)
    if not player:
        await query.edit_message_text("Pemain tidak ditemukan.")
        return

    await query.edit_message_text(
        f"Kamu bertemu dengan {chosen}! Pertarungan dimulai..."
    )
    await start_battle(update, context, player, chosen)


async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text if update.message else ""
    if text == "📜 Profile":
        await profile(update, context)
    elif text == "🎒 Inventory":
        await inventory(update, context)
    elif text == "🏪 Shop":
        await shop(update, context)
    elif text == "⚔️ Adventure":
        await adventure(update, context)
    elif text == "🔄 Reset":
        await resetme(update, context)
    elif text == "🎭 Pilih Karakter":
        await pilih_karakter_handler(update, context)


async def on_startup(application: Application) -> None:
    await create_tables()
    await seed_shop_items()
    logger.info("Database ready.")


def build_application(token: str | None = None) -> Application:
    if not token:
        token = BOT_TOKEN
    if not token:
        raise RuntimeError("BOT_TOKEN is not configured")

    application = ApplicationBuilder().token(token).post_init(on_startup).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("inventory", inventory))
    application.add_handler(CommandHandler("shop", shop))
    application.add_handler(CommandHandler("buy", buy))
    application.add_handler(CommandHandler("adventure", adventure))
    application.add_handler(CommandHandler("resetme", resetme))

    application.add_handler(
        MessageHandler(filters.Regex("^🎭 Pilih Karakter$"), pilih_karakter_handler)
    )
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_router))

    application.add_handler(CallbackQueryHandler(class_selection_callback, r"^class\|"))
    application.add_handler(CallbackQueryHandler(hero_navigation_callback, r"^hero\|next"))
    application.add_handler(CallbackQueryHandler(hero_navigation_callback, r"^hero\|prev"))
    application.add_handler(CallbackQueryHandler(hero_back_callback, pattern=r"^hero\|back"))
    application.add_handler(CallbackQueryHandler(hero_confirm_callback, pattern=r"^hero\|select"))

    return application


def main() -> None:
    application = build_application()
    application.run_polling()


if __name__ == "__main__":
    main()
