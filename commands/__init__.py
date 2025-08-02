import logging
from discord.ext import commands
import importlib

# Commands package
from .help import setup as help_setup
from .refresh import setup as refresh_setup
from .setup import setup as setup_setup

async def setup(bot: commands.Bot) -> None:
    """Add admin commands to the bot."""
    logger = logging.getLogger(__name__)
    msg = "Loaded commands.{}"
    
    await help_setup(bot)
    logger.debug(msg.format("help"))
    
    await refresh_setup(bot)
    logger.debug(msg.format("refresh"))
    
    await setup_setup(bot)
    logger.debug(msg.format("setup"))