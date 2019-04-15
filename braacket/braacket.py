"""
Created on Nov 19, 2017
@author: Dan Barry
"""

import discord
import requests
import logging
import urllib.error
from bs4 import BeautifulSoup
from redbot.core import Config, checks, commands
from redbot.core.i18n import Translator, cog_i18n

_ = Translator('Audio', __file__)

log = logging.getLogger('red.braacket')


@cog_i18n(_)
class Braacket(commands.Cog):
    """Interact with the Stevens Melee Braacket page"""

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.config = Config.get_conf(self, 5151798315418247, force_registration=True)
        self.config.register_guild(
            league=None,
            pr=None,
            tourneypage=None
        )

    @commands.group()
    @commands.guild_only()
    async def braacketset(self, ctx):
        """Fetches the latest tourney bracket"""
        pass

    @braacketset.command()
    @checks.mod()
    async def league(self, ctx, league: str):
        """Sets the league ID. For example, the ID StevensMelee has the url https://braacket.com/league/StevensMelee"""
        try:
            with urlopen('https://braacket.com/league/{}'.format(league)) as x:
                pass
        except urllib.error.HTTPError as e:
            await self._embed_msg(
                ctx, _('League does not appear to exist, failed with error code {}').format(str(e.code))
            )
        except urllib.error.URLError as e:
            await self._embed_msg(
                ctx, _('An error occurred while trying to open the league page - Reason: {}').format(str(e.reason))
            )
        else:
            await self.config.guild(ctx.guild).league.set(league)
            await self._embed_msg(
                ctx, _('Set Braacket league id to {}').format(league)
            )

    @braacketset.command(name='pr')
    @checks.mod()
    async def setpr(self, ctx, pr: str):
        """Sets the league ID. For example, the ID StevensMelee has the url https://braacket.com/league/StevensMelee"""
        if pr.lower() == 'none':
            await self.config.guild(ctx.guild).pr(None)
            return await self._embed_msg(
                ctx, _('I will now use the league\'s default ranking')
            )
        league = await self.config.guild(ctx.guild).league()
        if league is None:
            return await self._embed_msg(
                ctx, _('No league ID has been set yet. Please do `!braacketset league [league-id]`')
            )
        try:
            with urlopen('https://braacket.com/{league}/ranking/{pr}'.format(league=league, pr=pr)) as x:
                pass
        except urllib.error.HTTPError as e:
            await self._embed_msg(
                ctx, _('Ranking does not appear to exist, failed with error code {}').format(str(e.code))
            )
        except urllib.error.URLError as e:
            await self._embed_msg(
                ctx, _('An error occurred while trying to open the ranking page - Reason: {}').format(str(e.reason))
            )
        else:
            await self.config.guild(ctx.guild).pr.set(pr)
            await self._embed_msg(
                ctx, _('Set league\'s ranking ID to {}').format(pr)
            )

    @commands.command()
    @commands.guild_only()
    async def bracket(self, ctx):
        """Fetches the latest tourney bracket"""
        league = await self.config.guild(ctx.guild).league()
        if league is None:
            return await self._embed_msg(
                ctx, _('League name has not been set yet. Use !setleague <league>')
            )
        url = 'https://braacket.com/league/{}/tournament'.format(league)
        try:
            tourneypage = requests.get(url).content
        except requests.exceptions.RequestException as e:
            await self._embed_msg(
                ctx, _('Accessing the tournament page failed with the following error: {}').format(e)
            )
            tourneypage = await self.config.guild(ctx.guild).tourneypage.get_raw()
        else:
            await self.config.guild(ctx.guild).tourneypage.set_raw(tourneypage)
        finally:
            tourneysoup = BeautifulSoup(tourneypage, 'html.parser')
            latest = tourneysoup.find(class_='col-xs-12 col-sm-6 col-md-4 col-lg-3').find('a').get('href')
            await self.bot.say('https://braacket.com' + latest + '/bracket')

    @commands.command()
    @commands.guild_only()
    async def pr(self):
        """Fetches the top players on the current Power Ranking"""
        pass

    @staticmethod
    async def _embed_msg(ctx, title):
        embed = discord.Embed(colour=await ctx.embed_colour(), title=title)
        await ctx.send(embed=embed)
