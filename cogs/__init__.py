import logging
from discord.ext import commands

# Import all cog modules
from . import verification
from . import welcome
from . import daily_access

async def setup(bot: commands.Bot) -> None:
    """Add all cogs to the bot."""
    logger = logging.getLogger(__name__)
    msg = "Loaded cogs.{}"
    await verification.setup(bot)
    logger.debug(msg.format("verification"))
    await welcome.setup(bot)
    logger.debug(msg.format("welcome"))
    await daily_access.setup(bot)
    logger.debug(msg.format("daily_access")) 