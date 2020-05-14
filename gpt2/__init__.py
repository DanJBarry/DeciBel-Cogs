from .gpt2 import Gpt2
from redbot.core import commands


def setup(bot: commands.Bot):
    bot.add_cog(Gpt2(bot))
