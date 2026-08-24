"""
cogs/character.py — Character creation, profile, stats, heal
Ghost Assistant RPG
"""

import discord
from discord.ext import commands
from discord import app_commands
import database as db
from game_data import CLASSES, LEVEL_ROLES
from utils import calculate_stats, create_profile_embed, hp_bar, format_coins


class ClassSelectView(discord.ui.View):
    """View with buttons to select character class."""

    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.selected_class = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Ini bukan menu kamu!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Warrior ⚔️", style=discord.ButtonStyle.danger)
    async def warrior_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.select_class(interaction, "warrior")

    @discord.ui.button(label="Mage 🔮", style=discord.ButtonStyle.primary)
    async def mage_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.select_class(interaction, "mage")

    @discord.ui.button(label="Assassin 🗡️", style=discord.ButtonStyle.secondary)
    async def assassin_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.select_class(interaction, "assassin")

    @discord.ui.button(label="Archer 🏹", style=discord.ButtonStyle.success)
    async def archer_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.select_class(interaction, "archer")

    async def select_class(self, interaction: discord.Interaction, class_name: str):
        self.selected_class = class_name
        class_data = CLASSES[class_name]

        # Create character in database
        await db.create_character(
            interaction.user.id, interaction.guild.id,
            class_name, class_data["base_hp"]
        )
        # Also ensure profile exists
        await db.get_profile(interaction.user.id, interaction.guild.id)

        embed = discord.Embed(
            title="✅ Karakter Berhasil Dibuat!",
            description=f"Kamu memilih class **{class_data['emoji']} {class_data['name']}**!",
            color=0x2ECC71,
        )
        embed.add_field(
            name="📋 Stats Awal",
            value=f"❤️ HP: **{class_data['base_hp']}**\n"
                  f"⚔️ ATK: **{class_data['base_atk']}**\n"
                  f"🛡️ DEF: **{class_data['base_def']}**\n"
                  f"💨 SPD: **{class_data['base_spd']}**\n"
                  f"🎯 Crit: **{class_data['base_crit']:.0%}**",
            inline=False,
        )
        embed.add_field(
            name="💡 Langkah Selanjutnya",
            value="🗡️ `/adventure` — Mulai petualangan!\n"
                  "🛒 `/shop` — Beli equipment\n"
                  "📊 `/profile` — Lihat profil kamu",
            inline=False,
        )
        embed.set_footer(text=f"{class_data['description']}")

        # Disable all buttons
        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()


class CharacterCog(commands.Cog):
    """Character management commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="start", description="Buat karakter baru dan mulai petualangan!")
    async def start_command(self, interaction: discord.Interaction):
        """Create a new character."""
        # Check if already has character
        existing = await db.get_character(interaction.user.id, interaction.guild.id)
        if existing:
            await interaction.response.send_message(
                f"❌ Kamu sudah punya karakter **{CLASSES[existing['class_name']]['emoji']} "
                f"{CLASSES[existing['class_name']]['name']}**!\n"
                f"Gunakan `/profile` untuk melihat profil kamu.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="🎮 Buat Karakter Baru",
            description="Pilih class untuk memulai petualangan!\nSetiap class punya kelebihan dan kelemahan masing-masing.",
            color=0x5865F2,
        )

        for class_id, data in CLASSES.items():
            embed.add_field(
                name=f"{data['emoji']} {data['name']}",
                value=f"❤️ HP: {data['base_hp']} | ⚔️ ATK: {data['base_atk']}\n"
                      f"🛡️ DEF: {data['base_def']} | 💨 SPD: {data['base_spd']}\n"
                      f"🎯 Crit: {data['base_crit']:.0%}\n"
                      f"*{data['description']}*",
                inline=True,
            )

        view = ClassSelectView(interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="profile", description="Lihat profil RPG kamu atau player lain")
    @app_commands.describe(user="Player yang ingin dilihat profilnya")
    async def profile_command(self, interaction: discord.Interaction, user: discord.Member = None):
        """View RPG profile."""
        target = user or interaction.user

        if target.bot:
            await interaction.response.send_message("❌ Bot tidak punya profil!", ephemeral=True)
            return

        character = await db.get_character(target.id, interaction.guild.id)
        if not character:
            if target == interaction.user:
                await interaction.response.send_message(
                    "❌ Kamu belum punya karakter! Gunakan `/start` untuk membuat karakter.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    f"❌ **{target.display_name}** belum punya karakter!",
                    ephemeral=True,
                )
            return

        await interaction.response.defer()

        profile = await db.get_profile(target.id, interaction.guild.id)
        equipment = await db.get_equipped_items(target.id, interaction.guild.id)
        active_pet = await db.get_active_pet(target.id, interaction.guild.id)
        stats = calculate_stats(character, equipment, active_pet)
        rank = await db.get_user_rank(target.id, interaction.guild.id)
        total_users = await db.get_total_users(interaction.guild.id)

        # Merge level from profile into character for stats calculation
        character["level"] = profile["level"]

        embed = create_profile_embed(target, profile, character, stats, rank, total_users, active_pet)

        # Add equipment info
        equip_text = ""
        from game_data import ITEMS
        for eq in equipment:
            item_data = ITEMS.get(eq["item_id"], {})
            equip_text += f"{item_data.get('emoji', '❓')} {item_data.get('name', eq['item_id'])} ({item_data.get('type', '?')})\n"

        if equip_text:
            embed.add_field(name="🎒 Equipment", value=equip_text, inline=True)
        else:
            embed.add_field(name="🎒 Equipment", value="*Tidak ada equipment*", inline=True)

        # HP bar
        embed.add_field(
            name="❤️ HP Saat Ini",
            value=hp_bar(character["current_hp"], stats["hp"]),
            inline=False,
        )

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="stats", description="Lihat detail stats karakter kamu")
    async def stats_command(self, interaction: discord.Interaction):
        """View detailed stats breakdown."""
        character = await db.get_character(interaction.user.id, interaction.guild.id)
        if not character:
            await interaction.response.send_message(
                "❌ Kamu belum punya karakter! Gunakan `/start`.", ephemeral=True
            )
            return

        await interaction.response.defer()

        profile = await db.get_profile(interaction.user.id, interaction.guild.id)
        character["level"] = profile["level"]
        equipment = await db.get_equipped_items(interaction.user.id, interaction.guild.id)
        active_pet = await db.get_active_pet(interaction.user.id, interaction.guild.id)

        class_data = CLASSES[character["class_name"]]
        level = profile["level"]

        # Base stats
        base = {
            "hp": class_data["base_hp"] + class_data["level_bonus"]["hp"] * (level - 1),
            "atk": class_data["base_atk"] + class_data["level_bonus"]["atk"] * (level - 1),
            "def": class_data["base_def"] + class_data["level_bonus"]["def"] * (level - 1),
            "spd": class_data["base_spd"] + class_data["level_bonus"]["spd"] * (level - 1),
            "crit": class_data["base_crit"] + class_data["level_bonus"]["crit"] * (level - 1),
        }

        total = calculate_stats(character, equipment, active_pet)

        embed = discord.Embed(
            title=f"📋 Detail Stats — {interaction.user.display_name}",
            description=f"{class_data['emoji']} **{class_data['name']}** Level {level}",
            color=0x5865F2,
        )

        # Format stat comparison
        stat_names = {"hp": "❤️ HP", "atk": "⚔️ ATK", "def": "🛡️ DEF", "spd": "💨 SPD"}
        stats_text = ""
        for key, label in stat_names.items():
            bonus = total[key] - base[key]
            bonus_text = f" (+{bonus})" if bonus > 0 else ""
            stats_text += f"{label}: **{total[key]}**{bonus_text}\n"

        crit_bonus = total["crit"] - base["crit"]
        crit_bonus_text = f" (+{crit_bonus:.0%})" if crit_bonus > 0 else ""
        stats_text += f"🎯 Crit: **{total['crit']:.0%}**{crit_bonus_text}\n"

        embed.add_field(name="📊 Total Stats", value=stats_text, inline=False)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="heal", description="Pulihkan HP karakter ke penuh")
    async def heal_command(self, interaction: discord.Interaction):
        """Heal character to full HP."""
        character = await db.get_character(interaction.user.id, interaction.guild.id)
        if not character:
            await interaction.response.send_message(
                "❌ Kamu belum punya karakter! Gunakan `/start`.", ephemeral=True
            )
            return

        profile = await db.get_profile(interaction.user.id, interaction.guild.id)
        character["level"] = profile["level"]
        equipment = await db.get_equipped_items(interaction.user.id, interaction.guild.id)
        active_pet = await db.get_active_pet(interaction.user.id, interaction.guild.id)
        stats = calculate_stats(character, equipment, active_pet)

        if character["current_hp"] >= stats["hp"]:
            await interaction.response.send_message("❤️ HP kamu sudah penuh!", ephemeral=True)
            return

        heal_cost = 30
        if profile["coins"] < heal_cost:
            await interaction.response.send_message(
                f"❌ Koin tidak cukup! Butuh **{heal_cost}** 🪙, kamu punya **{profile['coins']}** 🪙.",
                ephemeral=True,
            )
            return

        await db.add_coins(interaction.user.id, interaction.guild.id, -heal_cost)
        await db.heal_character(interaction.user.id, interaction.guild.id)
        await db.update_character_hp(interaction.user.id, interaction.guild.id, stats["hp"], stats["hp"])

        embed = discord.Embed(
            title="💚 HP Dipulihkan!",
            description=f"HP kamu sudah penuh!\n"
                        f"{hp_bar(stats['hp'], stats['hp'])}\n\n"
                        f"💰 Biaya: **-{heal_cost}** 🪙",
            color=0x2ECC71,
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(CharacterCog(bot))
