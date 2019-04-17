import logging
import re
from uuid import UUID

import aiohttp
import discord
from bs4 import BeautifulSoup
from redbot.core import Config, checks, commands
from redbot.core.i18n import Translator, cog_i18n

_ = Translator("Braacket", __file__)

log = logging.getLogger("red.braacket")

_VALID_ID_REGEX = re.compile(r"^[\w-]+$")


@cog_i18n(_)
class Braacket(commands.Cog):
    """Interact with a Braacket league"""

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self._session = aiohttp.ClientSession()
        self.config = Config.get_conf(self, 5151798315418247, force_registration=True)
        self.config.register_guild(league=None, pr=None)

    def __unload(self):
        self.bot.loop.create_task(self._session.close())

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
        then the league ID is StevensMelee
        """
        if not _VALID_ID_REGEX.match(league):
            return await self._embed_msg(
                ctx,
                _(
                    "League ID can only contain alphanumeric characters, dashes, and underscores"
                ),
            )
        await self._fetch(ctx, f"https://www.braacket.com/league/{league}")
        await self.config.guild(ctx.guild).league.set(league)
        log.info(f"User {ctx.author} set league ID to {league} in guild {ctx.guild}")
        await self._embed_msg(ctx, _(f"Set Braacket league id to {league}"))

    @braacketset.command(name="pr")
    @checks.mod()
    async def set_pr(self, ctx: commands.Context, uuid: str):
        """Sets the ranking UUID.
        For example, if the URL to your desired ranking page is
        https://braacket.com/league/StevensMelee/ranking/39E07092-9936-4710-9EAA-1CDD3396A544
        then the ranking UUID is 39E07092-9936-4710-9EAA-1CDD3396A544

        !braacketset pr default will reset to the league's default ranking
        """
        if uuid.lower() == "default":
            await self.config.guild(ctx.guild).pr(None)
            log.info(
                f"User {ctx.author} set ranking UUID to league default in guild {ctx.guild}"
            )
            return await self._embed_msg(
                ctx, _("I will now use the league's default ranking")
            )
        try:
            uuid = UUID(uuid, version=4)
        except ValueError:
            return await self._embed_msg(ctx, _("This does not look like a valid UUID"))
        league = await self.config.guild(ctx.guild).league()
        if league is None:
            return await self._embed_msg(
                ctx,
                _(
                    "No league ID has been set yet. Please do !braacketset league [league-id]"
                ),
            )
        await self._fetch(
            ctx, f"https://www.braacket.com/league/{league}/ranking/{uuid}"
        )
        await self.config.guild(ctx.guild).pr.set(str(uuid).upper())
        log.info(
            f"User {ctx.author} set ranking UUID to {uuid} for {league} in guild {ctx.guild}"
        )
        await self._embed_msg(ctx, _(f"Set league's ranking UUID to {uuid}"))

    @commands.command()
    @commands.guild_only()
    async def bracket(self, ctx: commands.Context):
        """Fetches the latest tourney bracket"""
        league = await self.config.guild(ctx.guild).league()
        if league is None:
            return await self._embed_msg(
                ctx,
                _("League name has not been set yet. Use !braacketset league <league>"),
            )
        url = f"https://braacket.com/league/{league}/tournament"
        tourney_request = await self._fetch(ctx, url)
        tourney_soup = BeautifulSoup(tourney_request, "html.parser")
        latest = (
            tourney_soup.find(class_="col-xs-12 col-sm-6 col-md-4 col-lg-3")
            .find("a")
            .get("href")
        )
        await ctx.send(f"https://braacket.com{latest}/bracket")

    @commands.command()
    @commands.guild_only()
    async def pr(self, ctx: commands.Context, count: int = 5):
        """Fetches the top players on the current Power Ranking"""
        if not 1 <= count <= 10:
            return await self._embed_msg(
                ctx, _("Please pick a number between 1 and 10")
            )
        league = await self.config.guild(ctx.guild).league()
        if league is None:
            return await self._embed_msg(
                ctx,
                _("League name has not been set yet. Please do !braacketset <league>"),
            )
        pr = await self.config.guild(ctx.guild).pr()
        url = f'https://www.braacket.com/league/{league}/ranking/{pr or ""}'
        pr_request = await self._fetch(ctx, url)
        pr_soup = BeautifulSoup(pr_request, "html.parser")
        players = pr_soup.find_all(
            lambda x: re.match(f"/league/{league}/player/", x["data-href"])
            if x.has_attr("data-href")
            else False
        )
        points = pr_soup.find_all(class_="min text-right")
        for i in range(count):
            name = players[i].get_text(strip="True")
            player_url = "https://www.braacket.com" + players[i].a.get("href")
            character_url = "https://www.braacket.com" + players[i].img.get("src")
            mains = players[i].span.find_all("img")
            embed_desc = ""
            for j in range(len(mains) - 1):
                embed_desc += mains[j].get("title") + ", "
            embed_desc += mains[-1].get("title")  # Always get the last main
            embed_desc += " || " + points[i].get_text(strip="True")

            embed = discord.Embed(
                description=embed_desc, color=await ctx.embed_colour()
            )
            embed.set_author(
                name=str(i + 1) + ".\t" + name, url=player_url, icon_url=character_url
            )
            await ctx.send(embed=embed)

    async def _fetch(self, ctx: commands.Context, url: str):
        try:
            async with self._session.get(url) as resp:
                return await resp .text()
        except aiohttp.ClientResponseError as e:
            log.error(e)
            await self._embed_msg(ctx, _(f"Connection to {url} failed: {e}"))

    @staticmethod
    async def _embed_msg(ctx: commands.Context, title: str):
        embed = discord.Embed(color=await ctx.embed_colour(), title=title)
        await ctx.send(embed=embed)
