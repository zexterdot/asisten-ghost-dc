"""
cogs/pvp.py — PvP duel system with ELO ranking
Ghost Assistant RPG
"""

import discord
from discord.ext import commands
from discord import app_commands
import database as db
from game_data import CLASSES, get_pvp_rank
from utils import calculate_stats, progress_bar
import random
import math


class DuelRequestView(discord.ui.View):
    """View for accepting/declining duel requests."""

    def __init__(self, challenger: discord.Member, defender: discord.Member, cog):
        super().__init__(timeout=60)
        self.challenger = challenger
        self.defender = defender
        self.cog = cog

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.defender.id:
            await interaction.response.send_message("❌ Tantangan ini bukan untukmu!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Terima ⚔️", style=discord.ButtonStyle.success)
    async def accept_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.start_duel(interaction, self.challenger, self.defender)
        self.stop()

    @discord.ui.button(label="Tolak ❌", style=discord.ButtonStyle.danger)
    async def decline_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="❌ Duel Ditolak",
            description=f"**{self.defender.display_name}** menolak tantangan dari **{self.challenger.display_name}**.",
            color=0xE74C3C,
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()


class DuelBattleView(discord.ui.View):
    """Battle buttons for PvP duel."""

    def __init__(self, current_turn_id: int, duel_id: int, cog):
        super().__init__(timeout=120)
        self.current_turn_id = current_turn_id
        self.duel_id = duel_id
        self.cog = cog

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.current_turn_id:
            await interaction.response.send_message("❌ Bukan giliranmu!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Serang", emoji="⚔️", style=discord.ButtonStyle.danger)
    async def attack_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.process_duel_action(interaction, "attack")

    @discord.ui.button(label="Bertahan", emoji="🛡️", style=discord.ButtonStyle.primary)
    async def defend_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.process_duel_action(interaction, "defend")


class PvPCog(commands.Cog):
    """PvP duel and ranking system."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Cache for duel stats
        self._duel_stats = {}

    def calculate_damage(self, attacker_atk: int, defender_def: int, crit_rate: float) -> tuple:
        """Calculate damage. Returns (damage, is_crit)."""
        base = attacker_atk * random.uniform(0.8, 1.2)
        reduction = defender_def * 0.5
        is_crit = random.random() < crit_rate
        multiplier = 1.5 if is_crit else 1.0
        damage = max(1, int((base - reduction) * multiplier))
        return damage, is_crit

    def calculate_elo_change(self, winner_elo: int, loser_elo: int, k: int = 32) -> tuple:
        """Calculate ELO changes. Returns (winner_change, loser_change)."""
        expected_winner = 1 / (1 + math.pow(10, (loser_elo - winner_elo) / 400))
        expected_loser = 1 - expected_winner

        winner_change = int(k * (1 - expected_winner))
        loser_change = int(k * (0 - expected_loser))

        return max(1, winner_change), min(-1, loser_change)

    @app_commands.command(name="duel", description="Tantang player lain ke duel PvP!")
    @app_commands.describe(lawan="Player yang ingin ditantang")
    async def duel_command(self, interaction: discord.Interaction, lawan: discord.Member):
        """Challenge another player to a duel."""
        if lawan.bot:
            await interaction.response.send_message("❌ Tidak bisa duel dengan bot!", ephemeral=True)
            return

        if lawan.id == interaction.user.id:
            await interaction.response.send_message("❌ Tidak bisa duel dengan diri sendiri!", ephemeral=True)
            return

        # Check both have characters
        c1 = await db.get_character(interaction.user.id, interaction.guild.id)
        c2 = await db.get_character(lawan.id, interaction.guild.id)

        if not c1:
            await interaction.response.send_message(
                "❌ Kamu belum punya karakter! Gunakan `/start`.", ephemeral=True
            )
            return
        if not c2:
            await interaction.response.send_message(
                f"❌ **{lawan.display_name}** belum punya karakter!", ephemeral=True
            )
            return

        # Check no active duels
        d1 = await db.get_active_duel(interaction.user.id, interaction.guild.id)
        d2 = await db.get_active_duel(lawan.id, interaction.guild.id)
        if d1 or d2:
            await interaction.response.send_message(
                "❌ Salah satu pemain masih dalam duel aktif!", ephemeral=True
            )
            return

        # Get both PvP stats
        pvp1 = await db.get_pvp_stats(interaction.user.id, interaction.guild.id)
        pvp2 = await db.get_pvp_stats(lawan.id, interaction.guild.id)
        rank1_name, rank1_emoji = get_pvp_rank(pvp1["elo"])
        rank2_name, rank2_emoji = get_pvp_rank(pvp2["elo"])

        embed = discord.Embed(
            title="⚔️ TANTANGAN DUEL!",
            description=f"**{interaction.user.display_name}** menantang **{lawan.display_name}** ke duel!",
            color=0x9B59B6,
        )

        class1 = CLASSES[c1["class_name"]]
        class2 = CLASSES[c2["class_name"]]
        embed.add_field(
            name=f"{class1['emoji']} {interaction.user.display_name}",
            value=f"Rank: {rank1_emoji} {rank1_name} ({pvp1['elo']})\n"
                  f"W/L: {pvp1['pvp_wins']}/{pvp1['pvp_losses']}",
            inline=True,
        )
        embed.add_field(name="⚡", value="VS", inline=True)
        embed.add_field(
            name=f"{class2['emoji']} {lawan.display_name}",
            value=f"Rank: {rank2_emoji} {rank2_name} ({pvp2['elo']})\n"
                  f"W/L: {pvp2['pvp_wins']}/{pvp2['pvp_losses']}",
            inline=True,
        )

        embed.set_footer(text=f"{lawan.display_name}, terima atau tolak tantangan ini!")

        view = DuelRequestView(interaction.user, lawan, self)
        await interaction.response.send_message(
            content=f"{lawan.mention} kamu ditantang duel!",
            embed=embed, view=view,
        )

    async def start_duel(self, interaction: discord.Interaction, challenger: discord.Member, defender: discord.Member):
        """Start the actual duel after acceptance."""
        # Get stats for both
        c1 = await db.get_character(challenger.id, interaction.guild.id)
        c2 = await db.get_character(defender.id, interaction.guild.id)
        p1 = await db.get_profile(challenger.id, interaction.guild.id)
        p2 = await db.get_profile(defender.id, interaction.guild.id)
        c1["level"] = p1["level"]
        c2["level"] = p2["level"]

        eq1 = await db.get_equipped_items(challenger.id, interaction.guild.id)
        eq2 = await db.get_equipped_items(defender.id, interaction.guild.id)
        pet1 = await db.get_active_pet(challenger.id, interaction.guild.id)
        pet2 = await db.get_active_pet(defender.id, interaction.guild.id)

        stats1 = calculate_stats(c1, eq1, pet1)
        stats2 = calculate_stats(c2, eq2, pet2)

        # Store stats in cache
        duel_key = f"{interaction.guild.id}"
        self._duel_stats[f"{challenger.id}_{duel_key}"] = stats1
        self._duel_stats[f"{defender.id}_{duel_key}"] = stats2

        # Determine first turn by speed
        first = challenger if stats1["spd"] >= stats2["spd"] else defender

        initial_log = f"⚔️ Duel dimulai! Giliran pertama: **{first.display_name}**"

        # Build duel embed
        embed = self.build_duel_embed(
            challenger, defender,
            stats1["hp"], stats1["hp"], stats2["hp"], stats2["hp"],
            stats1, stats2, c1, c2,
            initial_log, first,
        )

        await interaction.response.edit_message(content=None, embed=embed, view=None)
        msg = await interaction.original_response()

        # Create duel in DB
        duel_id = await db.create_duel(
            challenger.id, defender.id, interaction.guild.id,
            interaction.channel.id, msg.id,
            stats1["hp"], stats2["hp"],
        )

        view = DuelBattleView(first.id, duel_id, self)
        await msg.edit(view=view)

    def build_duel_embed(self, p1, p2, p1_hp, p1_max, p2_hp, p2_max,
                         stats1, stats2, char1, char2, log, current_turn):
        """Build duel battle embed."""
        c1_data = CLASSES[char1["class_name"]]
        c2_data = CLASSES[char2["class_name"]]

        embed = discord.Embed(
            title="⚔️ PVP DUEL",
            color=0x9B59B6,
        )

        bar1 = progress_bar(p1_hp, p1_max)
        embed.add_field(
            name=f"{c1_data['emoji']} {p1.display_name}",
            value=f"❤️ [{bar1}] {p1_hp}/{p1_max}\n"
                  f"⚔️ ATK: {stats1['atk']} | 🛡️ DEF: {stats1['def']}",
            inline=False,
        )

        embed.add_field(name="\u200b", value="⚡ **VS** ⚡", inline=False)

        bar2 = progress_bar(p2_hp, p2_max)
        embed.add_field(
            name=f"{c2_data['emoji']} {p2.display_name}",
            value=f"❤️ [{bar2}] {p2_hp}/{p2_max}\n"
                  f"⚔️ ATK: {stats2['atk']} | 🛡️ DEF: {stats2['def']}",
            inline=False,
        )

        if log:
            # Keep last 4 lines
            lines = log.strip().split("\n")
            if len(lines) > 4:
                lines = lines[-4:]
            embed.add_field(name="📜 Log", value="\n".join(lines), inline=False)

        embed.set_footer(text=f"🎯 Giliran: {current_turn.display_name}")
        return embed

    async def process_duel_action(self, interaction: discord.Interaction, action: str):
        """Process duel battle action."""
        duel = await db.get_active_duel(interaction.user.id, interaction.guild.id)
        if not duel:
            await interaction.response.send_message("❌ Tidak ada duel aktif!", ephemeral=True)
            return

        guild_key = str(interaction.guild.id)
        challenger = interaction.guild.get_member(duel["challenger_id"])
        defender = interaction.guild.get_member(duel["defender_id"])

        if not challenger or not defender:
            await db.end_duel(duel["id"])
            await interaction.response.send_message("❌ Duel dibatalkan: pemain tidak ditemukan.", ephemeral=True)
            return

        stats1 = self._duel_stats.get(f"{challenger.id}_{guild_key}", {"atk": 10, "def": 10, "spd": 10, "crit": 0.05, "hp": 100})
        stats2 = self._duel_stats.get(f"{defender.id}_{guild_key}", {"atk": 10, "def": 10, "spd": 10, "crit": 0.05, "hp": 100})

        is_challenger = interaction.user.id == duel["challenger_id"]
        attacker_stats = stats1 if is_challenger else stats2
        defender_stats = stats2 if is_challenger else stats1

        c_hp = duel["challenger_hp"]
        d_hp = duel["defender_hp"]
        log = duel["battle_log"] or ""

        attacker_name = interaction.user.display_name
        new_log_lines = []

        if action == "attack":
            damage, is_crit = self.calculate_damage(attacker_stats["atk"], defender_stats["def"], attacker_stats["crit"])
            crit_text = " 💥**CRIT!**" if is_crit else ""

            if is_challenger:
                d_hp = max(0, d_hp - damage)
                new_log_lines.append(f"⚔️ {attacker_name} menyerang! -{damage} HP{crit_text}")
            else:
                c_hp = max(0, c_hp - damage)
                new_log_lines.append(f"⚔️ {attacker_name} menyerang! -{damage} HP{crit_text}")

        elif action == "defend":
            # Heal 8% of max HP
            heal = int(attacker_stats["hp"] * 0.08)
            if is_challenger:
                c_hp = min(duel["challenger_max"], c_hp + heal)
            else:
                d_hp = min(duel["defender_max"], d_hp + heal)
            new_log_lines.append(f"🛡️ {attacker_name} bertahan! +{heal} HP")

        full_log = log + "\n".join(new_log_lines) + "\n"

        # Check for victory
        if c_hp <= 0 or d_hp <= 0:
            winner = challenger if d_hp <= 0 else defender
            loser = defender if d_hp <= 0 else challenger

            # Calculate ELO
            winner_pvp = await db.get_pvp_stats(winner.id, interaction.guild.id)
            loser_pvp = await db.get_pvp_stats(loser.id, interaction.guild.id)
            w_change, l_change = self.calculate_elo_change(winner_pvp["elo"], loser_pvp["elo"])

            await db.update_pvp_result(winner.id, interaction.guild.id, True, w_change)
            await db.update_pvp_result(loser.id, interaction.guild.id, False, l_change)

            # Rewards
            coins_reward = random.randint(20, 50)
            xp_reward = random.randint(30, 60)
            await db.add_coins(winner.id, interaction.guild.id, coins_reward)
            await db.add_xp(winner.id, interaction.guild.id, xp_reward)
            await db.add_xp(loser.id, interaction.guild.id, 10)  # Consolation XP

            await db.end_duel(duel["id"])
            # Clean up cached stats
            self._duel_stats.pop(f"{challenger.id}_{guild_key}", None)
            self._duel_stats.pop(f"{defender.id}_{guild_key}", None)

            new_winner_rank, new_winner_emoji = get_pvp_rank(winner_pvp["elo"] + w_change)

            embed = discord.Embed(
                title=f"👑 {winner.display_name} MENANG!",
                description=f"**{winner.display_name}** mengalahkan **{loser.display_name}** dalam duel!",
                color=0xFFD700,
            )
            embed.add_field(
                name="🏆 Hadiah Pemenang",
                value=f"⭐ XP: **+{xp_reward}**\n"
                      f"🪙 Coins: **+{coins_reward}**\n"
                      f"📊 ELO: **+{w_change}** → {new_winner_emoji} {winner_pvp['elo'] + w_change}",
                inline=True,
            )
            embed.add_field(
                name="📉 Kekalahan",
                value=f"⭐ XP: **+10**\n"
                      f"📊 ELO: **{l_change}** → {loser_pvp['elo'] + l_change}",
                inline=True,
            )

            await interaction.response.edit_message(embed=embed, view=None)
            return

        # Switch turns
        next_turn = duel["defender_id"] if is_challenger else duel["challenger_id"]
        await db.update_duel(duel["id"], c_hp, d_hp, next_turn, full_log)

        next_member = defender if is_challenger else challenger
        c1 = await db.get_character(challenger.id, interaction.guild.id)
        c2 = await db.get_character(defender.id, interaction.guild.id)

        embed = self.build_duel_embed(
            challenger, defender,
            c_hp, duel["challenger_max"], d_hp, duel["defender_max"],
            stats1, stats2, c1, c2,
            full_log, next_member,
        )

        view = DuelBattleView(next_turn, duel["id"], self)
        await interaction.response.edit_message(embed=embed, view=view)

    @app_commands.command(name="pvpstats", description="Lihat statistik PvP")
    @app_commands.describe(user="Player yang ingin dilihat")
    async def pvpstats_command(self, interaction: discord.Interaction, user: discord.Member = None):
        """View PvP stats."""
        target = user or interaction.user
        pvp = await db.get_pvp_stats(target.id, interaction.guild.id)
        rank_name, rank_emoji = get_pvp_rank(pvp["elo"])

        total = pvp["pvp_wins"] + pvp["pvp_losses"]
        win_rate = (pvp["pvp_wins"] / total * 100) if total > 0 else 0

        embed = discord.Embed(
            title=f"⚔️ PvP Stats — {target.display_name}",
            color=0x9B59B6,
        )
        embed.add_field(
            name="🏆 Rank",
            value=f"{rank_emoji} **{rank_name}**\n📊 ELO: **{pvp['elo']}**",
            inline=True,
        )
        embed.add_field(
            name="📋 Record",
            value=f"✅ Menang: **{pvp['pvp_wins']}**\n"
                  f"❌ Kalah: **{pvp['pvp_losses']}**\n"
                  f"📈 Win Rate: **{win_rate:.0f}%**",
            inline=True,
        )
        embed.add_field(
            name="🔥 Streak",
            value=f"Saat ini: **{pvp['pvp_streak']}**\n"
                  f"Terbaik: **{pvp['best_streak']}**",
            inline=True,
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(PvPCog(bot))
