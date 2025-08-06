import asyncio
import io
import discord
from discord.ext import commands
from discord import app_commands
import logging
import os
import json
from datetime import datetime, timezone
from .verification import VerificationView

# Import the function from main.py to avoid duplication
from main import get_or_create_welcome_message

WELCOME_MESSAGE_FILE = 'welcome_message.json'
USER_DATA_FILE = 'user_data.json'

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.role_assignment_task = None
        self.logged_members = set()  # Track members that have been logged
        self.load_logged_members()

    @commands.Cog.listener()
    async def on_ready(self):
        """Setup welcome channel when bot is ready (persistent message)"""
        try:
            guild_id = os.getenv('GUILD_ID')
            guild = self.bot.get_guild(int(guild_id)) if guild_id and hasattr(self.bot, 'get_guild') else None
            if not guild:
                logging.error(f"Guild with ID {guild_id} not found")
                return
            welcome_channel_id = os.getenv('WELCOME_CHANNEL_ID')
            if not welcome_channel_id:
                logging.error("WELCOME_CHANNEL_ID is not set in environment variables")
                return
            welcome_channel = self.bot.get_channel(int(welcome_channel_id))
            if not welcome_channel:
                logging.error(f"Welcome channel with ID {welcome_channel_id} not found")
                return
            # Create new welcome embed
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
            embed.set_footer(text="Book Your Onboarding Call Today!")
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1370122090631532655/1401222798336200834/20.38.48_73b12891.jpg")
            # Use persistent message logic
            msg = await get_or_create_welcome_message(welcome_channel, embed, VerificationView())
            logging.info(f"Welcome message is now persistent: {msg.jump_url}")
            
            # Start role assignment loop
            self.role_assignment_task = self.bot.loop.create_task(self.role_assignment_loop())
            
            # Sync user data with actual Discord roles to prevent incorrect assignments
            await self.sync_user_data_with_roles()
        except Exception as e:
            logging.error(f"Error in on_ready welcome setup: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Handle new member joins with duplicate prevention"""
        try:
            guild_id = int(os.getenv('GUILD_ID', 0))
            unverified_role_id = int(os.getenv('UNVERIFIED_ROLE_ID', 0))
            logs_channel_id = int(os.getenv('LOGS_CHANNEL_ID', 0))
            
            if not guild_id or not unverified_role_id:
                logging.error("GUILD_ID or UNVERIFIED_ROLE_ID not set")
                return
            
            guild = member.guild
            if guild.id != guild_id:
                return
            
            # Check if this member has already been logged (duplicate prevention)
            if member.id in self.logged_members:
                logging.info(f"Duplicate member join event for {member.display_name} ({member.id}) - skipping log")
                return
            
            # Mark as logged immediately to prevent duplicates
            self.logged_members.add(member.id)
            self.save_logged_members()
            
            # Get the unverified role
            unverified_role = guild.get_role(unverified_role_id)
            if not unverified_role:
                logging.error(f"Unverified role {unverified_role_id} not found")
                return
            
            # Remove member role first if they have it (in case they rejoined)
            member_role_id = int(os.getenv('MEMBER_ROLE_ID', 0))
            if member_role_id:
                member_role = guild.get_role(member_role_id)
                if member_role and member_role in member.roles:
                    await member.remove_roles(member_role)
                    logging.info(f"Removed member role from {member.display_name} ({member.id}) - they rejoined")
            
            # Assign unverified role
            if unverified_role not in member.roles:
                await member.add_roles(unverified_role)
                logging.info(f"Assigned unverified role to {member.display_name} ({member.id})")
            else:
                logging.info(f"User {member.display_name} ({member.id}) already has unverified role")
            
            # Log to logs channel (only once per member)
            if logs_channel_id:
                logs_channel = guild.get_channel(logs_channel_id)
                if logs_channel:
                    embed = discord.Embed(
                        title="👋 New Member Joined",
                        description=f"**{member.mention}** has joined the server",
                        color=0x00ff00,
                        timestamp=datetime.now(timezone.utc)
                    )
                    embed.add_field(name="User ID", value=f"`{member.id}`", inline=True)
                    embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
                    embed.add_field(name="Role Assigned", value=f"✅ Unverified Role", inline=True)
                    embed.set_thumbnail(url=member.display_avatar.url)
                    embed.set_footer(text=f"Member #{guild.member_count}")
                    
                    try:
                        await logs_channel.send(embed=embed)
                    except discord.Forbidden:
                        logging.warning(f"Bot doesn't have permission to send messages to logs channel {logs_channel_id}")
                    except Exception as e:
                        logging.error(f"Error sending log message: {e}")
                    
                    logging.info(f"Logged member join for {member.display_name} ({member.id})")
            
            # Record user data for role assignment
            try:
                with open(USER_DATA_FILE, 'r') as f:
                    user_data = json.load(f)
            except FileNotFoundError:
                user_data = {}
            
            user_id = str(member.id)
            current_time = datetime.now(timezone.utc).timestamp()
            
            user_data[user_id] = {
                'joined_at': current_time,
                'has_access': False,
                'role_assigned': False,
                'unverified_role_assigned': True,
                'button_clicked_at': 0  # Reset button click when they rejoin
            }
            
            with open(USER_DATA_FILE, 'w') as f:
                json.dump(user_data, f, indent=2)
                
        except Exception as e:
            logging.error(f"Error handling member join for {member.id}: {e}")
            # Remove from logged_members if there was an error
            self.logged_members.discard(member.id)

    def load_logged_members(self):
        """Load logged members from file"""
        try:
            with open('logged_members.json', 'r') as f:
                data = json.load(f)
                self.logged_members = set(data.get('logged_members', []))
                logging.info(f"Loaded {len(self.logged_members)} logged members")
        except FileNotFoundError:
            self.logged_members = set()
            logging.info("No logged members file found, starting fresh")
        except Exception as e:
            logging.error(f"Error loading logged members: {e}")
            self.logged_members = set()

    def save_logged_members(self):
        """Save logged members to file"""
        try:
            with open('logged_members.json', 'w') as f:
                json.dump({'logged_members': list(self.logged_members)}, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving logged members: {e}")

    async def role_assignment_loop(self):
        """Background task to assign member roles and remove unverified roles"""
        while True:
            try:
                await self.check_and_assign_roles()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logging.error(f"Error in role assignment loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def check_and_assign_roles(self):
        """Check if any users need role assignment"""
        try:
            # Load user data
            try:
                with open(USER_DATA_FILE, 'r') as f:
                    user_data = json.load(f)
            except FileNotFoundError:
                return
            
            current_time = datetime.now(timezone.utc).timestamp()
            delay_seconds = int(os.getenv('ROLE_ASSIGNMENT_DELAY', 300))  # 5 minutes in seconds
            
            # Create a list of users to remove (can't modify dict while iterating)
            users_to_remove = []
            
            for user_id_str, data in user_data.items():
                user_id = int(user_id_str)
                
                # Check if user is still in the guild
                guild_id = int(os.getenv('GUILD_ID', 0))
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue
                
                member = guild.get_member(user_id)
                if not member:
                    # User left the server, mark for removal
                    users_to_remove.append(user_id_str)
                    logging.info(f"User {user_id} left the server, will remove from data")
                    continue
                
                # Only assign member role if user clicked the button
                button_clicked_at = data.get('button_clicked_at', 0)
                if button_clicked_at and not data.get('has_access', False) and not data.get('role_assigned', False):
                    if current_time - button_clicked_at >= delay_seconds:
                        await self.assign_member_role(user_id)
                        # Remove unverified role when they get member role
                        await self.remove_unverified_role(user_id)
            
            # Remove users who left the server
            for user_id_str in users_to_remove:
                del user_data[user_id_str]
                logging.info(f"Removed user {user_id_str} from data (left server)")
            
            # Save updated data if any users were removed
            if users_to_remove:
                with open(USER_DATA_FILE, 'w') as f:
                    json.dump(user_data, f, indent=2)
                    
        except Exception as e:
            logging.error(f"Error checking role assignments: {e}")

    async def assign_member_role(self, user_id):
        """Assign member role to user"""
        try:
            guild_id = int(os.getenv('GUILD_ID', 0))
            member_role_id = int(os.getenv('MEMBER_ROLE_ID', 0))
            logs_channel_id = int(os.getenv('LOGS_CHANNEL_ID', 0))
            
            if not guild_id or not member_role_id:
                logging.error("GUILD_ID or MEMBER_ROLE_ID not set")
                return
            
            guild = self.bot.get_guild(guild_id)
            if not guild:
                logging.error(f"Guild {guild_id} not found")
                return
            
            member = guild.get_member(user_id)
            if not member:
                logging.info(f"Member {user_id} not found in guild (likely left)")
                return
            
            role = guild.get_role(member_role_id)
            if not role:
                logging.error(f"Role {member_role_id} not found")
                return
            
            if role in member.roles:
                logging.info(f"User {user_id} already has member role")
                # Update user data to reflect they already have the role
                try:
                    with open(USER_DATA_FILE, 'r') as f:
                        user_data = json.load(f)
                except FileNotFoundError:
                    user_data = {}
                
                user_id_str = str(user_id)
                if user_id_str in user_data:
                    user_data[user_id_str]['has_access'] = True
                    user_data[user_id_str]['role_assigned'] = True
                    
                    with open(USER_DATA_FILE, 'w') as f:
                        json.dump(user_data, f, indent=2)
                return
            
            await member.add_roles(role)
            logging.info(f"Assigned member role to user {user_id}")
            
            # Log to logs channel
            if logs_channel_id:
                logs_channel = guild.get_channel(logs_channel_id)
                if logs_channel:
                    embed = discord.Embed(
                        title="✅ Member Role Assigned",
                        description=f"**{member.mention}** has been assigned the Member role",
                        color=0x00ff00,
                        timestamp=datetime.now(timezone.utc)
                    )
                    embed.add_field(name="User ID", value=f"`{user_id}`", inline=True)
                    embed.add_field(name="Role", value=f"✅ Member", inline=True)
                    embed.set_thumbnail(url=member.display_avatar.url)
                    
                    try:
                        await logs_channel.send(embed=embed)
                    except discord.Forbidden:
                        logging.warning(f"Bot doesn't have permission to send messages to logs channel {logs_channel_id}")
                    except Exception as e:
                        logging.error(f"Error sending log message: {e}")
            
            # Update user data
            try:
                with open(USER_DATA_FILE, 'r') as f:
                    user_data = json.load(f)
            except FileNotFoundError:
                user_data = {}
            
            user_id_str = str(user_id)
            if user_id_str in user_data:
                user_data[user_id_str]['has_access'] = True
                user_data[user_id_str]['role_assigned'] = True
                
                with open(USER_DATA_FILE, 'w') as f:
                    json.dump(user_data, f, indent=2)
            
        except Exception as e:
            logging.error(f"Error assigning member role to {user_id}: {e}")

    async def remove_unverified_role(self, user_id):
        """Remove unverified role from user"""
        try:
            guild_id = int(os.getenv('GUILD_ID', 0))
            unverified_role_id = int(os.getenv('UNVERIFIED_ROLE_ID', 0))
            logs_channel_id = int(os.getenv('LOGS_CHANNEL_ID', 0))
            
            if not guild_id or not unverified_role_id:
                logging.error("GUILD_ID or UNVERIFIED_ROLE_ID not set")
                return
            
            guild = self.bot.get_guild(guild_id)
            if not guild:
                logging.error(f"Guild {guild_id} not found")
                return
            
            member = guild.get_member(user_id)
            if not member:
                logging.info(f"Member {user_id} not found in guild (likely left)")
                return
            
            role = guild.get_role(unverified_role_id)
            if not role:
                logging.error(f"Role {unverified_role_id} not found")
                return
            
            if role not in member.roles:
                logging.info(f"User {user_id} doesn't have unverified role")
                return
            
            await member.remove_roles(role)
            logging.info(f"Removed unverified role from user {user_id}")
            
            # Log to logs channel
            if logs_channel_id:
                logs_channel = guild.get_channel(logs_channel_id)
                if logs_channel:
                    embed = discord.Embed(
                        title="🔓 Unverified Role Removed",
                        description=f"**{member.mention}** has had their Unverified role removed",
                        color=0xffa500,
                        timestamp=datetime.now(timezone.utc)
                    )
                    embed.add_field(name="User ID", value=f"`{user_id}`", inline=True)
                    embed.add_field(name="Role Removed", value=f"🔓 Unverified", inline=True)
                    embed.set_thumbnail(url=member.display_avatar.url)
                    
                    try:
                        await logs_channel.send(embed=embed)
                    except discord.Forbidden:
                        logging.warning(f"Bot doesn't have permission to send messages to logs channel {logs_channel_id}")
                    except Exception as e:
                        logging.error(f"Error sending log message: {e}")
            
            # Update user data to mark unverified role as removed
            try:
                with open(USER_DATA_FILE, 'r') as f:
                    user_data = json.load(f)
            except FileNotFoundError:
                user_data = {}
            
            user_id_str = str(user_id)
            if user_id_str in user_data:
                user_data[user_id_str]['unverified_role_assigned'] = False
                
                with open(USER_DATA_FILE, 'w') as f:
                    json.dump(user_data, f, indent=2)
            
        except Exception as e:
            logging.error(f"Error removing unverified role from {user_id}: {e}")

    async def sync_user_data_with_roles(self):
        """Sync user data with actual Discord roles to prevent incorrect assignments"""
        try:
            guild_id = int(os.getenv('GUILD_ID', 0))
            member_role_id = int(os.getenv('MEMBER_ROLE_ID', 0))
            unverified_role_id = int(os.getenv('UNVERIFIED_ROLE_ID', 0))
            
            if not guild_id:
                logging.error("GUILD_ID not set")
                return
            
            guild = self.bot.get_guild(guild_id)
            if not guild:
                logging.error(f"Guild {guild_id} not found")
                return
            
            # Load user data
            try:
                with open(USER_DATA_FILE, 'r') as f:
                    user_data = json.load(f)
            except FileNotFoundError:
                logging.info("No user data file found, skipping sync")
                return
            
            member_role = guild.get_role(member_role_id) if member_role_id else None
            unverified_role = guild.get_role(unverified_role_id) if unverified_role_id else None
            
            updated = False
            users_to_remove = []
            
            for user_id_str, data in user_data.items():
                user_id = int(user_id_str)
                member = guild.get_member(user_id)
                
                if not member:
                    # User left the server, mark for removal
                    users_to_remove.append(user_id_str)
                    logging.info(f"User {user_id} left the server, will remove from sync data")
                    continue
                
                # Check if user has member role
                has_member_role = member_role and member_role in member.roles
                has_unverified_role = unverified_role and unverified_role in member.roles
                
                # Update data to match actual Discord state
                if data.get('has_access', False) != has_member_role:
                    data['has_access'] = has_member_role
                    data['role_assigned'] = has_member_role
                    updated = True
                    logging.info(f"Synced member role status for user {user_id}: {has_member_role}")
                
                if data.get('unverified_role_assigned', False) != has_unverified_role:
                    data['unverified_role_assigned'] = has_unverified_role
                    updated = True
                    logging.info(f"Synced unverified role status for user {user_id}: {has_unverified_role}")
                
                # If user has member role but no button click recorded, reset their data
                if has_member_role and not data.get('button_clicked_at', 0):
                    data['button_clicked_at'] = 0
                    updated = True
                    logging.info(f"Reset button click data for user {user_id} - they have member role but no click recorded")
            
            # Remove users who left the server
            for user_id_str in users_to_remove:
                del user_data[user_id_str]
                logging.info(f"Removed user {user_id_str} from sync data (left server)")
                updated = True
            
            if updated:
                with open(USER_DATA_FILE, 'w') as f:
                    json.dump(user_data, f, indent=2)
                logging.info("User data synced with Discord roles")
            
        except Exception as e:
            logging.error(f"Error syncing user data with roles: {e}")

async def setup(bot):
    await bot.add_cog(Welcome(bot))