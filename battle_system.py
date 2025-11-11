# =====================================================
# ⚔️ BATTLE SYSTEM — Dunia Eldrathia
# =====================================================
import random
import asyncio

from data.monsters.monsters_rank_F import monsters_rank_F



# ========== Fungsi memilih monster ==========
def get_monster_by_name(name: str):
    """Mengambil data monster dari daftar berdasarkan nama"""
    for monster in monsters_rank_F:
        if monster["name"].lower() == name.lower():
            return monster
    return None


# ========== Sistem Pertarungan ==========
async def start_battle(update, context, player, monster_name: str):
    """
    Melakukan simulasi pertarungan antara player dan monster.
    Digunakan oleh Quest Elaine, dungeon, atau area farming.
    """
    monster = get_monster_by_name(monster_name)
    if not monster:
        await update.message.reply_text("❌ Monster tidak ditemukan di database!")
        return

    # Ambil data dasar player
    _, username, first_name, class_name, level, exp, gold, max_exp, current_kingdom, location, story_progress = player

    # Ambil statistik dasar karakter dari class-nya (sementara diatur manual sederhana)
    base_stats = {
        "Fighter": {"hp": 120, "atk": 18, "def": 10},
        "Mage": {"hp": 90, "atk": 22, "def": 7},
        "Paladin": {"hp": 140, "atk": 15, "def": 14},
        "Tank": {"hp": 180, "atk": 12, "def": 20},
        "Assassin": {"hp": 100, "atk": 24, "def": 8},
        "Archer": {"hp": 110, "atk": 21, "def": 9},
    }

    stats = base_stats.get(class_name, {"hp": 100, "atk": 15, "def": 8})

    player_hp = stats["hp"] + (level * 10)
    player_atk = stats["atk"] + (level * 2)
    player_def = stats["def"] + (level * 1)

    monster_hp = monster["hp"]
    monster_atk = monster["atk"]
    monster_def = monster["def"]

    battle_log = [
        f"🔥 *Pertarungan Dimulai!*",
        f"Kau melawan *{monster['name']}* (HP: {monster_hp})!",
        "",
    ]

    await update.message.reply_text("\n".join(battle_log), parse_mode="Markdown")
    await asyncio.sleep(1)

    # ======== Simulasi Pertempuran ========
    while monster_hp > 0 and player_hp > 0:
        # Pemain menyerang
        damage_to_monster = max(1, random.randint(player_atk - 3, player_atk + 3) - monster_def // 8)
        monster_hp -= damage_to_monster
        await update.message.reply_text(f"🗡️ Kamu menyerang {monster['name']} dan memberikan *{damage_to_monster} dmg!*", parse_mode="Markdown")

        if monster_hp <= 0:
            battle_log.append(f"💥 {monster['name']} dikalahkan!")
            break

        await asyncio.sleep(1)

        # Monster menyerang balik
        damage_to_player = max(1, random.randint(monster_atk - 3, monster_atk + 3) - player_def // 8)
        player_hp -= damage_to_player
        await update.message.reply_text(f"👾 {monster['name']} menyerang balik dan memberikan *{damage_to_player} dmg!*", parse_mode="Markdown")

        await asyncio.sleep(1)

    # ======== Hasil Pertarungan ========
    if player_hp > 0:
        exp_gain = monster["exp"]
        gold_gain = monster["gold_drop"]
        await update.message.reply_text(
            f"🏆 *Kemenangan!*\n✨ +{exp_gain} EXP  💰 +{gold_gain} Gold",
            parse_mode="Markdown",
        )
        return {"win": True, "exp": exp_gain, "gold": gold_gain}

    else:
        await update.message.reply_text("💀 Kamu dikalahkan oleh monster... Cobalah lagi setelah memulihkan diri.")
        return {"win": False, "exp": 0, "gold": 0}
