"""
cogs/adventure.py — Dungeon exploration, battle engine, boss fights
Ghost Assistant RPG
"""

import discord
from discord.ext import commands
from discord import app_commands
import database as db
from game_data import CLASSES, ITEMS, get_random_monster, get_boss, get_zone_name
from utils import calculate_stats, create_battle_embed, progress_bar, format_coins
import random
from datetime import datetime, timezone


ADVENTURE_COOLDOWN = 30   # seconds
BOSS_COOLDOWN = 300       # seconds (5 minutes)


class BattleView(discord.ui.View):
    """Interactive battle buttons."""

    def __init__(self, user_id: int, battle_id: int, cog):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.battle_id = battle_id
        self.cog = cog

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Ini bukan pertempuran kamu!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Serang", emoji="⚔️", style=discord.ButtonStyle.danger)
    async def attack_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.process_battle_action(interaction, "attack")

    @discord.ui.button(label="Bertahan", emoji="🛡️", style=discord.ButtonStyle.primary)
    async def defend_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.process_battle_action(interaction, "defend")

    @discord.ui.button(label="Potion", emoji="🧪", style=discord.ButtonStyle.success)
    async def potion_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.process_battle_action(interaction, "potion")

    @discord.ui.button(label="Kabur", emoji="🏃", style=discord.ButtonStyle.secondary)
    async def flee_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.process_battle_action(interaction, "flee")


class AdventureCog(commands.Cog):
    """Dungeon exploration and battle system."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def calculate_damage(self, attacker_atk: int, defender_def: int, crit_rate: float) -> tuple:
        """Calculate damage. Returns (damage, is_crit)."""
        base = attacker_atk * random.uniform(0.8, 1.2)
        reduction = defender_def * 0.5
        is_crit = random.random() < crit_rate
        multiplier = 1.5 if is_crit else 1.0
        damage = max(1, int((base - reduction) * multiplier))
        return damage, is_crit

    async def process_battle_action(self, interaction: discord.Interaction, action: str):
        """Process a battle action (attack/defend/potion/flee)."""
        battle = await db.get_active_battle(interaction.user.id, interaction.guild.id)
        if not battle:
            await interaction.response.send_message("❌ Kamu tidak sedang bertarung!", ephemeral=True)
            return

        character = await db.get_character(interaction.user.id, interaction.guild.id)
        profile = await db.get_profile(interaction.user.id, interaction.guild.id)
        character["level"] = profile["level"]
        equipment = await db.get_equipped_items(interaction.user.id, interaction.guild.id)
        active_pet = await db.get_active_pet(interaction.user.id, interaction.guild.id)
        stats = calculate_stats(character, equipment, active_pet)

        player_hp = character["current_hp"]
        monster_hp = battle["monster_hp"]
        battle_log = battle["battle_log"] or ""
        new_log_lines = []

        # ---- PLAYER TURN ----
        if action == "flee":
            # Flee: lose some coins
            coins_lost = random.randint(5, 15)
            await db.add_coins(interaction.user.id, interaction.guild.id, -coins_lost)
            await db.end_battle(interaction.user.id, interaction.guild.id)

            embed = discord.Embed(
                title="🏃 Kabur dari Pertempuran!",
                description=f"Kamu berhasil kabur dari **{battle['monster_emoji']} {battle['monster_name']}**!\n"
                            f"💰 Kehilangan **{coins_lost}** 🪙",
                color=0x95A5A6,
            )
            for child in interaction.message.components[0].children if interaction.message.components else []:
                pass
            await interaction.response.edit_message(embed=embed, view=None)
            return

        if action == "potion":
            # Try to use health potion
            has_potion = await db.get_item_count(interaction.user.id, interaction.guild.id, "potion_hp")
            has_big_potion = await db.get_item_count(interaction.user.id, interaction.guild.id, "potion_hp_big")
            has_mega = await db.get_item_count(interaction.user.id, interaction.guild.id, "potion_hp_mega")

            healed = 0
            potion_used = None
            if has_mega > 0:
                healed = 500
                potion_used = "potion_hp_mega"
            elif has_big_potion > 0:
                healed = 150
                potion_used = "potion_hp_big"
            elif has_potion > 0:
                healed = 50
                potion_used = "potion_hp"
            else:
                new_log_lines.append("🧪 Tidak ada potion! Giliran terbuang.")
                # Still let monster attack
                action = "no_potion"

            if potion_used:
                await db.remove_item(interaction.user.id, interaction.guild.id, potion_used)
                old_hp = player_hp
                player_hp = min(stats["hp"], player_hp + healed)
                actual_heal = player_hp - old_hp
                potion_name = ITEMS[potion_used]["name"]
                new_log_lines.append(f"🧪 Menggunakan {potion_name}! +{actual_heal} HP")

        elif action == "attack":
            damage, is_crit = self.calculate_damage(stats["atk"], battle["monster_def"], stats["crit"])
            monster_hp = max(0, monster_hp - damage)
            crit_text = " **CRIT!** 💥" if is_crit else ""
            new_log_lines.append(f"⚔️ Kamu menyerang! Damage: {damage}{crit_text}")

        elif action == "defend":
            new_log_lines.append("🛡️ Kamu bertahan! (Damage -50%, Heal +5%)")

        # ---- CHECK MONSTER DEATH ----
        if monster_hp <= 0:
            await self.handle_victory(interaction, battle, character, profile, stats, player_hp, battle_log, new_log_lines)
            return

        # ---- MONSTER TURN ----
        monster_damage, _ = self.calculate_damage(battle["monster_atk"], stats["def"], 0.05)
        if action == "defend":
            monster_damage = max(1, monster_damage // 2)
            heal_amount = int(stats["hp"] * 0.05)
            player_hp = min(stats["hp"], player_hp + heal_amount)
            new_log_lines.append(f"🛡️ Bertahan! Mengurangi damage dan heal +{heal_amount} HP")

        player_hp = max(0, player_hp - monster_damage)
        new_log_lines.append(f"👾 {battle['monster_name']} menyerang! Damage: {monster_damage}")

        # Pet heal per turn (Unicorn special)
        if active_pet:
            from game_data import PETS
            pet_data = PETS.get(active_pet.get("pet_id", ""))
            if pet_data and pet_data.get("special") == "heal_per_turn":
                pet_heal = int(stats["hp"] * 0.10)
                player_hp = min(stats["hp"], player_hp + pet_heal)
                new_log_lines.append(f"🦄 Pet menyembuhkan +{pet_heal} HP!")

        # ---- CHECK PLAYER DEATH ----
        if player_hp <= 0:
            await self.handle_defeat(interaction, battle, character, profile, battle_log, new_log_lines)
            return

        # ---- UPDATE BATTLE STATE ----
        # Keep only last 5 log lines to avoid embed overflow
        full_log = battle_log + "\n".join(new_log_lines) + "\n"
        log_lines = full_log.strip().split("\n")
        if len(log_lines) > 6:
            log_lines = log_lines[-6:]
        trimmed_log = "\n".join(log_lines)

        await db.update_battle(battle["id"], monster_hp, trimmed_log)
        await db.update_character_hp(interaction.user.id, interaction.guild.id, player_hp)

        # Build updated embed
        class_data = CLASSES[character["class_name"]]
        pet_info = ""
        if active_pet:
            from game_data import PETS
            pd = PETS.get(active_pet["pet_id"], {})
            pet_info = f"🐾 {pd.get('emoji', '')} {active_pet.get('pet_name') or pd.get('name', '')}"

        # Get boss image if applicable
        boss_image = None
        if battle["is_boss"]:
            from game_data import BOSSES
            boss_data = BOSSES.get(battle["floor_num"])
            if boss_data:
                boss_image = boss_data.get("image")

        embed = create_battle_embed(
            player_name=interaction.user.display_name,
            player_class_emoji=class_data["emoji"],
            player_hp=player_hp, player_max_hp=stats["hp"],
            player_atk=stats["atk"], player_def=stats["def"],
            player_pet_info=pet_info,
            monster_name=battle["monster_name"], monster_emoji=battle["monster_emoji"],
            monster_hp=monster_hp, monster_max_hp=battle["monster_max_hp"],
            monster_atk=battle["monster_atk"], monster_def=battle["monster_def"],
            floor=battle["floor_num"],
            zone_name=get_zone_name(battle["floor_num"]),
            battle_log=trimmed_log,
            is_boss=battle["is_boss"],
            image_url=boss_image,
        )

        view = BattleView(interaction.user.id, battle["id"], self)
        await interaction.response.edit_message(embed=embed, view=view)

    async def handle_victory(self, interaction, battle, character, profile, stats, player_hp, old_log, new_log_lines):
        """Handle monster defeat."""
        new_log_lines.append(f"\n🎉 **{battle['monster_name']} dikalahkan!**")

        # Rewards
        from game_data import BOSSES, MONSTERS
        monster_data = None

        # Find original monster data for loot
        if battle["is_boss"]:
            monster_data = BOSSES.get(battle["floor_num"])
        else:
            for (low, high), monsters in MONSTERS.items():
                for m in monsters:
                    if m["id"] == battle["monster_id"]:
                        monster_data = m
                        break

        coins_earned = 0
        xp_earned = 0
        loot_drops = []

        if monster_data:
            coins_earned = random.randint(*monster_data["coins"])
            xp_earned = random.randint(*monster_data["xp"])

            # Loot drops
            for item_id, drop_rate in monster_data.get("loot", []):
                if random.random() < drop_rate:
                    await db.add_item(interaction.user.id, interaction.guild.id, item_id)
                    item_data = ITEMS.get(item_id, {})
                    loot_drops.append(f"{item_data.get('emoji', '❓')} {item_data.get('name', item_id)}")

        await db.add_coins(interaction.user.id, interaction.guild.id, coins_earned)
        new_level, leveled_up, levels_gained = await db.add_xp(interaction.user.id, interaction.guild.id, xp_earned)
        await db.record_game(interaction.user.id, interaction.guild.id, "adventure", "win", xp_earned, coins_earned)
        await db.update_character_hp(interaction.user.id, interaction.guild.id, player_hp)
        await db.end_battle(interaction.user.id, interaction.guild.id)

        # Pet XP
        active_pet = await db.get_active_pet(interaction.user.id, interaction.guild.id)
        pet_level_up = False
        if active_pet:
            pet_xp = random.randint(5, 15)
            _, pet_level_up = await db.add_pet_xp(active_pet["id"], pet_xp)

        # Floor progression
        floor_advanced = False
        if battle["is_boss"]:
            # Boss always advances floor
            new_floor = battle["floor_num"] + 1
            await db.update_floor(interaction.user.id, interaction.guild.id, new_floor)
            floor_advanced = True
        else:
            # Regular monster: 30% chance to advance floor
            if random.random() < 0.30:
                new_floor = battle["floor_num"] + 1
                await db.update_floor(interaction.user.id, interaction.guild.id, new_floor)
                floor_advanced = True

        # Build victory embed
        embed = discord.Embed(
            title="🎉 KEMENANGAN!" if not battle["is_boss"] else "👑 BOSS DIKALAHKAN!",
            description=f"**{battle['monster_emoji']} {battle['monster_name']}** telah dikalahkan!",
            color=0xFFD700 if battle["is_boss"] else 0x2ECC71,
        )

        reward_text = f"⭐ XP: **+{xp_earned}**\n🪙 Coins: **+{coins_earned}**"
        if loot_drops:
            reward_text += f"\n🎒 Loot: {', '.join(loot_drops)}"
        embed.add_field(name="🏆 Hadiah", value=reward_text, inline=False)

        if leveled_up:
            embed.add_field(
                name="🎊 LEVEL UP!",
                value=f"Level **{profile['level']}** → **{new_level}**!",
                inline=False,
            )
            # Check for role rewards
            for req_level, role_name in LEVEL_ROLES.items():
                if profile["level"] < req_level <= new_level:
                    role = discord.utils.get(interaction.guild.roles, name=role_name)
                    if role:
                        try:
                            await interaction.user.add_roles(role)
                            embed.add_field(
                                name="🏅 Role Baru!",
                                value=f"Mendapat role **{role_name}**!",
                                inline=False,
                            )
                        except discord.Forbidden:
                            pass

        if pet_level_up:
            embed.add_field(name="🐾 Pet Level Up!", value="Pet kamu naik level!", inline=False)

        if floor_advanced:
            embed.add_field(
                name="🗺️ Floor Baru!",
                value=f"Floor **{battle['floor_num']}** → **{battle['floor_num'] + 1}** terbuka!",
                inline=False,
            )

        await interaction.response.edit_message(embed=embed, view=None)

    async def handle_defeat(self, interaction, battle, character, profile, old_log, new_log_lines):
        """Handle player defeat."""
        coins_lost = random.randint(10, 30)
        await db.add_coins(interaction.user.id, interaction.guild.id, -coins_lost)
        await db.update_character_hp(interaction.user.id, interaction.guild.id, 1)
        await db.record_game(interaction.user.id, interaction.guild.id, "adventure", "lose", 5, -coins_lost)
        await db.add_xp(interaction.user.id, interaction.guild.id, 5)  # Small consolation XP
        await db.end_battle(interaction.user.id, interaction.guild.id)

        embed = discord.Embed(
            title="💀 KALAH!",
            description=f"Kamu dikalahkan oleh **{battle['monster_emoji']} {battle['monster_name']}**!",
            color=0xE74C3C,
        )
        embed.add_field(
            name="📉 Kerugian",
            value=f"🪙 Kehilangan **{coins_lost}** coins\n"
                  f"❤️ HP tersisa: **1**\n"
                  f"⭐ XP penghiburan: **+5**",
            inline=False,
        )
        embed.add_field(
            name="💡 Tips",
            value="🧪 Gunakan `/heal` untuk memulihkan HP\n"
                  "🛒 Beli equipment di `/shop`\n"
                  "🐾 Aktifkan pet untuk bantuan!",
            inline=False,
        )

        await interaction.response.edit_message(embed=embed, view=None)

    @app_commands.command(name="adventure", description="Jelajahi dungeon dan lawan monster!")
    async def adventure_command(self, interaction: discord.Interaction):
        """Start a dungeon adventure."""
        character = await db.get_character(interaction.user.id, interaction.guild.id)
        if not character:
            await interaction.response.send_message(
                "❌ Kamu belum punya karakter! Gunakan `/start`.", ephemeral=True
            )
            return

        # Check active battle
        active = await db.get_active_battle(interaction.user.id, interaction.guild.id)
        if active:
            await interaction.response.send_message(
                "⚔️ Kamu masih dalam pertempuran! Selesaikan dulu.", ephemeral=True
            )
            return

        # Check HP
        if character["current_hp"] <= 0:
            await interaction.response.send_message(
                "💀 HP kamu habis! Gunakan `/heal` untuk memulihkan.", ephemeral=True
            )
            return

        # Check cooldown
        if character["last_adventure"]:
            last = datetime.fromisoformat(character["last_adventure"])
            elapsed = (datetime.now(timezone.utc) - last).total_seconds()
            if elapsed < ADVENTURE_COOLDOWN:
                remaining = int(ADVENTURE_COOLDOWN - elapsed)
                await interaction.response.send_message(
                    f"⏳ Cooldown! Tunggu **{remaining} detik** lagi.", ephemeral=True
                )
                return

        await interaction.response.defer()

        # Get player stats
        profile = await db.get_profile(interaction.user.id, interaction.guild.id)
        character["level"] = profile["level"]
        equipment = await db.get_equipped_items(interaction.user.id, interaction.guild.id)
        active_pet = await db.get_active_pet(interaction.user.id, interaction.guild.id)
        stats = calculate_stats(character, equipment, active_pet)

        # Update max HP based on current stats
        await db.update_character_hp(
            interaction.user.id, interaction.guild.id,
            min(character["current_hp"], stats["hp"]),
            stats["hp"]
        )

        # Get monster
        floor = character["floor_level"]
        monster = get_random_monster(floor)
        zone = get_zone_name(floor)

        # Send battle embed
        class_data = CLASSES[character["class_name"]]
        pet_info = ""
        if active_pet:
            from game_data import PETS
            pd = PETS.get(active_pet["pet_id"], {})
            pet_info = f"🐾 {pd.get('emoji', '')} {active_pet.get('pet_name') or pd.get('name', '')}"

        initial_log = f"🌟 Kamu menemukan **{monster['emoji']} {monster['name']}** di {zone}!"

        embed = create_battle_embed(
            player_name=interaction.user.display_name,
            player_class_emoji=class_data["emoji"],
            player_hp=character["current_hp"], player_max_hp=stats["hp"],
            player_atk=stats["atk"], player_def=stats["def"],
            player_pet_info=pet_info,
            monster_name=monster["name"], monster_emoji=monster["emoji"],
            monster_hp=monster["hp"], monster_max_hp=monster["hp"],
            monster_atk=monster["atk"], monster_def=monster["def"],
            floor=floor, zone_name=zone,
            battle_log=initial_log,
        )

        msg = await interaction.followup.send(embed=embed, wait=True)

        # Create battle in DB
        battle_id = await db.create_battle(
            interaction.user.id, interaction.guild.id,
            interaction.channel.id, msg.id,
            monster, floor
        )
        await db.update_battle(battle_id, monster["hp"], initial_log)
        await db.update_last_adventure(interaction.user.id, interaction.guild.id)

        # Add battle view
        view = BattleView(interaction.user.id, battle_id, self)
        await msg.edit(view=view)

    @app_commands.command(name="boss", description="Tantang boss di floor saat ini!")
    async def boss_command(self, interaction: discord.Interaction):
        """Challenge the boss at the current floor."""
        character = await db.get_character(interaction.user.id, interaction.guild.id)
        if not character:
            await interaction.response.send_message(
                "❌ Kamu belum punya karakter! Gunakan `/start`.", ephemeral=True
            )
            return

        # Check active battle
        active = await db.get_active_battle(interaction.user.id, interaction.guild.id)
        if active:
            await interaction.response.send_message(
                "⚔️ Kamu masih dalam pertempuran!", ephemeral=True
            )
            return

        if character["current_hp"] <= 0:
            await interaction.response.send_message(
                "💀 HP kamu habis! Gunakan `/heal`.", ephemeral=True
            )
            return

        floor = character["floor_level"]
        boss = get_boss(floor)
        if not boss:
            await interaction.response.send_message(
                f"🏔️ Tidak ada boss di Floor **{floor}**. Boss muncul setiap 5 floor (5, 10, 15, ...).\n"
                f"Gunakan `/adventure` untuk melawan monster biasa.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        # Get player stats
        profile = await db.get_profile(interaction.user.id, interaction.guild.id)
        character["level"] = profile["level"]
        equipment = await db.get_equipped_items(interaction.user.id, interaction.guild.id)
        active_pet = await db.get_active_pet(interaction.user.id, interaction.guild.id)
        stats = calculate_stats(character, equipment, active_pet)

        await db.update_character_hp(
            interaction.user.id, interaction.guild.id,
            min(character["current_hp"], stats["hp"]), stats["hp"]
        )

        zone = get_zone_name(floor)
        class_data = CLASSES[character["class_name"]]
        pet_info = ""
        if active_pet:
            from game_data import PETS
            pd = PETS.get(active_pet["pet_id"], {})
            pet_info = f"🐾 {pd.get('emoji', '')} {active_pet.get('pet_name') or pd.get('name', '')}"

        initial_log = f"👹 **BOSS MUNCUL!** {boss['emoji']} {boss['name']} menghalangi jalanmu!"

        embed = create_battle_embed(
            player_name=interaction.user.display_name,
            player_class_emoji=class_data["emoji"],
            player_hp=character["current_hp"], player_max_hp=stats["hp"],
            player_atk=stats["atk"], player_def=stats["def"],
            player_pet_info=pet_info,
            monster_name=boss["name"], monster_emoji=boss["emoji"],
            monster_hp=boss["hp"], monster_max_hp=boss["hp"],
            monster_atk=boss["atk"], monster_def=boss["def"],
            floor=floor, zone_name=zone,
            battle_log=initial_log,
            is_boss=True,
            image_url=boss.get("image"),
        )

        msg = await interaction.followup.send(embed=embed, wait=True)

        battle_id = await db.create_battle(
            interaction.user.id, interaction.guild.id,
            interaction.channel.id, msg.id,
            boss, floor, is_boss=True
        )
        await db.update_battle(battle_id, boss["hp"], initial_log)
        await db.update_last_adventure(interaction.user.id, interaction.guild.id)

        view = BattleView(interaction.user.id, battle_id, self)
        await msg.edit(view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(AdventureCog(bot))
