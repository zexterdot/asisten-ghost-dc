"""
cogs/pets.py — Pet gacha, management, naming, feeding
Ghost Assistant RPG
"""

import discord
from discord.ext import commands
from discord import app_commands
import database as db
from game_data import PETS, GACHA_COST, GACHA_10_COST, do_gacha, RARITY_EMOJI
from utils import format_rarity, get_rarity_color, pet_xp_bar
import random


class PetsCog(commands.Cog):
    """Pet gacha and management commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="gacha", description="Gacha pet! (100 🪙 per pull)")
    async def gacha_command(self, interaction: discord.Interaction):
        """Single gacha pull."""
        profile = await db.get_profile(interaction.user.id, interaction.guild.id)
        if profile["coins"] < GACHA_COST:
            await interaction.response.send_message(
                f"❌ Koin tidak cukup! Butuh **{GACHA_COST}** 🪙, kamu punya **{profile['coins']}** 🪙.",
                ephemeral=True,
            )
            return

        await db.add_coins(interaction.user.id, interaction.guild.id, -GACHA_COST)

        # Do gacha
        pet_id = do_gacha()
        pet_data = PETS[pet_id]
        pet_db_id = await db.add_pet(interaction.user.id, interaction.guild.id, pet_id)

        # Build result embed
        rarity = pet_data["rarity"]
        embed = discord.Embed(
            title="🎰 GACHA RESULT!",
            color=get_rarity_color(rarity),
        )

        # Rarity-based effects
        if rarity == "legendary":
            embed.description = "✨✨✨ **LEGENDARY!!!** ✨✨✨"
        elif rarity == "epic":
            embed.description = "🔥🔥 **EPIC!!** 🔥🔥"
        elif rarity == "rare":
            embed.description = "💫 **RARE!** 💫"
        else:
            embed.description = "🎉 Kamu mendapat pet baru!"

        bonus_text = []
        for stat, val in pet_data["bonus"].items():
            if stat == "crit":
                bonus_text.append(f"🎯 Crit +{val:.0%}")
            else:
                emoji_map = {"atk": "⚔️", "def": "🛡️", "hp": "❤️", "spd": "💨"}
                bonus_text.append(f"{emoji_map.get(stat, '📊')} {stat.upper()} +{val}")

        embed.add_field(
            name=f"{pet_data['emoji']} {pet_data['name']}",
            value=f"{format_rarity(rarity)}\n"
                  f"*{pet_data['description']}*\n\n"
                  f"📊 Bonus: {' | '.join(bonus_text)}",
            inline=False,
        )

        if pet_data.get("special"):
            special_names = {
                "auto_revive": "🔄 Auto Revive — Bangkit 1x per battle dengan 30% HP",
                "heal_per_turn": "💚 Heal — Menyembuhkan 10% max HP per giliran",
            }
            embed.add_field(
                name="⭐ Kemampuan Spesial",
                value=special_names.get(pet_data["special"], pet_data["special"]),
                inline=False,
            )

        embed.add_field(
            name="💡 Tips",
            value=f"Gunakan `/setpet {pet_db_id}` untuk mengaktifkan pet ini!\n"
                  f"Gunakan `/namepet {pet_db_id} [nama]` untuk memberi nama.",
            inline=False,
        )

        embed.set_footer(text=f"Pet ID: {pet_db_id} | 🪙 Sisa: {profile['coins'] - GACHA_COST:,}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="gacha10", description="10x Gacha! (900 🪙, diskon 10%)")
    async def gacha10_command(self, interaction: discord.Interaction):
        """10x gacha pull."""
        profile = await db.get_profile(interaction.user.id, interaction.guild.id)
        if profile["coins"] < GACHA_10_COST:
            await interaction.response.send_message(
                f"❌ Koin tidak cukup! Butuh **{GACHA_10_COST}** 🪙, kamu punya **{profile['coins']}** 🪙.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        await db.add_coins(interaction.user.id, interaction.guild.id, -GACHA_10_COST)

        results = []
        best_rarity = "common"
        rarity_order = {"common": 0, "uncommon": 1, "rare": 2, "epic": 3, "legendary": 4}

        for _ in range(10):
            pet_id = do_gacha()
            pet_data = PETS[pet_id]
            pet_db_id = await db.add_pet(interaction.user.id, interaction.guild.id, pet_id)
            results.append((pet_id, pet_data, pet_db_id))

            if rarity_order.get(pet_data["rarity"], 0) > rarity_order.get(best_rarity, 0):
                best_rarity = pet_data["rarity"]

        embed = discord.Embed(
            title="🎰 10x GACHA RESULTS!",
            description=f"💰 Cost: **{GACHA_10_COST}** 🪙 (10% diskon!)",
            color=get_rarity_color(best_rarity),
        )

        result_lines = []
        for pet_id, pet_data, pet_db_id in results:
            rarity_e = RARITY_EMOJI.get(pet_data["rarity"], "⬜")
            result_lines.append(
                f"{rarity_e} {pet_data['emoji']} **{pet_data['name']}** (ID: {pet_db_id})"
            )

        embed.add_field(
            name="🐾 Hasil",
            value="\n".join(result_lines),
            inline=False,
        )

        embed.set_footer(text=f"🪙 Sisa: {profile['coins'] - GACHA_10_COST:,} | /setpet [id] untuk aktifkan")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="pets", description="Lihat semua pet yang kamu miliki")
    async def pets_command(self, interaction: discord.Interaction):
        """View all owned pets."""
        pets = await db.get_pets(interaction.user.id, interaction.guild.id)

        if not pets:
            embed = discord.Embed(
                title="🐾 Pet Collection — Kosong",
                description="Kamu belum punya pet!\n"
                            "Gunakan `/gacha` untuk mendapat pet pertamamu!",
                color=0xE91E63,
            )
            await interaction.response.send_message(embed=embed)
            return

        embed = discord.Embed(
            title=f"🐾 Pet Collection — {interaction.user.display_name}",
            description=f"Total: **{len(pets)}** pet",
            color=0xE91E63,
        )

        for pet in pets[:15]:  # Max 15 pets shown
            pet_data = PETS.get(pet["pet_id"], {})
            name = pet.get("pet_name") or pet_data.get("name", "Unknown")
            rarity_e = RARITY_EMOJI.get(pet_data.get("rarity", "common"), "⬜")
            active_tag = " 🟢 **AKTIF**" if pet["is_active"] else ""
            xp_needed = pet["pet_level"] * 50
            bar = pet_xp_bar(pet["pet_xp"], xp_needed, pet["pet_level"])

            embed.add_field(
                name=f"{rarity_e} {pet_data.get('emoji', '🐾')} {name}{active_tag}",
                value=f"ID: `{pet['id']}` | {bar}",
                inline=True,
            )

        if len(pets) > 15:
            embed.set_footer(text=f"... dan {len(pets) - 15} pet lainnya")
        else:
            embed.set_footer(text="/setpet [id] untuk aktifkan | /namepet [id] [nama] untuk beri nama")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setpet", description="Aktifkan pet untuk ikut battle")
    @app_commands.describe(pet_id="ID pet (lihat di /pets)")
    async def setpet_command(self, interaction: discord.Interaction, pet_id: int):
        """Set active pet."""
        success = await db.set_active_pet(interaction.user.id, interaction.guild.id, pet_id)

        if not success:
            await interaction.response.send_message(
                f"❌ Pet dengan ID `{pet_id}` tidak ditemukan!\nGunakan `/pets` untuk melihat daftar pet.",
                ephemeral=True,
            )
            return

        # Get pet info
        pets = await db.get_pets(interaction.user.id, interaction.guild.id)
        pet = next((p for p in pets if p["id"] == pet_id), None)
        pet_data = PETS.get(pet["pet_id"], {}) if pet else {}
        name = pet.get("pet_name") or pet_data.get("name", "Unknown") if pet else "Unknown"

        embed = discord.Embed(
            title="✅ Pet Diaktifkan!",
            description=f"{pet_data.get('emoji', '🐾')} **{name}** sekarang ikut bertarung bersamamu!",
            color=0xE91E63,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="namepet", description="Beri nama custom untuk pet kamu")
    @app_commands.describe(pet_id="ID pet", nama="Nama baru untuk pet")
    async def namepet_command(self, interaction: discord.Interaction, pet_id: int, nama: str):
        """Name a pet."""
        if len(nama) > 30:
            await interaction.response.send_message("❌ Nama maksimal 30 karakter!", ephemeral=True)
            return

        success = await db.name_pet(pet_id, interaction.user.id, interaction.guild.id, nama)
        if not success:
            await interaction.response.send_message(
                f"❌ Pet dengan ID `{pet_id}` tidak ditemukan!", ephemeral=True
            )
            return

        await interaction.response.send_message(f"✅ Pet `{pet_id}` diberi nama **{nama}**! 🐾")

    @app_commands.command(name="feedpet", description="Beri makan pet aktif (+XP, 20 🪙)")
    async def feedpet_command(self, interaction: discord.Interaction):
        """Feed active pet."""
        active_pet = await db.get_active_pet(interaction.user.id, interaction.guild.id)
        if not active_pet:
            await interaction.response.send_message(
                "❌ Kamu belum punya pet aktif! Gunakan `/setpet` dulu.", ephemeral=True
            )
            return

        feed_cost = 20
        profile = await db.get_profile(interaction.user.id, interaction.guild.id)
        if profile["coins"] < feed_cost:
            await interaction.response.send_message(
                f"❌ Koin tidak cukup! Butuh **{feed_cost}** 🪙.", ephemeral=True
            )
            return

        await db.add_coins(interaction.user.id, interaction.guild.id, -feed_cost)
        pet_xp_gained = random.randint(10, 25)
        new_level, leveled_up = await db.add_pet_xp(active_pet["id"], pet_xp_gained)

        pet_data = PETS.get(active_pet["pet_id"], {})
        name = active_pet.get("pet_name") or pet_data.get("name", "Unknown")

        embed = discord.Embed(
            title=f"🍖 {name} diberi makan!",
            description=f"🐾 +{pet_xp_gained} XP\n💰 -{feed_cost} 🪙",
            color=0xE91E63,
        )

        if leveled_up:
            embed.add_field(
                name="🎉 PET LEVEL UP!",
                value=f"Level **{active_pet['pet_level']}** → **{new_level}**!",
                inline=False,
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(PetsCog(bot))
