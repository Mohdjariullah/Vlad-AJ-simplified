import discord
from discord.ext import commands

async def setup(bot):
    @bot.tree.command(name="help_admin", description="List all admin commands and their descriptions")
    async def help_admin(interaction: discord.Interaction):
        """List all admin commands and their descriptions"""
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
        
        embed = discord.Embed(
            title="🔧 Admin Commands",
            description="Available admin commands for the AJ Trading Academy bot",
            color=0x00ff00
        )
        
        embed.add_field(
            name="/setup",
            value="Set up the initial welcome message in the welcome channel",
            inline=False
        )
        
        embed.add_field(
            name="/refresh",
            value="Refresh the welcome message in the welcome channel",
            inline=False
        )
        
        embed.add_field(
            name="/help_admin",
            value="Show this help message with all admin commands",
            inline=False
        )
        
        embed.set_footer(text="All commands require Administrator permissions and must be used in the authorized server")
        
        await interaction.response.send_message(embed=embed, ephemeral=True) 