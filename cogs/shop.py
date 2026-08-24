"""
cogs/shop.py — Shop system: buy and sell items
Ghost Assistant RPG
"""

import discord
from discord.ext import commands
from discord import app_commands
import database as db
from game_data import ITEMS, SHOP_ITEMS, RARITY_EMOJI
from utils import format_coins, format_rarity, get_rarity_color


ITEMS_PER_PAGE = 8


class ShopView(discord.ui.View):
    """Paginated shop view."""

    def __init__(self, user_id: int, pages: list, current_page: int = 0):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.pages = pages
        self.current_page = current_page
        self.update_buttons()

    def update_buttons(self):
        self.prev_btn.disabled = self.current_page <= 0
        self.next_btn.disabled = self.current_page >= len(self.pages) - 1

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Ini bukan shop kamu!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="◀️ Prev", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = max(0, self.current_page - 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = min(len(self.pages) - 1, self.current_page + 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)


class ShopCog(commands.Cog):
    """Shop buy/sell commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="shop", description="Lihat dan beli item di shop!")
    async def shop_command(self, interaction: discord.Interaction):
        """View the shop."""
        profile = await db.get_profile(interaction.user.id, interaction.guild.id)

        # Group shop items by type
        categories = {"weapon": [], "armor": [], "accessory": [], "consumable": []}
        for item_id, item_data in sorted(SHOP_ITEMS.items(), key=lambda x: x[1].get("buy_price", 0)):
            item_type = item_data.get("type", "consumable")
            if item_type in categories:
                categories[item_type].append((item_id, item_data))

        # Build pages
        pages = []
        all_items = []
        for cat_name, cat_items in categories.items():
            all_items.extend(cat_items)

        for i in range(0, len(all_items), ITEMS_PER_PAGE):
            page_items = all_items[i:i + ITEMS_PER_PAGE]
            embed = discord.Embed(
                title="🛒 Ghost Shop",
                description=f"🪙 Koin kamu: **{profile['coins']:,}**\n"
                            f"Gunakan `/buy [item]` untuk membeli.",
                color=0xF1C40F,
            )

            for item_id, item_data in page_items:
                rarity_e = RARITY_EMOJI.get(item_data.get("rarity", "common"), "⬜")
                price = item_data.get("buy_price", "?")
                stats_text = ""
                if "stats" in item_data:
                    parts = []
                    for stat, val in item_data["stats"].items():
                        if stat == "crit":
                            parts.append(f"Crit +{val:.0%}")
                        else:
                            parts.append(f"{stat.upper()} +{val}")
                    stats_text = f" ({', '.join(parts)})"
                elif "effect" in item_data:
                    eff = item_data["effect"]
                    if "heal" in eff:
                        stats_text = f" (Heal {eff['heal']} HP)"

                embed.add_field(
                    name=f"{rarity_e} {item_data['emoji']} {item_data['name']} — 🪙 {price}",
                    value=f"{item_data['description']}{stats_text}",
                    inline=False,
                )

            page_num = i // ITEMS_PER_PAGE + 1
            total_pages = (len(all_items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
            embed.set_footer(text=f"Halaman {page_num}/{total_pages} | /sell [item] untuk jual item")
            pages.append(embed)

        if not pages:
            await interaction.response.send_message("🛒 Shop sedang kosong!", ephemeral=True)
            return

        view = ShopView(interaction.user.id, pages) if len(pages) > 1 else None
        await interaction.response.send_message(embed=pages[0], view=view)

    @app_commands.command(name="buy", description="Beli item dari shop")
    @app_commands.describe(item="Nama item yang ingin dibeli", jumlah="Jumlah (default: 1)")
    async def buy_command(self, interaction: discord.Interaction, item: str, jumlah: int = 1):
        """Buy an item from the shop."""
        if jumlah < 1:
            await interaction.response.send_message("❌ Jumlah minimal 1!", ephemeral=True)
            return

        # Find item
        item_lower = item.lower().strip()
        found_id = None
        for item_id, item_data in SHOP_ITEMS.items():
            if item_data["name"].lower() == item_lower or item_id == item_lower:
                found_id = item_id
                break

        if not found_id:
            await interaction.response.send_message(
                f"❌ Item **{item}** tidak ada di shop!\nGunakan `/shop` untuk melihat daftar.",
                ephemeral=True,
            )
            return

        item_data = ITEMS[found_id]
        total_cost = item_data["buy_price"] * jumlah

        # Check coins
        profile = await db.get_profile(interaction.user.id, interaction.guild.id)
        if profile["coins"] < total_cost:
            await interaction.response.send_message(
                f"❌ Koin tidak cukup! Butuh **{total_cost:,}** 🪙, kamu punya **{profile['coins']:,}** 🪙.",
                ephemeral=True,
            )
            return

        # Purchase
        await db.add_coins(interaction.user.id, interaction.guild.id, -total_cost)
        await db.add_item(interaction.user.id, interaction.guild.id, found_id, jumlah)

        embed = discord.Embed(
            title="✅ Pembelian Berhasil!",
            description=f"{item_data['emoji']} **{item_data['name']}** x{jumlah}\n"
                        f"💰 Total: **-{total_cost:,}** 🪙\n"
                        f"💰 Sisa: **{profile['coins'] - total_cost:,}** 🪙",
            color=0x2ECC71,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sell", description="Jual item dari inventory")
    @app_commands.describe(item="Nama item yang ingin dijual", jumlah="Jumlah (default: 1)")
    async def sell_command(self, interaction: discord.Interaction, item: str, jumlah: int = 1):
        """Sell an item from inventory."""
        if jumlah < 1:
            await interaction.response.send_message("❌ Jumlah minimal 1!", ephemeral=True)
            return

        # Find item
        item_lower = item.lower().strip()
        found_id = None
        for item_id, item_data in ITEMS.items():
            if item_data["name"].lower() == item_lower or item_id == item_lower:
                found_id = item_id
                break

        if not found_id:
            await interaction.response.send_message(
                f"❌ Item **{item}** tidak ditemukan!", ephemeral=True
            )
            return

        item_data = ITEMS[found_id]
        sell_price = item_data.get("sell_price", 1)
        total_earn = sell_price * jumlah

        # Try to remove from inventory
        success = await db.remove_item(interaction.user.id, interaction.guild.id, found_id, jumlah)
        if not success:
            await interaction.response.send_message(
                f"❌ Kamu tidak punya cukup **{item_data['name']}** di inventory!",
                ephemeral=True,
            )
            return

        await db.add_coins(interaction.user.id, interaction.guild.id, total_earn)

        embed = discord.Embed(
            title="💰 Item Terjual!",
            description=f"{item_data['emoji']} **{item_data['name']}** x{jumlah}\n"
                        f"💰 Dapat: **+{total_earn:,}** 🪙",
            color=0xF1C40F,
        )
        await interaction.response.send_message(embed=embed)

    @buy_command.autocomplete("item")
    async def buy_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplete for buy command."""
        choices = []
        for item_id, item_data in SHOP_ITEMS.items():
            name = item_data["name"]
            if current.lower() in name.lower():
                price = item_data.get("buy_price", "?")
                choices.append(app_commands.Choice(name=f"{name} — 🪙 {price}", value=name))
        return choices[:25]

    @sell_command.autocomplete("item")
    async def sell_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplete for sell command."""
        items = await db.get_inventory(interaction.user.id, interaction.guild.id)
        choices = []
        seen = set()
        for inv_item in items:
            if inv_item["is_equipped"]:
                continue
            item_data = ITEMS.get(inv_item["item_id"])
            if not item_data or inv_item["item_id"] in seen:
                continue
            seen.add(inv_item["item_id"])
            name = item_data["name"]
            if current.lower() in name.lower():
                price = item_data.get("sell_price", 1)
                choices.append(app_commands.Choice(
                    name=f"{name} (x{inv_item['quantity']}) — 🪙 {price} ea",
                    value=name,
                ))
        return choices[:25]


async def setup(bot: commands.Bot):
    await bot.add_cog(ShopCog(bot))
