import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
import asyncio
from datetime import datetime, timedelta
import re
import random
import database as db

# Load environment variables
load_dotenv()

# Bot configuration
TOKEN = os.getenv('DISCORD_TOKEN')
OWNER_ID = os.getenv('OWNER_ID')  # Your Discord User ID for DM logs

# Intents setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Bot instance (no prefix needed for slash-only bot)
bot = commands.Bot(command_prefix="!", intents=intents)


# ==================== EVENTS ====================

@bot.event
async def on_ready():
    """Called when the bot is ready and connected."""
    print(f'[OK] {bot.user.name} is online!')
    print(f'[STATS] Connected to {len(bot.guilds)} server(s)')
    print(f'[ID] Bot ID: {bot.user.id}')
    print('-' * 40)

    # Initialize database
    await db.init_db()

    # Load RPG cogs
    cog_list = [
        'cogs.character',
        'cogs.adventure',
        'cogs.inventory',
        'cogs.shop',
        'cogs.pets',
        'cogs.pvp',
        'cogs.games',
        'cogs.economy',
        'cogs.leaderboard',
        'cogs.voice',
    ]
    for cog in cog_list:
        try:
            await bot.load_extension(cog)
            print(f'[COG] Loaded {cog}')
        except Exception as e:
            print(f'[ERROR] Failed to load {cog}: {e}')

    # Set bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name="/start untuk mulai RPG! ⚔️"
        )
    )

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'[SYNC] Synced {len(synced)} slash command(s)')
    except Exception as e:
        print(f'[ERROR] Failed to sync commands: {e}')


@bot.event
async def on_close():
    """Graceful shutdown."""
    await db.close_db()


@bot.event
async def on_message_delete(message):
    """Log deleted messages to owner's DM."""
    if not OWNER_ID:
        return

    if message.author.bot:
        return

    if not message.content and not message.attachments:
        return

    if not message.guild:
        return

    try:
        owner = await bot.fetch_user(int(OWNER_ID))

        # Try to find who deleted the message from Audit Log
        deleter = None
        try:
            async for entry in message.guild.audit_logs(limit=5, action=discord.AuditLogAction.message_delete):
                if (entry.target.id == message.author.id and 
                    entry.extra.channel.id == message.channel.id):
                    time_diff = (datetime.now(entry.created_at.tzinfo) - entry.created_at).total_seconds()
                    if time_diff < 5:
                        deleter = entry.user
                        break
        except:
            pass

        embed = discord.Embed(
            title="🗑️ Pesan Dihapus",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )

        embed.add_field(
            name="👤 Penulis Pesan",
            value=f"{message.author} ({message.author.id})",
            inline=True
        )

        # Who deleted the message
        if deleter:
            if deleter.id == message.author.id:
                deleted_by = f"🔄 {message.author} (dihapus sendiri)"
            else:
                deleted_by = f"🛡️ {deleter} ({deleter.id})"
        else:
            deleted_by = f"🔄 {message.author} (dihapus sendiri)"

        embed.add_field(name="🗑️ Dihapus Oleh", value=deleted_by, inline=True)
        embed.add_field(name="📍 Channel", value=f"#{message.channel.name}", inline=True)
        embed.add_field(name="🏠 Server", value=message.guild.name, inline=True)

        content = message.content if message.content else "*Tidak ada teks*"
        if len(content) > 1024:
            content = content[:1021] + "..."
        embed.add_field(name="💬 Isi Pesan", value=content, inline=False)

        # Download attachments before they expire
        files = []
        if message.attachments:
            attachments_info = []
            for att in message.attachments:
                try:
                    file_bytes = await att.read()
                    files.append(discord.File(
                        fp=__import__('io').BytesIO(file_bytes),
                        filename=att.filename,
                    ))
                    # If it's an image, show it in embed
                    if att.content_type and att.content_type.startswith("image/") and len(files) == 1:
                        embed.set_image(url=f"attachment://{att.filename}")
                        attachments_info.append(f"🖼️ {att.filename}")
                    else:
                        attachments_info.append(f"📎 {att.filename}")
                except Exception:
                    attachments_info.append(f"❌ {att.filename} (gagal download)")
            embed.add_field(name="📁 Attachments", value="\n".join(attachments_info), inline=False)

        embed.set_thumbnail(url=message.author.display_avatar.url)
        embed.set_footer(text=f"Message ID: {message.id}")

        await owner.send(embed=embed, files=files if files else None)

    except Exception as e:
        print(f"[ERROR] Error sending delete log: {e}")


@bot.event
async def on_bulk_message_delete(messages):
    """Log bulk deleted messages to owner's DM."""
    if not OWNER_ID or not messages:
        return

    first_msg = messages[0]
    if not first_msg.guild:
        return

    try:
        owner = await bot.fetch_user(int(OWNER_ID))

        deleter = None
        try:
            async for entry in first_msg.guild.audit_logs(limit=5, action=discord.AuditLogAction.message_bulk_delete):
                time_diff = (datetime.now(entry.created_at.tzinfo) - entry.created_at).total_seconds()
                if time_diff < 10:
                    deleter = entry.user
                    break
        except:
            pass

        embed = discord.Embed(
            title="🗑️ BULK DELETE",
            description=f"**{len(messages)}** pesan dihapus sekaligus!",
            color=discord.Color.dark_red(),
            timestamp=datetime.now()
        )

        embed.add_field(name="📍 Channel", value=f"#{first_msg.channel.name}", inline=True)
        embed.add_field(name="🏠 Server", value=first_msg.guild.name, inline=True)

        deleted_by = f"🛡️ {deleter} ({deleter.id})" if deleter else "❓ Tidak diketahui"
        embed.add_field(name="🗑️ Dihapus Oleh", value=deleted_by, inline=True)

        msg_list = []
        for i, msg in enumerate(messages[:10], 1):
            content = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
            if content:
                msg_list.append(f"**{i}.** {msg.author.name}: {content}")

        if msg_list:
            remaining = len(messages) - 10
            msg_text = "\n".join(msg_list)
            if remaining > 0:
                msg_text += f"\n\n*...dan {remaining} pesan lainnya*"
            embed.add_field(name="📝 Pesan yang Dihapus", value=msg_text[:1024], inline=False)

        embed.set_footer(text=f"Total: {len(messages)} pesan")
        await owner.send(embed=embed)

    except Exception as e:
        print(f"[ERROR] Error sending bulk delete log: {e}")


@bot.event
async def on_message_edit(before, after):
    """Log edited messages to owner's DM."""
    if not OWNER_ID:
        return

    if before.author.bot:
        return

    if before.content == after.content:
        return

    if not before.guild:
        return

    if not before.content and not after.content:
        return

    try:
        owner = await bot.fetch_user(int(OWNER_ID))

        embed = discord.Embed(
            title="✏️ Pesan Diedit",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )

        embed.add_field(name="👤 Author", value=f"{before.author} ({before.author.id})", inline=True)
        embed.add_field(name="📍 Channel", value=f"#{before.channel.name}", inline=True)
        embed.add_field(name="🏠 Server", value=before.guild.name, inline=True)

        before_content = before.content if before.content else "*Kosong*"
        if len(before_content) > 1024:
            before_content = before_content[:1021] + "..."
        embed.add_field(name="📤 Sebelum", value=before_content, inline=False)

        after_content = after.content if after.content else "*Kosong*"
        if len(after_content) > 1024:
            after_content = after_content[:1021] + "..."
        embed.add_field(name="📥 Sesudah", value=after_content, inline=False)

        embed.add_field(
            name="🔗 Link",
            value=f"[Klik untuk lihat](https://discord.com/channels/{before.guild.id}/{before.channel.id}/{before.id})",
            inline=False
        )

        embed.set_thumbnail(url=before.author.display_avatar.url)
        embed.set_footer(text=f"Message ID: {before.id}")

        await owner.send(embed=embed)

    except Exception as e:
        print(f"[ERROR] Error sending edit log: {e}")


# ==================== MODALS ====================

class SayModal(discord.ui.Modal, title="📝 Kirim Pesan"):
    """Modal for /say command — supports multi-line text input + reply."""

    message = discord.ui.TextInput(
        label="Pesan",
        placeholder="Tulis pesan multi-line di sini...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=2000
    )

    reply_to = discord.ui.TextInput(
        label="Reply ke Message ID (kosongkan jika tidak)",
        placeholder="Klik kanan pesan → Copy Message ID",
        style=discord.TextStyle.short,
        required=False,
        max_length=25
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Pesan terkirim!", ephemeral=True)

        # If reply_to is provided, reply to that message
        if self.reply_to.value and self.reply_to.value.strip():
            try:
                target_msg = await interaction.channel.fetch_message(int(self.reply_to.value.strip()))
                await target_msg.reply(self.message.value)
                return
            except (discord.NotFound, ValueError):
                # Message not found — send normally
                pass

        await interaction.channel.send(self.message.value)


class GiveawayModal(discord.ui.Modal, title="🎁 Buat Giveaway"):
    """Modal for /giveaway — multi-line prize description support."""

    prize = discord.ui.TextInput(
        label="Hadiah",
        placeholder="Contoh:\n🎬 Netflix — 1 Bulan\n🎵 Spotify — 2 Bulan",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1024
    )

    duration = discord.ui.TextInput(
        label="Durasi (contoh: 1h, 12h, 1d, 3d, 7d)",
        placeholder="24h",
        style=discord.TextStyle.short,
        required=False,
        default="24h",
        max_length=10
    )

    winners_count = discord.ui.TextInput(
        label="Jumlah Pemenang",
        placeholder="1",
        style=discord.TextStyle.short,
        required=False,
        default="1",
        max_length=3
    )

    extra_note = discord.ui.TextInput(
        label="Catatan Tambahan (opsional)",
        placeholder="Contoh: Syarat & ketentuan berlaku!",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Parse duration
        dur_text = self.duration.value.strip() if self.duration.value else "24h"
        seconds = parse_duration(dur_text)
        if seconds is None:
            await interaction.response.send_message(
                "❌ Format durasi salah! Gunakan: `1h`, `12h`, `1d`, `3d`, `7d`", ephemeral=True
            )
            return

        # Parse winners
        try:
            winners = int(self.winners_count.value.strip()) if self.winners_count.value else 1
            if winners < 1:
                winners = 1
        except ValueError:
            winners = 1

        end_time = datetime.now() + timedelta(seconds=seconds)
        end_timestamp = int(end_time.timestamp())

        # Build embed
        embed = discord.Embed(
            title="🎁 ✨ 𝗚𝗜𝗩𝗘𝗔𝗪𝗔𝗬 ✨ 🎁",
            color=0xFF6B6B
        )

        embed.add_field(
            name="🏆 𝗛𝗮𝗱𝗶𝗮𝗵",
            value=self.prize.value,
            inline=False
        )

        embed.add_field(
            name="👥 𝗝𝘂𝗺𝗹𝗮𝗵 𝗣𝗲𝗺𝗲𝗻𝗮𝗻𝗴",
            value=f"**{winners}** orang",
            inline=True
        )

        embed.add_field(
            name="⏰ 𝗕𝗲𝗿𝗮𝗸𝗵𝗶𝗿",
            value=f"<t:{end_timestamp}:R> (<t:{end_timestamp}:F>)",
            inline=True
        )

        embed.add_field(
            name="🎯 𝗖𝗮𝗿𝗮 𝗜𝗸𝘂𝘁",
            value="React 🎉 di bawah untuk ikut giveaway!",
            inline=False
        )

        if self.extra_note.value and self.extra_note.value.strip():
            embed.add_field(
                name="📌 𝗖𝗮𝘁𝗮𝘁𝗮𝗻",
                value=self.extra_note.value,
                inline=False
            )

        embed.set_footer(
            text=f"Dibuat oleh {interaction.user.display_name} • Ends at",
            icon_url=interaction.user.display_avatar.url
        )
        embed.timestamp = end_time

        await interaction.response.send_message("✅ Giveaway dibuat!", ephemeral=True)
        giveaway_msg = await interaction.channel.send(embed=embed)
        await giveaway_msg.add_reaction("🎉")


# ==================== HELPERS ====================

def parse_duration(text: str) -> int | None:
    """Parse duration string like '1h', '12h', '1d', '3d', '7d' to seconds."""
    text = text.strip().lower()
    match = re.match(r'^(\d+)\s*(h|d|m)$', text)
    if not match:
        return None
    value = int(match.group(1))
    unit = match.group(2)
    if unit == 'm':
        return value * 60
    elif unit == 'h':
        return value * 3600
    elif unit == 'd':
        return value * 86400
    return None


# ==================== SLASH COMMANDS ====================

@bot.tree.command(name="say", description="Bot mengirim pesan (support multi-line!)")
@app_commands.default_permissions(manage_messages=True)
async def slash_say(interaction: discord.Interaction):
    """Opens a modal for multi-line message input."""
    await interaction.response.send_modal(SayModal())


@bot.tree.command(name="createga", description="Buat giveaway dengan embed keren!")
@app_commands.default_permissions(manage_messages=True)
async def slash_createga(interaction: discord.Interaction):
    """Opens a modal to create a giveaway."""
    await interaction.response.send_modal(GiveawayModal())


@bot.tree.command(name="pickwinner", description="Pilih pemenang dari react di pesan tertentu!")
@app_commands.describe(
    message_id="ID pesan yang ada react-nya (klik kanan pesan → Copy Message ID)",
    emoji="Emoji react yang dihitung (default: 🔥)",
    winners="Jumlah pemenang (default: 1)"
)
@app_commands.default_permissions(manage_messages=True)
async def slash_pickwinner(
    interaction: discord.Interaction,
    message_id: str,
    emoji: str = "🔥",
    winners: int = 1
):
    """Pick random winner(s) from reactions on a specific message."""
    await interaction.response.defer()

    # Fetch the message
    try:
        msg = await interaction.channel.fetch_message(int(message_id))
    except (discord.NotFound, ValueError):
        await interaction.followup.send(
            "❌ Pesan tidak ditemukan! Pastikan Message ID benar dan pesan ada di channel ini.",
            ephemeral=True
        )
        return
    except discord.Forbidden:
        await interaction.followup.send(
            "❌ Bot tidak punya akses ke pesan ini!",
            ephemeral=True
        )
        return

    # Find the matching reaction
    target_reaction = None
    for reaction in msg.reactions:
        if str(reaction.emoji) == emoji:
            target_reaction = reaction
            break

    if not target_reaction:
        await interaction.followup.send(
            f"❌ Tidak ada react {emoji} di pesan itu!",
            ephemeral=True
        )
        return

    # Get users who reacted (exclude bots)
    users = []
    async for user in target_reaction.users():
        if not user.bot:
            users.append(user)

    if not users:
        await interaction.followup.send(
            f"❌ Tidak ada user yang react {emoji} (bot tidak dihitung).",
            ephemeral=True
        )
        return

    # Pick winners
    if winners > len(users):
        winners = len(users)

    chosen = random.sample(users, winners)

    # Build result embed
    embed = discord.Embed(
        title="🎉 ✨ 𝗣𝗘𝗠𝗘𝗡𝗔𝗡𝗚 𝗚𝗜𝗩𝗘𝗔𝗪𝗔𝗬 ✨ 🎉",
        color=0xFFD700
    )

    winner_list = "\n".join([f"🏆 {w.mention} ({w.display_name})" for w in chosen])
    embed.add_field(
        name=f"👑 Pemenang ({len(chosen)} orang)",
        value=winner_list,
        inline=False
    )

    embed.add_field(
        name="📊 Total Peserta",
        value=f"**{len(users)}** orang react {emoji}",
        inline=True
    )

    embed.add_field(
        name="🔗 Pesan Giveaway",
        value=f"[Klik untuk lihat](https://discord.com/channels/{interaction.guild.id}/{interaction.channel.id}/{message_id})",
        inline=True
    )

    embed.set_footer(
        text=f"Dipilih oleh {interaction.user.display_name}",
        icon_url=interaction.user.display_avatar.url
    )
    embed.timestamp = datetime.now()

    await interaction.followup.send(embed=embed)

    # Also mention winners in a separate message for notification
    mentions = " ".join([w.mention for w in chosen])
    await interaction.channel.send(f"🎊 Selamat kepada {mentions}! Kamu menang giveaway! 🎊")


@bot.tree.command(name="reroll", description="Pilih ulang pemenang giveaway!")
@app_commands.describe(
    message_id="ID pesan giveaway (klik kanan → Copy Message ID)",
    emoji="Emoji react yang dihitung (default: 🔥)",
    winners="Jumlah pemenang (default: 1)",
    exclude="User ID yang di-exclude, pisah koma (opsional)"
)
@app_commands.default_permissions(manage_messages=True)
async def slash_reroll(
    interaction: discord.Interaction,
    message_id: str,
    emoji: str = "🔥",
    winners: int = 1,
    exclude: str = ""
):
    """Re-pick winner(s) from reactions, excluding previous winners."""
    await interaction.response.defer()

    # Fetch the message
    try:
        msg = await interaction.channel.fetch_message(int(message_id))
    except (discord.NotFound, ValueError):
        await interaction.followup.send(
            "❌ Pesan tidak ditemukan! Pastikan Message ID benar dan pesan ada di channel ini.",
            ephemeral=True
        )
        return

    # Find the matching reaction
    target_reaction = None
    for reaction in msg.reactions:
        if str(reaction.emoji) == emoji:
            target_reaction = reaction
            break

    if not target_reaction:
        await interaction.followup.send(
            f"❌ Tidak ada react {emoji} di pesan itu!",
            ephemeral=True
        )
        return

    # Parse excluded user IDs
    excluded_ids = set()
    if exclude.strip():
        for uid in exclude.split(","):
            uid = uid.strip()
            if uid.isdigit():
                excluded_ids.add(int(uid))

    # Get users who reacted (exclude bots and excluded users)
    users = []
    async for user in target_reaction.users():
        if not user.bot and user.id not in excluded_ids:
            users.append(user)

    if not users:
        await interaction.followup.send(
            f"❌ Tidak ada user yang tersisa untuk di-reroll!",
            ephemeral=True
        )
        return

    if winners > len(users):
        winners = len(users)

    chosen = random.sample(users, winners)

    # Build result embed
    embed = discord.Embed(
        title="🔄 ✨ 𝗥𝗘𝗥𝗢𝗟𝗟 𝗚𝗜𝗩𝗘𝗔𝗪𝗔𝗬 ✨ 🔄",
        color=0xFF6B6B
    )

    winner_list = "\n".join([f"🏆 {w.mention} ({w.display_name})" for w in chosen])
    embed.add_field(
        name=f"👑 Pemenang Baru ({len(chosen)} orang)",
        value=winner_list,
        inline=False
    )

    embed.add_field(
        name="📊 Peserta Tersisa",
        value=f"**{len(users)}** orang (excluded: {len(excluded_ids)})",
        inline=True
    )

    embed.set_footer(
        text=f"Rerolled oleh {interaction.user.display_name}",
        icon_url=interaction.user.display_avatar.url
    )
    embed.timestamp = datetime.now()

    await interaction.followup.send(embed=embed)

    mentions = " ".join([w.mention for w in chosen])
    await interaction.channel.send(f"🔄 Reroll! Selamat kepada {mentions}! Kamu menang giveaway! 🎊")


# ==================== POLL ====================

POLL_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]


class PollModal(discord.ui.Modal, title="📊 Buat Polling"):
    """Modal for creating a poll."""

    question = discord.ui.TextInput(
        label="Pertanyaan",
        placeholder="Contoh: Mau giveaway apa?",
        style=discord.TextStyle.short,
        required=True,
        max_length=256
    )

    options = discord.ui.TextInput(
        label="Pilihan (1 per baris, maks 5)",
        placeholder="Netflix\nSpotify\nYouTube Premium\nDisney+",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Parse options
        option_list = [o.strip() for o in self.options.value.strip().split("\n") if o.strip()]

        if len(option_list) < 2:
            await interaction.response.send_message(
                "❌ Minimal 2 pilihan!", ephemeral=True
            )
            return

        if len(option_list) > 5:
            option_list = option_list[:5]

        # Build poll embed
        embed = discord.Embed(
            title=f"📊 {self.question.value}",
            color=0x5865F2
        )

        description_lines = []
        for i, option in enumerate(option_list):
            description_lines.append(f"{POLL_EMOJIS[i]}  **{option}**")

        embed.description = "\n\n".join(description_lines)

        embed.set_footer(
            text=f"Poll oleh {interaction.user.display_name} • React untuk vote!",
            icon_url=interaction.user.display_avatar.url
        )
        embed.timestamp = datetime.now()

        await interaction.response.send_message("✅ Poll dibuat!", ephemeral=True)
        poll_msg = await interaction.channel.send(embed=embed)

        # Add reaction emojis
        for i in range(len(option_list)):
            await poll_msg.add_reaction(POLL_EMOJIS[i])


@bot.tree.command(name="poll", description="Buat polling dengan emoji reactions!")
@app_commands.default_permissions(manage_messages=True)
async def slash_poll(interaction: discord.Interaction):
    """Opens a modal to create a poll."""
    await interaction.response.send_modal(PollModal())


@bot.tree.command(name="clear", description="Hapus pesan di channel")
@app_commands.describe(amount="Jumlah pesan yang ingin dihapus (1-100)")
@app_commands.default_permissions(manage_messages=True)
async def slash_clear(interaction: discord.Interaction, amount: int = 5):
    """Clear messages in the channel."""
    if amount < 1 or amount > 100:
        await interaction.response.send_message("❌ Jumlah harus antara 1-100!", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    try:
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"🗑️ Berhasil menghapus **{len(deleted)}** pesan!", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("❌ Bot tidak punya izin untuk menghapus pesan!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


# ==================== HELP ====================

@bot.tree.command(name="help", description="Lihat daftar semua command bot")
async def slash_help(interaction: discord.Interaction):
    """Show all available commands."""
    embed = discord.Embed(
        title="Ghost Assistant \u2014 Command List",
        description="Daftar lengkap command yang tersedia.",
        color=0x5865F2
    )

    embed.add_field(
        name="🎮 RPG — Memulai",
        value=(
            "`/start` \u2014 Buat karakter baru\n"
            "`/profile` \u2014 Lihat profil RPG\n"
            "`/stats` \u2014 Detail stats karakter\n"
            "`/heal` \u2014 Pulihkan HP"
        ),
        inline=True
    )

    embed.add_field(
        name="⚔️ Adventure",
        value=(
            "`/adventure` \u2014 Jelajahi dungeon\n"
            "`/boss` \u2014 Tantang boss\n"
        ),
        inline=True
    )

    embed.add_field(
        name="🎒 Item & Shop",
        value=(
            "`/inventory` \u2014 Lihat inventory\n"
            "`/equip` \u2014 Pasang equipment\n"
            "`/unequip` \u2014 Lepas equipment\n"
            "`/use` \u2014 Pakai consumable\n"
            "`/shop` \u2014 Lihat shop\n"
            "`/buy` \u2014 Beli item\n"
            "`/sell` \u2014 Jual item"
        ),
        inline=True
    )

    embed.add_field(
        name="🐾 Pet",
        value=(
            "`/gacha` \u2014 Gacha pet (100 🪙)\n"
            "`/gacha10` \u2014 10x Gacha (900 🪙)\n"
            "`/pets` \u2014 Lihat pet\n"
            "`/setpet` \u2014 Aktifkan pet\n"
            "`/namepet` \u2014 Beri nama pet\n"
            "`/feedpet` \u2014 Beri makan pet"
        ),
        inline=True
    )

    embed.add_field(
        name="⚔️ PvP",
        value=(
            "`/duel` \u2014 Tantang duel PvP\n"
            "`/pvpstats` \u2014 Lihat stats PvP"
        ),
        inline=True
    )

    embed.add_field(
        name="🎰 Mini-Games",
        value=(
            "`/trivia` \u2014 Quiz trivia\n"
            "`/rps` \u2014 Batu-Kertas-Gunting\n"
            "`/coinflip` \u2014 Lempar koin\n"
            "`/slots` \u2014 Slot machine\n"
            "`/mathquiz` \u2014 Soal matematika\n"
            "`/wordscramble` \u2014 Susun huruf"
        ),
        inline=True
    )

    embed.add_field(
        name="💰 Ekonomi",
        value=(
            "`/daily` \u2014 Hadiah harian\n"
            "`/balance` \u2014 Cek saldo\n"
            "`/give` \u2014 Transfer coins"
        ),
        inline=True
    )

    embed.add_field(
        name="🏆 Leaderboard",
        value=(
            "`/leaderboard` \u2014 Top 10\n"
            "`/rank` \u2014 Posisi rank\n"
            "`/top` \u2014 Quick top 3"
        ),
        inline=True
    )

    embed.add_field(
        name="\u2709\ufe0f  Messaging",
        value=(
            "`/say` \u2014 Kirim pesan multi-line\n"
            "`/clear` \u2014 Hapus pesan di channel"
        ),
        inline=True
    )

    embed.add_field(
        name="✨ Giveaway",
        value=(
            "`/createga` \u2014 Buat giveaway\n"
            "`/pickwinner` \u2014 Pilih pemenang\n"
            "`/reroll` \u2014 Pilih ulang\n"
            "`/poll` \u2014 Buat polling"
        ),
        inline=True
    )

    embed.set_footer(
        text="Ghost Assistant RPG \u2022 v3.0 \u2022 /start untuk mulai!",
        icon_url=bot.user.display_avatar.url
    )

    await interaction.response.send_message(embed=embed)


# ==================== RUN BOT ====================
if __name__ == "__main__":
    if not TOKEN:
        print("[ERROR] DISCORD_TOKEN tidak ditemukan!")
        print("[INFO] Pastikan file .env sudah dibuat dengan benar.")
    else:
        print("[START] Starting Ghost Assistant...")
        bot.run(TOKEN)
