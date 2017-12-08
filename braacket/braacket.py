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
		self._pr_url = None

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
	async def pr(self, players=5):
		'''Fetches the top players on the current Power Ranking'''
		if self._pr_url is None:
			return await self.bot.say('No URL has been set. Use !setpr <url>')
		if not 0 < players <= 10:
			return await self.bot.say('Players must be between and including 1 through 10')
		async with aiohttp.get(self._pr_url) as response: #Look at the html of https://braacket.com/league/StevensMelee/ranking if you want to understand this code at all
			soupObject = BeautifulSoup(await response.text(), 'html.parser')
		try:
			table = soupObject.find_all(class_='panel-body')[1].table.tbody.find_all(class_='ellipsis') #Gets the table of players
			points = soupObject.find_all(class_='panel-body')[1].table.tbody.find_all(class_='min text-right') #Gets the table of points for each player
			for player in range(players): #We're gonna do this for the top 10
				name = table[player].get_text(strip='True') #The names are the plaintext elements
				player_url = 'https://www.braacket.com' + table[player].a.get('href') #Grabs the link of each player
				character_url = 'https://www.braacket.com' + table[player].img.get('src') #Grabs the icon for the first character of each player
				description = ''
				if len(table[player].span.find_all('img')) > 1: #If the player has more than one main listed we do this
					for mains in range(len(table[player].span.find_all('img')) - 1): #Does this for each character minus the last one
						description += table[player].span.find_all('img')[mains].get('title') + ', '
				description += table[player].span.find_all('img')[-1].get('title') #Gets the very last character
				description += ' || ' + points[player].get_text(strip='True') #Adds the player's points to the description

				embed = discord.Embed(description=description) #Starts creating the embed, beginning with description
				embed.set_author(name=str(player + 1) + ". "+ name, url=player_url, icon_url=character_url) #Sets author info as the player's info
				await self.bot.say(embed=embed)

		except:
			await self.bot.say('Couldn\'t find the latest PR. Something broke.')

	@commands.command()
	async def setpr(self, url):
		'''Set the URL to use for !pr'''
		try:
			test_url = url.strip().split('/')
			if not ((test_url[0] == 'https:' or test_url[0] == 'http:') and test_url[2] == 'braacket.com' and test_url[3] == 'league' and test_url[5] == 'ranking'):
				return await self.bot.say('Failed to set URL. Must be some form of https://braacket.com/league/[league name]/ranking')
			if url[-1] == '/':
				url = url[:-1]
			self._pr_url = url
			await self.bot.say('Successfully set the URL to ' + url)
		except:
			await self.bot.say('Something broke :(')
		

def setup(bot):
	if soupAvailable:
		bot.add_cog(Braacket(bot))
	else:
		raise RuntimeError('You need to run `pip3 install beautifulsoup4`')