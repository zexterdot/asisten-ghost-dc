"""
cogs/games.py — Mini-games: trivia, RPS, coinflip, slots, mathquiz, wordscramble
Ghost Assistant RPG
"""

import discord
from discord.ext import commands
from discord import app_commands
import database as db
from game_data import TRIVIA_QUESTIONS, WORD_SCRAMBLE_WORDS, scramble_word
import random
import asyncio


class TriviaView(discord.ui.View):
    """Trivia answer buttons."""

    def __init__(self, user_id: int, correct_index: int, options: list):
        super().__init__(timeout=15)
        self.user_id = user_id
        self.correct_index = correct_index
        self.answered = False

        labels = ["A", "B", "C", "D"]
        for i, option in enumerate(options):
            button = discord.ui.Button(
                label=f"{labels[i]}. {option}",
                style=discord.ButtonStyle.secondary,
                custom_id=f"trivia_{i}",
            )
            button.callback = self.make_callback(i)
            self.add_item(button)

    def make_callback(self, index: int):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("❌ Ini bukan quiz kamu!", ephemeral=True)
                return
            if self.answered:
                return
            self.answered = True

            correct = index == self.correct_index
            if correct:
                xp = 25
                coins = 15
                await db.add_xp(interaction.user.id, interaction.guild.id, xp)
                await db.add_coins(interaction.user.id, interaction.guild.id, coins)
                await db.record_game(interaction.user.id, interaction.guild.id, "trivia", "win", xp, coins)

                embed = discord.Embed(
                    title="✅ BENAR!",
                    description=f"Jawaban yang benar! 🎉\n"
                                f"⭐ +{xp} XP | 🪙 +{coins} Coins",
                    color=0x2ECC71,
                )
            else:
                xp = 5
                await db.add_xp(interaction.user.id, interaction.guild.id, xp)
                await db.record_game(interaction.user.id, interaction.guild.id, "trivia", "lose", xp, 0)

                embed = discord.Embed(
                    title="❌ SALAH!",
                    description=f"Jawaban yang benar: **{interaction.message.embeds[0].fields[0].value.split(chr(10))[self.correct_index]}**\n"
                                f"⭐ +{xp} XP (penghiburan)",
                    color=0xE74C3C,
                )

            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(embed=embed, view=self)
            self.stop()

        return callback

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True


class RPSView(discord.ui.View):
    """Rock Paper Scissors buttons."""

    def __init__(self, user_id: int):
        super().__init__(timeout=15)
        self.user_id = user_id
        self.played = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Ini bukan game kamu!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Batu", emoji="🪨", style=discord.ButtonStyle.secondary)
    async def rock_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play(interaction, "rock")

    @discord.ui.button(label="Kertas", emoji="📄", style=discord.ButtonStyle.secondary)
    async def paper_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play(interaction, "paper")

    @discord.ui.button(label="Gunting", emoji="✂️", style=discord.ButtonStyle.secondary)
    async def scissors_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play(interaction, "scissors")

    async def play(self, interaction: discord.Interaction, player_choice: str):
        if self.played:
            return
        self.played = True

        choices = ["rock", "paper", "scissors"]
        emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        names = {"rock": "Batu", "paper": "Kertas", "scissors": "Gunting"}
        bot_choice = random.choice(choices)

        # Determine winner
        if player_choice == bot_choice:
            result = "draw"
        elif (player_choice == "rock" and bot_choice == "scissors") or \
             (player_choice == "paper" and bot_choice == "rock") or \
             (player_choice == "scissors" and bot_choice == "paper"):
            result = "win"
        else:
            result = "lose"

        if result == "win":
            xp, coins = 15, 10
            await db.add_xp(interaction.user.id, interaction.guild.id, xp)
            await db.add_coins(interaction.user.id, interaction.guild.id, coins)
            await db.record_game(interaction.user.id, interaction.guild.id, "rps", "win", xp, coins)
            title = "🎉 MENANG!"
            desc = f"⭐ +{xp} XP | 🪙 +{coins} Coins"
            color = 0x2ECC71
        elif result == "draw":
            xp = 5
            await db.add_xp(interaction.user.id, interaction.guild.id, xp)
            await db.record_game(interaction.user.id, interaction.guild.id, "rps", "draw", xp, 0)
            title = "🤝 SERI!"
            desc = f"⭐ +{xp} XP"
            color = 0xF1C40F
        else:
            xp = 3
            await db.add_xp(interaction.user.id, interaction.guild.id, xp)
            await db.record_game(interaction.user.id, interaction.guild.id, "rps", "lose", xp, 0)
            title = "💀 KALAH!"
            desc = f"⭐ +{xp} XP (penghiburan)"
            color = 0xE74C3C

        embed = discord.Embed(title=title, color=color)
        embed.add_field(
            name="Hasil",
            value=f"Kamu: {emojis[player_choice]} {names[player_choice]}\n"
                  f"Bot: {emojis[bot_choice]} {names[bot_choice]}\n\n{desc}",
            inline=False,
        )

        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()


class GamesCog(commands.Cog):
    """Mini-games commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="trivia", description="Jawab pertanyaan quiz dan dapatkan hadiah!")
    @app_commands.checks.cooldown(1, 30, key=lambda i: (i.user.id, i.guild_id))
    async def trivia_command(self, interaction: discord.Interaction):
        """Trivia quiz game."""
        q = random.choice(TRIVIA_QUESTIONS)

        embed = discord.Embed(
            title=f"❓ Trivia — {q['category']}",
            description=f"**{q['question']}**",
            color=0x3498DB,
        )

        labels = ["A", "B", "C", "D"]
        options_text = "\n".join([f"**{labels[i]}.** {opt}" for i, opt in enumerate(q["options"])])
        embed.add_field(name="Pilihan", value=options_text, inline=False)
        embed.set_footer(text="⏱️ Waktu: 15 detik!")

        view = TriviaView(interaction.user.id, q["answer"], q["options"])
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="rps", description="Main suit Batu-Kertas-Gunting!")
    @app_commands.checks.cooldown(1, 15, key=lambda i: (i.user.id, i.guild_id))
    async def rps_command(self, interaction: discord.Interaction):
        """Rock Paper Scissors game."""
        embed = discord.Embed(
            title="✊ Batu-Kertas-Gunting!",
            description="Pilih tanganmu!",
            color=0x3498DB,
        )
        embed.set_footer(text="⏱️ Waktu: 15 detik!")

        view = RPSView(interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="coinflip", description="Lempar koin! Tebak Heads atau Tails")
    @app_commands.describe(sisi="Pilih Heads atau Tails", taruhan="Jumlah coins yang ditaruhkan")
    @app_commands.choices(sisi=[
        app_commands.Choice(name="🪙 Heads", value="heads"),
        app_commands.Choice(name="🪙 Tails", value="tails"),
    ])
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id, i.guild_id))
    async def coinflip_command(self, interaction: discord.Interaction, sisi: str, taruhan: int = 10):
        """Coin flip gambling game."""
        if taruhan < 1:
            await interaction.response.send_message("❌ Taruhan minimal 1 🪙!", ephemeral=True)
            return

        if taruhan > 500:
            await interaction.response.send_message("❌ Taruhan maksimal 500 🪙!", ephemeral=True)
            return

        profile = await db.get_profile(interaction.user.id, interaction.guild.id)
        if profile["coins"] < taruhan:
            await interaction.response.send_message(
                f"❌ Koin tidak cukup! Kamu punya **{profile['coins']}** 🪙.", ephemeral=True
            )
            return

        result = random.choice(["heads", "tails"])
        won = sisi == result

        result_emoji = "👑" if result == "heads" else "🪙"

        if won:
            winnings = taruhan
            await db.add_coins(interaction.user.id, interaction.guild.id, winnings)
            await db.record_game(interaction.user.id, interaction.guild.id, "coinflip", "win", 0, winnings)

            embed = discord.Embed(
                title=f"🎉 MENANG! {result_emoji} {result.upper()}",
                description=f"Kamu menebak dengan benar!\n🪙 **+{winnings}** Coins!",
                color=0x2ECC71,
            )
        else:
            await db.add_coins(interaction.user.id, interaction.guild.id, -taruhan)
            await db.record_game(interaction.user.id, interaction.guild.id, "coinflip", "lose", 0, -taruhan)

            embed = discord.Embed(
                title=f"💀 KALAH! {result_emoji} {result.upper()}",
                description=f"Sayang sekali! Kamu menebak **{sisi}**.\n🪙 **-{taruhan}** Coins",
                color=0xE74C3C,
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="slots", description="Spin slot machine! 🎰")
    @app_commands.describe(taruhan="Jumlah coins yang ditaruhkan (default: 10)")
    @app_commands.checks.cooldown(1, 15, key=lambda i: (i.user.id, i.guild_id))
    async def slots_command(self, interaction: discord.Interaction, taruhan: int = 10):
        """Slot machine game."""
        if taruhan < 1 or taruhan > 500:
            await interaction.response.send_message("❌ Taruhan 1-500 🪙!", ephemeral=True)
            return

        profile = await db.get_profile(interaction.user.id, interaction.guild.id)
        if profile["coins"] < taruhan:
            await interaction.response.send_message(
                f"❌ Koin tidak cukup! Kamu punya **{profile['coins']}** 🪙.", ephemeral=True
            )
            return

        symbols = ["🍒", "🍋", "🔔", "💎", "⭐", "7️⃣"]
        weights = [30, 25, 20, 12, 8, 5]  # 7️⃣ is rarest

        result = random.choices(symbols, weights=weights, k=3)

        # Calculate winnings
        multiplier = 0
        if result[0] == result[1] == result[2]:
            if result[0] == "7️⃣":
                multiplier = 10  # Jackpot!
            elif result[0] == "💎":
                multiplier = 7
            else:
                multiplier = 5
        elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
            multiplier = 2

        slot_display = f"┃ {result[0]} ┃ {result[1]} ┃ {result[2]} ┃"

        if multiplier > 0:
            winnings = taruhan * multiplier - taruhan  # Net gain
            await db.add_coins(interaction.user.id, interaction.guild.id, winnings)
            await db.record_game(interaction.user.id, interaction.guild.id, "slots", "win", 0, winnings)

            if multiplier >= 10:
                title = "🎰💥 JACKPOT!!! 💥🎰"
            elif multiplier >= 5:
                title = "🎰🎉 TRIPLE MATCH! 🎉🎰"
            else:
                title = "🎰 DOUBLE MATCH! 🎰"

            embed = discord.Embed(
                title=title,
                description=f"{slot_display}\n\n"
                            f"Multiplier: **{multiplier}x**\n"
                            f"🪙 **+{winnings}** Coins!",
                color=0xFFD700,
            )
        else:
            await db.add_coins(interaction.user.id, interaction.guild.id, -taruhan)
            await db.record_game(interaction.user.id, interaction.guild.id, "slots", "lose", 0, -taruhan)

            embed = discord.Embed(
                title="🎰 Tidak Beruntung...",
                description=f"{slot_display}\n\n"
                            f"🪙 **-{taruhan}** Coins",
                color=0x95A5A6,
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="mathquiz", description="Soal matematika cepat!")
    @app_commands.checks.cooldown(1, 20, key=lambda i: (i.user.id, i.guild_id))
    async def mathquiz_command(self, interaction: discord.Interaction):
        """Math quiz game."""
        ops = ["+", "-", "×"]
        op = random.choice(ops)

        if op == "+":
            a, b = random.randint(10, 99), random.randint(10, 99)
            answer = a + b
        elif op == "-":
            a = random.randint(20, 99)
            b = random.randint(1, a)
            answer = a - b
        else:  # ×
            a, b = random.randint(2, 15), random.randint(2, 15)
            answer = a * b

        embed = discord.Embed(
            title="🔢 Soal Matematika!",
            description=f"**{a} {op} {b} = ?**\n\nKetik jawabanmu di chat dalam 10 detik!",
            color=0x3498DB,
        )
        embed.set_footer(text="⏱️ Waktu: 10 detik!")
        await interaction.response.send_message(embed=embed)

        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=10)
            try:
                user_answer = int(msg.content.strip())
            except ValueError:
                embed = discord.Embed(
                    title="❌ Jawaban Tidak Valid!",
                    description=f"Jawaban yang benar: **{answer}**",
                    color=0xE74C3C,
                )
                await interaction.followup.send(embed=embed)
                await db.record_game(interaction.user.id, interaction.guild.id, "mathquiz", "lose", 5, 0)
                await db.add_xp(interaction.user.id, interaction.guild.id, 5)
                return

            if user_answer == answer:
                xp, coins = 20, 15
                await db.add_xp(interaction.user.id, interaction.guild.id, xp)
                await db.add_coins(interaction.user.id, interaction.guild.id, coins)
                await db.record_game(interaction.user.id, interaction.guild.id, "mathquiz", "win", xp, coins)

                embed = discord.Embed(
                    title="✅ BENAR!",
                    description=f"**{a} {op} {b} = {answer}** ✔️\n"
                                f"⭐ +{xp} XP | 🪙 +{coins} Coins",
                    color=0x2ECC71,
                )
                await interaction.followup.send(embed=embed)
            else:
                await db.add_xp(interaction.user.id, interaction.guild.id, 5)
                await db.record_game(interaction.user.id, interaction.guild.id, "mathquiz", "lose", 5, 0)

                embed = discord.Embed(
                    title="❌ SALAH!",
                    description=f"Jawaban kamu: **{user_answer}**\n"
                                f"Jawaban benar: **{answer}**\n"
                                f"⭐ +5 XP (penghiburan)",
                    color=0xE74C3C,
                )
                await interaction.followup.send(embed=embed)

        except asyncio.TimeoutError:
            await db.record_game(interaction.user.id, interaction.guild.id, "mathquiz", "lose", 3, 0)
            await db.add_xp(interaction.user.id, interaction.guild.id, 3)

            embed = discord.Embed(
                title="⏱️ WAKTU HABIS!",
                description=f"Jawaban yang benar: **{answer}**\n⭐ +3 XP",
                color=0x95A5A6,
            )
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="wordscramble", description="Susun huruf acak jadi kata!")
    @app_commands.checks.cooldown(1, 20, key=lambda i: (i.user.id, i.guild_id))
    async def wordscramble_command(self, interaction: discord.Interaction):
        """Word scramble game."""
        word = random.choice(WORD_SCRAMBLE_WORDS)
        scrambled = scramble_word(word)

        embed = discord.Embed(
            title="🔤 Word Scramble!",
            description=f"Susun huruf ini menjadi kata yang benar:\n\n"
                        f"**`{scrambled.upper()}`**\n\n"
                        f"💡 Hint: {len(word)} huruf\n"
                        f"Ketik jawabanmu di chat dalam 30 detik!",
            color=0x3498DB,
        )
        embed.set_footer(text="⏱️ Waktu: 30 detik!")
        await interaction.response.send_message(embed=embed)

        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30)
            user_answer = msg.content.strip().lower()

            if user_answer == word.lower():
                xp, coins = 30, 20
                await db.add_xp(interaction.user.id, interaction.guild.id, xp)
                await db.add_coins(interaction.user.id, interaction.guild.id, coins)
                await db.record_game(interaction.user.id, interaction.guild.id, "wordscramble", "win", xp, coins)

                embed = discord.Embed(
                    title="✅ BENAR!",
                    description=f"Kata yang benar: **{word.upper()}** ✔️\n"
                                f"⭐ +{xp} XP | 🪙 +{coins} Coins",
                    color=0x2ECC71,
                )
                await interaction.followup.send(embed=embed)
            else:
                await db.add_xp(interaction.user.id, interaction.guild.id, 5)
                await db.record_game(interaction.user.id, interaction.guild.id, "wordscramble", "lose", 5, 0)

                embed = discord.Embed(
                    title="❌ SALAH!",
                    description=f"Jawabanmu: **{user_answer}**\n"
                                f"Jawaban benar: **{word.upper()}**\n"
                                f"⭐ +5 XP (penghiburan)",
                    color=0xE74C3C,
                )
                await interaction.followup.send(embed=embed)

        except asyncio.TimeoutError:
            await db.record_game(interaction.user.id, interaction.guild.id, "wordscramble", "lose", 3, 0)
            await db.add_xp(interaction.user.id, interaction.guild.id, 3)

            embed = discord.Embed(
                title="⏱️ WAKTU HABIS!",
                description=f"Kata yang benar: **{word.upper()}**\n⭐ +3 XP",
                color=0x95A5A6,
            )
            await interaction.followup.send(embed=embed)

    # Cooldown error handler
    @trivia_command.error
    @rps_command.error
    @coinflip_command.error
    @slots_command.error
    @mathquiz_command.error
    @wordscramble_command.error
    async def game_cooldown_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"⏳ Cooldown! Tunggu **{error.retry_after:.0f} detik** lagi.",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(GamesCog(bot))
