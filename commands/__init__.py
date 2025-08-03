import logging
from discord.ext import commands
import importlib

# Commands package
from .help import setup as help_setup
from .refresh import setup as refresh_setup
from .daily_access import setup as daily_access_setup

async def setup(bot: commands.Bot) -> None:
    """Add admin commands to the bot."""
    logger = logging.getLogger(__name__)
    msg = "Loaded commands.{}"
    
    await help_setup(bot)
    logger.debug(msg.format("help"))
    
    await refresh_setup(bot)
    logger.debug(msg.format("refresh"))
    
    await daily_access_setup(bot)
    logger.debug(msg.format("daily_access"))
    