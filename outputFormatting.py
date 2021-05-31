def GetCSV(pokemon):
    typeString = ""
    weaknessString = ""
    resistanceString = ""
    immunityString = ""
    locationString = ""
    eggString = ""
    speciesString = ""

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

    i = len(pokemon.GetLocations())
    if i > 0:
        for location in pokemon.GetLocations():
            i -= 1
            locationString += location
            if i > 0:
                locationString += ","

    i = len(pokemon.GetEggGroups())
    if i > 0:
        for group in pokemon.GetEggGroups():
            i -= 1
            eggString += group
            if i > 0:
                eggString += ","

    speciesString += pokemon.GetSpecies()

    csv = {
        'DexId': pokemon.GetDexId(),
        'Name': pokemon.GetName(),
        'Types': typeString,
        'Weaknesses': weaknessString,
        'Resistances': resistanceString,
        'Immunities': immunityString,
        'Locations': locationString,
        'Species': speciesString,
        'EggGroups': eggString,
    }

    return csv


def GetConsoleString(pokemon):
    string = "#"
    string += str(pokemon.GetDexId()) + " " + \
        pokemon.GetName() + " is of type(s): "
    for types in pokemon.GetTypes():
        string += types['name'] + ", "

    string += " (species: " + pokemon.GetSpecies() +") "

        # Weaknesses
    string += "and is weak against: "
    for weakness in pokemon.GetWeaknesses():
        string += weakness + ", "

        # Resistances
    string += "but resistant to "
    for resistance in pokemon.GetResistances():
        string += resistance + ", "

    # Immunities
    if len(pokemon.GetImmunities()):
        string += "and immune to "
        for immunity in pokemon.GetImmunities():
            string += immunity + ","

    string += " and can be found: "
    for location in pokemon.GetLocations():
        string += location + ", "

    string += "\n. Egg Groups: ("
    for group in pokemon.GetEggGroups():
        string += group + ", "
    string +=")"

    return string
