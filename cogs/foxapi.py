import types
import time
import asyncio
import websockets
from discord.ext import commands, tasks
from colorama import Fore
from libs.spotifycon import spotify
from libs.logger import Logger



logger = Logger('FoxApi', Fore.YELLOW)
PORT = 7890
listenuri = "ws://127.0.0.1:7890"

webhookurl = ""

class WebSocketServer():
	def __init__(self):
		self.CHUNK_DIVIDER = "~"
		self.VALUE_DIVIDER = ":"
		self.connected = set()
		self.message_callbacks = list()
		self.connect_callbacks = list()
		self.last_update_cache = {}
		self.update_cache = {}

	async def broadcast(self,message_cache):
		#Prepare string using the DIVIDERS
		message_string = "update"+self.CHUNK_DIVIDER
		for key in message_cache:
			message_string = ''.join([message_string, key, self.VALUE_DIVIDER,message_cache[key],self.CHUNK_DIVIDER])
		logger.log("[Broadcast]"+message_string)
		for conn in self.connected:
			await conn.send(message_string)

	async def add_to_cache(self,cache):
		for key in cache:
			if cache[key] is not None:
				self.update_cache[key] = cache[key]

	async def broadcast_update_cache(self):
		#Trim data that hasn't changed since last broadcast, and put the new values in self.last_update_cache
		trimmed_update_cache = {}
		for key in self.update_cache:
			if key not in self.last_update_cache or self.last_update_cache[key] != self.update_cache[key]:
				trimmed_update_cache[key] = self.update_cache[key]
				self.last_update_cache[key] = self.update_cache[key]
		self.update_cache = {}
		if len(trimmed_update_cache) > 0:
			await self.broadcast(trimmed_update_cache)

	@asyncio.coroutine
	async def server(self, websocket, path):
		logger.log("New connection")
		self.connected.add(websocket)
		await self.on_connect()
		try:
			async for message in websocket:
				params = message.split("/")
				logger.log(f"Recieved WS: {message}")
				await self.on_message(message)
				#DiscordWebhook(url=webhookurl,content=f"-foxapi send {message}").execute()
		except websockets.exceptions.ConnectionClosed as e:
			logger.log(f"A Client disconnected")
		finally:
			self.connected.remove(websocket)

	async def on_message(self,message):
		for callback in self.message_callbacks:
			await callback(message)

	async def on_connect(self):
		for callback in self.connect_callbacks:
			await callback()

	def registerForMessage(self,callback: types.FunctionType):
		self.message_callbacks.append(callback)

	def registerForConnect(self, callback: types.FunctionType):
		self.connect_callbacks.append(callback)

ws = WebSocketServer()

class FoxApi(commands.Cog):
	CHUNKCONCAT = "~"
	VALUEDIVIDER = ":"

	@commands.Cog.listener()
	async def on_ready(self):
		logger.log(f"Starting FoxApi")
		await websockets.serve(ws.server,"127.0.0.1",PORT)

		self.songUpdate.start()
		await self.reset_spotify_data()

		logger.log(f"Running Websockets on PORT {PORT}")

	def __init__(self, client):
		ws.registerForMessage(self.handleCommand)
		ws.registerForConnect(self.reset_spotify_data)
		self.client = client
		self.data = {}

	async def reset_spotify_data(self):
		self.data = self.get_spotify_data()
		await ws.broadcast(self.data)

	def get_spotify_data(self):
		cur = spotify.currently_playing()
		if cur is None:
			return {}

		playlist_name = None #context['name']
		playlist_image = None #context['images'][0]['url']
		context = None
		if cur['context'] is not None:
			match cur['context']['type']:
				case "playlist":
					context = spotify.playlist(cur['context']['uri'])
				case "artist":
					context = spotify.artist(cur['context']['uri'])
				case "album":
					context = spotify.album(cur['context']['uri'])
		else:
			if cur['item'] is not None:
				context = spotify.artist(cur['item']['album']['artists'][0]['uri'])

		playlist_name = context['name']
		playlist_image = context['images'][0]['url']

		track_name = None
		track_artist = None
		track_image = None
		track_progression = []
		if cur['item'] is not None:
			track_name = cur['item']['name']
			track_artist = cur['item']['album']['artists'][0]['name']
			track_image = cur['item']['album']['images'][0]['url']
			track_progression = [time.strftime('%#M:%S', time.gmtime(cur['progress_ms']/1000)), "\n", time.strftime('%#M:%S', time.gmtime(cur['item']['duration_ms']/1000))]

		is_playing = str(cur['is_playing'])

		data = {
			"track_name": track_name,
			"track_artist": track_artist,
			"track_image": track_image,
			"playlist_name": playlist_name,
			"playlist_image": playlist_image,
			"is_playing": is_playing,
			"progression": "".join(track_progression)
		}
		return data

	@tasks.loop(seconds=1.0)
	async def songUpdate(self):
		if len(ws.connected) > 0:
			await ws.add_to_cache(self.get_spotify_data())
			await ws.broadcast_update_cache()

	async def spotifySkip(self):
		spotify.next_track()

	async def spotifyPrev(self):
		spotify.previous_track()

	async def spotifyPlay(self):
		if spotify.currently_playing()['is_playing']:
			spotify.pause_playback()
		else:
			spotify.start_playback()

	async def handleSpotifyCommand(self,params):
		match params[0]:
			case "skip":
				await self.spotifySkip()
			case "play":
				await self.spotifyPlay()
			case "prev":
				await self.spotifyPrev()

	async def handleCommand(self,command):
		params = command.split("~")
		match params[0]:
			case "spotify":
				await self.handleSpotifyCommand(params[1:])

	@commands.group(name="foxapi",invoke_without_command=True)
	async def foxapi(self, ctx,*,msg):
		self.broadcast(msg)

async def setup(client):
	await client.add_cog(FoxApi(client))
