import discord
from discord import ui
import json
import logging
from datetime import datetime, timezone
import os

USER_DATA_FILE = 'user_data.json'

class OnboardingButton(ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.green,
            label="🔒 Book Your Onboarding Call",
            custom_id="book_onboarding"
        )

    async def callback(self, interaction: discord.Interaction):
        """Handle button click"""
        logging.info(f"Button callback triggered for user {interaction.user.id}")
        
        try:
            # Load user data
            try:
                with open(USER_DATA_FILE, 'r') as f:
                    user_data = json.load(f)
            except FileNotFoundError:
                user_data = {}
            
            user_id = str(interaction.user.id)
            current_time = datetime.now(timezone.utc).timestamp()
            
            # Check if user already has access
            if user_id in user_data and user_data[user_id].get('has_access', False):
                embed = discord.Embed(
                    title="✅ Already Have Access!",
                    description="You already have access to the community. Welcome back!",
                    color=0x00ff00
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                logging.info(f"User {user_id} already has access")
                return
            
            # Check if user has unverified role
            unverified_role_id = int(os.getenv('UNVERIFIED_ROLE_ID', 0))
            has_unverified_role = False
            
            if unverified_role_id and interaction.guild:
                unverified_role = interaction.guild.get_role(unverified_role_id)
                if unverified_role and unverified_role in interaction.user.roles:
                    has_unverified_role = True
                    logging.info(f"User {user_id} has unverified role")
            
            # Record the button click
            user_data[user_id] = {
                'button_clicked_at': current_time,
                'has_access': False,
                'role_assigned': False,
                'unverified_role_assigned': has_unverified_role
            }
            
            # Save user data
            with open(USER_DATA_FILE, 'w') as f:
                json.dump(user_data, f, indent=2)
            
            logging.info(f"Recorded button click for user {user_id} with unverified_role_assigned: {has_unverified_role}")
            
            # Send ephemeral message
            embed = discord.Embed(
                title="📅 Book Your Onboarding Call Below",
                description=(
                    "**Free Onboarding Call - For strategic planning**\n\n"
                    "👉 **FREE ONBOARDING CALL** 👈\n\n"
                    "After booking, return here and try again with the same email address.\n\n"
                    "*(If you already booked a call, you'll receive access to the community in 5 minutes.)*"
                ),
                color=0x00ff00
            )
            
            # Add Calendly link
            calendly_link = os.getenv('CALENDLY_LINK', 'https://calendly.com/ajtradingprofits-support/mastermind-call')
            embed.add_field(
                name="🔗 Book Your Call",
                value=f"[Click here to book your free onboarding call]({calendly_link})",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logging.info(f"Sent ephemeral message to user {user_id}")
            
            # Log to logs channel
            logs_channel_id = int(os.getenv('LOGS_CHANNEL_ID', 0))
            if logs_channel_id:
                guild = interaction.guild
                if guild:
                    logs_channel = guild.get_channel(logs_channel_id)
                    if logs_channel:
                        embed = discord.Embed(
                            title="🔒 Onboarding Button Clicked",
                            description=f"**{interaction.user.mention}** clicked the onboarding button",
                            color=0x0099ff,
                            timestamp=datetime.now(timezone.utc)
                        )
                        embed.add_field(name="User ID", value=f"`{user_id}`", inline=True)
                        embed.add_field(name="Action", value="🔒 Button Clicked", inline=True)
                        embed.add_field(name="Has Unverified Role", value=f"{'✅ Yes' if has_unverified_role else '❌ No'}", inline=True)
                        embed.set_thumbnail(url=interaction.user.display_avatar.url)
                        
                        await logs_channel.send(embed=embed)
            
        except Exception as e:
            logging.error(f"Error in button callback: {e}")
            await interaction.response.send_message(
                "❌ An error occurred. Please try again later.", 
                ephemeral=True
            )

class VerificationView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(OnboardingButton())

async def setup(bot):
    # This cog doesn't need any setup, just the VerificationView class
    pass 