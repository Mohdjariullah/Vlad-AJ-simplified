import discord
from discord.ext import commands
from datetime import datetime
import os
import json
from cogs.verification import VerificationView

USER_DATA_FILE = 'user_data.json'

async def setup(bot):
    @bot.tree.command(name="setup", description="Set up the welcome message")
    async def setup_welcome(interaction: discord.Interaction):
        """Set up the initial welcome message in the welcome channel"""
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
        
        # Get configuration from main.py
        from main import WELCOME_CHANNEL_ID, get_or_create_welcome_message
        
        # Get the welcome channel
        welcome_channel = interaction.guild.get_channel(WELCOME_CHANNEL_ID)
        if not welcome_channel:
            await interaction.response.send_message("❌ Welcome channel not found!", ephemeral=True)
            return
        
        # Create welcome embed
        embed = discord.Embed(
            title="👋 Welcome To The AJ Trading Academy!",
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
        embed.set_footer(text="Join our community today!")
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1370122090631532655/1401222798336200834/20.38.48_73b12891.jpg")
        
        # Use VerificationView
        msg = await get_or_create_welcome_message(welcome_channel, embed, VerificationView())
        
        await interaction.response.send_message(f"✅ Welcome message set up successfully! {msg.jump_url}", ephemeral=True)

    @bot.tree.command(name="fix_roles", description="Manually fix unverified roles")
    async def fix_roles(interaction: discord.Interaction):
        """Manually trigger role assignment for all users with unverified roles"""
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
        
        await interaction.response.send_message("🔄 Fixing roles... This may take a moment.", ephemeral=True)
        
        # Get the welcome cog
        welcome_cog = bot.get_cog('Welcome')
        if welcome_cog:
            await welcome_cog.check_and_assign_roles()
            await interaction.followup.send_message("✅ Role assignment completed!", ephemeral=True)
        else:
            await interaction.followup.send_message("❌ Welcome cog not found!", ephemeral=True)

    @bot.tree.command(name="check_user", description="Check user status and roles")
    async def check_user(interaction: discord.Interaction, user: discord.Member):
        """Check the status of a specific user"""
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
            # Load user data
            try:
                with open(USER_DATA_FILE, 'r') as f:
                    user_data = json.load(f)
            except FileNotFoundError:
                user_data = {}
            
            user_id_str = str(user.id)
            data = user_data.get(user_id_str, {})
            
            # Get role information
            member_role_id = int(os.getenv('MEMBER_ROLE_ID', 0))
            unverified_role_id = int(os.getenv('UNVERIFIED_ROLE_ID', 0))
            
            member_role = interaction.guild.get_role(member_role_id)
            unverified_role = interaction.guild.get_role(unverified_role_id)
            
            has_member_role = member_role in user.roles if member_role else False
            has_unverified_role = unverified_role in user.roles if unverified_role else False
            
            # Create embed
            embed = discord.Embed(
                title=f"👤 User Status: {user.display_name}",
                description=f"User ID: `{user.id}`",
                color=0x0099ff,
                timestamp=datetime.now()
            )
            
            # User data
            embed.add_field(
                name="📊 User Data",
                value=f"**In Database:** {'✅' if user_id_str in user_data else '❌'}\n"
                      f"**Has Access:** {'✅' if data.get('has_access', False) else '❌'}\n"
                      f"**Role Assigned:** {'✅' if data.get('role_assigned', False) else '❌'}\n"
                      f"**Unverified Role Assigned:** {'✅' if data.get('unverified_role_assigned', False) else '❌'}",
                inline=False
            )
            
            # Timestamps
            if data.get('button_clicked_at'):
                embed.add_field(
                    name="⏰ Button Clicked",
                    value=f"<t:{int(data['button_clicked_at'])}:R>",
                    inline=True
                )
            
            if data.get('joined_at'):
                embed.add_field(
                    name="⏰ Joined Server",
                    value=f"<t:{int(data['joined_at'])}:R>",
                    inline=True
                )
            
            # Current roles
            embed.add_field(
                name="🎭 Current Roles",
                value=f"**Member Role:** {'✅' if has_member_role else '❌'}\n"
                      f"**Unverified Role:** {'✅' if has_unverified_role else '❌'}",
                inline=False
            )
            
            embed.set_thumbnail(url=user.display_avatar.url)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error checking user: {e}", ephemeral=True) 