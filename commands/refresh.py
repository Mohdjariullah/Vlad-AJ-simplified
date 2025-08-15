import discord
from discord.ext import commands
from datetime import datetime
import os
import logging
from cogs.verification import VerificationView

async def setup(bot):
    @bot.tree.command(name="refresh", description="Refresh the welcome message")
    async def refresh_welcome(interaction: discord.Interaction):
        """Refresh the welcome message in the welcome channel"""
        try:
            # SECURITY: Check authorization
            from main import is_authorized_guild_or_owner
            if not is_authorized_guild_or_owner(interaction):
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ You are not authorized to use this command.", ephemeral=True
                    )
                return
            
            # SECURITY: Block DMs and check admin permissions
            if not interaction.guild:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ This command can only be used in a server!", ephemeral=True)
                return
            
            if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.administrator:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ You need Administrator permissions!", ephemeral=True)
                return
            
            # Get configuration from main.py
            from main import WELCOME_CHANNEL_ID, get_or_create_welcome_message
            
            # Get the welcome channel
            welcome_channel = interaction.guild.get_channel(WELCOME_CHANNEL_ID)
            if not welcome_channel:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Welcome channel not found!", ephemeral=True)
                return
            
            # Create welcome embed
            embed = discord.Embed(
                title="**__👋 WELCOME TO THE AJ TRADING ACADEMY!__**",
                description=(
                    "To maximize your free community access & the education inside, book your free onboarding call below.\n\n"
                    "You'll speak to our senior trading success coach, who will show you how you can make the most out of your free membership and discover:\n\n"
                    "• What you're currently doing right in your trading\n"
                    "• What you're currently doing wrong in your trading\n"
                    "• How can you can improve to hit your trading goals ASAP\n\n"
                    "You will learn how you can take advantage of the free community and education to get on track to consistent market profits in just 60 minutes per day without hit-or-miss time-consuming strategies, risky trades, or losing thousands on failed challenges.\n\n"
                    "(If you have already booked your onboarding call on the last page click the button below and you'll automatically gain access to the community)"
                ),
                color=0xFFFFFF
            )
            embed.set_footer(text="Book Your Onboarding Call Today!")
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1370122090631532655/1401222798336200834/20.38.48_73b12891.jpg")
            
            # Use VerificationView
            try:
                msg = await get_or_create_welcome_message(welcome_channel, embed, VerificationView())
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"✅ Welcome message refreshed! {msg.jump_url}", ephemeral=True)
            except Exception as e:
                logging.error(f"Error refreshing welcome message: {e}")
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Failed to refresh welcome message. Check logs for details.", ephemeral=True)
                    
        except Exception as e:
            logging.error(f"Error in refresh command: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ An error occurred while processing the command.", ephemeral=True)
            except Exception as response_error:
                logging.error(f"Error sending error response: {response_error}") 