# #catherine.py
import os
import discord
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
from colorama import Fore
from libs.logger import Logger


#SETUP DISCORD
load_dotenv()
TOKEN = os.getenv('catherine')

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix='.', intents=intents)

client.asyncloop = asyncio.new_event_loop()
logger = Logger('Bot', Fore.MAGENTA)


@client.event
async def on_message(message):
	ctx = await client.get_context(message)
	if ctx.valid:
		await client.invoke(ctx)


@client.event
async def on_ready():
	logger.log(f'{client.user} has connected to Discord!')
	# Setting `Listening ` status
	await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="♡~Sleepy Senko~♡"))


@client.command()
async def load(ctx, extension):
	if f'cogs.{extension}' not in client.extensions.keys():
		client.load_extension(f'cogs.{extension}')
		logger.log(f'{extension} loaded')
		await ctx.send(content=f'{extension} loaded')
	else:
		await ctx.send(content=f'{extension} already loaded')


@client.command()
async def unload(ctx, extension):
	if f'cogs.{extension}' in client.extensions.keys():
		client.unload_extension(f'cogs.{extension}')
		logger.log(f'{extension} unloaded')
		await ctx.send(content=f'{extension} unloaded')
	else:
		await ctx.send(content=f'{extension} already unloaded')


@client.command()
async def reload(ctx, extension):
	if f'cogs.{extension}' in client.extensions.keys():
		client.reload_extension(f'cogs.{extension}')
	else:
		client.load_extension(f'cogs.{extension}')
	logger.log(f'{extension} reloaded')
	await ctx.send(content=f'{extension} reloaded~')

async def load_extensions():
	for filename in os.listdir('./cogs'):
		if filename.endswith('.py'):
			await client.load_extension(f'cogs.{filename[:-3]}')

async def main():
    async with client:
        await load_extensions()
        await client.start(TOKEN)
asyncio.run(main())

