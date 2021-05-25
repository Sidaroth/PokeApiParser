# Pokedata class contains:
# - Pokedex ID (National)
# - Pokemon Name
# - Types
# - Weaknesses
# - Immunities
# - Resistances
# - Locations (in which game)

class Pokedata:
    """Model for all pokemon data"""

    def __init__(self):
        """Constructor/Object model"""
        self.name = ""					# pokemon name
        self.dexId = 0					# national dex number
        self.types = []					# typename, url
        self.weaknesses = []			# Weaknesses (typename)
        self.immunities = []			# Immunities (typename)
        self.resistances = []			# Resistances (typename)
        self.locations = []				# encounter locations (i.e pallet-town(yellow, red, blue))

        # Types
    def AddType(self, type):
        self.types.append(type)

    def GetTypes(self):
        return self.types

        # Weaknesses
    def AddWeakness(self, weakness):
        self.weaknesses.append(weakness)

    def GetWeaknesses(self):
        return self.weaknesses

    def RemoveWeakness(self, weakness):
        self.weaknesses.remove(weakness)

        # Resistances
    def AddResistance(self, resistance):
        self.resistances.append(resistance)

    def GetResistances(self):
        return self.resistances

    def RemoveResistance(self, resistance):
        self.resistances.remove(resistance)

        # Immunities
    def AddImmunity(self, immunity):
        self.immunities.append(immunity)

    def GetImmunities(self):
        return self.immunities

        # Encounter Locations

    def AddLocation(self, location):
        self.locations.append(location)

    def GetLocations(self):
        return self.locations

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

    def CheckDuplicates(self):
        """ Check immunities, resistances and weaknesses for duplicates that cancel out """
        self.SortWeaknesses()
        self.SortResistances()
        self.SortImmunities()

        # Check all resistances up against all immunities.
        for resistance in self.resistances:
            for immunity in self.immunities:
                if resistance == immunity:              # Pokemon is immune, remove resistance from list.
                    self.RemoveResistance(resistance)
        for weakness in self.weaknesses:              # Check all weaknesses up against all immunities
            for immunity in self.immunities:
                if weakness == immunity:                # Pokemon is immune, remove weakness from list.
                    self.RemoveWeakness(weakness)
        for weakness in self.weaknesses:                # Check all weakness up against all resistances
            for resistance in self.resistances:
                if weakness == resistance:              # 1/2 x 2x == 1x, they cancel out.
                    self.RemoveWeakness(weakness)
                    self.RemoveResistance(resistance)
