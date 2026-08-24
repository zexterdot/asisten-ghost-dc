"""
cogs/leaderboard.py — Leaderboard, rankings, top players
Ghost Assistant RPG
"""

import discord
from discord.ext import commands
from discord import app_commands
import database as db
from game_data import CLASSES, get_pvp_rank
from utils import format_coins


MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}


class LeaderboardView(discord.ui.View):
    """Paginated leaderboard with category tabs."""

    def __init__(self, user_id: int, guild: discord.Guild, pages: dict, current_cat: str = "xp"):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.guild = guild
        self.pages = pages
        self.current_cat = current_cat
        self.update_styles()

    def update_styles(self):
        for child in self.children:
            if hasattr(child, "custom_id") and child.custom_id:
                if child.custom_id == f"lb_{self.current_cat}":
                    child.style = discord.ButtonStyle.primary
                else:
                    child.style = discord.ButtonStyle.secondary

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True  # Anyone can navigate leaderboard

    @discord.ui.button(label="⭐ XP", custom_id="lb_xp", style=discord.ButtonStyle.primary)
    async def xp_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_cat = "xp"
        self.update_styles()
        await interaction.response.edit_message(embed=self.pages["xp"], view=self)

    @discord.ui.button(label="🪙 Coins", custom_id="lb_coins", style=discord.ButtonStyle.secondary)
    async def coins_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_cat = "coins"
        self.update_styles()
        await interaction.response.edit_message(embed=self.pages["coins"], view=self)

    @discord.ui.button(label="⚔️ PvP", custom_id="lb_pvp", style=discord.ButtonStyle.secondary)
    async def pvp_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_cat = "pvp"
        self.update_styles()
        await interaction.response.edit_message(embed=self.pages["pvp"], view=self)

    @discord.ui.button(label="🏔️ Floor", custom_id="lb_floor", style=discord.ButtonStyle.secondary)
    async def floor_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_cat = "floor"
        self.update_styles()
        await interaction.response.edit_message(embed=self.pages["floor"], view=self)

    @discord.ui.button(label="🎮 Games", custom_id="lb_games", style=discord.ButtonStyle.secondary)
    async def games_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_cat = "games"
        self.update_styles()
        await interaction.response.edit_message(embed=self.pages["games"], view=self)


class LeaderboardCog(commands.Cog):
    """Leaderboard and ranking commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def build_leaderboard_pages(self, guild: discord.Guild) -> dict:
        """Build all leaderboard page embeds."""
        pages = {}

        # XP Leaderboard
        xp_data = await db.get_leaderboard(guild.id, "xp", 10)
        embed = discord.Embed(
            title="🏆 Leaderboard — ⭐ XP & Level",
            color=0xFFD700,
        )
        if xp_data:
            lines = []
            for i, entry in enumerate(xp_data, 1):
                medal = MEDALS.get(i, f"**{i}.**")
                member = guild.get_member(entry["user_id"])
                name = member.display_name if member else f"User#{entry['user_id']}"
                lines.append(f"{medal} **{name}** — Lv.{entry['level']} | {entry['xp']:,} XP")
            embed.description = "\n".join(lines)
        else:
            embed.description = "*Belum ada data*"
        embed.set_footer(text=f"Server: {guild.name}")
        pages["xp"] = embed

        # Coins Leaderboard
        coins_data = await db.get_leaderboard(guild.id, "coins", 10)
        embed = discord.Embed(
            title="🏆 Leaderboard — 🪙 Terkaya",
            color=0xFFD700,
        )
        if coins_data:
            lines = []
            for i, entry in enumerate(coins_data, 1):
                medal = MEDALS.get(i, f"**{i}.**")
                member = guild.get_member(entry["user_id"])
                name = member.display_name if member else f"User#{entry['user_id']}"
                lines.append(f"{medal} **{name}** — 🪙 {entry['coins']:,}")
            embed.description = "\n".join(lines)
        else:
            embed.description = "*Belum ada data*"
        embed.set_footer(text=f"Server: {guild.name}")
        pages["coins"] = embed

        # PvP Leaderboard
        pvp_data = await db.get_pvp_leaderboard(guild.id, 10)
        embed = discord.Embed(
            title="🏆 Leaderboard — ⚔️ PvP Arena",
            color=0xFFD700,
        )
        if pvp_data:
            lines = []
            for i, entry in enumerate(pvp_data, 1):
                medal = MEDALS.get(i, f"**{i}.**")
                member = guild.get_member(entry["user_id"])
                name = member.display_name if member else f"User#{entry['user_id']}"
                rank_name, rank_emoji = get_pvp_rank(entry["elo"])
                total = entry["pvp_wins"] + entry["pvp_losses"]
                wr = (entry["pvp_wins"] / total * 100) if total > 0 else 0
                lines.append(f"{medal} **{name}** — {rank_emoji} {entry['elo']} ELO ({wr:.0f}% WR)")
            embed.description = "\n".join(lines)
        else:
            embed.description = "*Belum ada data PvP*"
        embed.set_footer(text=f"Server: {guild.name}")
        pages["pvp"] = embed

        # Floor Leaderboard
        floor_data = await db.get_floor_leaderboard(guild.id, 10)
        embed = discord.Embed(
            title="🏆 Leaderboard — 🏔️ Dungeon Floor",
            color=0xFFD700,
        )
        if floor_data:
            lines = []
            for i, entry in enumerate(floor_data, 1):
                medal = MEDALS.get(i, f"**{i}.**")
                member = guild.get_member(entry["user_id"])
                name = member.display_name if member else f"User#{entry['user_id']}"
                class_data = CLASSES.get(entry["class_name"], {})
                class_emoji = class_data.get("emoji", "❓")
                lines.append(f"{medal} **{name}** — {class_emoji} Floor {entry['floor_level']}")
            embed.description = "\n".join(lines)
        else:
            embed.description = "*Belum ada data*"
        embed.set_footer(text=f"Server: {guild.name}")
        pages["floor"] = embed

        # Games Leaderboard
        games_data = await db.get_leaderboard(guild.id, "games", 10)
        embed = discord.Embed(
            title="🏆 Leaderboard — 🎮 Gamer Tergiat",
            color=0xFFD700,
        )
        if games_data:
            lines = []
            for i, entry in enumerate(games_data, 1):
                medal = MEDALS.get(i, f"**{i}.**")
                member = guild.get_member(entry["user_id"])
                name = member.display_name if member else f"User#{entry['user_id']}"
                wr = (entry["games_won"] / entry["total_games"] * 100) if entry["total_games"] > 0 else 0
                lines.append(f"{medal} **{name}** — {entry['total_games']} games ({wr:.0f}% WR)")
            embed.description = "\n".join(lines)
        else:
            embed.description = "*Belum ada data*"
        embed.set_footer(text=f"Server: {guild.name}")
        pages["games"] = embed

        return pages

    @app_commands.command(name="leaderboard", description="Lihat leaderboard server!")
    async def leaderboard_command(self, interaction: discord.Interaction):
        """View server leaderboard."""
        await interaction.response.defer()

        pages = await self.build_leaderboard_pages(interaction.guild)
        view = LeaderboardView(interaction.user.id, interaction.guild, pages)
        await interaction.followup.send(embed=pages["xp"], view=view)

    @app_commands.command(name="rank", description="Lihat posisi rank kamu di server")
    @app_commands.describe(user="Player yang ingin dilihat")
    async def rank_command(self, interaction: discord.Interaction, user: discord.Member = None):
        """View user rank."""
        target = user or interaction.user
        if target.bot:
            await interaction.response.send_message("❌ Bot tidak punya rank!", ephemeral=True)
            return

        profile = await db.get_profile(target.id, interaction.guild.id)
        xp_rank = await db.get_user_rank(target.id, interaction.guild.id, "xp")
        coins_rank = await db.get_user_rank(target.id, interaction.guild.id, "coins")
        total = await db.get_total_users(interaction.guild.id)

        character = await db.get_character(target.id, interaction.guild.id)
        pvp = await db.get_pvp_stats(target.id, interaction.guild.id)
        pvp_rank_name, pvp_rank_emoji = get_pvp_rank(pvp["elo"])

        embed = discord.Embed(
            title=f"📊 Rank — {target.display_name}",
            color=0xFFD700,
        )

        embed.add_field(
            name="⭐ XP Rank",
            value=f"#{xp_rank}/{total}\n"
                  f"Level **{profile['level']}** ({profile['xp']:,} XP)",
            inline=True,
        )
        embed.add_field(
            name="🪙 Wealth Rank",
            value=f"#{coins_rank}/{total}\n"
                  f"**{profile['coins']:,}** Coins",
            inline=True,
        )
        embed.add_field(
            name="⚔️ PvP Rank",
            value=f"{pvp_rank_emoji} **{pvp_rank_name}**\n"
                  f"ELO: **{pvp['elo']}**",
            inline=True,
        )

        if character:
            embed.add_field(
                name="🏔️ Dungeon",
                value=f"Floor **{character['floor_level']}**",
                inline=True,
            )

        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="top", description="Quick view: top 3 di setiap kategori")
    async def top_command(self, interaction: discord.Interaction):
        """Quick top 3 view."""
        await interaction.response.defer()

        embed = discord.Embed(
            title=f"👑 Top 3 — {interaction.guild.name}",
            color=0xFFD700,
        )

        # Top 3 XP
        xp_data = await db.get_leaderboard(interaction.guild.id, "xp", 3)
        if xp_data:
            lines = []
            for i, e in enumerate(xp_data, 1):
                m = interaction.guild.get_member(e["user_id"])
                n = m.display_name if m else f"User#{e['user_id']}"
                lines.append(f"{MEDALS.get(i, '')} {n} — Lv.{e['level']}")
            embed.add_field(name="⭐ Level Tertinggi", value="\n".join(lines), inline=True)

        # Top 3 Coins
        coins_data = await db.get_leaderboard(interaction.guild.id, "coins", 3)
        if coins_data:
            lines = []
            for i, e in enumerate(coins_data, 1):
                m = interaction.guild.get_member(e["user_id"])
                n = m.display_name if m else f"User#{e['user_id']}"
                lines.append(f"{MEDALS.get(i, '')} {n} — 🪙 {e['coins']:,}")
            embed.add_field(name="🪙 Terkaya", value="\n".join(lines), inline=True)

        # Top 3 PvP
        pvp_data = await db.get_pvp_leaderboard(interaction.guild.id, 3)
        if pvp_data:
            lines = []
            for i, e in enumerate(pvp_data, 1):
                m = interaction.guild.get_member(e["user_id"])
                n = m.display_name if m else f"User#{e['user_id']}"
                _, emoji = get_pvp_rank(e["elo"])
                lines.append(f"{MEDALS.get(i, '')} {n} — {emoji} {e['elo']}")
            embed.add_field(name="⚔️ PvP Terkuat", value="\n".join(lines), inline=True)

        embed.set_footer(text="/leaderboard untuk detail lengkap")
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(LeaderboardCog(bot))
