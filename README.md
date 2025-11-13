# Eldrathia

Eldrathia adalah bot RPG berbasis [python-telegram-bot] yang menghadirkan
petualangan teks sederhana: pemain dapat memilih karakter, melihat profil,
mengelola inventaris, membeli item, dan menjalani petualangan singkat.

## Menjalankan bot secara lokal

1. Buat virtualenv dan instal dependensi:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install python-telegram-bot==20.8 aiosqlite
   ```

2. Ekspor token bot Telegram Anda:

   ```bash
   export BOT_TOKEN="123456:ABC..."
   ```

3. Jalankan bot:

   ```bash
   python rpg.py
   ```

Bot akan membuat database SQLite `game.db` di direktori kerja dan otomatis
mengisi daftar item toko setiap kali aplikasi dijalankan.

## Struktur utama

- `rpg.py` – titik masuk aplikasi dan seluruh handler Telegram.
- `database.py` – utilitas asinkron untuk membaca/menulis data game.
- `database_utils.py` – dekorator dan fungsi tambahan untuk progress area.
- `data/` – data statis karakter, area, dan monster.
- `battle_system.py` – simulasi pertarungan berbasis teks.

## Pengujian manual

Bot belum dilengkapi suite pengujian otomatis. Setelah menjalankan bot,
Anda dapat menguji alur dasar berikut melalui Telegram:

1. `/start` lalu pilih karakter.
2. Gunakan tombol menu untuk melihat profil, inventaris, serta toko.
3. Jalankan `/adventure` untuk mendapatkan EXP dan gold.
4. Coba `/buy <id> <jumlah>` untuk membeli item.
5. Jalankan `/resetme` untuk menghapus karakter.

[python-telegram-bot]: https://docs.python-telegram-bot.org/
