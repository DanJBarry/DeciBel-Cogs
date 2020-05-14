import asyncio
import logging
import pathlib
import typing

import discord
import gpt_2_simple
from redbot import core
from redbot.core import checks, commands, data_manager, i18n

translator = i18n.Translator("Gpt2", __file__)

log = logging.getLogger("red.gpt2")


@i18n.cog_i18n(translator)
class Gpt2(commands.Cog):
    """Interact with a Braacket league"""

    async def _begin_generator(self) -> asyncio.Future:
        async with self.config.model() as model:
            async with self.config.max_size() as max_size:
                self.generate_samples: asyncio.Future = asyncio.run_coroutine_threadsafe(
                    self._generate_samples(model, max_size), self.bot.loop
                )

    async def _generate_samples(self, model: typing.Optional[str] = None, max_size=31):
        if model == None:
            return
        cog_data_path = data_manager.cog_data_path(self)
        model_path: pathlib.Path = cog_data_path / "models" / model
        if not model_path.exists():
            log.error(f"Model {model} not found in {str(cog_data_path)}")
            return
        tf_session = gpt_2_simple.start_tf_sess()
        gpt_2_simple.load_gpt2(
            tf_session,
            checkpoint_dir=str(cog_data_path / "checkpoints"),
            model_name=model,
            model_dir=str(model_path.parent),
        )
        while True:
            new_sample = gpt_2_simple.generate(
                tf_session,
                return_as_list=True,
                truncate="<|endoftext|>",
                temperature=1.0,
            )[0]
            async with self.full:
                if len(self.samples) >= max_size:
                    log.info("Cache full, waiting for next command")
                    await self.full.wait()
                self.samples.append(new_sample)
            async with self.empty:
                if len(self.samples) == 1:
                    self.empty.notify()

    def __init__(self, bot: commands.Bot):
        super().__init__()
        samples_lock = asyncio.Lock()
        self.bot = bot
        self.config = core.Config.get_conf(
            self, 3133310390284153, force_registration=True
        )
        self.samples = []
        self.samples_lock = samples_lock
        self.empty = asyncio.Condition(samples_lock)
        self.full = asyncio.Condition(samples_lock)
        self.waiting_guilds = set()
        self._begin_generator()

    def cog_unload(self):
        super().cog_unload()
        self.generate_samples.cancel()

    @commands.command()
    @commands.guild_only()
    async def gpt(self, ctx: commands.Context):
        if self.generate_samples.done():
            await self._begin_generator()
        guild: discord.Guild = ctx.guild()
        if guild in self.waiting_guilds:
            return
        max_size = await self.config.max_size()
        async with self.empty:
            if len(self.samples) <= 0:
                log.info(f"Cache empty, {guild.name} waiting for a new sample")
                await ctx.send("Waiting for a new response, this may take a while...")
                self.waiting_guilds.add(guild.id)
                await self.empty.wait()
                self.waiting_guilds.remove(guild.id)
            await ctx.send(self.samples.pop(0))
        async with self.full:
            if len(self.samples) == max_size - 1:
                self.full.notify()

    @commands.group()
    @commands.guild_only()
    async def gptset(self, ctx: commands.Context):
        """Gpt2 client configuration options"""

    @gptset.command(name="max")
    @checks.is_owner()
    async def set_max(self, ctx: commands.Context, max_size: str):
        """Sets the max number of saved responses"""
        try:
            parsed_max = int(max_size)
        except ValueError:
            log.error(f"Tried to set max cache size to invalid value: {max_size}")
            return await ctx.send(translator("Not a number"))
        if parsed_max <= 0:
            return await ctx.send(translator("Must be a positive number"))
        self.generate_samples.cancel()
        await self.config.max_size.set(parsed_max)
        await self._begin_generator()
        log.info(f"Max cache size set: {parsed_max}")
        await ctx.send(translator(f"Set max cache size to {parsed_max}"))

    @gptset.command(name="mode")
    @checks.is_owner()
    async def set_model(self, ctx: commands.Context, model: str):
        """Sets the model name, will download if set to a base model"""
        stripped_model = model.strip()
        if stripped_model == None:
            return await ctx.send(translator("Please give a model name"))
        cog_data_path = data_manager.cog_data_path(self)
        model_path: pathlib.Path = cog_data_path / "models" / stripped_model
        base_model_path = str(model_path.parent)
        if not model_path.exists():
            if stripped_model in ("124M", "335M", "774M", "1558M"):
                log.info(f"Downloading model {model}")
                await ctx.send(f"Downloading model {model}")
                gpt_2_simple.download_gpt2(base_model_path, stripped_model)
            else:
                log.info(f"Attempted to set model to {str(model_path)}")
                await ctx.send(
                    translator(
                        f"{model} does not exist, please place the model in {base_model_path}"
                    )
                )
        self.generate_samples.cancel()
        await self.config.model.set(stripped_model)
        await self._begin_generator()
        log.info(f"Model set: {stripped_model}")
        await ctx.send(translator(f"Set model to {stripped_model}"))

    @commands.command()
    @checks.is_owner()
    async def clearcache(self, ctx: commands.Context):
        """Clear the responses cache"""
        async with self.samples_lock:
            self.samples.clear()
        log.info("Cache cleared")
        await ctx.send(translator("Cache cleared"))
