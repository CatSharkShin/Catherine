from discord.ext import commands
#from discord import Webhook,RequestsWebhookAdapter,Embed

from discord_webhook import DiscordWebhook
import codecs
import asyncio

from colorama import Fore
from libs.logger import Logger
import websockets

from discord import File


logger = Logger('Brain', Fore.CYAN)

decode_hex = codecs.getdecoder("hex_codec")

class FoxApi(commands.Cog):
	@commands.Cog.listener()
	async def on_ready(ctx):
		logger.log("Brain cog loaded ~Constant coffee fuel needed~")

	@commands.command(name="decode")
	async def decode(self,ctx,type,*,data):
		print("Got: "+data)
		if type == "hex":
			data = data.replace(" ","")
			data = data.replace("0x","")
			chars = data.split(",")
			data = data.replace(",","")
			print("data: "+data)
			decoded = ""
			for char in chars:
				print(char)
				decoded = decoded + decode_hex(str(char))[0].decode("utf-8")
			await ctx.send(content=f"Decoded to: {str(decoded)}")




async def setup(client):
	await client.add_cog(FoxApi(client))
