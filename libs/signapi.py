# Request handling and parsing
import requests
import urllib.request
from html.parser import HTMLParser

# Image processing
import io
from PIL import Image, ImageOps, ImageFile

# File saving etc.
import shutil
import os

# *Not used* type specification in functions
from typing import Callable, Any, Iterable, List

# id generation
import random
import string

# Debug coloring NOT USED BUT SHOUUULD
from colorama import init

# For listing the cache
from os import listdir
from os.path import isfile, join

#init() for colorama
init()

letters = "abcdefghijklmnopqrstuvwxyz"

class MyHTMLParser(HTMLParser):
	elements = []
	lastelementindex = None
	def handle_starttag(self,tag,attrs):
		element = dict()
		element['tag'] = tag
		element['attrs'] = dict()
		element['data'] = ""
		for attr in attrs:
			element['attrs'][attr[0]] = attr[1]
		self.elements.append(element)
		self.lastelementindex = len(self.elements)-1
	def handle_data(self, data):
		if self.lastelementindex is not None:
			self.elements[self.lastelementindex]['data'] += data


def clear_cache():
	cache = "__signcache__/"
	for filename in os.listdir(cache):
		file_path = os.path.join(cache,filename)
		try:
			if os.path.isfile(file_path) or os.path.islink(file_path):
				os.unlink(file_path)
			elif os.path.isdir(file_path):
				shutil.rmtree(file_path)
		except OSError as e:
			print(e)
##print('Failed to delete %s. Reason: %s' %(file_path,e) )


# Just a random ID generator to handle multiple requests later, i guess. idk
def id_generator(size=10, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

def getsizes(uri):
	# get file size *and* image size (None if not known)
	file = urllib.request.urlopen(uri)
	size = file.headers.get("content-length")
	if size: size = int(size)
	p = ImageFile.Parser()
	while 1:
		data = file.read(1024)
		if not data:
			break
		p.feed(data)
		if p.image:
			return size, p.image.size
			break
	file.close()
	return size, None

def is_grey_scale(img):
	w, h = img.size
	img = img.convert()
	##print("Checking for bnw: "+str(img.getpixel((0,0))))
	# First checks for format:
	if(isinstance(img.getpixel((0,0)),int)):
		# If the pixel format is Int, its only a value so its greyscale
		##print("Is bnw "+str(img.getpixel((0,0))))
		return True

	# If the pixel format isn't Int its RGB. we continue to check
	# We check w/10 pixels at h/2 and see if there is anything else then Black or White
	# So basically we cut the image in half horizontally, and check 10 pixels, see if they are BNW or not
	for i in range(0,w,int(w/10)):
		##print(str(img.getpixel((i,h/2))))
		r,g,b = img.getpixel((i,h/2))
		if r != g != b:
			##print("Isnt bnw")
			return False
	##print("Is bnw")
	return True

class SignContainer:
	def __init__(self,sign,logcallback,greyscales=None,onlynamed=False):
		#Settings
		self.sign = sign
		self.greyscales = greyscales
		self.onlynamed = onlynamed

		#callback
		self.logcallback = logcallback

		#Fetch
		self.image_groups = []
		self.gifs = []
		self.hints = []

		#Idk yet
		self.downloaded = []

	def clear_cache():
		files = [f for f in listdir(cache) if (isfile(join(cache, f)) and len([i for i in downloaded if i in f]) > 0 )]
		for file in files:
			os.remove(file)

	async def get_gifs(self,include=["downloaded_gif","generated_gif"]):
		cache = "__signcache__/"
		# Gives back paths to the gifs

		getdownloaded = bool(len([i for i in include if i in "downloaded_gif"]))
		getgenerated = bool(len([i for i in include if i in "generated_gif"]))

		#Fetch if needed
		if getdownloaded and not self.gifs:
			if getgenerated and not self.image_groups:
				await self.fetch()
			else:
				await self.fetch(getimages=False)
		else:
			if getgenerated and not self.image_groups:
				await self.fetch(getgifs=False)

		#Download if needed
		if not self.downloaded:
			if getdownloaded:
				for gif in self.gifs:
					gif.download()
			if getgenerated:
				for gif in self.image_groups:
					gif.download_gif()

		# check if they are files, and if any item of "include" is in its filename
		files = [f for f in listdir(cache) if (isfile(join(cache, f)) and len([i for i in include if i in f]) > 0 )]
		await self.logcallback(f"Found {len(files)} files")
		return iter(files)


	#Returns an array of io.BytesIO()
	async def get_images(self):

		#Fetch if needed
		if not self.image_groups:
			await self.fetch(getgifs = False)

		images = []
		for image_group in self.image_groups:
			images.extend(await image_group.get_images())
		print(len(images))
		await self.logcallback(f"Found {len(images)} files")
		return images


	#Parses lifeprint.com for the sign set. Fills up this container
	async def fetch(self,getgifs=True,getimages=True):
		r = requests.get(f"https://lifeprint.com/asl101/index/{self.sign[0]}.htm")
		groupParser = MyHTMLParser()
		groupParser.feed(r.text)
		src = next((x for x in groupParser.elements if (x['tag'] == 'a' and self.sign.lower() in x['data'].lower())), None)
		if('compound' in r.text):
			self.hints.append('compound')
		if src is None:
			print("[SignAPI] Sign not found")
			await self.logcallback("Sign not found%")
		else:
			print("[SignAPI] Sign found")
			await self.logcallback("Sign found! Please wait~")
			link = "https://lifeprint.com/asl101"+src['attrs']['href'][2:]
			# Get the site and parse it:
			await self.logcallback(f"Downloading...")
			r = requests.get(link)
			siteParser = MyHTMLParser()
			siteParser.feed(r.text)
			lastImageSize = None
			await self.logcallback(f"Processing {len(siteParser.elements)} elements...")
			for element in siteParser.elements:
				# If its an img tag
				if(element['tag'] == 'img'):
					if(getgifs and 'gif' in element['attrs']['src']):
						#If its a gif just save it in signurls['gifs']
						giflink = element['attrs']['src']
						if(giflink[0] == '.'):
							giflink = "https://lifeprint.com/asl101"+giflink[5:]
						gifObj = SignGif(self,giflink)
						self.gifs.append(gifObj)
					elif getimages:
						#If it isn't a gif its an image
						#Create the image's link
						imglink = element['attrs']['src']
						if(imglink[0] == '.'):
							imglink = "https://lifeprint.com/asl101/pages-signs"+imglink[2:]
						elif(imglink[0] != '/'):
							imglink = "https://lifeprint.com/asl101/pages-signs/"+sign.lower()[0]+"/"+imglink

						#Get current image's size
						currentImageSize = getsizes(imglink)[1]

						#If this is a new image group, create a new image group in signurls['image_groups']
						if(lastImageSize != currentImageSize):
							self.image_groups.append(SignImageGroup(self,currentImageSize))

						# Append the last image group created with the image
						self.image_groups[len(self.image_groups)-1].urls.append(imglink)
						lastImageSize = currentImageSize
			await self.logcallback(f"Processing done")
	@property
	async def images(self):
		return await self.get_images()

class SignGif:
	def __init__(self,container: SignContainer,url):
		self.url = url
		#Container assignment so it can look at the settings for the search
		self.container = container
		self.downloaded = False

	def download(self):
		r = requests.get(self.url)
		with Image.open(io.BytesIO(r.content)) as gif:
			if(self.container.greyscales is None or (greyscales and is_grey_Scale(gif))):
				if(self.container.onlynamed and sign in self.url or not self.container.onlynamed):
					id = id_generator()
					gif.save('__signcache__/'+'downloaded_gif_'+id+'.gif')
					self.container.downloaded.append(id)
					self.downloaded = True
					self.id = id
		return id


class SignImageGroup:
	# int id //set in download_gif()

	def is_gif():
		return not len(self.urls) == 1
	def is_image():
		return len(self.urls) == 1

	def __init__(self,container,size):
		self.size = size
		self.downloaded = False
		self.container = container
		self.urls = []

	def download_gif(self):
		if not len(self.urls) == 1:
			images = []
			for url in self.urls:
				r = requests.get(url,allow_redirects=True,stream=False)
				images.append(Image.open(io.BytesIO(r.content)))
			images.append(images[len(images)-1])
			images.append(images[len(images)-1])
			id = id_generator()
			images[0].save('__signcache__/'+'generated_gif_'+str(id)+'.gif',save_all=True,append_images=images[0:],loop=0,duration=200)
			self.container.downloaded.append(id)
			self.id = id
			self.downloaded = True
		return id

	#Returns a bytestream for the image
	def get_image(self):
		r = requests.get(self.urls[0],allow_redirects=True,stream=False)
		img_byte_arr = io.BytesIO()
		with Image.open(io.BytesIO(r.content)) as image:
			image.save(img_byte_arr, format="PNG")
		img_byte_arr = img_byte_arr.getvalue()
		stream = io.BytesIO(img_byte_arr)
		return stream

	def get_images(self):
		images = []
		for url in self.urls:
			r = requests.get(url,allow_redirects=True,stream=False)
			img_byte_arr = io.BytesIO()
			with Image.open(io.BytesIO(r.content)) as image:
				image.save(img_byte_arr, format="PNG")
			img_byte_arr = img_byte_arr.getvalue()
			stream = io.BytesIO(img_byte_arr)
			images.append(stream)
		return images

clear_cache()
