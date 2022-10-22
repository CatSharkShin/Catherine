import discord
import time
from discord.ext import commands
from colorama import Fore
from libs.logger import Logger
from libs.spotifycon import spotify

logger = Logger("Spotify", Fore.GREEN)


class Spotify(commands.Cog):
	def __init__(self, client):
		self.client = client

	async def subcommand_checker(self, ctx):
		def check(m):
			return m.author == ctx.author
		message = await self.client.wait_for("message", check=check)
		if message.content == "skip":
			await self.skip_subcommand(ctx)
		if message.content in ['play', 'resume', 'pause', 'start', 'stop', 'p']:
			await self.play_subcommand(ctx)

	@commands.Cog.listener()
	async def on_ready(ctx):
		logger.log("Spotify cog loaded")

	#.spotify
	@commands.group(name="spotify", invoke_without_command=True)
	async def spotify_basecommand(self, ctx):
		cur = spotify.currently_playing()
		listening = "" if spotify.currently_playing()['is_playing'] else "not "
		embedMsg = discord.Embed(title='Currently ' + listening + 'listening to',
                           description="Use '.spotify skip' or 'skip' to skip", color=0x1dB954)
		embedMsg.set_thumbnail(url=cur['item']['album']['images'][0]['url'])
		embedMsg.add_field(name=cur['item']['name'], value=cur['item']
                     ['album']['artists'][0]['name'], inline=False)
		await ctx.send(embed=embedMsg)
		await self.subcommand_checker(ctx)

	#.skip
	@spotify_basecommand.command(name="skip")
	async def skip_subcommand(self, ctx):
		spotify.next_track()

		async def currently():
			time.sleep(0.5)
			cur = spotify.currently_playing()
			embedMsg = discord.Embed(title="Skipped!, Now listening to",
                            description="Use '.spotify skip' or 'skip' to skip", color=0x1dB954)
			embedMsg.set_thumbnail(url=cur['item']['album']['images'][0]['url'])
			embedMsg.add_field(name=cur['item']['name'], value=cur['item']
                            ['album']['artists'][0]['name'], inline=False)
			await ctx.send(embed=embedMsg)
		self.client.asyncloop.create_task(currently())
		await self.subcommand_checker(ctx)

	#.play
	@spotify_basecommand.command(name="play", aliases=['resume', 'pause', 'start', 'stop', 'p'])
	async def play_subcommand(self, ctx):
		if spotify.currently_playing()['is_playing']:
			spotify.pause_playback()
		else:
			spotify.start_playback()
		await self.spotify_basecommand(ctx)


async def setup(client):
	await client.add_cog(Spotify(client))
