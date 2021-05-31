import sys
import requests


class PokeapiParser:
    """ Retrieves and Parses PokeAPI data """

    def __init__(self):
        self.typeCache = []
        self.pokeApiUrl = "https://pokeapi.co/api/v2/pokemon/"

    def ParsePokemon(self, pokemon):
        json = self.requestInitialPokemonJson(pokemon)
        self.ParseTypeData(pokemon, json)
        self.ParseLocationData(pokemon, json)
        self.ParseBreedingData(pokemon, json)
        self.CalculateTypeEffectiveness(pokemon)

    def PreCacheType(self, type):
        """ Pre-cache A known type """
        response = requests.get("http://pokeapi.co/api/v2/type/" + str(type))
        json = response.json()
        self.typeCache.append(json)

    def requestInitialPokemonJson(self, pokemon):
        """ Request the pokemon JSON data from the poke API """
        try:
            response = requests.get(self.pokeApiUrl + str(pokemon.GetDexId()))
            json = response.json()
            return json
        except requests.exceptions.RequestException as exception:
            print(exception)
            sys.exit(True)

    def ParseTypeData(self, pokemon, json):
        """Find pokemon name and type(s) for the given DexId"""

        # capitalizes the pokemon name
        pokemon.SetName(json['name'].title())
        for pokemonType in json['types']:
            pokemon.AddType(pokemonType['type'])

    def ParseLocationData(self, pokemon, json):
        """  Set locations the pokemon is available for capture/encounter """
        response = requests.get(json['location_area_encounters'])
        locationData = response.json()

        for loc in locationData:
            area = loc['location_area']
            versions = loc['version_details']
            location = area['name'] + ' ('

            for index, version in enumerate(versions):
                location += version['version']['name']
                if index != len(versions) - 1:  # if not last element.
                    location += ', '

            location += ')'
            pokemon.AddLocation(location)

    def ParseBreedingData(self, pokemon, json):
        """ Set breeding egg group and species """

        pokemon.SetSpecies(json['species']['name'])
        response = requests.get(json['species']['url'])
        data = response.json()

        for group in data['egg_groups']:
            pokemon.AddEggGroup(group['name'])

    def CalculateTypeEffectiveness(self, pokemon):
        """ Using the types found for the Pokemon, determine Type Effectiveness(weaknesses, resistances, immunities) """
        for pokemonType in pokemon.GetTypes():
            match = False
            for cachedType in self.typeCache:								# Check for cached types
                if pokemonType['name'] == cachedType['name']:
                    targetType = cachedType
                    match = True
                    break

            assert match == True													# Make sure we have a match

            # Immunity
            for immunity in targetType['damage_relations']['no_damage_from']:
                pokemon.AddImmunity(immunity['name'])

                # Resistance
            for resistance in targetType['damage_relations']['half_damage_from']:
                pokemon.AddResistance(resistance['name'])

                # Weakness
            for weakness in targetType['damage_relations']['double_damage_from']:
                pokemon.AddWeakness(weakness['name'])

        pokemon.CheckDuplicates()

    def ValidateTypeCache(self, NUMBER_OF_TYPES):
        """ Validates/Guarantees that we have cached all types """
        assert len(self.typeCache) == NUMBER_OF_TYPES
