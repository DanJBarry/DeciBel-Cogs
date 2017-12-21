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
		self._league = None
		self._pr_url = None
		self._player_list = {}

	@commands.command()
	async def bracket(self):
		'''Fetches the latest tourney bracket'''
		if self._league is None:
			return await self.bot.say('League name has not been set yet. Use !setleague <league>')
		url = 'https://braacket.com/league/' + self._league + '/tournament' #build the web address
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
		if self._league is None:
			return await self.bot.say('League name has not been set yet. Use !setleague <league>')
		if not 0 < players <= 10:
			return await self.bot.say('Players must be between and including 1 through 10')
		if self._pr_url is None:
			url = 'https://www.braacket.com/league/' + self._league + '/ranking'
		else:
			url = 'https://www.braacket.com/league/' + self._league + '/ranking/' + self._pr_url
		async with aiohttp.get(url) as response: #Look at the html of https://braacket.com/league/StevensMelee/ranking if you want to understand this code at all
			soupObject = BeautifulSoup(await response.text(), 'html.parser')
		try:
			table = soupObject.find_all(class_='panel-body')[1].table.tbody.find_all(class_='ellipsis') #Gets the table of players
			points = soupObject.find_all(class_='panel-body')[1].table.tbody.find_all(class_='min text-right') #Gets the table of points for each player
			for player in range(players): #We're gonna do this for the number of players specified
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
				embed.set_author(name=str(player + 1) + ". 	"+ name, url=player_url, icon_url=character_url) #Sets author info as the player's info
				await self.bot.say(embed=embed)

		except:
			await self.bot.say('Couldn\'t find the latest PR. Something broke.')

	@commands.command()
	async def playerinfo(self, player):
		'''Fetches info about the specified player from Braacket'''
		try:
			if player not in self._player_list:
				listurl = 'https://www.braacket.com/league/' + self._league + '/player?rows=200'
				async with aiohttp.get(listurl) as response:
					bigListOfPlayers = BeautifulSoup(await response.text(), 'html.parser') #Yeah I realize I'm using both camel case and underscores, fuck off
				table = bigListOfPlayers.find(class_='panel-body').find_all('a')
				for i in len(table):
					name = table[i].get_text()
					if name not in self._player_list:
						self._player_list[name] =  table[i].get('href')
			if player not in self._player_list:
				return await self.bot.say('Sorry, player could not be found.')
			player_url = 'https://www.braacket.com' + self._player_list[player]
			await self.bot.say(player_url)
		except:
			await.self.bot.say('Something broke :(')

	@commands.command()
	async def setpr(self, url=None):
		'''Set the ID of the pr to use for !pr. Leave blank to use the default'''
		try:
			if url is None:
				self._pr_url = None
				return await self.bot.say('Successfully set the PR to the default')
			self._pr_url = url.strip()
			await self.bot.say('Successfully set the PR ID to ' + self._pr_url)

		except:
			await self.bot.say('Something broke :(')

	@commands.command()
	async def setleague(self, league):
		'''Sets the league name'''
		try:
			self._league = league.strip()
			self._player_list = {}
			listurl = 'https://www.braacket.com/league/' + self._league + '/player?rows=200'
			async with aiohttp.get(listurl) as response:
				bigListOfPlayers = BeautifulSoup(await response.text(), 'html.parser')
			table = bigListOfPlayers.find(class_='panel-body').find_all('a')
			for i in len(table):
				name = table[i].get_text()
				self._player_list[name] =  table[i].get('href')
			await self.bot.say('Successfully set the league id to ' + self._league)
		except:
			await self.bot.say('Something broke :(')

		

def setup(bot):
	if soupAvailable:
		bot.add_cog(Braacket(bot))
	else:
		raise RuntimeError('You need to run `pip3 install beautifulsoup4`')