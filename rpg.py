from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InputMediaPhoto
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from database import (
    create_tables,
    add_player,
    get_player,
    add_item,
    get_inventory,
    get_shop_items,
    seed_shop_items,
)
from data.characters import CHARACTERS

from data.areas.areas_data import AREAS
from database_utils import get_area_progress, update_kill_count, save_area_progress
from database_utils import require_player, prevent_if_has_character


import asyncio
import random
import aiosqlite
import re


# Ganti teks di bawah dengan token dari BotFather
BOT_TOKEN = "7978895482:AAHvw7ZJZ8c0wDQwib5feOdIoP5u4KYFInI"

# ========= ++++++++>>>  START   <<<+++++++ =========
async def show_main_menu(update: Update):
    keyboard = [
        ["📜 Profile", "⚔️ Adventure"],
        ["🎒 Inventory", "🏪 Shop"],
        ["🏦 Market", "🔄 Reset"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text(
        "🏰 *Menu Utama Eldrathia*\nSilakan pilih aksi:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )



# ====== START INTRO ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    player = await get_player(user.id)

    if player:
        await show_main_menu(update)
        return

    intro_text = (
        "🌄 *Selamat datang di Dunia Eldrathia!*\n\n"
        "Ratusan tahun yang lalu, kristal Aetherium pecah menjadi lima fragmen dan dunia terjerumus dalam kekacauan.\n"
        "Kini, kerajaan Eldoria memanggil para petualang dari seluruh penjuru dunia untuk mengembalikan keseimbangan.\n\n"
        "Kamu adalah salah satu dari mereka — seorang *petualang muda* yang baru saja tiba di gerbang kota.\n\n"
        "✨ Petualanganmu baru saja dimulai...\n\n"
        "_Tekan tombol di bawah untuk memilih karaktermu!_"
    )

    reply_markup = ReplyKeyboardMarkup(
        [["🎭 Pilih Karakter"]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await update.message.reply_photo(
        photo="https://raw.githubusercontent.com/oflannahar-gif/Eldrathia/main/Eldrathia.jpg",
        caption=intro_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# ====== TOMBOL PILIH KARAKTER ======
async def pilih_karakter_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # 🌀 Step 1: Kirim pesan pertama sambil hapus tombol bawah
    msg = await update.message.reply_text("🎭 Pilih Karakter", reply_markup=ReplyKeyboardRemove())

    # Hapus pesan terakhir (biar bersih)
    await asyncio.sleep(0.4)
    try:
        await msg.delete()
    except:
        pass

    # ✨ Step 3: Kirim banner + pilihan class
    keyboard = [
        [
            InlineKeyboardButton("⚔️ Fighter", callback_data="class_Fighter"),
            InlineKeyboardButton("🔮 Mage", callback_data="class_Mage"),
        ],
        [
            InlineKeyboardButton("🗡️ Assassin", callback_data="class_Assassin"),
            InlineKeyboardButton("✝️ Paladin", callback_data="class_Paladin"),
        ],
        [
            InlineKeyboardButton("🛡️ Tank", callback_data="class_Tank"),
            InlineKeyboardButton("🏹 Archer", callback_data="class_Archer"),
        ]
    ]

    banner_url = "https://cobacoba123.my.id/Eldrathia/ClassBanner.jpeg"

    caption = (
        "⚔️ *Pilih Class Karaktermu*\n\n"
        "Setiap Class memiliki gaya bertarung dan kekuatan unik.\n"
        "Kamu bisa melihat karakternya satu per satu sebelum memilih."
    )

    await update.message.reply_photo(
        photo=banner_url,
        caption=caption,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )





# ====== PILIH CLASS DAN TAMPILKAN HERO ======
async def choose_character_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    class_name = query.data.split("_")[1]
    context.user_data["class_list"] = list(CHARACTERS.keys())
    context.user_data["current_class_index"] = context.user_data["class_list"].index(class_name)
    context.user_data["current_hero_index"] = 0

    await show_current_hero(query, context)


# ====== FUNGSI MENAMPILKAN HERO BERDASARKAN INDEX ======
async def show_current_hero(query, context):
    class_list = context.user_data["class_list"]
    class_idx = context.user_data["current_class_index"]
    hero_idx = context.user_data["current_hero_index"]

    class_name = class_list[class_idx]
    heroes = CHARACTERS[class_name]
    hero = heroes[hero_idx]

    caption = (
        f"*{hero['name']}* — {class_name}\n\n"
        f"_{hero['desc']}_"
    )

    keyboard = [
        [
            InlineKeyboardButton("⬅️", callback_data="prev_hero"),
            InlineKeyboardButton("➡️", callback_data="next_hero")
        ],
        [InlineKeyboardButton("🗡️ Pilih Karakter Ini", callback_data=f"select_hero|{class_name}|{hero['name']}")],
        [InlineKeyboardButton("🔙 Kembali ke Pilihan Class", callback_data="back_to_class")]
    ]

    # Edit pesan jika sudah ada, kirim baru kalau belum
    try:
        await query.edit_message_media(
            media=InputMediaPhoto(media=hero["image"], caption=caption, parse_mode="Markdown"),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception:
        await query.message.reply_photo(
            photo=hero["image"],
            caption=caption,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# ====== GESER KANAN & KIRI ======
@prevent_if_has_character
async def next_hero_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    class_list = context.user_data["class_list"]
    class_idx = context.user_data["current_class_index"]
    heroes = CHARACTERS[class_list[class_idx]]

    context.user_data["current_hero_index"] = (context.user_data["current_hero_index"] + 1) % len(heroes)
    await show_current_hero(query, context)


@prevent_if_has_character
async def prev_hero_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    class_list = context.user_data["class_list"]
    class_idx = context.user_data["current_class_index"]
    heroes = CHARACTERS[class_list[class_idx]]

    context.user_data["current_hero_index"] = (context.user_data["current_hero_index"] - 1) % len(heroes)
    await show_current_hero(query, context)

# ====== KEMBALI KE PILIH CLASS ======
@prevent_if_has_character
async def back_to_class_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # 🧹 Hapus pesan lama (yang menampilkan hero)
    try:
        await query.message.delete()
    except Exception:
        pass  # kalau gagal hapus, abaikan aja biar gak error

    # 🔘 Tampilkan ulang banner dan tombol class

    keyboard = [
        [
            InlineKeyboardButton("⚔️ Fighter", callback_data="class_Fighter"),
            InlineKeyboardButton("🔮 Mage", callback_data="class_Mage"),
        ],
        [
            InlineKeyboardButton("🗡️ Assassin", callback_data="class_Assassin"),
            InlineKeyboardButton("✝️ Paladin", callback_data="class_Paladin"),
        ],
        [
            InlineKeyboardButton("🛡️ Tank", callback_data="class_Tank"),
            InlineKeyboardButton("🏹 Archer", callback_data="class_Archer"),
        ]
    ]

    # Gambar banner pilihan class
    image_url = "https://cobacoba123.my.id/Eldrathia/ClassBanner.jpeg"

    caption = (
        "⚔️ *Pilih Class Karaktermu Lagi*\n\n"
        "Setiap Class memiliki gaya bertarung dan kekuatan unik.\n"
        "Kamu bisa melihat karakternya satu per satu sebelum memilih."
    )

    # Kirim pesan baru (bukan edit), supaya tidak error Markdown
    await query.message.reply_photo(
        photo=image_url,
        caption=caption,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )



# ====== PILIH HERO ======
@prevent_if_has_character
async def select_hero_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, class_name, hero_name = query.data.split("|")
    context.user_data["selected_class"] = class_name
    context.user_data["selected_hero"] = hero_name

    keyboard = [
        [
            InlineKeyboardButton("✅ Yakin", callback_data="confirm_hero"),
            InlineKeyboardButton("❌ Batal", callback_data="cancel_hero")
        ]
    ]

    await query.message.reply_text(
        f"Apakah kamu yakin ingin memilih *{hero_name}* dari class *{class_name}*?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ====== KONFIRMASI ======
@prevent_if_has_character
async def confirm_hero_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    hero_name = context.user_data.get("selected_hero")
    class_name = context.user_data.get("selected_class")

    if not hero_name or not class_name:
        await query.edit_message_text("❌ Terjadi kesalahan saat memilih karakter.")
        return

    # Simpan ke database
    await add_player(user.id, user.username, user.first_name, class_name)
    await add_item(user.id, "Potion", "Common")
    await add_item(user.id, "Potion", "Common")
    await add_item(user.id, "Iron Sword", "Uncommon")

    await query.edit_message_text(
        f"🎉 Kamu telah memilih *{hero_name}*!\n"
        f"Class: {class_name}\n\n"
        f"🎁 Hadiah Awal:\n• 2x Potion\n• 1x Iron Sword\n💰 Gold: 1000",
        parse_mode="Markdown"
    )

    await asyncio.sleep(2)
    await enter_arvendale(update, context)

# ====== BATAL ======
@prevent_if_has_character
async def cancel_hero_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Hapus pesan konfirmasi agar tidak menumpuk
    await query.delete_message()

    # Langsung panggil fungsi kembali ke pilihan class
    await back_to_class_callback(update, context)


# ========== Masuk ke Kerajaan Arvendale ==========
async def enter_arvendale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    image_url = "https://cobacoba123.my.id/Eldrathia/Arvendale.jpg"

    intro_text = (
        "🏰 *Selamat datang di Kerajaan Arvendale!*\n\n"
        "Di bawah cahaya lembut matahari senja, tembok putih kota *Solmare* "
        "berdiri megah di depanmu. Para penjaga menatap tajam, namun ramah.\n\n"
        "Di sini perjalananmu akan dimulai.\n"
        "✨ *Tujuan pertamamu*: Temui Komandan *Elaine Crestborne* di gerbang kota untuk menerima pelatihan dasar."
    )

    # Update lokasi pemain di database
    async with aiosqlite.connect("game.db") as db:
        await db.execute("""
            UPDATE players
            SET current_kingdom = 'Arvendale', location = 'Solmare', story_progress = 0
            WHERE user_id = ?
        """, (user.id,))
        await db.commit()

    await query.message.reply_photo(
    photo=image_url,
    caption=intro_text,
    parse_mode="Markdown",
    reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("➡️ Lanjutkan", callback_data="tutorial_quest_start")]
    ])
)

async def tutorial_quest_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await tutorial_quest(update, context)


# === QUEST PERTAMA: PELATIHAN DASAR ===
async def tutorial_quest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Deteksi apakah dipanggil dari command (/tutorial) atau callback (button/confirm)
    message = None
    user = None

    if update.message:  # jika dipanggil dari command
        message = update.message
        user = update.effective_user
    elif update.callback_query:  # jika dari callback button
        query = update.callback_query
        await query.answer()
        message = query.message
        user = query.from_user

    if not user or not message:
        return  # safety check biar gak error lagi

    player = await get_player(user.id)
    if not player:
        await message.reply_text("Kamu belum terdaftar! Ketik /start dulu.")
        return

    # Ambil data player
    _, username, first_name, class_name, level, exp, gold, max_exp, current_kingdom, location, story_progress = player

    # Pastikan quest ini hanya muncul jika pemain baru masuk Arvendale
    if story_progress == 0:
        image_url = "https://cobacoba123.my.id/Eldrathia/Background.jpg"
        intro = (
            "<b>👩‍✈️ Komandan Elaine Crestborne</b>:\n"
            "'Selamat datang, petualang muda.'\n\n"
            "Aku adalah <b>Elaine Crestborne</b>, pelatih para prajurit di Arvendale.\n"
            "Sebelum kau diizinkan menjelajah dunia luar, tunjukkan kemampuanmu!\n"
            "Latih dirimu dengan mengalahkan seekor <b>Slime</b> di padang latihan.\n\n"
            "✨ Gunakan perintah <b>/goto_PadangLatihan</b> untuk memulai pelatihan pertamamu!"
        )

        # ✅ gunakan 'message', bukan 'update.message'
        await message.reply_photo(photo=image_url, caption=intro, parse_mode="HTML")

        # Update progress supaya tahu pemain sedang dalam pelatihan
        async with aiosqlite.connect("game.db") as db:
            await db.execute("UPDATE players SET story_progress = 1 WHERE user_id = ?", (user.id,))
            await db.commit()
    else:
        await message.reply_text(
            "Kamu sudah menerima pelatihan dasar dari Komandan Elaine. "
            "Lanjutkan petualanganmu, pahlawan!",
            reply_markup=ReplyKeyboardMarkup(
                [["📜 Profile", "⚔️ Adventure"], ["🎒 Inventory", "🏪 Shop"]],
                resize_keyboard=True
            )
        )
        return


# =====================================================
# 📊 AREA PROGRESS MANAGEMENT
# =====================================================

async def get_area_progress(user_id, area_name):
    async with aiosqlite.connect("game.db") as db:
        async with db.execute("""
            SELECT monster_name, kills FROM area_progress
            WHERE user_id = ? AND area_name = ?
        """, (user_id, area_name)) as cursor:
            rows = await cursor.fetchall()
            return {row[0]: row[1] for row in rows}  # contoh: {"Slime": 3, "Boar": 1}


async def update_kill_count(user_id, area_name, monster_name):
    async with aiosqlite.connect("game.db") as db:
        # cek dulu apakah sudah ada record
        async with db.execute("""
            SELECT kills FROM area_progress
            WHERE user_id = ? AND area_name = ? AND monster_name = ?
        """, (user_id, area_name, monster_name)) as cursor:
            row = await cursor.fetchone()

        if row:
            await db.execute("""
                UPDATE area_progress
                SET kills = kills + 1
                WHERE user_id = ? AND area_name = ? AND monster_name = ?
            """, (user_id, area_name, monster_name))
        else:
            await db.execute("""
                INSERT INTO area_progress (user_id, area_name, monster_name, kills)
                VALUES (?, ?, ?, 1)
            """, (user_id, area_name, monster_name))

        await db.commit()








# =====================================================
# 🌄 GOTO AREA HANDLER: Padang Latihan
# =====================================================
@require_player
async def goto_padanglatihan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    area_name = "PadangLatihan"
    area = AREAS[area_name]

    # Ambil progress user (jumlah musuh yang sudah dikalahkan)
    progress = await get_area_progress(user.id, area_name)
    monsters = area["monsters"]

    # Format daftar musuh (tampilkan ???? kalau belum dikalahkan)
    monster_lines = []
    for monster in monsters:
        name = monster["name"]
        goal = monster["goal"]
        kills = progress.get(name, 0)
        bar = f"😈 {name} ({kills}/{goal})" if kills > 0 else "😈 ????"
        monster_lines.append(bar)

    text = (
        f"============================\n"
        f"{area['name']}\n"
        f"============================\n\n"
        f"{area['description']}\n\n"
        + "\n".join(monster_lines)
        + "\n\nKalahkan semua musuh yang ada di sini masing-masing minimal 5x "
          "untuk bisa lanjut ke area berikutnya."
    )

    keyboard = [
        [InlineKeyboardButton("🔍 Telusuri", callback_data="explore_padanglatihan")]
    ]

    # ✅ Kirim gambar area + caption
    try:
        await update.message.reply_photo(
            photo=area["image"],
            caption=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        # Jika gambar gagal dimuat, fallback ke teks biasa
        await update.message.reply_text(
            text + f"\n\n⚠️ (Gambar area gagal dimuat: {e})",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# =====================================================
# 🔍 TELUSURI AREA (versi upgrade)
# =====================================================
@require_player
async def explore_padanglatihan_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    area_name = "PadangLatihan"
    area = AREAS[area_name]
    await query.answer()

    progress = await get_area_progress(user.id, area_name)
    monsters = area["monsters"]

    # Cek monster yang masih terkunci (belum pernah dilawan)
    locked_monsters = [m for m in monsters if progress.get(m["name"], 0) == 0]

    # Kondisi 1: masih ada yang terkunci → buka yang pertama dari atas
    if locked_monsters:
        monster = locked_monsters[0]
        monster_name = monster["name"]
        encounter = [monster_name]
    else:
        # Kondisi 2: semua sudah terbuka → encounter acak 1-4 musuh
        import random
        total_fight = random.randint(1, 4)
        encounter = [m["name"] for m in random.sample(monsters, total_fight)]

    # Format tampilan encounter
    enemy_lines = "\n".join([f"😈 {name}" for name in encounter])
    encounter_text = (
        f"============================\n"
        f"{area['name']}\n"
        f"============================\n\n"
        f"Kamu menelusuri *{area.get('display_name', area['name'])}* dan dihadang oleh {len(encounter)} musuh:\n\n"
        f"{enemy_lines}\n\n"
        f"============================"
    )

    # Callback_data untuk tiap musuh (jika ada lebih dari 1)
    keyboard = [
        [InlineKeyboardButton(f"⚔️ Lawan ({len(encounter)} musuh)", callback_data=f"fight_{'_'.join(encounter)}")]
    ]

    try:
        await query.edit_message_caption(
            caption=encounter_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception:
        # Jika caption belum ada (pesan bukan foto), fallback edit text
        await query.edit_message_text(
            text=encounter_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )



# =====================================================
# ⚔️ FIGHT HANDLER — Simulasi Battle Cepat
# =====================================================
@require_player
async def fight_monsters_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    area_name = "PadangLatihan"
    area = AREAS[area_name]

    await query.answer()

    # Ambil nama monster dari callback_data
    data = query.data  # contoh: "fight_Cave Slime_Wild Wolf"
    monster_names = data.replace("fight_", "").split("_")

    # Import data monster rank F
    from data.monsters.monsters_rank_F import monsters_rank_F

    # Ambil info monster yang sesuai
    enemy_list = [m for m in monsters_rank_F if m["name"] in monster_names]

    total_enemy_hp = sum(e["hp"] for e in enemy_list)
    total_enemy_atk = sum(e["atk"] for e in enemy_list)
    total_exp = sum(e["exp"] for e in enemy_list)
    total_gold = sum(e["gold_drop"] for e in enemy_list)

    # Simulasi serangan (sederhana)
    import random
    player_damage = random.randint(7000, 9000)
    enemy_damage = random.randint(0, 20)

    # Update progress area
    progress = await get_area_progress(user.id, area_name)
    for enemy in enemy_list:
        name = enemy["name"]
        progress[name] = progress.get(name, 0) + 1
    await save_area_progress(user.id, area_name, progress)

    # Format teks hasil pertempuran
    enemy_lines = "\n".join([f"😈 {e['name']}" for e in enemy_list])
    result_text = (
        f"============================\n"
        f"{area['name']}\n"
        f"============================\n\n"
        f"Kamu memutuskan untuk melawan {len(enemy_list)} musuh:\n\n"
        f"{enemy_lines}\n\n"
        f"Pertarungan berlangsung sengit...\n\n"
        f"Kamu memberikan total {player_damage:,} DMG ⚔️\n"
        f"Musuh kalah dalam sekali serang dan tak sempat membalas!\n\n"
        f"🏆 KAMU MENANG!\n"
        f"+{total_exp} EXP\n"
        f"+{total_gold} Gold"
    )

    keyboard = [
        [InlineKeyboardButton("🔁 Telusuri Lagi", callback_data="explore_padanglatihan")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_padanglatihan")]
    ]

    await query.edit_message_caption(
        caption=result_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )







# +++++++++++ COMMAND ++++++++++

# ========== /profile ==========
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = await get_player(user.id)
    if data:
        _, username, first_name, class_name, level, exp, gold, max_exp = data
        # Tampilkan profil pemain
        await update.message.reply_text(
            f"📜 Profil Pemain\n"
            f"Nama: {first_name}\n"
            f"Username: @{username}\n"
            f"Class: {class_name}\n"
            f"Level: {level}\n"
            f"Exp: {exp}\n"
            f"Gold: 💰 {gold}"
        )
    else:
        await update.message.reply_text("Kamu belum terdaftar! Ketik /start dulu.")


# =========== /adventure ===========
async def adventure(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    # Ambil data pemain
    async with aiosqlite.connect("game.db") as db:
        async with db.execute("SELECT level, exp, gold, max_exp FROM players WHERE user_id = ?", (user_id,)) as cursor:
            player = await cursor.fetchone()

        if not player:
            await update.message.reply_text("Kamu belum terdaftar! Ketik /start dulu.")
            return

        level, exp, gold, max_exp = player

        # Simulasi hasil petualangan
        gained_exp = random.randint(10, 30)
        gained_gold = random.randint(5, 20)

        # 🎁 Loot system (item acak)
        loot_table = [
            ("Potion", "Common"),
            ("Iron Sword", "Uncommon"),
            ("Steel Armor", "Rare"),
            ("Golden Dagger", "Epic"),
            ("Dragon Scale", "Legendary")
        ]

        # Peluang rarity
        rarity_chance = random.random()
        if rarity_chance < 0.6:
            item = loot_table[0]  # Common
        elif rarity_chance < 0.85:
            item = loot_table[1]
        elif rarity_chance < 0.95:
            item = loot_table[2]
        elif rarity_chance < 0.985:
            item = loot_table[3]
        else:
            item = loot_table[4]

        item_name, rarity = item

        # Simpan ke database
        
        await add_item(user_id, item_name, rarity)

        # Update stats pemain
        exp += gained_exp
        gold += gained_gold
        message = (
            f"🏕️ Kamu pergi berpetualang dan mendapatkan:\n"
            f"✨ {gained_exp} EXP\n"
            f"💰 {gained_gold} Gold\n"
            f"🎁 Item: {item_name}\n\n"
            f"\nTotal EXP: {exp}/{max_exp}\n"
            f"Total Gold: 💰 {gold}"
        )

        # Cek naik level
        if exp >= max_exp:
            level += 1
            exp -= max_exp
            max_exp = int(max_exp * 1.2)  # semakin tinggi, makin susah naik
            message += f"\n🎉 SELAMAT! Kamu naik ke Level {level}!"

        # Simpan perubahan
        await db.execute(
            "UPDATE players SET level = ?, exp = ?, gold = ?, max_exp = ? WHERE user_id = ?",
            (level, exp, gold, max_exp, user_id)
        )
        await db.commit()

    # Kirim hasil ke user
    await update.message.reply_text(message)


#   =========== /resetme ===========
async def resetme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    async with aiosqlite.connect("game.db") as db:
        # ⚠️ AKTIFKAN FOREIGN KEY CASCADE
        await db.execute("PRAGMA foreign_keys = ON;")

        # Hapus data pemain → otomatis hapus inventory karena CASCADE
        await db.execute("DELETE FROM players WHERE user_id = ?", (user.id,))
        await db.commit()

    await update.message.reply_text("✅ Semua data kamu sudah dihapus total. Ketik /start untuk memulai dari awal!")



# ============== /inventory =============
async def inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Cek apakah user sudah terdaftar
    data = await get_player(user.id)
    if not data:
        await update.message.reply_text("Kamu belum terdaftar! Ketik /start dulu.")
        return

    # Lanjut tampilkan inventory
    items = await get_inventory(user.id)

    if not items:
        await update.message.reply_text("🎒 Inventory kamu kosong. Pergilah berpetualang untuk mendapatkan item!")
        return

    # Tampilkan daftar item
    text_lines = ["🎒 Inventory Kamu:"]
    for item_name, rarity, qty in items:
        # Tampilkan "Potion 3x (Common)" atau "Iron Sword (Uncommon)" jika qty == 1
        if qty > 1:
            text_lines.append(f"• {item_name} {qty}")
        else:
            text_lines.append(f"• {item_name}")

    text = "\n".join(text_lines)

    await update.message.reply_text(text)


# ============= SHOP =============

#  /shop 
async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # ✅ Cek apakah pemain sudah terdaftar
    data = await get_player(user.id)
    if not data:
        await update.message.reply_text("⚠️ Kamu belum terdaftar! Ketik /start dulu untuk memulai permainan.")
        return

    # Kalau sudah terdaftar, tampilkan daftar item shop
    items = await get_shop_items()
    if not items:
        await update.message.reply_text("🏪 Toko masih kosong untuk saat ini.")
        return

    text = (f"🏪 **Toko Item RPG** 🏪\n"
            "Gunakan /buy_NamaItem untuk membeli item.\n\n"
    )
    for item_id, name, rarity, price in items:
        text += f"• {name} — 💰 {price}\n"

    await update.message.reply_text(text)


# /buy_<itemname>_<jumlah>
async def buy_item_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message_text = update.message.text.strip()
 

    # ✅ Cek apakah pemain sudah terdaftar
    data = await get_player(user.id)
    if not data:
        await update.message.reply_text("⚠️ Kamu belum terdaftar! Ketik /start dulu untuk memulai permainan.")
        return

    # Cek apakah format sesuai /buy_Item_Jumlah
    if not message_text.startswith("/buy_"):
        return

    try:
        parts = message_text.split("_")
        if len(parts) < 3:
            await update.message.reply_text("Format salah! Contoh: /buy_Potion_5 atau /buy_IronSword_2")
            return

        # Gabung kata
        item_name_raw = "_".join(parts[1:-1])
        qty = int(parts[-1])    

    except Exception:
        await update.message.reply_text("Format salah! Contoh: /buy_Potion_5")
        return
    
    if qty <= 0:
        await update.message.reply_text("Jumlah pembelian minimal 1.")
        return
    
    # 🧠 Ubah format nama item: IronSword -> Iron Sword
    item_name = re.sub(r"([a-z])([A-Z])", r"\1 \2", item_name_raw).title()
    
    
    # Ambil data item dari shop
    items = await get_shop_items()
    shop_item = None
    for item_id, name, rarity, price in items:
        if name.lower() == item_name.lower():
            shop_item = (item_id, name, rarity, price)
            break

    if not shop_item:
        await update.message.reply_text(
            f"❌ Item '{item_name}' tidak ditemukan."
        )
        return

    _, name, rarity, price = shop_item
    total_price = price * qty

    
    # Cek apakah pemain punya cukup gold
    async with aiosqlite.connect("game.db") as db:
        async with db.execute("SELECT gold FROM players WHERE user_id = ?", (user.id,)) as cursor:
            player = await cursor.fetchone()
        
        if not player:
            await update.message.reply_text(
                "Kamu belum terdaftar! Ketik /start dulu."
            )
            return

        gold = player[0]
        if gold < total_price:
            await update.message.reply_text(
                f"💸 Gold tidak cukup! Harga total {total_price}, kamu hanya punya {gold}."
            )
            return

    # ✅ Jika cukup, tampilkan tombol konfirmasi 
    # Buat data sementara untuk callback
    callback_data = f"confirm_buy|{item_name}|{rarity}|{qty}|{price}"

    # Buat tombol konfirmasi
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=callback_data),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_buy")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"🛒 Kamu akan membeli {name} {qty}X seharga total 💰{total_price}.\n"
        "Apakah kamu yakin?",
        reply_markup=reply_markup
    )


# confirm /buy
async def confirm_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # biar tombol berhenti loading

    data = query.data.split("|")
    if len(data) < 5:
        await query.edit_message_text("❌ Terjadi kesalahan pada data konfirmasi.")
        return

    _, item_name, rarity, qty, price = data
    user = query.from_user
    qty = int(qty)
    price = int(price)
    total_price = price * qty

    async with aiosqlite.connect("game.db") as db:
        async with db.execute("SELECT gold FROM players WHERE user_id = ?", (user.id,)) as cursor:
            player = await cursor.fetchone()

        if not player:
            await query.edit_message_text("Kamu belum terdaftar! Ketik /start dulu.")
            return

        gold = player[0]
        if gold < total_price:
            await query.edit_message_text(f"💸 Gold tidak cukup! Kamu punya {gold}, perlu {total_price}.")
            return

        # Kurangi gold
        new_gold = gold - total_price
        await db.execute("UPDATE players SET gold = ? WHERE user_id = ?", (new_gold, user.id))
        await db.commit()

    # Tambahkan item
    for _ in range(qty):
        await add_item(user.id, item_name, rarity)

    await query.edit_message_text(
        f"✅ Pembelian berhasil!\n"
        f"Kamu mendapatkan {item_name} {qty}X  seharga 💰{total_price}.\n"
        f"Gold Kamu: 💰 {gold} >> {new_gold}"
    )


async def cancel_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🚫 Transaksi dibatalkan.")


# /sell_<itemname>_<jumlah>
async def sell_item_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    user = update.effective_user
    message_text = update.message.text.strip()

    # ✅ Cek apakah pemain sudah terdaftar
    data = await get_player(user.id)
    if not data:
        await update.message.reply_text("⚠️ Kamu belum terdaftar! Ketik /start dulu untuk memulai permainan.")
        return

    # Cek format perintah
    if not message_text.startswith("/sell_"):
        return

    try:
        parts = message_text.split("_")
        if len(parts) < 3:
            await update.message.reply_text("Format salah! Contoh: /sell_Potion_5 atau /sell_IronSword_2")
            return

        item_name_raw = "_".join(parts[1:-1])
        qty = int(parts[-1])
        item_name = re.sub(r"([a-z])([A-Z])", r"\1 \2", item_name_raw).replace("_", " ").title()
    
    except Exception:
        await update.message.reply_text("Format salah! Contoh: /sell_Potion_5 atau /sell_IronSword_2")
        return

    if qty <= 0:
        await update.message.reply_text("Jumlah penjualan minimal 1.")
        return

    # 🏪 Ambil daftar harga dari shop
    items = await get_shop_items()
    shop_item = None
    for item_id, name, rarity, price in items:
        if name.lower() == item_name.lower():
            shop_item = (item_id, name, rarity, price)
            break

    if not shop_item:
        await update.message.reply_text(f"❌ Item '{item_name}' tidak dikenali di toko, jadi tidak bisa dijual.")
        return

    _, name, rarity, price = shop_item
    sell_price = int(price * 0.5)  # harga jual = 50% harga beli
    total_price = sell_price * qty


    # 💼 Cek inventory pemain
    async with aiosqlite.connect("game.db") as db:
        async with db.execute(
            "SELECT COUNT(*) FROM inventory WHERE user_id = ? AND item_name = ? AND rarity = ?",
            (user.id, name, rarity)
        ) as cursor:
            owned_qty = (await cursor.fetchone())[0]

        if owned_qty < qty:
            await update.message.reply_text(
                f"❌ Kamu hanya punya {owned_qty}x {name}, tidak cukup untuk dijual {qty}x."
            )
            return

    # 🔘 Tampilkan konfirmasi
    callback_data = f"confirm_sell|{item_name}|{rarity}|{qty}|{sell_price}"
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=callback_data),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_sell")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"💸 Kamu akan menjual {qty}x {item_name} seharga 💰 {total_price} .\nApakah kamu yakin?",
        reply_markup=reply_markup
    )

# confirm /sell
async def confirm_sell_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("|")
    if len(data) < 5:
        await query.edit_message_text("❌ Terjadi kesalahan pada data konfirmasi.")
        return

    _, item_name, rarity, qty, sell_price = data
    user = query.from_user
    qty = int(qty)
    sell_price = int(sell_price)
    total_price = qty * sell_price

    async with aiosqlite.connect("game.db") as db:
        # 🔎  1. Cek apakah user masih punya item
        async with db.execute(
            "SELECT COUNT(*) FROM inventory WHERE user_id = ? AND item_name = ? AND rarity = ?",
            (user.id, item_name, rarity,)
        ) as cursor:
            result = await cursor.fetchone()
        
        owned_qty = result[0] if result else 0

        if owned_qty < qty:
            await query.edit_message_text("⚠️ Kamu tidak memiliki cukup item untuk dijual.")
            return

        # 2. Ambil gold lama untuk ditampilkan
        async with db.execute("SELECT gold FROM players WHERE user_id = ?", (user.id,)) as cursor:
            player = await cursor.fetchone()
            old_gold = player[0] if player else 0

        # 🗑️ 3. Hapus item
        await db.execute(
            "DELETE FROM inventory WHERE id IN (SELECT id FROM inventory WHERE user_id = ? AND item_name = ? AND rarity = ? LIMIT ?)",
            (user.id, item_name, rarity, qty)
        )

        # 💰 4. Tambahkan gold ke pemain
        await db.execute(
            "UPDATE players SET gold = gold + ? WHERE user_id = ?",
            (total_price, user.id)
        )
        
        # 🔁 Simpan perubahan
        await db.commit()

        # 5. Ambil gold baru untuk ditampilkan
        async with db.execute("SELECT gold FROM players WHERE user_id = ?", (user.id,)) as cursor:
            new_gold = (await cursor.fetchone())[0]
        
        
     

    # 📝 6. Tampilkan hasil ke user
    await query.edit_message_text(
        f"✅ Penjualan berhasil!\n"
        f"✅ Kamu menjual {item_name} {qty}X dan mendapatkan 💰{total_price}!\n"
        f"Gold Kamu: 💰 {old_gold} >> {new_gold}\n\n"
        f"Terima kasih sudah berdagang di toko RPG! 🏪"
    )

async def cancel_sell_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🚫 Penjualan dibatalkan.")



# Market antar pemain
async def sell_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    # Pastikan user terdaftar
    player = await get_player(user.id)
    if not player:
        await update.message.reply_text("⚠️ Kamu belum terdaftar! Ketik /start dulu.")
        return

    try:
        parts = text.split("_")
        if len(parts) < 4:
            await update.message.reply_text("Format salah! Gunakan: /sell_<itemname>_<qty>_<harga>")
            return

        item_name = parts[1].replace("-", " ").title()
        qty = int(parts[2])
        price = int(parts[3])
    except Exception:
        await update.message.reply_text("Format salah! Contoh: /sell_Potion_5_100")
        return

    # Cek inventory
    async with aiosqlite.connect("game.db") as db:
        async with db.execute("""
            SELECT COUNT(*) FROM inventory 
            WHERE user_id = ? AND item_name = ?
        """, (user.id, item_name)) as cursor:
            item_count = (await cursor.fetchone())[0]

        if item_count < qty:
            await update.message.reply_text(f"❌ Kamu hanya punya {item_count}x {item_name}, tidak cukup untuk dijual!")
            return

        # Kurangi item dari inventory
        await db.execute("""
            DELETE FROM inventory
            WHERE id IN (
                SELECT id FROM inventory 
                WHERE user_id = ? AND item_name = ?
                LIMIT ?
            )
        """, (user.id, item_name, qty))

        # Tambahkan ke market
        await db.execute("""
            INSERT INTO market (seller_id, item_name, rarity, qty, price)
            VALUES (?, ?, (SELECT rarity FROM inventory WHERE user_id = ? AND item_name = ? LIMIT 1), ?, ?)
        """, (user.id, item_name, user.id, item_name, qty, price))
        await db.commit()

    await update.message.reply_text(
        f"🛒 {qty}x {item_name} berhasil dijual ke market dengan harga 💰 {price} per item!"
    )

# /market
async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    async with aiosqlite.connect("game.db") as db:
        async with db.execute("""
            SELECT id, seller_id, item_name, rarity, qty, price FROM market
        """) as cursor:
            listings = await cursor.fetchall()

    if not listings:
        await update.message.reply_text("📭 Market sedang kosong.")
        return

    text_lines = ["🏦 **Market Antar Pemain** 🏦\nGunakan `/buyfrom_<id>` untuk membeli.\n"]
    for listing_id, seller_id, name, rarity, qty, price in listings:
        seller_tag = f"[{seller_id}]"  # nanti bisa ganti jadi username
        text_lines.append(f"🆔 {listing_id} | {name} ({rarity}) x{qty} — 💰 {price} | Penjual: {seller_tag}")

    await update.message.reply_text("\n".join(text_lines))


# /buyfrom_<id>
async def buyfrom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    try:
        listing_id = int(text.split("_")[1])
    except Exception:
        await update.message.reply_text("Gunakan format: /buyfrom_<id>")
        return

    async with aiosqlite.connect("game.db") as db:
        async with db.execute("SELECT seller_id, item_name, rarity, qty, price FROM market WHERE id = ?", (listing_id,)) as cursor:
            listing = await cursor.fetchone()

        if not listing:
            await update.message.reply_text("❌ Item tidak ditemukan atau sudah terjual.")
            return

        seller_id, item_name, rarity, qty, price = listing
        total_price = qty * price

        # Cek gold pembeli
        async with db.execute("SELECT gold FROM players WHERE user_id = ?", (user.id,)) as cursor:
            buyer_gold = (await cursor.fetchone())[0]

        if buyer_gold < total_price:
            await update.message.reply_text("💸 Gold kamu tidak cukup untuk membeli item ini.")
            return

        # Proses transaksi
        new_gold = buyer_gold - total_price
        await db.execute("UPDATE players SET gold = ? WHERE user_id = ?", (new_gold, user.id))

        # Tambah gold ke penjual
        await db.execute("UPDATE players SET gold = gold + ? WHERE user_id = ?", (total_price, seller_id))

        # Tambahkan item ke pembeli
        for _ in range(qty):
            await add_item(user.id, item_name, rarity)

        # Hapus listing dari market
        await db.execute("DELETE FROM market WHERE id = ?", (listing_id,))
        await db.commit()

    await update.message.reply_text(f"✅ Kamu membeli {qty}x {item_name} ({rarity}) dari pemain lain seharga 💰 {total_price}!")







# Handler untuk tombol teks
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # kalau user sedang memilih class
    
    text = update.message.text
    print(f"Button pressed: {text}")

    if text == "📜 Profile":
        await profile(update, context)
    elif text == "⚔️ Adventure":
        await adventure(update, context)
    elif text == "🔄 Reset":
        await resetme(update, context)
    elif text == "🎒 Inventory":
        await inventory(update, context)
    elif text == "🏪 Shop":
        await shop(update, context)
    elif text == "🏦 Market":
        await market(update, context)
    else:
        await update.message.reply_text("Perintah tidak dikenal. Gunakan tombol yang tersedia.")











# <<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<


# +++++++++++ FUNGSI UTAMA [main()] ++++++++++ #
async def init_database(app):
    # Jalankan create_tables dan seed shop setelah bot siap
    await create_tables(app)
    await seed_shop_items()
    print("Database & Shop sudah siap ✅")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(init_database).build()

    # Command utama
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("resetme", resetme))
    app.add_handler(CommandHandler("adventure", adventure))
    app.add_handler(CommandHandler("inventory", inventory))
    app.add_handler(CommandHandler("shop", shop))
    app.add_handler(CommandHandler("market", market))

    # ReplyKeyboardHandler untuk “🎭 Pilih Karakter”
    app.add_handler(MessageHandler(filters.Regex("^🎭 Pilih Karakter$"), pilih_karakter_handler))

    # Callback untuk pemilihan class
    app.add_handler(CallbackQueryHandler(choose_character_callback, pattern="^class_"))

    # Tombol kembali ke daftar class
    app.add_handler(CallbackQueryHandler(back_to_class_callback, pattern="^back_to_class$"))

    # Tombol memulai quest tutorial setelah masuk Arvendale
    app.add_handler(CallbackQueryHandler(tutorial_quest_start_callback, pattern="^tutorial_quest_start$"))
    app.add_handler(CommandHandler("goto_PadangLatihan", goto_padanglatihan))
    app.add_handler(CallbackQueryHandler(explore_padanglatihan_callback, pattern="^explore_padanglatihan$"))
    app.add_handler(CallbackQueryHandler(fight_monsters_callback, pattern=r"^fight_"))





    # Command khusus format teks
    app.add_handler(MessageHandler(filters.Regex(r"^/buy_"), buy_item_by_name))
    app.add_handler(MessageHandler(filters.Regex(r"^/sell_"), sell_item_by_name))
    app.add_handler(MessageHandler(filters.Regex(r"^/buyfrom_"), buyfrom))

    # Callback tombol konfirmasi
    app.add_handler(CallbackQueryHandler(confirm_buy_callback, pattern="^confirm_buy"))
    app.add_handler(CallbackQueryHandler(cancel_buy_callback, pattern="^cancel_buy$"))
    app.add_handler(CallbackQueryHandler(confirm_sell_callback, pattern="^confirm_sell"))
    app.add_handler(CallbackQueryHandler(cancel_sell_callback, pattern="^cancel_sell$"))

    # Handler tombol menu & pilihan class (satu pintu)
    app.add_handler(CallbackQueryHandler(choose_character_callback, pattern="^choose_character$"))
    app.add_handler(CallbackQueryHandler(next_hero_callback, pattern="^next_hero$"))
    app.add_handler(CallbackQueryHandler(prev_hero_callback, pattern="^prev_hero$"))
    app.add_handler(CallbackQueryHandler(select_hero_callback, pattern="^select_hero"))
    app.add_handler(CallbackQueryHandler(confirm_hero_callback, pattern="^confirm_hero$"))
    app.add_handler(CallbackQueryHandler(cancel_hero_callback, pattern="^cancel_hero$"))


    # Command quest
    app.add_handler(CommandHandler("tutorial", tutorial_quest))



    print("Bot sedang berjalan...")
    app.run_polling()



if __name__ == "__main__":
    main()
