# Retrieving select data from "https://pokeapi.co/" for all pokemon for use in spreadsheets/Databases. 
# Author: Sidaroth (Last edit: 2021-05-25)
# Copyright 2021 Christian Holt
# Requires: requests, csv --> Use (python -m pip install requests) to install requests if necessary. 

from output import GetCSV, GetConsoleString
from pokedata import Pokedata

												#             Generation
												#  1  |  2  |  3  |  4  |  5  |  6 | 7  |  8
STARTING_POKEMON 			= 1					# 151 + 100 + 135 + 107 + 156 + 72 + 88 + 89 == 898
END_POKEMON      		    = 898				# Total as of Generation 8 - Sword/Shield
NUMBER_OF_TYPES 			= 18				# of types as of Generation 8 - Sword/Shield == 18
NUMBER_OF_THREADS 			= 12				# 6 (x2) cores
NUMBER_OF_PRINTER_THREADS 	= 3
LOG_TO_CONSOLE 				= False

################## CLASSES #######################

class Parser:
	"""Connects, retrieves and parses data from PokeApi"""

	def __init__ (self):
		""" Constructor / Object Model """
		print("Welcome, be advised this may run for some time due to the amount of time requests take from PokeApi...")
		self.baseUrl = "https://pokeapi.co/api/v2/pokemon/"											
		self.fieldnames = ['DexId', 'Name', 'Types', 'Weaknesses', 'Resistances', 'Immunities', 'Locations']
		self.csvfile = open('poketypes.csv', 'w')
		self.writer = csv.DictWriter(self.csvfile,fieldnames=self.fieldnames,lineterminator='\n')
		self.writer.writeheader()

		self.typeCache = []
		self.threadedList = queue.Queue()
		self.threadedDex = queue.Queue()
		self.printLock = threading.RLock()

	def PreCacheType(self, type):
		""" Pre-cache all known types """
		response = requests.get("http://pokeapi.co/api/v2/type/" + str(type))
		json = response.json()
		self.typeCache.append(json)

	def requestPokemonJson(self, pokemon):
		""" Request the pokemon JSON data from the poke API """ 
		try:
			response = requests.get(self.baseUrl + str(pokemon.GetDexId()))
			json = response.json()
			return json
		except requests.exceptions.RequestException as exception:
			print(exception)
			sys.exit(True)

	def FillTypesFromJson(self, pokemon, json):
		"""Find pokemon name and type(s) for the given DexId"""
		pokemon.SetName(json['name'].title())								# capitalizes the pokemon name
		for pokemonType in json['types']:
			pokemon.AddType(pokemonType['type'])

	def FillLocationsFromJson(self, pokemon, json):
		"""  Set locations the pokemon is available for capture/encounter """
		response = requests.get(json['location_area_encounters'])
		locationData = response.json()

		for loc in locationData:
			area = loc['location_area']
			versions = loc['version_details']
			location = area['name'] + ' ('

			for index, version in enumerate(versions):
				location += version['version']['name']
				if index != len(versions) - 1: # if not last element.
					location += ', '
			
			location += ')'
			pokemon.AddLocation(location)

	def DetermineTypeEffectiveness(self, pokemon):
		"""Using the types found for the Pokemon, determine Type Effectiveness(weaknesses, resistances, immunities)"""
		for pokemonType in pokemon.GetTypes():
			match = False
			for cachedType in self.typeCache:								# Check for cached types
				if pokemonType['name'] == cachedType['name']:
					targetType = cachedType
					match = True
					break

			assert match == True													# Make sure we have a match

				## Immunity
			for immunity in targetType['damage_relations']['no_damage_from']:
				pokemon.AddImmunity(immunity['name'])

				## Resistance
			for resistance in targetType['damage_relations']['half_damage_from']:
				pokemon.AddResistance(resistance['name'])
								
				## Weakness
			for weakness in targetType['damage_relations']['double_damage_from']:
				pokemon.AddWeakness(weakness['name'])

		pokemon.CheckDuplicates()

	def PrintThreaded(self):
		""" 'worker' threads that prints pokemon currently in the queue """
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

			pokemon = Pokedata()
			pokemon.SetDexId(dexId)
			json = self.requestPokemonJson(pokemon)

			self.FillTypesFromJson(pokemon, json)
			self.FillLocationsFromJson(pokemon, json)
			self.DetermineTypeEffectiveness(pokemon)

			self.threadedList.put(pokemon)
			time.sleep(0.1)
			self.threadedDex.task_done()

	def StartThreaded(self):
		""" Initiates the threads -- Boilerplate """
		producerThreads = []
		workerThreads = []
		cacheThreads = []

		## Precache types
		print("Pre-caching all types")
		for i in range(1, NUMBER_OF_TYPES + 1):
			thread = threading.Thread(target=self.PreCacheType, args=(i,))
			cacheThreads.append(thread)
			thread.daemon = True
			thread.start()

		for thread in cacheThreads:
			thread.join()

		assert len(self.typeCache) == NUMBER_OF_TYPES

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
	parser = Parser()
	parser.StartThreaded()
	print('Took {}s'.format(time.time() - timeStamp))

if __name__ == '__main__':							## Because windows...
	import csv
	import requests
	import threading
	import queue
	import time
	import sys
	from collections import Counter
	main()
