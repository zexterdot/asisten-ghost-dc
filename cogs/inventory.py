"""
cogs/inventory.py — Inventory management, equip, unequip, use items
Ghost Assistant RPG
"""

import discord
from discord.ext import commands
from discord import app_commands
import database as db
from game_data import ITEMS, RARITY_EMOJI
from utils import get_item_display, format_rarity, get_rarity_color


class InventoryCog(commands.Cog):
    """Inventory management commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="inventory", description="Lihat semua item di inventory kamu")
    async def inventory_command(self, interaction: discord.Interaction):
        """View inventory."""
        character = await db.get_character(interaction.user.id, interaction.guild.id)
        if not character:
            await interaction.response.send_message(
                "❌ Kamu belum punya karakter! Gunakan `/start`.", ephemeral=True
            )
            return

        await interaction.response.defer()
        items = await db.get_inventory(interaction.user.id, interaction.guild.id)

        if not items:
            embed = discord.Embed(
                title="🎒 Inventory — Kosong",
                description="Inventory kamu masih kosong!\n"
                            "🗡️ Gunakan `/adventure` untuk mendapat loot\n"
                            "🛒 Atau beli di `/shop`",
                color=0x2ECC71,
            )
            await interaction.followup.send(embed=embed)
            return

        # Group items by type
        categories = {"weapon": [], "armor": [], "accessory": [], "consumable": [], "material": []}
        for item in items:
            item_data = ITEMS.get(item["item_id"])
            if not item_data:
                continue
            item_type = item_data.get("type", "material")
            equipped_tag = " `[EQUIPPED]`" if item["is_equipped"] else ""
            qty_tag = f" x{item['quantity']}" if item["quantity"] > 1 and not item["is_equipped"] else ""
            rarity_emoji = RARITY_EMOJI.get(item_data.get("rarity", "common"), "⬜")
            line = f"{rarity_emoji} {item_data['emoji']} **{item_data['name']}**{qty_tag}{equipped_tag}"
            if item_type in categories:
                categories[item_type].append(line)
            else:
                categories["material"].append(line)

        embed = discord.Embed(
            title=f"🎒 Inventory — {interaction.user.display_name}",
            color=0x2ECC71,
        )

        category_names = {
            "weapon": "⚔️ Senjata",
            "armor": "🛡️ Armor",
            "accessory": "💍 Aksesoris",
            "consumable": "🧪 Consumable",
            "material": "📦 Material",
        }

        for cat_key, cat_name in category_names.items():
            if categories[cat_key]:
                embed.add_field(
                    name=cat_name,
                    value="\n".join(categories[cat_key][:10]),
                    inline=False,
                )

        embed.set_footer(text="Gunakan /equip untuk memasang equipment | /use untuk pakai consumable")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="equip", description="Pasang equipment (weapon/armor/accessory)")
    @app_commands.describe(item="Nama item yang ingin dipasang")
    async def equip_command(self, interaction: discord.Interaction, item: str):
        """Equip an item."""
        character = await db.get_character(interaction.user.id, interaction.guild.id)
        if not character:
            await interaction.response.send_message(
                "❌ Kamu belum punya karakter! Gunakan `/start`.", ephemeral=True
            )
            return

        # Find item by name (case insensitive)
        item_lower = item.lower().strip()
        found_id = None
        for item_id, item_data in ITEMS.items():
            if item_data["name"].lower() == item_lower or item_id == item_lower:
                if item_data["type"] in ("weapon", "armor", "accessory"):
                    found_id = item_id
                    break

        if not found_id:
            await interaction.response.send_message(
                f"❌ Item **{item}** tidak ditemukan atau bukan equipment!\n"
                f"Gunakan `/inventory` untuk melihat item yang kamu punya.",
                ephemeral=True,
            )
            return

        item_data = ITEMS[found_id]
        success = await db.equip_item(
            interaction.user.id, interaction.guild.id,
            found_id, item_data["type"]
        )

        if not success:
            await interaction.response.send_message(
                f"❌ Kamu tidak punya **{item_data['emoji']} {item_data['name']}** di inventory!",
                ephemeral=True,
            )
            return

        stats_text = ""
        if "stats" in item_data:
            stat_lines = []
            for stat, value in item_data["stats"].items():
                if stat == "crit":
                    stat_lines.append(f"🎯 Crit +{value:.0%}")
                else:
                    emoji_map = {"atk": "⚔️", "def": "🛡️", "hp": "❤️", "spd": "💨"}
                    stat_lines.append(f"{emoji_map.get(stat, '📊')} {stat.upper()} +{value}")
            stats_text = " | ".join(stat_lines)

        embed = discord.Embed(
            title="✅ Equipment Dipasang!",
            description=f"{item_data['emoji']} **{item_data['name']}** ({item_data['type']})\n"
                        f"{format_rarity(item_data['rarity'])}\n"
                        f"📊 {stats_text}",
            color=get_rarity_color(item_data["rarity"]),
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unequip", description="Lepas equipment dari slot")
    @app_commands.describe(slot="Slot yang ingin dilepas")
    @app_commands.choices(slot=[
        app_commands.Choice(name="⚔️ Weapon", value="weapon"),
        app_commands.Choice(name="🛡️ Armor", value="armor"),
        app_commands.Choice(name="💍 Accessory", value="accessory"),
    ])
    async def unequip_command(self, interaction: discord.Interaction, slot: str):
        """Unequip item from slot."""
        unequipped_id = await db.unequip_item(interaction.user.id, interaction.guild.id, slot)

        if not unequipped_id:
            slot_names = {"weapon": "Senjata", "armor": "Armor", "accessory": "Aksesoris"}
            await interaction.response.send_message(
                f"❌ Tidak ada equipment di slot **{slot_names.get(slot, slot)}**!",
                ephemeral=True,
            )
            return

        item_data = ITEMS.get(unequipped_id, {})
        await interaction.response.send_message(
            f"✅ **{item_data.get('emoji', '❓')} {item_data.get('name', unequipped_id)}** dilepas dan dikembalikan ke inventory.",
        )

    @app_commands.command(name="use", description="Gunakan item consumable (potion, boost)")
    @app_commands.describe(item="Nama item yang ingin digunakan")
    async def use_command(self, interaction: discord.Interaction, item: str):
        """Use a consumable item."""
        character = await db.get_character(interaction.user.id, interaction.guild.id)
        if not character:
            await interaction.response.send_message(
                "❌ Kamu belum punya karakter! Gunakan `/start`.", ephemeral=True
            )
            return

        # Find consumable
        item_lower = item.lower().strip()
        found_id = None
        for item_id, item_data in ITEMS.items():
            if (item_data["name"].lower() == item_lower or item_id == item_lower) and item_data["type"] == "consumable":
                found_id = item_id
                break

        if not found_id:
            await interaction.response.send_message(
                f"❌ Item consumable **{item}** tidak ditemukan!",
                ephemeral=True,
            )
            return

        # Check if has item
        count = await db.get_item_count(interaction.user.id, interaction.guild.id, found_id)
        if count <= 0:
            await interaction.response.send_message(
                f"❌ Kamu tidak punya **{ITEMS[found_id]['name']}**!",
                ephemeral=True,
            )
            return

        item_data = ITEMS[found_id]
        effect = item_data.get("effect", {})

        if "heal" in effect:
            # Get current stats for max HP
            profile = await db.get_profile(interaction.user.id, interaction.guild.id)
            character["level"] = profile["level"]
            equipment = await db.get_equipped_items(interaction.user.id, interaction.guild.id)
            active_pet = await db.get_active_pet(interaction.user.id, interaction.guild.id)
            from utils import calculate_stats
            stats = calculate_stats(character, equipment, active_pet)

            old_hp = character["current_hp"]
            new_hp = min(stats["hp"], old_hp + effect["heal"])
            actual_heal = new_hp - old_hp

            if actual_heal <= 0:
                await interaction.response.send_message(
                    "❤️ HP kamu sudah penuh!", ephemeral=True
                )
                return

            await db.remove_item(interaction.user.id, interaction.guild.id, found_id)
            await db.update_character_hp(interaction.user.id, interaction.guild.id, new_hp)

            embed = discord.Embed(
                title=f"🧪 {item_data['name']} Digunakan!",
                description=f"❤️ +{actual_heal} HP\n"
                            f"HP: **{old_hp}** → **{new_hp}** / {stats['hp']}",
                color=0x2ECC71,
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                f"ℹ️ Item ini hanya bisa digunakan saat battle!",
                ephemeral=True,
            )

    @equip_command.autocomplete("item")
    async def equip_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplete for equip command."""
        items = await db.get_inventory(interaction.user.id, interaction.guild.id)
        choices = []
        for inv_item in items:
            if inv_item["is_equipped"]:
                continue
            item_data = ITEMS.get(inv_item["item_id"])
            if not item_data or item_data["type"] not in ("weapon", "armor", "accessory"):
                continue
            name = item_data["name"]
            if current.lower() in name.lower():
                choices.append(app_commands.Choice(name=name, value=name))
        return choices[:25]

    @use_command.autocomplete("item")
    async def use_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplete for use command."""
        items = await db.get_inventory(interaction.user.id, interaction.guild.id)
        choices = []
        for inv_item in items:
            item_data = ITEMS.get(inv_item["item_id"])
            if not item_data or item_data["type"] != "consumable":
                continue
            name = item_data["name"]
            if current.lower() in name.lower():
                choices.append(app_commands.Choice(name=f"{name} (x{inv_item['quantity']})", value=name))
        return choices[:25]


async def setup(bot: commands.Bot):
    await bot.add_cog(InventoryCog(bot))
