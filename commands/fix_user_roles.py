import discord
from discord.ext import commands
import os
import logging
import json
from datetime import datetime, timezone

async def setup(bot):
    @bot.tree.command(name="fixuser", description="Fix user roles and status")
    @discord.app_commands.default_permissions(administrator=True)
    async def fix_user_roles(interaction: discord.Interaction, user: discord.Member):
        """Fix user roles and status (admin only)"""
        # SECURITY: Check authorization
        from main import is_authorized_guild_or_owner
        if not is_authorized_guild_or_owner(interaction):
            return await interaction.response.send_message(
                "❌ You are not authorized to use this command.", ephemeral=True
            )
        
        # SECURITY: Block DMs and check admin permissions
        if not interaction.guild:
            return await interaction.response.send_message("❌ This command can only be used in a server!", ephemeral=True)
        if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ You need Administrator permissions!", ephemeral=True)
        
        try:
            member_role_id = int(os.getenv('MEMBER_ROLE_ID', 0))
            unverified_role_id = int(os.getenv('UNVERIFIED_ROLE_ID', 0))
            
            member_role = interaction.guild.get_role(member_role_id) if member_role_id else None
            unverified_role = interaction.guild.get_role(unverified_role_id) if unverified_role_id else None
            
            # Check current roles
            has_member_role = member_role and member_role in user.roles
            has_unverified_role = unverified_role and unverified_role in user.roles
            
            # Load user data
            try:
                with open('user_data.json', 'r') as f:
                    user_data = json.load(f)
                user_info = user_data.get(str(user.id), {})
            except FileNotFoundError:
                user_info = {}
            
            actions_taken = []
            
            # Check if user should have unverified role
            if not has_unverified_role and not has_member_role:
                if unverified_role:
                    await user.add_roles(unverified_role)
                    actions_taken.append("✅ Added unverified role")
                    has_unverified_role = True
            
            # Check if user should have member role
            button_clicked_at = user_info.get('button_clicked_at', 0)
            if button_clicked_at and not has_member_role:
                current_time = datetime.now(timezone.utc).timestamp()
                delay_seconds = int(os.getenv('ROLE_ASSIGNMENT_DELAY', 300))
                
                if current_time - button_clicked_at >= delay_seconds:
                    if member_role:
                        await user.add_roles(member_role)
                        actions_taken.append("✅ Added member role")
                        has_member_role = True
                        
                        # Remove unverified role
                        if has_unverified_role and unverified_role:
                            await user.remove_roles(unverified_role)
                            actions_taken.append("🔓 Removed unverified role")
                            has_unverified_role = False
            
            # Update user data
            user_data[str(user.id)] = {
                'joined_at': user_info.get('joined_at', 0),
                'has_access': has_member_role,
                'role_assigned': has_member_role,
                'unverified_role_assigned': has_unverified_role,
                'button_clicked_at': button_clicked_at
            }
            
            with open('user_data.json', 'w') as f:
                json.dump(user_data, f, indent=2)
            
            # Create response embed
            embed = discord.Embed(
                title=f"🔧 User Role Fix: {user.display_name}",
                description=f"User ID: `{user.id}`",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            # Current status
            status_info = []
            if has_member_role:
                status_info.append("✅ Member Role")
            else:
                status_info.append("❌ Member Role")
            
            if has_unverified_role:
                status_info.append("🔒 Unverified Role")
            else:
                status_info.append("🔓 No Unverified Role")
            
            embed.add_field(name="Current Roles", value="\n".join(status_info), inline=False)
            
            # Actions taken
            if actions_taken:
                embed.add_field(name="Actions Taken", value="\n".join(actions_taken), inline=False)
            else:
                embed.add_field(name="Actions Taken", value="No actions needed", inline=False)
            
            # User data info
            data_info = []
            if button_clicked_at:
                button_time = datetime.fromtimestamp(button_clicked_at, tz=timezone.utc)
                data_info.append(f"🔘 Button clicked: {button_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            else:
                data_info.append("❌ Button not clicked")
            
            data_info.append(f"✅ Has access: {has_member_role}")
            data_info.append(f"🎭 Role assigned: {has_member_role}")
            data_info.append(f"🔒 Unverified role assigned: {has_unverified_role}")
            
            embed.add_field(name="User Data", value="\n".join(data_info), inline=False)
            
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.set_footer(text=f"Fixed by {interaction.user.name}")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logging.error(f"Error fixing user roles: {e}")
            await interaction.response.send_message("❌ An error occurred while fixing user roles.", ephemeral=True) 