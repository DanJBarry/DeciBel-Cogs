from .braacket import Braacket
from redbot.core import commands


def setup(bot: commands.Bot):
    bot.add_cog(Braacket(bot))
