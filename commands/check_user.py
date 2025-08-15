import discord
from discord.ext import commands
import os
import logging
import json
from datetime import datetime, timezone

async def setup(bot):
    @bot.tree.command(name="checkuser", description="Check user status and roles")
    @discord.app_commands.default_permissions(administrator=True)
    async def check_user(interaction: discord.Interaction, user: discord.Member):
        """Check user status and roles (admin only)"""
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
            
            member_role_id = int(os.getenv('MEMBER_ROLE_ID', 0))
            unverified_role_id = int(os.getenv('UNVERIFIED_ROLE_ID', 0))
            
            member_role = interaction.guild.get_role(member_role_id) if member_role_id else None
            unverified_role = interaction.guild.get_role(unverified_role_id) if unverified_role_id else None
            
            # Check Discord roles
            has_member_role = member_role and member_role in user.roles
            has_unverified_role = unverified_role and unverified_role in user.roles
            
            # Load user data
            try:
                with open('user_data.json', 'r') as f:
                    user_data = json.load(f)
                user_info = user_data.get(str(user.id), {})
            except FileNotFoundError:
                user_info = {}
            
            embed = discord.Embed(
                title=f"👤 User Status: {user.display_name}",
                description=f"User ID: `{user.id}`",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            # Discord Roles
            roles_info = []
            if has_member_role:
                roles_info.append("✅ Member Role")
            else:
                roles_info.append("❌ Member Role")
            
            if has_unverified_role:
                roles_info.append("🔒 Unverified Role")
            else:
                roles_info.append("🔓 No Unverified Role")
            
            embed.add_field(name="Discord Roles", value="\n".join(roles_info), inline=False)
            
            # User Data
            data_info = []
            if user_info.get('button_clicked_at'):
                button_time = datetime.fromtimestamp(user_info['button_clicked_at'], tz=timezone.utc)
                data_info.append(f"🔘 Button clicked: {button_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            else:
                data_info.append("❌ Button not clicked")
            
            if user_info.get('joined_at'):
                join_time = datetime.fromtimestamp(user_info['joined_at'], tz=timezone.utc)
                data_info.append(f"📥 Joined: {join_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            else:
                data_info.append("❌ Join time not recorded")
            
            data_info.append(f"✅ Has access: {user_info.get('has_access', False)}")
            data_info.append(f"🎭 Role assigned: {user_info.get('role_assigned', False)}")
            data_info.append(f"🔒 Unverified role assigned: {user_info.get('unverified_role_assigned', False)}")
            
            # Check button cooldown status
            try:
                from cogs.verification import COOLDOWN_FILE, RATE_LIMIT_SECONDS
                import time
                
                try:
                    with open(COOLDOWN_FILE, 'r') as f:
                        cooldowns = json.load(f)
                    last_click = cooldowns.get(str(user.id), 0)
                    if last_click:
                        current_time = time.time()
                        time_since_click = current_time - last_click
                        if time_since_click < RATE_LIMIT_SECONDS:
                            remaining = int(RATE_LIMIT_SECONDS - time_since_click)
                            data_info.append(f"⏳ Button cooldown: {remaining}s remaining")
                        else:
                            data_info.append("✅ Button cooldown: Expired")
                    else:
                        data_info.append("✅ Button cooldown: None")
                except FileNotFoundError:
                    data_info.append("✅ Button cooldown: No file")
                except Exception as e:
                    data_info.append(f"❓ Button cooldown: Error ({e})")
            except ImportError:
                data_info.append("❓ Button cooldown: Module not available")
            
            embed.add_field(name="User Data", value="\n".join(data_info), inline=False)
            
            # Status Summary
            status = []
            if has_member_role and user_info.get('has_access'):
                status.append("✅ **CORRECT**: User has member role and data shows access")
            elif has_member_role and not user_info.get('has_access'):
                status.append("⚠️ **MISMATCH**: User has member role but data shows no access")
            elif not has_member_role and user_info.get('has_access'):
                status.append("⚠️ **MISMATCH**: User doesn't have member role but data shows access")
            else:
                status.append("✅ **CORRECT**: User doesn't have member role and data shows no access")
            
            embed.add_field(name="Status Summary", value="\n".join(status), inline=False)
            
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.set_footer(text=f"Checked by {interaction.user.name}")
            
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
        except Exception as e:
            logging.error(f"Error checking user: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ An error occurred while checking the user.", ephemeral=True)
            except Exception as response_error:
                logging.error(f"Error sending error response: {response_error}") 