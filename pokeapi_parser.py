# Retrieving select data from "https://pokeapi.co/" for all pokemon for use in spreadsheets/Databases. 
# Author: Sidaroth (Last edit: 2016-03-15)
# Copyright 2016 Christian Holt
# Requires: requests, csv --> Use (python -m pip install requests) to install requests if necessary. 

# Pokedata class contains:
# - Pokedex ID (National)
# - Pokemon Name
# - Types
# - Weaknesses
# - Resistances
# - Immunities
# - ... (Location in-game?)					

# TODO
# Consider restructuring to support a second, asynchronously filled pokemon queue for potential benefit between FindType and DetermineTypeEffectiveness
# i.e https://stackoverflow.com/questions/2632520/what-is-the-fastest-way-to-send-100-000-http-requests-in-python


												#             Generation
												#  1  |  2  |  3  |  4  |  5  |  6
STARTING_POKEMON 			= 1;				# 151 + 100 + 135 + 107 + 156 + 72 == 721
END_POKEMON      		    = 721;				# Total as of Generation 6 - XYORAS
NUMBER_OF_TYPES 			= 18;				# of types as of Generation 6 - XYORAS == 18
NUMBER_OF_THREADS 			= 12;				# 6 (x2) cores
NUMBER_OF_PRINTER_THREADS 	= 3;

################## CLASSES #######################
class Pokedata:
	"""Container for all pokemon data"""

	def __init__(self):
		"""Constructor/Object model"""
		self.name = ""					# 
		self.dexId = 0					# 
		self.types = []					# typename, url
		self.weaknesses = []			# typename
		self.immunities = []			# typename
		self.resistances = []			# typename

		## Types
	def AddType(self, type):
		self.types.append(type)
	def GetTypes(self):
		return self.types
		
		## Weaknesses
	def AddWeakness(self, weakness):
		self.weaknesses.append(weakness)
	def GetWeaknesses(self):
		return self.weaknesses
	def RemoveWeakness(self, weakness):
		self.weaknesses.remove(weakness) 

		## Resistances
	def AddResistance(self, resistance):
		self.resistances.append(resistance)
	def GetResistances(self):
		return self.resistances
	def RemoveResistance(self, resistance):
		self.resistances.remove(resistance)

		## Immunities
	def AddImmunity(self, immunity):
		self.immunities.append(immunity)
	def GetImmunities(self):
		return self.immunities
		
		## GET/SET ##
	def SetName(self, name):
		self.name = name
	def SetDexId(self, dexId):
		self.dexId = dexId
	def GetName(self):
		return self.name
	def GetDexId(self):
		return self.dexId

		## Sort ##
	def SortImmunities(self):
		self.immunities.sort()
	def SortWeaknesses(self):
		self.weaknesses.sort()
	def SortResistances(self):
		self.resistances.sort()

class Parser:
	"""Connects, retrieves and parses data from PokeApi"""

	def __init__ (self):
		""" Constructor / Object Model """
		print("Welcome, be advised this may run for some time due to the amount of time requests take from PokeApi...")
		self.baseUrl = "http://pokeapi.co/api/v2/pokemon/"											
		self.fieldnames = ['DexId', 'Name', 'Types', 'Weaknesses', 'Resistances', 'Immunities']
		self.csvfile = open('poketypes.csv', 'w')
		self.writer = csv.DictWriter(self.csvfile,fieldnames=self.fieldnames,lineterminator='\n')
		self.writer.writeheader()

		self.typeCache = []
		self.threadedList = queue.Queue()
		self.threadedDex = queue.Queue()
		self.printLock = threading.RLock()

	def FindType(self, pokemon):
		"""Find pokemon name and type(s) for the given DexId"""
		try:
			response = requests.get(self.baseUrl + str(pokemon.GetDexId()))
			json = response.json()

			pokemon.SetName(json['name'].title())								# capitalizes the pokemon name
			for pokemonType in json['types']:
				pokemon.AddType(pokemonType['type'])

		except requests.exceptions.RequestException as exception:
			print(exception)
			sys.exit(True)

		

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

		self.CheckDuplicates(pokemon)

	def CheckDuplicates(self, pokemon):
		""" Check immunities, resistances and weaknesses for duplicates that cancel out """			
		pokemon.SortWeaknesses()
		pokemon.SortResistances()
		pokemon.SortImmunities()

		for resistance in pokemon.GetResistances():			## Check all resistances up against all immunities.
			for immunity in pokemon.GetImmunities():
				if resistance == immunity:					## Pokemon is immune, remove resistance from list. 
					pokemon.RemoveResistance(resistance)
		for weakness in pokemon.GetWeaknesses():			## Check all weaknesses up against all immunities
			for immunity in pokemon.GetImmunities():
				if weakness == immunity:					## Pokemon is immune, remove weakness from list. 
					pokemon.RemoveWeakness(weakness)
		for weakness in pokemon.GetWeaknesses():			## Check all weakness up against all resistances
			for resistance in pokemon.GetResistances():
				if weakness == resistance:					## 1/2 x 2x == 1x, they cancel out. 
					pokemon.RemoveWeakness(weakness)
					pokemon.RemoveResistance(resistance)

															## Count resistances to check for 1/4x resistance
															## Count Weaknesses to check for 4x weakness

	def PrintThreaded(self):
		""" 'worker' threads that prints pokemon currently in the queue """
		while True:
			time.sleep(0.1)
			pokemon = self.threadedList.get()
			if pokemon is None:
				with self.printLock:
					print("printerThread received stop signal!")
				break

				## Console
				##### blablabla string formatting #####
			string = "#"
			string += str(pokemon.GetDexId()) + " " + pokemon.GetName() + " is of type(s): "
			for types in pokemon.GetTypes():
				string += types['name'] + ", "

				## Weaknesses
			string += "and is weak against: "
			for weakness in pokemon.GetWeaknesses():
				string += weakness + ", "

				## Resistances
			string += "but resistant to "
			for resistance in pokemon.GetResistances():
				string += resistance + ", "

			## Immunities
			if len(pokemon.GetImmunities()):
				string += "and immune to "
				for immunity in pokemon.GetImmunities():
					string += immunity + ","

			with self.printLock:
				print(string)

				## CSV
			##### blablabla string formatting #####
			typeString = ""
			weaknessString = ""
			resistanceString = ""
			immunityString = ""

			i = len(pokemon.GetTypes())
			for pokeType in pokemon.GetTypes():
				i -= 1
				typeString += pokeType['name']
				if i > 0:
					typeString += ","

			i = len(pokemon.GetWeaknesses())
			if i > 0:										
				for weakness in pokemon.GetWeaknesses():
					i -= 1
					weaknessString += weakness
					if i > 0:
						weaknessString += ","
			else:
				weaknessString += "none"

			i = len(pokemon.GetResistances())
			if i > 0:
				for resistance in pokemon.GetResistances():
					i -= 1
					resistanceString += resistance
					if i > 0:
						resistanceString += ","
			else:
				resistanceString += "none"

			i = len(pokemon.GetImmunities())
			if i > 0:
				for immunity in pokemon.GetImmunities():
					i -= 1
					immunityString += immunity
					if i > 0:
						immunityString += ","
			else:
				immunityString += "none"

			## Write to file
			with self.printLock:		
				self.writer.writerow({'DexId': pokemon.GetDexId(), 'Name': pokemon.GetName(), 'Types': typeString, 'Weaknesses': weaknessString,
		  						 'Resistances': resistanceString, 'Immunities': immunityString})
				self.csvfile.flush()

			self.threadedList.task_done()

	def RunThreaded(self):
		""" Runs through registered pokedex numbers from a queue to retrieve information """
		while True:
			dexId = self.threadedDex.get()
			if dexId is None:
				with self.printLock:
					print("Producerthread received stop signal.")
				break

			with self.printLock:
				print("New pokemon #" + str(dexId))

			pokemon = Pokedata()
			pokemon.SetDexId(dexId)

			self.FindType(pokemon)
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
		print("Running...")
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

	def PreCacheType(self, type):
		""" Pre-cache all known types """
		response = requests.get("http://pokeapi.co/api/v2/type/" + str(type))
		json = response.json()
		self.typeCache.append(json)

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
	from collections import Counter
	main()
