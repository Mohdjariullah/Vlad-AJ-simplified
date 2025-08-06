import discord
from discord.ext import commands
import os
import logging
import json

async def setup(bot):
    @bot.tree.command(name="removemember", description="Remove member role from a user")
    @discord.app_commands.default_permissions(administrator=True)
    async def remove_member_role(interaction: discord.Interaction, user: discord.Member):
        """Remove member role from a user (admin only)"""
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
            if not member_role_id:
                await interaction.response.send_message("❌ MEMBER_ROLE_ID not configured!", ephemeral=True)
                return
            
            member_role = interaction.guild.get_role(member_role_id)
            if not member_role:
                await interaction.response.send_message("❌ Member role not found!", ephemeral=True)
                return
            
            if member_role not in user.roles:
                await interaction.response.send_message(f"❌ {user.mention} doesn't have the member role!", ephemeral=True)
                return
            
            await user.remove_roles(member_role)
            
            # Update user data
            try:
                with open('user_data.json', 'r') as f:
                    user_data = json.load(f)
            except FileNotFoundError:
                user_data = {}
            
            user_id_str = str(user.id)
            if user_id_str in user_data:
                user_data[user_id_str]['has_access'] = False
                user_data[user_id_str]['role_assigned'] = False
                
                with open('user_data.json', 'w') as f:
                    json.dump(user_data, f, indent=2)
            
            embed = discord.Embed(
                title="🔓 Member Role Removed",
                description=f"**{user.mention}** has had their Member role removed",
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="User ID", value=f"`{user.id}`", inline=True)
            embed.add_field(name="Role Removed", value=f"🔓 Member", inline=True)
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.set_footer(text=f"Removed by {interaction.user.name}")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Log to logs channel
            logs_channel_id = int(os.getenv('LOGS_CHANNEL_ID', 0))
            if logs_channel_id:
                logs_channel = interaction.guild.get_channel(logs_channel_id)
                if logs_channel:
                    await logs_channel.send(embed=embed)
                    
        except Exception as e:
            logging.error(f"Error removing member role: {e}")
            await interaction.response.send_message("❌ An error occurred while removing the role.", ephemeral=True) 