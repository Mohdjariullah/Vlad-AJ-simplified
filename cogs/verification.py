import discord
from discord import ui
import json
import logging
from datetime import datetime, timezone
import os
import time
from utils import safe_json_write, safe_json_read, report_critical_error

USER_DATA_FILE = 'user_data.json'
COOLDOWN_FILE = 'button_cooldowns.json'
RATE_LIMIT_SECONDS = 10  # 10 second rate limit

class OnboardingButton(ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.green,
            label="🔒 Book Your Onboarding Call",
            custom_id="book_onboarding"
        )
        # Load cooldowns from file
        self.button_cooldowns = self.load_cooldowns()

    def load_cooldowns(self):
        """Load cooldowns from file"""
        try:
            data = safe_json_read(COOLDOWN_FILE, {})
            # Filter out expired cooldowns
            current_time = time.time()
            cooldowns = {}
            for user_id_str, last_click in data.items():
                if current_time - last_click < RATE_LIMIT_SECONDS:
                    cooldowns[user_id_str] = last_click
            return cooldowns
        except Exception as e:
            logging.error(f"Error loading cooldowns: {e}")
            return {}

    def save_cooldowns(self):
        """Save cooldowns to file"""
        safe_json_write(COOLDOWN_FILE, self.button_cooldowns)

    def cleanup_expired_cooldowns(self):
        """Remove expired cooldowns from memory and file"""
        current_time = time.time()
        expired_users = []
        
        for user_id, last_click in self.button_cooldowns.items():
            if current_time - last_click >= RATE_LIMIT_SECONDS:
                expired_users.append(user_id)
        
        for user_id in expired_users:
            del self.button_cooldowns[user_id]
        
        if expired_users:
            self.save_cooldowns()
            logging.debug(f"Cleaned up {len(expired_users)} expired cooldowns")

    async def callback(self, interaction: discord.Interaction):
        """Handle button click with rate limiting"""
        user_id = str(interaction.user.id)
        current_time = time.time()
        
        # Clean up expired cooldowns periodically
        if len(self.button_cooldowns) > 100:  # Clean up when we have many cooldowns
            self.cleanup_expired_cooldowns()
        
        # Check rate limit
        last_click = self.button_cooldowns.get(user_id, 0)
        if current_time - last_click < RATE_LIMIT_SECONDS:
            remaining_time = int(RATE_LIMIT_SECONDS - (current_time - last_click))
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        f"⏳ Please wait **{remaining_time} seconds** before trying again.",
                        ephemeral=True
                    )
            except Exception as e:
                logging.error(f"Error sending rate limit response: {e}")
            logging.info(f"Rate limited user {user_id} - {remaining_time}s remaining")
            return
        
        logging.info(f"Button callback triggered for user {interaction.user.id}")
        
        try:
            # Load user data
            user_data = safe_json_read(USER_DATA_FILE, {})
            
            # Check roles
            member_role_id = int(os.getenv('MEMBER_ROLE_ID', 0))
            unverified_role_id = int(os.getenv('UNVERIFIED_ROLE_ID', 0))
            
            has_member_role = False
            has_unverified_role = False
            
            if interaction.guild:
                if member_role_id:
                    member_role = interaction.guild.get_role(member_role_id)
                    if member_role and member_role in interaction.user.roles:
                        has_member_role = True
                
                if unverified_role_id:
                    unverified_role = interaction.guild.get_role(unverified_role_id)
                    if unverified_role and unverified_role in interaction.user.roles:
                        has_unverified_role = True
            
            # Check if user already has member role
            if has_member_role:
                embed = discord.Embed(
                    title="✅ Already Verified!",
                    description="You already have access to the community.",
                    color=0x00ff00
                )
                try:
                    if not interaction.response.is_done():
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                except Exception as e:
                    logging.error(f"Error sending already verified response: {e}")
                logging.info(f"User {user_id} already has member role")
                return
            
            # If user doesn't have unverified role, add it
            if not has_unverified_role and unverified_role_id and interaction.guild:
                unverified_role = interaction.guild.get_role(unverified_role_id)
                if unverified_role:
                    try:
                        await interaction.user.add_roles(unverified_role)
                        has_unverified_role = True
                        logging.info(f"Added unverified role to user {user_id}")
                    except Exception as e:
                        logging.error(f"Error adding unverified role to user {user_id}: {e}")
                        # Continue processing even if role assignment fails
            
            # Update cooldown AFTER successful processing
            self.button_cooldowns[user_id] = current_time
            self.save_cooldowns()
            
            # Record the button click (preserve existing data)
            existing_data = user_data.get(user_id, {})
            user_data[user_id] = {
                'joined_at': existing_data.get('joined_at', 0),
                'button_clicked_at': current_time,
                'has_access': False,
                'role_assigned': False,
                'unverified_role_assigned': has_unverified_role
            }
            
            # Save user data
            safe_json_write(USER_DATA_FILE, user_data)
            
            logging.info(f"Recorded button click for user {user_id} with unverified_role_assigned: {has_unverified_role}")
            
            # Send ephemeral message
            embed = discord.Embed(
                title="📅 Book Your Onboarding Call Below",
                description=(
                    "**Free Onboarding Call - For strategic planning**\n\n"
                    f"👉 **[FREE ONBOARDING CALL]({os.getenv('CALENDLY_LINK', 'https://ajtradingprofits.com/book-your-onboarding-call-today')})** 👈\n\n"
                    "You will discover how you can take advantage of the free community and education to get on track to consistent market profits in just 60 minutes per day without hit-or-miss time-consuming strategies, risky trades, or losing thousands on failed challenges.\n\n"
                    "*(If you already booked a call, you'll receive access to the community in 5 minutes.)*"
                ),
                color=0x00ff00
            )
            
            # Add Calendly link
            calendly_link = os.getenv('CALENDLY_LINK', 'https://ajtradingprofits.com/book-your-onboarding-call-today')
            embed.add_field(
                name="🔗 Book Your Call",
                value=f"[Click here to book your free onboarding call]({calendly_link})",
                inline=False
            )
            
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    logging.info(f"Sent ephemeral message to user {user_id}")
            except Exception as e:
                logging.error(f"Error sending main response: {e}")
            
            # Log to logs channel
            logs_channel_id = int(os.getenv('LOGS_CHANNEL_ID', 0))
            if logs_channel_id:
                guild = interaction.guild
                if guild:
                    logs_channel = guild.get_channel(logs_channel_id)
                    if logs_channel:
                        try:
                            log_embed = discord.Embed(
                                title="🔒 Onboarding Button Clicked",
                                description=f"**{interaction.user.mention}** clicked the onboarding button",
                                color=0x0099ff,
                                timestamp=datetime.now(timezone.utc)
                            )
                            log_embed.add_field(name="User ID", value=f"`{user_id}`", inline=True)
                            log_embed.add_field(name="Action", value="🔒 Button Clicked", inline=True)
                            log_embed.add_field(name="Has Unverified Role", value=f"{'✅ Yes' if has_unverified_role else '❌ No'}", inline=True)
                            log_embed.set_thumbnail(url=interaction.user.display_avatar.url)
                            
                            await logs_channel.send(embed=log_embed)
                        except discord.Forbidden:
                            logging.warning(f"Bot doesn't have permission to send messages to logs channel {logs_channel_id}")
                        except Exception as e:
                            logging.error(f"Error sending log message: {e}")
            
        except Exception as e:
            logging.error(f"Error in button callback: {e}")
            
            # Report critical error to owners
            try:
                # Get bot instance from interaction
                bot = interaction.client if hasattr(interaction, 'client') else None
                await report_critical_error("Button Callback Error", f"Error in onboarding button callback: {e}", bot, interaction)
            except Exception as report_error:
                logging.error(f"Failed to report critical error: {report_error}")
            
            # Try to send user-friendly error message
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ An error occurred. Please try again later.", 
                        ephemeral=True
                    )
            except Exception as response_error:
                logging.error(f"Error sending error response: {response_error}")

class VerificationView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(OnboardingButton())

async def setup(bot):
    # This cog doesn't need any setup, just the VerificationView class
    pass 