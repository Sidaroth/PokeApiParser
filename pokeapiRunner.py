# Retrieving select data from "https://pokeapi.co/" for all pokemon for use in spreadsheets/Databases. 
# Author: Sidaroth (Last edit: 2021-05-31)
# Copyright 2016 Christian Holt
# Requires: requests, csv --> Use (python -m pip install requests) to install requests if necessary. 

from pokeapiParser import PokeapiParser
from outputFormatting import GetCSV, GetConsoleString
from pokemon import Pokemon

												#             Generation
												#  1  |  2  |  3  |  4  |  5  |  6 | 7  |  8
STARTING_POKEMON 			= 1					# 151 + 100 + 135 + 107 + 156 + 72 + 88 + 89 == 898
END_POKEMON      		    = 898				# Total as of Generation 8 - Sword/Shield
NUMBER_OF_TYPES 			= 18				# of types as of Generation 8 - Sword/Shield == 18
NUMBER_OF_THREADS 			= 12				# 6 (x2) cores
NUMBER_OF_PRINTER_THREADS 	= 3
LOG_TO_CONSOLE 				= True

class Runner:
	""" Runs the PokeApiParser in threaded mode. """

	def __init__ (self):
		print("Welcome, be advised this may run for some time due to the amount of time requests take from PokeApi...")
		
		self.pokeApiParser = PokeapiParser()
		self.fieldnames = ['DexId', 'Name', 'Types', 'Weaknesses', 'Resistances', 'Immunities', 'Locations', 'Species', 'EggGroups']
		self.csvfile = open('poketypes.csv', 'w')
		self.writer = csv.DictWriter(self.csvfile,fieldnames=self.fieldnames,lineterminator='\n')
		self.writer.writeheader()

		self.threadedList = queue.Queue()
		self.threadedDex = queue.Queue()
		self.printLock = threading.RLock()

	def PrintThreaded(self):
		""" 'worker' threads that prints pokemon currently in the queue to console/CSV """
		while True:
			time.sleep(0.1)
			pokemon = self.threadedList.get()

			if pokemon is None:
				with self.printLock:
					print("printerThread received stop signal!")
				break

			if LOG_TO_CONSOLE:
				string = GetConsoleString(pokemon)
				with self.printLock:
					print(string)

			## Write to file
			csvObj = GetCSV(pokemon)
			with self.printLock:		
				self.writer.writerow(csvObj)
				self.csvfile.flush()

			self.threadedList.task_done()

	def RunThreaded(self):
		""" Runs through registered pokedex numbers from a queue to retrieve information """
		while True:
			dexId = self.threadedDex.get()
			if dexId is None:
				if LOG_TO_CONSOLE:
					with self.printLock:
						print("Producerthread received stop signal.")
				break
			
			if LOG_TO_CONSOLE:
				with self.printLock:
					print("New pokemon #" + str(dexId))

			pokemon = Pokemon()
			pokemon.SetDexId(dexId)
			self.pokeApiParser.ParsePokemon(pokemon)

			self.threadedList.put(pokemon)
			time.sleep(0.1)
			self.threadedDex.task_done()

	def StartThreads(self):
		""" Initiates the threads -- Boilerplate """
		producerThreads = []
		workerThreads = []
		cacheThreads = []

		## Precache all known types
		print("Pre-caching all types")
		for i in range(1, NUMBER_OF_TYPES + 1):
			thread = threading.Thread(target=self.pokeApiParser.PreCacheType, args=(i,))
			cacheThreads.append(thread)
			thread.daemon = True
			thread.start()

		for thread in cacheThreads:
			thread.join()

		self.pokeApiParser.ValidateTypeCache(NUMBER_OF_TYPES)

		## Main program
		print("Starting...")
		for i in range(NUMBER_OF_THREADS):
			thread = threading.Thread(target=self.RunThreaded)
			producerThreads.append(thread)
			thread.start()

		for i in range(NUMBER_OF_PRINTER_THREADS):
			thread = threading.Thread(target=self.PrintThreaded)
			workerThreads.append(thread)
			thread.start()

		# Enter pokedex numbers in the specified range
		for i in range(STARTING_POKEMON, END_POKEMON + 1):
			self.threadedDex.put(i)

		## Thread cleanup
		self.threadedDex.join()
		self.threadedList.join()

		print("Done! Cleaning up...")
		for i in range(len(producerThreads) + 1):
			self.threadedDex.put(None)
		for i in range(len(workerThreads) + 1):
			self.threadedList.put(None)

		for thread in producerThreads:
			thread.join()

		for thread in workerThreads:
			thread.join()

		self.csvfile.close()

########## THE HUGE MAIN PROGRAM ##########
def main():
	timeStamp = time.time()
	runner = Runner()
	runner.StartThreads()
	print('Took {}s'.format(time.time() - timeStamp))

if __name__ == '__main__':							## Because windows...
	import csv
	import threading
	import queue
	import time
	main()
