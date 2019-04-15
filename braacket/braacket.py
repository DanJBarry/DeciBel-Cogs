"""
Created on Nov 19, 2017
@author: Dan Barry
"""

import discord
import logging
import urllib.error
from redbot.core import Config, checks, commands
from redbot.core.i18n import Translator, cog_i18n
from urllib.request import urlopen

_ = Translator("Audio", __file__)

log = logging.getLogger("red.braacket")


@cog_i18n(_)
class Braacket(commands.Cog):
    """Interact with the Stevens Melee Braacket page"""

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.config = Config.get_conf(self, 5151798315418247, force_registration=True)
        self.config.register_global(
            globalsettings=False,
            league=None,
            pr=None
        )
        self.config.register_guild(
            league=None,
            pr=None
        )

    @commands.command()
    @commands.guild_only()
    async def braacketset(self):
        """Fetches the latest tourney bracket"""
        pass

    @braacketset.command(name="global")
    @checks.is_owner()
    async def toggleglobal(self, ctx):
        globalsettings = await self.config.globalsettings()
        await self.config.globalsettings.set(not globalsettings)
        await self._embed_msg(
            ctx, _("Set global Braacket league to {true_or_false}").format(true_or_false=not globalsettings)
        )

    @braacketset.command()
    @checks.mod()
    async def league(self, ctx, league: str):
        """Sets the league ID. For example, the ID StevensMelee has the url https://braacket.com/league/StevensMelee"""
        if await self.config.globalsettings():
            return await self._embed_msg(
                ctx, _("Global settings active, cannot change league ID")
            )
        try:
            with urlopen("https://braacket.com/league/{}".format(league)) as x:
                pass
        except urllib.error.HTTPError as e:
            await self._embed_msg(
                ctx, _("League does not appear to exist, failed with error code {}").format(str(e.code))
            )
        except urllib.error.URLError as e:
            await self._embed_msg(
                ctx, _("An error occurred while trying to open the league page - Reason: {}").format(str(e.reason))
            )
        else:
            await self.config.guild(ctx.guild).league.set(league)
            await self._embed_msg(
                ctx, _("Set Braacket league id to {}").format(league)
            )

    @braacketset.command(name="pr")
    @checks.mod()
    async def setpr(self, ctx, pr: str):
        """Sets the league ID. For example, the ID StevensMelee has the url https://braacket.com/league/StevensMelee"""
        if await self.config.globalsettings():
            return await self._embed_msg(
                ctx, _("Global settings active, cannot change PR")
            )
        if pr.lower() == "none":
            await self.config.guild(ctx.guild).pr(None)
            return await self._embed_msg(
                ctx, _("I will now use the league's default ranking")
            )
        league = await self.config.guild(ctx.guild).league()
        if league is None:
            return await self._embed_msg(
                ctx, _("No league ID has been set yet. Please do `!braacketset league [league-id]`")
            )
        try:
            with urlopen("https://braacket.com/{league}/ranking/{pr}".format(league=league, pr=pr)) as x:
                pass
        except urllib.error.HTTPError as e:
            await self._embed_msg(
                ctx, _("Ranking does not appear to exist, failed with error code {}").format(str(e.code))
            )
        except urllib.error.URLError as e:
            await self._embed_msg(
                ctx, _("An error occurred while trying to open the ranking page - Reason: {}").format(str(e.reason))
            )
        else:
            await self.config.guild(ctx.guild).pr.set(pr)
            await self._embed_msg(
                ctx, _("Set league's ranking ID to {}").format(pr)
            )

    @commands.command()
    @commands.guild_only()
    async def bracket(self):
        """Fetches the latest tourney bracket"""
        pass

    @commands.command()
    @commands.guild_only()
    async def pr(self):
        """Fetches the latest tourney bracket"""
        pass
