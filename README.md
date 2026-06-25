# 🤖 Ghost Assistant - Discord Bot

Bot asisten Discord dengan fitur lengkap untuk server kamu!

## ✨ Fitur

| Command | Deskripsi |
|---------|-----------|
| `!ping` | Cek latency bot |
| `!info` | Info tentang bot |
| `!serverinfo` | Info tentang server |
| `!avatar [@user]` | Lihat avatar user |
| `!clear [jumlah]` | Hapus pesan (perlu izin) |
| `!say [pesan]` | Bot mengirim pesan |

**Slash Commands:** `/ping`, `/info`, `/avatar`

## 🚀 Setup

### 1. Buat Discord Bot
1. Pergi ke [Discord Developer Portal](https://discord.com/developers/applications)
2. Klik **"New Application"** → Beri nama → Create
3. Pergi ke **"Bot"** → **"Add Bot"**
4. **Reset Token** → Copy token
5. Aktifkan **"Message Content Intent"** di bagian bawah

### 2. Invite Bot ke Server
1. Pergi ke **"OAuth2"** → **"URL Generator"**
2. Pilih Scopes: `bot`, `applications.commands`
3. Pilih Permissions: `Administrator` (atau sesuaikan)
4. Copy URL → Buka di browser → Pilih server

### 3. Setup Lokal
```bash
# Clone/download project
cd asisten-ghost-dc

# Buat virtual environment (opsional)
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy dan edit .env
copy .env.example .env
# Edit .env dengan token bot kamu

# Jalankan bot
python bot.py
```

### 4. Deploy ke Railway
1. Push code ke GitHub
2. Buka [Railway](https://railway.app)
3. **New Project** → **Deploy from GitHub Repo**
4. Pilih repository
5. Set variable: `DISCORD_TOKEN` = token bot kamu
6. Deploy!

## 📁 Struktur File

```
asisten-ghost-dc/
├── bot.py           # Main bot code
├── requirements.txt # Dependencies
├── runtime.txt      # Python version
├── railway.toml     # Railway config
├── .env.example     # Environment template
├── .gitignore       # Git ignore
└── README.md        # Dokumentasi
```

## 🔧 Konfigurasi

| Variable | Deskripsi | Default |
|----------|-----------|---------|
| `DISCORD_TOKEN` | Token bot Discord | (required) |
| `BOT_PREFIX` | Prefix command | `!` |

## ❤️ Made by Ghost
