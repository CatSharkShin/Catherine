import libs.signapi as signs
from discord.ext import commands
from colorama import Fore
from libs.logger import Logger
from discord import File


logger = Logger('Signs', Fore.YELLOW)


class Signs(commands.Cog):
	def __init__(self, client):
		self.client = client

	@commands.Cog.listener()
	async def on_ready(ctx):
		logger.log("Signs cog loaded")

	@commands.command(name="sign")
	async def sign(self, ctx, sign, type):
		signApi = signs.SignContainer(sign)
		logger.log(type)
		if type == "gif":
			for file in signApi.get_gifs():
				await ctx.send(file=File(filename="gif.gif", fp="./__signcache__/"+file))
		if type == "img":
			for file in signApi.get_images():
				await ctx.send(file=File(filename="image.png", fp=file))


async def setup(client):
	await client.add_cog(Signs(client))
