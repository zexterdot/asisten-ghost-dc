"""
utils.py — Helper functions untuk Ghost Assistant RPG
Progress bars, embed builders, formatters
"""

import discord
from game_data import RARITY_COLORS, RARITY_EMOJI, ITEMS, CLASSES


def progress_bar(current: int, maximum: int, length: int = 10, filled: str = "█", empty: str = "░") -> str:
    """Generate ASCII progress bar."""
    if maximum <= 0:
        return empty * length
    ratio = min(current / maximum, 1.0)
    filled_count = int(ratio * length)
    empty_count = length - filled_count
    return filled * filled_count + empty * empty_count


def hp_bar(current: int, maximum: int) -> str:
    """Generate HP bar with emoji."""
    bar = progress_bar(current, maximum)
    return f"❤️ [{bar}] {current}/{maximum}"


def xp_bar(current_xp: int, needed_xp: int, level: int) -> str:
    """Generate XP bar with level info."""
    bar = progress_bar(current_xp, needed_xp)
    return f"⭐ Lv.{level} [{bar}] {current_xp}/{needed_xp}"


def pet_xp_bar(current: int, needed: int, level: int) -> str:
    """Generate pet XP bar."""
    bar = progress_bar(current, needed)
    return f"🐾 Lv.{level} [{bar}] {current}/{needed}"


def format_coins(amount: int) -> str:
    """Format coins with emoji and thousands separator."""
    return f"🪙 {amount:,}"


def format_rarity(rarity: str) -> str:
    """Format rarity with emoji."""
    emoji = RARITY_EMOJI.get(rarity, "⬜")
    return f"{emoji} {rarity.capitalize()}"


def get_item_display(item_id: str) -> str:
    """Get display string for an item."""
    item = ITEMS.get(item_id)
    if not item:
        return f"❓ {item_id}"
    return f"{item['emoji']} {item['name']}"


def get_rarity_color(rarity: str) -> int:
    """Get embed color for rarity."""
    return RARITY_COLORS.get(rarity, 0x969696)


def calculate_stats(character: dict, equipment: list, active_pet: dict = None) -> dict:
    """
    Calculate total stats including base, level bonus, equipment, and pet.
    Returns dict with: hp, atk, def, spd, crit
    """
    class_data = CLASSES.get(character["class_name"])
    if not class_data:
        return {"hp": 100, "atk": 10, "def": 10, "spd": 10, "crit": 0.05}

    level = character.get("level", 1)
    level_bonus = class_data["level_bonus"]

    # Base stats + level bonuses
    stats = {
        "hp": class_data["base_hp"] + level_bonus["hp"] * (level - 1),
        "atk": class_data["base_atk"] + level_bonus["atk"] * (level - 1),
        "def": class_data["base_def"] + level_bonus["def"] * (level - 1),
        "spd": class_data["base_spd"] + level_bonus["spd"] * (level - 1),
        "crit": class_data["base_crit"] + level_bonus["crit"] * (level - 1),
    }

    # Equipment bonuses
    for equip in equipment:
        item_data = ITEMS.get(equip.get("item_id", ""))
        if item_data and "stats" in item_data:
            for stat, value in item_data["stats"].items():
                if stat in stats:
                    stats[stat] += value

    # Pet bonuses
    if active_pet:
        from game_data import PETS
        pet_data = PETS.get(active_pet.get("pet_id", ""))
        if pet_data:
            pet_level = active_pet.get("pet_level", 1)
            for stat, value in pet_data["bonus"].items():
                if stat in stats:
                    stats[stat] += value
            # Pet level bonus
            for stat, value in pet_data.get("level_bonus", {}).items():
                if stat in stats:
                    stats[stat] += value * (pet_level - 1)

    return stats


def create_profile_embed(user: discord.Member, profile: dict, character: dict,
                         stats: dict, rank: int, total_users: int,
                         active_pet: dict = None) -> discord.Embed:
    """Create a rich profile embed."""
    class_data = CLASSES.get(character["class_name"], {})
    class_emoji = class_data.get("emoji", "❓")
    class_name = class_data.get("name", "Unknown")

    embed = discord.Embed(
        title=f"{class_emoji} {user.display_name}",
        description=f"**{class_name}** — Rank #{rank}/{total_users}",
        color=0x5865F2,
    )

    # Level & XP
    from database import get_total_xp_for_level
    current_level = profile["level"]
    current_xp = profile["xp"]
    xp_for_current = get_total_xp_for_level(current_level)
    xp_for_next = get_total_xp_for_level(current_level + 1)
    xp_in_level = current_xp - xp_for_current
    xp_needed = xp_for_next - xp_for_current

    embed.add_field(
        name="📊 Level & XP",
        value=f"{xp_bar(xp_in_level, xp_needed, current_level)}\n"
              f"Total XP: **{current_xp:,}**",
        inline=False,
    )

    # Stats
    embed.add_field(
        name="📋 Stats",
        value=f"❤️ HP: **{stats['hp']}** | ⚔️ ATK: **{stats['atk']}**\n"
              f"🛡️ DEF: **{stats['def']}** | 💨 SPD: **{stats['spd']}**\n"
              f"🎯 Crit: **{stats['crit']:.0%}**",
        inline=True,
    )

    # Economy
    embed.add_field(
        name="💰 Ekonomi",
        value=f"🪙 Coins: **{profile['coins']:,}**\n"
              f"🔥 Daily Streak: **{profile['daily_streak']}**",
        inline=True,
    )

    # Game stats
    win_rate = 0
    if profile["total_games"] > 0:
        win_rate = profile["games_won"] / profile["total_games"] * 100
    embed.add_field(
        name="🎮 Game Stats",
        value=f"Total: **{profile['total_games']}** game\n"
              f"Menang: **{profile['games_won']}** ({win_rate:.0f}%)\n"
              f"🏔️ Floor: **{character.get('floor_level', 1)}**",
        inline=True,
    )

    # Active pet
    if active_pet:
        from game_data import PETS
        pet_data = PETS.get(active_pet["pet_id"], {})
        pet_name = active_pet.get("pet_name") or pet_data.get("name", "Unknown")
        pet_emoji = pet_data.get("emoji", "🐾")
        embed.add_field(
            name="🐾 Pet Aktif",
            value=f"{pet_emoji} **{pet_name}** (Lv.{active_pet['pet_level']})\n"
                  f"{format_rarity(pet_data.get('rarity', 'common'))}",
            inline=True,
        )

    embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text="Ghost Assistant RPG • /help untuk daftar command")

    return embed


def create_battle_embed(
    player_name: str, player_class_emoji: str, player_hp: int, player_max_hp: int,
    player_atk: int, player_def: int, player_pet_info: str,
    monster_name: str, monster_emoji: str, monster_hp: int, monster_max_hp: int,
    monster_atk: int, monster_def: int,
    floor: int, zone_name: str, battle_log: str = "",
    is_boss: bool = False, image_url: str = None,
) -> discord.Embed:
    """Create a battle embed with HP bars and action log."""
    title = f"👹 BOSS BATTLE — Floor {floor}" if is_boss else f"⚔️ BATTLE — Floor {floor}"
    color = 0xFF6B35 if is_boss else 0xE74C3C

    embed = discord.Embed(
        title=f"{title}: {zone_name}",
        color=color,
    )

    # Monster info
    monster_bar = progress_bar(monster_hp, monster_max_hp)
    embed.add_field(
        name=f"{monster_emoji} {monster_name}",
        value=f"❤️ [{monster_bar}] {monster_hp}/{monster_max_hp}\n"
              f"⚔️ ATK: {monster_atk} | 🛡️ DEF: {monster_def}",
        inline=False,
    )

    embed.add_field(name="\u200b", value="⚡ **VS** ⚡", inline=False)

    # Player info
    player_bar = progress_bar(player_hp, player_max_hp)
    pet_text = f" | {player_pet_info}" if player_pet_info else ""
    embed.add_field(
        name=f"{player_class_emoji} {player_name}",
        value=f"❤️ [{player_bar}] {player_hp}/{player_max_hp}\n"
              f"⚔️ ATK: {player_atk} | 🛡️ DEF: {player_def}{pet_text}",
        inline=False,
    )

    # Battle log
    if battle_log:
        if len(battle_log) > 1024:
            battle_log = battle_log[-1020:] + "..."
        embed.add_field(name="📜 Battle Log", value=battle_log, inline=False)

    if image_url:
        embed.set_thumbnail(url=image_url)

    return embed
