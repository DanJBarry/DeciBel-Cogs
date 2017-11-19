'''
Created on Nov 19, 2017

@author: Dan Barry
'''

import discord
from discord.ext import commands

try: # check if BeautifulSoup4 is installed
    from bs4 import BeautifulSoup
    soupAvailable = True
except:
    soupAvailable = False
import aiohttp


class Braacket:
    '''Interact with the Stevens Melee Braacket page'''

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def bracket(self):
        '''Fetches the latest tourney bracket'''
        url = 'https://braacket.com/league/StevensMelee/tournament' #build the web address
        async with aiohttp.get(url) as response:
            soupObject = BeautifulSoup(await response.text(), 'html.parser')
        try:
            latest = soupObject.find(class_='col-xs-12 col-sm-6 col-md-4 col-lg-3').find('a').get('href')
            await self.bot.say('https://braacket.com/league/StevensMelee' + latest + '/bracket')
        except:
            await self.bot.say('Couldn\'t find the latest bracket. Something broke.')

def setup(bot):
    if soupAvailable:
        bot.add_cog(Braacket(bot))
    else:
        raise RuntimeError('You need to run `pip3 install beautifulsoup4`')