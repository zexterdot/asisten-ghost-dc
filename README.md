# 🤖⚔️ Ghost Assistant RPG — Discord Bot

Bot Discord dengan **RPG ecosystem lengkap** untuk meningkatkan aktivitas member di server! Dilengkapi dungeon adventure, pet gacha, PvP arena, mini-games, dan leaderboard.

## ✨ Fitur Utama

### 🎮 RPG System
| Fitur | Deskripsi |
|-------|-----------|
| **Character & Class** | 4 class (Warrior, Mage, Assassin, Archer) dengan stats unik |
| **Dungeon Adventure** | 50 floor, 30+ monster, 10 boss, turn-based battle |
| **Inventory & Equipment** | Weapon, Armor, Accessory dengan 5 rarity tier |
| **Shop** | Beli/jual item, potion, equipment |
| **Pet Gacha** | 13 pet dari Common sampai Legendary, bisa level up |
| **PvP Arena** | Duel antar player dengan ELO ranking system |

### 🎰 Mini-Games
| Game | Deskripsi |
|------|-----------|
| `/trivia` | Quiz pengetahuan umum |
| `/rps` | Batu-Kertas-Gunting |
| `/coinflip` | Tebak koin |
| `/slots` | Slot machine |
| `/mathquiz` | Soal matematika cepat |
| `/wordscramble` | Susun huruf acak |

### 📊 Economy & Leaderboard
- **XP dari chat** — Aktif ngobrol = naik level!
- **Daily reward** dengan streak bonus
- **Leaderboard** 5 kategori (XP, Coins, PvP, Floor, Games)
- **Auto role** di milestone level (5, 10, 20, 50)

### 📝 Utility (Fitur Lama)
| Command | Deskripsi |
|---------|-----------|
| `/say` | Kirim pesan multi-line |
| `/clear` | Hapus pesan di channel |
| `/createga` | Buat giveaway |
| `/pickwinner` | Pilih pemenang giveaway |
| `/reroll` | Pilih ulang pemenang |
| `/poll` | Buat polling |

---

## 📋 Daftar Semua Slash Commands

### 🧙 Character
| Command | Deskripsi |
|---------|-----------|
| `/start` | Buat karakter baru dan pilih class |
| `/profile [@user]` | Lihat profil RPG lengkap |
| `/stats` | Detail stats karakter |
| `/heal` | Pulihkan HP (30 🪙) |

### ⚔️ Adventure
| Command | Deskripsi |
|---------|-----------|
| `/adventure` | Jelajahi dungeon, lawan monster |
| `/boss` | Tantang boss (setiap 5 floor) |

### 🎒 Inventory
| Command | Deskripsi |
|---------|-----------|
| `/inventory` | Lihat semua item |
| `/equip [item]` | Pasang equipment |
| `/unequip [slot]` | Lepas equipment |
| `/use [item]` | Pakai consumable |

### 🛒 Shop
| Command | Deskripsi |
|---------|-----------|
| `/shop` | Lihat daftar item di shop |
| `/buy [item] [jumlah]` | Beli item |
| `/sell [item] [jumlah]` | Jual item |

### 🐾 Pet
| Command | Deskripsi |
|---------|-----------|
| `/gacha` | Gacha pet (100 🪙) |
| `/gacha10` | 10x Gacha (900 🪙, diskon!) |
| `/pets` | Lihat koleksi pet |
| `/setpet [id]` | Aktifkan pet untuk battle |
| `/namepet [id] [nama]` | Beri nama custom |
| `/feedpet` | Beri makan pet (+XP) |

### ⚔️ PvP
| Command | Deskripsi |
|---------|-----------|
| `/duel @user` | Tantang player ke duel |
| `/pvpstats [@user]` | Lihat stats PvP & ELO |

### 💰 Economy
| Command | Deskripsi |
|---------|-----------|
| `/daily` | Klaim hadiah harian |
| `/balance [@user]` | Cek saldo coins |
| `/give @user [jumlah]` | Transfer coins |

### 🏆 Leaderboard
| Command | Deskripsi |
|---------|-----------|
| `/leaderboard` | Top 10 (5 kategori) |
| `/rank [@user]` | Posisi rank di server |
| `/top` | Quick top 3 |

---

## 🚀 Setup

### 1. Buat Discord Bot
1. Pergi ke [Discord Developer Portal](https://discord.com/developers/applications)
2. Klik **"New Application"** → Beri nama → Create
3. Pergi ke **"Bot"** → **"Add Bot"**
4. **Reset Token** → Copy token
5. Aktifkan **"Message Content Intent"** dan **"Server Members Intent"**

### 2. Invite Bot ke Server
1. Pergi ke **"OAuth2"** → **"URL Generator"**
2. Pilih Scopes: `bot`, `applications.commands`
3. Pilih Permissions: `Administrator`
4. Copy URL → Buka di browser → Pilih server

### 3. Setup Database (Railway)
1. Buka [Railway](https://railway.app)
2. Buat **PostgreSQL** add-on di project kamu
3. Copy **DATABASE_URL** dari PostgreSQL settings

### 4. Setup Lokal
```bash
# Clone project
cd asisten-ghost-dc

# Install dependencies
pip install -r requirements.txt

# Copy dan edit .env
copy .env.example .env
# Edit .env:
#   DISCORD_TOKEN=token_bot_kamu
#   OWNER_ID=id_discord_kamu
#   DATABASE_URL=postgresql://... (dari Railway)

# Jalankan bot
python bot.py
```

### 5. Deploy ke Railway
1. Push code ke GitHub
2. Buka [Railway](https://railway.app)
3. **New Project** → **Deploy from GitHub Repo**
4. Pilih repository
5. Set environment variables:
   - `DISCORD_TOKEN` = token bot
   - `OWNER_ID` = Discord user ID kamu
   - `DATABASE_URL` = URL dari PostgreSQL add-on
6. Deploy!

---

## 📁 Struktur File

```
asisten-ghost-dc/
├── bot.py              # Main bot entry point
├── database.py         # PostgreSQL database manager (asyncpg)
├── game_data.py        # Semua data game (classes, monsters, items, pets)
├── utils.py            # Helper functions (progress bar, embed builder)
├── cogs/
│   ├── __init__.py     # Package init
│   ├── character.py    # Character creation, profile, stats
│   ├── adventure.py    # Dungeon exploration, battle engine
│   ├── inventory.py    # Inventory management
│   ├── shop.py         # Shop buy/sell
│   ├── pets.py         # Pet gacha & management
│   ├── pvp.py          # PvP duel & ELO ranking
│   ├── games.py        # Mini-games (trivia, RPS, slots, etc)
│   ├── economy.py      # XP from chat, daily, balance
│   └── leaderboard.py  # Leaderboard & rankings
├── images/             # Boss & class images (optional)
├── requirements.txt    # Dependencies
├── runtime.txt         # Python version
├── railway.toml        # Railway config
├── .env.example        # Environment template
└── .gitignore          # Git ignore
```

## 🔧 Konfigurasi

| Variable | Deskripsi | Required |
|----------|-----------|----------|
| `DISCORD_TOKEN` | Token bot Discord | ✅ |
| `OWNER_ID` | Discord User ID untuk log | ✅ |
| `DATABASE_URL` | PostgreSQL connection URL | ✅ |

## ⚙️ Tech Stack

- **Python 3.11+** — Runtime
- **discord.py 2.3+** — Discord API wrapper
- **asyncpg** — Async PostgreSQL driver
- **Railway** — Hosting & PostgreSQL

## 🎮 Game Balance

| Aspek | Detail |
|-------|--------|
| **Level Formula** | XP needed = level × 100 |
| **Chat XP** | 1-3 XP per pesan (60s cooldown) |
| **Daily Reward** | 50 + streak × 10 coins (max 250) |
| **Gacha Rate** | Common 80%, Uncommon 16%, Rare 3.2%, Epic 0.5%, Legendary 0.1% |
| **PvP ELO** | K-factor = 32, start 1000 |
| **Dungeon** | 50 floors, boss setiap 5 floor |

---

## ❤️ Made by Ghost
