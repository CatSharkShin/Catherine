import discord
import numpy as np
import io
import requests
import re
import os
import libs.colorswapper as cs
import moviepy.editor as mpy
import time
from discord.ext import commands
from colorama import Fore
from libs.logger import Logger
from PIL import Image
from discord import File

logger = Logger("Colors", Fore.CYAN)


def get_avg_fps(PIL_Image_object):
	""" Returns the average framerate of a PIL Image object """
	PIL_Image_object.seek(0)
	frames = duration = 0
	while True:
		try:
			frames += 1
			duration += PIL_Image_object.info['duration']
			PIL_Image_object.seek(PIL_Image_object.tell() + 1)
		except EOFError:
			return frames / duration * 1000
	return None


class Colors(commands.Cog):
	def __init__(self, client):
		self.client = client

	@commands.Cog.listener()
	async def on_ready(ctx):
		logger.log("Colors cog loaded")

	@commands.command(name="color")
	async def color(self, ctx, hue=None):
		if hue is None:
			await ctx.send(content="Hue value?(0-100)")

			def check(m):
				return m.author == ctx.author
			message = await self.client.wait_for("message", check=check)
			try:
				hue = int(message.content)
			except ValueError:
				embedMsg = discord.Embed(title="Value isn't an integer",
                            description="Big dum :|", color=0x910000)
				await ctx.send(embed=embedMsg)
				return
		else:
			hue = int(hue)
		if hue < 0 or hue > 100:
			embedMsg = discord.Embed(title='Value out of range',
                           description="Big dum :|", color=0x910000)
			await ctx.send(embed=embedMsg)
			return
		if not ctx.message.attachments:
			await ctx.send(content="Image pleaseeee")

			def check(m):
				return m.author == ctx.author
			message = await self.client.wait_for("message", check=check)
			if not message.attachments:
				return
			urls = message.attachments
		else:
			urls = ctx.message.attachments
		progress = 0
		maxprogress = len(urls)
		progress_message = await ctx.send(content=f"Yes 😵 Processing! [0/{maxprogress}]")
		#PROCESS IMAGES
		for url in urls:
			tic = time.perf_counter()
			url = url.url
			r = requests.get(url, allow_redirects=True, stream=False)

			logger.log("Request done in "+format(time.perf_counter()-tic, '.2f'))

			if(r.headers["content-type"] in ("image/png", "image/jpeg", "image/jpg")):
				if int(r.headers["content-length"]) < 50000000:
					fname = ''
					if "Content-Disposition" in r.headers.keys():
						fname = re.findall("filename=(.+)", r.headers["Content-Disposition"])[0]
					else:
						fname = url.split("/")[-1]
					tic = time.perf_counter()

					img_byte_arr = io.BytesIO()
					with Image.open(io.BytesIO(r.content)) as image:
						arr = np.array(image)
						# HUE SHIFT
						read_image = Image.fromarray(cs.shift_hue(arr, float(hue)/100))
						read_image.save(img_byte_arr, format="PNG")
					img_byte_arr = img_byte_arr.getvalue()
					stream = io.BytesIO(img_byte_arr)

					logger.log("Hue conversion done in "
					           + format(time.perf_counter()-tic, '.2f'))
					await ctx.send(file=File(filename=fname, fp=stream))
					progress += 1
					await progress_message.edit(content=f"Yes 😵 Processing! [{progress}/{maxprogress}]")
				else:
					embedMsg = discord.Embed(title='Image too big dummy',
					                         description="Send me money on paypal and i'll increase the limit bitchhh", color=0x910000)
					await ctx.send(embed=embedMsg)
					progress += 1
					await progress_message.edit(content=f"Yes 😵 Processing! [{progress}/{maxprogress}]")
			elif(r.headers["content-type"] == "image/gif"):
				if int(r.headers["content-length"]) < 50000000:
					fname = ''
					if "Content-Disposition" in r.headers.keys():
						fname = re.findall("filename=(.+)", r.headers["Content-Disposition"])[0]
					else:
						fname = url.split("/")[-1]
					tic = time.perf_counter()
					with Image.open(io.BytesIO(r.content)) as gif:
						gif_np_list = []
						for frame in range(0, gif.n_frames):
							gif.seek(frame)
							#gif.save(f"before{frame}.png")
							arr = np.array(gif.convert())
							#frame_image = Image.fromarray()
							#frame_image.save(f"after{frame}.png",format="PNG")
							img_np_array = np.array(cs.shift_hue(arr, float(hue)/100))
							gif_np_list.append(img_np_array)
						gif = mpy.ImageSequenceClip(gif_np_list, fps=get_avg_fps(gif))
						gif.write_gif(fname, logger=None)
					print(f"fname: {fname}")
					await ctx.send(file=File("./"+fname))
					os.remove(fname)
					logger.log("Hue shifting done in: "
					           + format((time.perf_counter()-tic), '.2f')+"s")
					progress += 1
					await progress_message.edit(content=f"Yes 😵 Processing! [{progress}/{maxprogress}]")
			else:
				embedMsg = discord.Embed(
					title='The file must be an image.', description=" ", color=0x910000)
				await ctx.send(embed=embedMsg)
				progress += 1
				await progress_message.edit(content=f"Yes 😵 Processing! [{progress}/{maxprogress}]")

	@commands.command(name="purple")
	async def purple(self, ctx):
		if ctx.author.id in [855528241342578730, 367479273436741642]:
		   await self.color(ctx, 75)
		else:
			embedMsg = discord.Embed(title='You are not Cat or his baby, Senko',
			                         description="use '.color' instead", color=0x910000)
			await ctx.send(embed=embedMsg)


async def setup(client):
	 await client.add_cog(Colors(client))
