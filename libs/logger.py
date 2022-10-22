# Log Debug coloring
from colorama import init, Fore

class Logger():
	def __init__(self,name,color):
		init(autoreset=True)
		self.name = f'{color}[{name}] '
	def log(self,text,tag="log"):
				# tag can be:
					# log: Purple, for normal logging
					# success or green:
					# error or red:
		if tag == 'log':
			print(f'{self.name} {Fore.BLUE} {text}')
