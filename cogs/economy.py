"""
cogs/economy.py — XP from chat, daily rewards, balance, transfers
Ghost Assistant RPG
"""

import discord
from discord.ext import commands
from discord import app_commands
import database as db
from game_data import LEVEL_ROLES
from utils import format_coins, xp_bar
import random
from datetime import datetime, timezone


XP_COOLDOWN_SECONDS = 60  # 1 minute cooldown for chat XP


class EconomyCog(commands.Cog):
    """Economy and XP from chat system."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # In-memory cooldown tracker (user_id -> last_xp_time)
        self._xp_cooldowns = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Award XP for chatting (with cooldown)."""
        # Ignore bots, DMs, and commands
        if message.author.bot or not message.guild:
            return
        if message.content.startswith(("!", "/")):
            return

        user_id = message.author.id
        guild_id = message.guild.id
        now = datetime.now(timezone.utc)

        # Check in-memory cooldown
        key = f"{user_id}_{guild_id}"
        last_xp = self._xp_cooldowns.get(key)
        if last_xp:
            elapsed = (now - last_xp).total_seconds()
            if elapsed < XP_COOLDOWN_SECONDS:
                return

        self._xp_cooldowns[key] = now

        # Check if user has a character (only award XP to players)
        character = await db.get_character(user_id, guild_id)
        if not character:
            return

        # Award 1-3 random XP
        xp_amount = random.randint(1, 3)
        profile = await db.get_profile(user_id, guild_id)
        old_level = profile["level"]

        new_level, leveled_up, levels_gained = await db.add_xp(user_id, guild_id, xp_amount)
        await db.update_last_xp_gain(user_id, guild_id)

        # Level up notification
        if leveled_up:
            embed = discord.Embed(
                title="🎊 LEVEL UP!",
                description=f"Selamat {message.author.mention}!\n"
                            f"Level **{old_level}** → **{new_level}**!",
                color=0xFFD700,
            )

            # Check for role rewards
            for req_level, role_name in LEVEL_ROLES.items():
                if old_level < req_level <= new_level:
                    role = discord.utils.get(message.guild.roles, name=role_name)
                    if role:
                        try:
                            await message.author.add_roles(role)
                            embed.add_field(
                                name="🏅 Role Baru!",
                                value=f"Mendapat role **{role_name}**!",
                                inline=False,
                            )
                        except discord.Forbidden:
                            pass

            embed.set_thumbnail(url=message.author.display_avatar.url)
            embed.set_footer(text="Terus aktif untuk naik level!")

            try:
                await message.channel.send(embed=embed, delete_after=15)
            except discord.Forbidden:
                pass

    @app_commands.command(name="daily", description="Klaim hadiah harian! (1x per hari)")
    async def daily_command(self, interaction: discord.Interaction):
        """Claim daily reward."""
        # Ensure profile exists
        await db.get_profile(interaction.user.id, interaction.guild.id)

        success, coins, streak, already_claimed = await db.claim_daily(
            interaction.user.id, interaction.guild.id
        )

        if already_claimed:
            embed = discord.Embed(
                title="📅 Daily Reward",
                description="❌ Kamu sudah klaim daily hari ini!\nCoba lagi besok.",
                color=0xE74C3C,
            )
            embed.add_field(name="🔥 Streak Saat Ini", value=f"**{streak}** hari", inline=True)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        streak_bonus = min(streak * 10, 200)
        embed = discord.Embed(
            title="📅 Daily Reward Diklaim!",
            description=f"🪙 **+{coins}** Coins!\n"
                        f"  ├ Base: 50 🪙\n"
                        f"  └ Streak Bonus: +{streak_bonus} 🪙",
            color=0x1ABC9C,
        )
        embed.add_field(name="🔥 Streak", value=f"**{streak}** hari berturut-turut!", inline=True)

        if streak >= 7:
            embed.add_field(
                name="🏆 Streak Bonus",
                value="Streak 7+ hari! Bonus maksimal aktif!",
                inline=True,
            )

        embed.set_footer(text="Login setiap hari untuk menjaga streak!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="balance", description="Cek saldo coins kamu atau player lain")
    @app_commands.describe(user="Player yang ingin dicek")
    async def balance_command(self, interaction: discord.Interaction, user: discord.Member = None):
        """Check coin balance."""
        target = user or interaction.user
        if target.bot:
            await interaction.response.send_message("❌ Bot tidak punya saldo!", ephemeral=True)
            return

        profile = await db.get_profile(target.id, interaction.guild.id)

        embed = discord.Embed(
            title=f"💰 Saldo — {target.display_name}",
            description=f"🪙 **{profile['coins']:,}** Coins",
            color=0x1ABC9C,
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="give", description="Transfer coins ke player lain")
    @app_commands.describe(user="Player tujuan", jumlah="Jumlah coins")
    async def give_command(self, interaction: discord.Interaction, user: discord.Member, jumlah: int):
        """Transfer coins to another player."""
        if user.bot or user.id == interaction.user.id:
            await interaction.response.send_message("❌ Tidak bisa transfer ke diri sendiri atau bot!", ephemeral=True)
            return

        if jumlah < 1:
            await interaction.response.send_message("❌ Jumlah minimal 1!", ephemeral=True)
            return

        # Check level requirement
        profile = await db.get_profile(interaction.user.id, interaction.guild.id)
        if profile["level"] < 5:
            await interaction.response.send_message(
                f"❌ Kamu harus Level 5+ untuk transfer! Kamu Level {profile['level']}.",
                ephemeral=True,
            )
            return

        if profile["coins"] < jumlah:
            await interaction.response.send_message(
                f"❌ Koin tidak cukup! Kamu punya **{profile['coins']:,}** 🪙.",
                ephemeral=True,
            )
            return

        await db.add_coins(interaction.user.id, interaction.guild.id, -jumlah)
        await db.add_coins(user.id, interaction.guild.id, jumlah)

        embed = discord.Embed(
            title="💸 Transfer Berhasil!",
            description=f"{interaction.user.mention} → {user.mention}\n"
                        f"🪙 **{jumlah:,}** Coins",
            color=0x1ABC9C,
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(EconomyCog(bot))
