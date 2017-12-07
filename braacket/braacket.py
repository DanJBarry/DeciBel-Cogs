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
            await self.bot.say('https://braacket.com' + latest + '/bracket')
        except:
            await self.bot.say('Couldn\'t find the latest bracket. Something broke.')

    @commands.command()
    async def pr(self):
        '''Fetches the top 10 players on the current Power Ranking'''
        url = 'https://braacket.com/league/StevensMelee/ranking'
        async with aiohttp.get(url) as response:
            soupObject = BeautifulSoup(await response.text(), 'html.parser')
        try:
            table = soupObject.find_all(class_='panel-body')[1].table.tbody.find_all(class_='ellipsis')
            points = soupObject.find_all(class_='panel-body')[1].table.tbody.find_all(class_='min text-right')
            for player in range(10):
                name = table[player].get_text(strip='True')
                player_url = 'https://www.braacket.com' + table[player].a.get('href')
                character_url = 'https://www.braacket.com' + table[player].img.get('src')
                description = ''
                if len(table[player].span.find_all('img')) > 1:
                    for mains in range(len(table[player].span.find_all('img')) - 1):
                        description += table[player].span.find_all('img')[mains].get('title') + ', '
                description += table[player].span.find_all('img')[-1].get('title')
                description += ' || ' + points[player].get_text(strip='True')

                embed = discord.Embed(description=description)
                embed.set_author(name=name, url=player_url, icon_url=character_url)
                await bot.say(embed=embed)

        except:
            await self.bot.say('Couldn\'t find the latest PR. Something broke.')
        

def setup(bot):
    if soupAvailable:
        bot.add_cog(Braacket(bot))
    else:
        raise RuntimeError('You need to run `pip3 install beautifulsoup4`')
