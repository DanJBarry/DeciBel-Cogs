"""
Created on Nov 19, 2017
@author: Dan Barry
"""

import discord
import requests
import logging
import re
from bs4 import BeautifulSoup
from redbot.core import Config, checks, commands
from redbot.core.i18n import Translator, cog_i18n

_ = Translator('Audio', __file__)

log = logging.getLogger('red.braacket')

_VALID_ID_REGEX = re.compile('^[A-Za-z0-9-_]+$')


@cog_i18n(_)
class Braacket(commands.Cog):
    """Interact with the Stevens Melee Braacket page"""

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.config = Config.get_conf(self, 5151798315418247, force_registration=True)
        self.config.register_guild(
            league=None,
            pr=None
        )

    @commands.group()
    @commands.guild_only()
    async def braacketset(self, ctx: commands.Context):
        """Braacket configuration options"""
        pass

    @braacketset.command()
    @checks.mod()
    async def league(self, ctx: commands.Context, league: str):
        """Sets the league ID.
        For example, if the URL to your league page is https://braacket.com/league/StevensMelee
        then the league ID is StevensMelee"""
        if not _VALID_ID_REGEX.match(league):
            return await self._embed_msg(
                ctx, _('League ID can only contain alphanumeric characters, dashes, and underscores')
            )
        try:
            leaguerequest = requests.get('https://braacket.com/league/{}'.format(league))
            leaguerequest.raise_for_status()
        except requests.exceptions.RequestException as e:
            await self._embed_msg(
                ctx, _('Accessing the ranking page failed with the following error: {}').format(e)
            )
            log.error(e)
        else:
            await self.config.guild(ctx.guild).league.set(league)
            log.info("User {} set league ID to {} in guild {}".format(ctx.author, league, ctx.guild))
            await self._embed_msg(
                ctx, _('Set Braacket league id to {}').format(league)
            )

    @braacketset.command(name='pr')
    @checks.mod()
    async def setpr(self, ctx: commands.Context, pr: str):
        """Sets the ranking ID.
        For example, if the URL to your desired ranking page is
        https://braacket.com/league/StevensMelee/ranking/39E07092-9936-4710-9EAA-1CDD3396A544
        then the ranking ID is 39E07092-9936-4710-9EAA-1CDD3396A544"""
        pr = pr.upper()
        if not _VALID_ID_REGEX.match(pr):
            return await self._embed_msg(
                ctx, _('Ranking ID can only contain alphanumeric characters, dashes, and underscores')
            )
        if pr.lower() == 'default':
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
            prrequest = requests.get('https://braacket.com/league/{league}/ranking/{pr}'.format(league=league, pr=pr))
            prrequest.raise_for_status()
        except requests.exceptions.RequestException as e:
            await self._embed_msg(
                ctx, _('Accessing the ranking page failed with the following error: {}').format(e)
            )
            log.error(e)
        else:
            await self.config.guild(ctx.guild).pr.set(pr)
            log.info("User {} set ranking ID to {} for {} in guild {}".format(ctx.author, pr, league, ctx.guild))
            await self._embed_msg(
                ctx, _('Set league\'s ranking ID to {}').format(pr)
            )

    @commands.command()
    @commands.guild_only()
    async def bracket(self, ctx: commands.Context):
        """Fetches the latest tourney bracket"""
        league = await self.config.guild(ctx.guild).league()
        if league is None:
            return await self._embed_msg(
                ctx, _('League name has not been set yet. Use !setleague <league>')
            )
        url = 'https://braacket.com/league/{}/tournament'.format(league)
        try:
            tourneyrequest = requests.get(url)
            tourneyrequest.raise_for_status()
        except requests.exceptions.RequestException as e:
            await self._embed_msg(
                ctx, _('Accessing the tournament page failed with the following error: {}').format(e)
            )
            log.error(e)
        else:
            tourneysoup = BeautifulSoup(tourneyrequest.content, 'html.parser')
            latest = tourneysoup.find(class_='col-xs-12 col-sm-6 col-md-4 col-lg-3').find('a').get('href')
            await ctx.send('https://braacket.com{}/bracket'.format(latest))

    @commands.command()
    @commands.guild_only()
    async def pr(self, ctx: commands.Context, count: int = 5):
        """Fetches the top players on the current Power Ranking"""
        if not 1 <= count <= 10:
            return await self._embed_msg(
                ctx, _('Please pick a number between 1 and 10')
            )
        league = await self.config.guild(ctx.guild).league()
        if league is None:
            return await self._embed_msg(
                ctx, _('League name has not been set yet. Use !setleague <league>')
            )
        pr = await self.config.guild(ctx.guild).league()
        url = 'https://www.braacket.com/league/{}/ranking/'.format(pr or "")
        try:
            prrequest = requests.get(url)
            prrequest.raise_for_status()
        except requests.exceptions.RequestException as e:
            await self._embed_msg(
                ctx, _('Accessing the tournament page failed with the following error: {}').format(e)
            )
            log.error(e)
        else:
            prsoup = BeautifulSoup(prrequest.content, 'html.parser')
            players = prsoup.find_all(
                lambda x:
                re.match('/league/StevensMelee/player/', x['data-href'])
                if x.has_attr('data-href')
                else False
            )
            points = prsoup.find_all(class_='min text-right')
            for i in range(count):
                name = players[i].get_text(strip='True')
                player_url = 'https://www.braacket.com' + players[i].a.get('href')
                character_url = 'https://www.braacket.com' + players[i].img.get('src')
                description = ''
                if len(players[i].span.find_all('img')) > 1:  # For when the player has more than one main
                    for mains in range(len(players[i].span.find_all('img')) - 1):
                        description += players[i].span.find_all('img')[mains].get('title') + ', '
                description += players[i].span.find_all('img')[-1].get('title')  # Always get the last main
                description += ' || ' + points[i].get_text(strip='True')

                embed = discord.Embed(description=description, color=await ctx.embed_colour())
                embed.set_author(name=str(i + 1) + ". 	" + name, url=player_url, icon_url=character_url)
                await ctx.send(embed=embed)

    @staticmethod
    async def _embed_msg(ctx: commands.Context, title: str):
        embed = discord.Embed(color=await ctx.embed_colour(), title=title)
        await ctx.send(embed=embed)
