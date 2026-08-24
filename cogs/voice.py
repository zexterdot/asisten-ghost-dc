"""
cogs/voice.py — Voice channel presence (join & stay 24/7)
Ghost Assistant RPG
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands


class VoiceCog(commands.Cog):
    """Voice channel commands — bot joins and stays 24/7."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.target_channels = {}  # guild_id -> channel_id (remember where to stay)

    @app_commands.command(name="joinvc", description="Bot join voice channel dan stay 24/7")
    @app_commands.describe(channel="Voice channel yang ingin di-join")
    @app_commands.checks.has_permissions(administrator=True)
    async def joinvc_command(self, interaction: discord.Interaction, channel: discord.VoiceChannel = None):
        """Join a voice channel and stay forever."""
        # Use provided channel or user's current voice channel
        if channel is None:
            if interaction.user.voice and interaction.user.voice.channel:
                channel = interaction.user.voice.channel
            else:
                await interaction.response.send_message(
                    "❌ Kamu harus di voice channel atau pilih channel!",
                    ephemeral=True,
                )
                return

        # Check if already in a voice channel in this guild
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_connected():
            if voice_client.channel.id == channel.id:
                await interaction.response.send_message(
                    f"✅ Bot sudah di {channel.mention}!",
                    ephemeral=True,
                )
                return
            # Move to new channel
            await voice_client.move_to(channel)
        else:
            # Join channel
            await channel.connect(self_deaf=True)

        # Remember this channel
        self.target_channels[interaction.guild.id] = channel.id

        embed = discord.Embed(
            title="🔊 Joined Voice Channel!",
            description=f"Bot akan stay di **{channel.name}** 24/7.\n"
                        f"Gunakan `/leavevc` untuk disconnect.",
            color=0x2ECC71,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leavevc", description="Bot leave voice channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def leavevc_command(self, interaction: discord.Interaction):
        """Leave voice channel."""
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_connected():
            channel_name = voice_client.channel.name
            self.target_channels.pop(interaction.guild.id, None)
            await voice_client.disconnect()

            embed = discord.Embed(
                title="🔇 Left Voice Channel",
                description=f"Bot sudah leave dari **{channel_name}**.",
                color=0xE74C3C,
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                "❌ Bot tidak sedang di voice channel!",
                ephemeral=True,
            )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Prevent bot from being disconnected — auto-rejoin if kicked."""
        if member.id != self.bot.user.id:
            return

        # Bot was disconnected
        if before.channel is not None and after.channel is None:
            guild_id = before.channel.guild.id
            target_channel_id = self.target_channels.get(guild_id)

            if target_channel_id:
                # Auto-rejoin
                try:
                    channel = self.bot.get_channel(target_channel_id)
                    if channel:
                        await channel.connect(self_deaf=True)
                except Exception:
                    pass

    @joinvc_command.error
    @leavevc_command.error
    async def voice_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ Hanya admin yang bisa menggunakan command ini!",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceCog(bot))
