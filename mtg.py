#!/usr/bin/env python
import requests
import argparse
import math
import re
import logging

### Functions ###
def getColor(card, ctype):
    logging.info('Getting the Color of the card.')
    # Get the color identity of the card.
    if u'colors' in card:
        numColors = len(card[u'colors'])
        if numColors > 1:
            color = ''
            for i in card[u'colors']:
                if i == "blue":
                    i = "U"
                color += i[0].capitalize()+'/'
            color = color[:-1]
        else:
            color = card[u'colors'][0].capitalize()
    # Special Case: Artifacts are colorless, their "color" is Artifact.
    elif u'Artifact' in ctype:
        color = 'Artifact'
    # Special Case: Lands are colorless, their "color" is Land.
    elif ctype == 'Land':
        color = ctype
    # Special Case: Some cards are simply colorless, i.e. Eldrazi and Ugin.
    else:
        color = ''
    return color

def getSupertype(card):
    logging.info('Getting the Supertype of the card.')
    if u'supertypes' in card:
        supertype = card[u'supertypes'][0].capitalize()+' '
    else:
        supertype = ''
    return supertype

def getType(card):
    logging.info('Getting the Type of the card.')
    # Get the Type of the card.  This is only really needed for
    # Artifact Creatures and Enchantment Creatures.
    typeArray = [x.capitalize() for x in card[u'types']]
    arrayLen = len(typeArray)
    # The Type array is alphabetized (why?!) at source.
    # Parse array into proper order.
    if arrayLen > 1:
        ctype = orderTypeArray(typeArray)
    else:
        ctype = card[u'types'][0].capitalize()
    #print ctype
    return ctype

def orderTypeArray(array):
    logging.info('Setting the proper Type order.')
    art = enc = cre = 'TEMP'
    for i in array:
        if i == 'Artifact':
            art = i
        elif i == 'Enchantment':
            enc = i
        elif i == 'Creature':
            cre = i
        else:
            print "ERROR: Cannot determine card type."
    orderedArray = [enc, art, cre]
    orderedArray.remove('TEMP') # Filter out any empty elements.
    return orderedArray[0]+' '+orderedArray[1]

def getSubtype(card):
    logging.info('Getting the Subtype of the card.')
    subtypeArray = [x.capitalize() for x in card[u'subtypes']]
    #print subtypeArray
    arrayLen = len(subtypeArray)
    # Subtype array is alphabetized (why?!) at source.
    # Parse array into proper order.
    if arrayLen > 1:
        subtype = orderSubtypeArray(subtypeArray)
    else:
        subtype = " - %s" %subtypeArray[0]
    #print subtype
    return subtype

def orderSubtypeArray(array):
    logging.info('Setting the proper Subtype order.')
    highRaceArray = ['Plant', 'Zombie']
    raceArray = ['Angel', 'Ape', 'Bat', 'Bird', 'Crocodile', 'Demon', 'Efreet', \
            'Elemental', 'Elk', 'Elephant', 'Elemental', 'Goblin', \
            'Hound', 'Human', 'Hydra', 'Insect', \
            'Orc', 'Shapeshifter', 'Spirit', 'Treefolk', 'Wall', \
            ]
    classArray = ['Advisor', 'Alchemist', 'Ally', 'Archer', 'Artificer', 'Assassin', \
            'Barbarian', 'Berserker', 'Bodyguard', 'Cleric', 'Coward', 'Druid', \
            'Flagbearer', 'Guardian', 'Hero', 'Knight', 'Lord', 'Mercenary', \
            'Minion', 'Monk', 'Mystic', 'Ninja', 'Nomad', 'Pirate', 'Rebel', \
            'Rigger', 'Rogue', 'Samurai', 'Scout', 'Shaman', 'Soldier', \
            'Spellshaper', 'Townsfolk', 'Warrior', 'Wizard']
    flag = False
    for i in array:
        if i in highRaceArray:
            prime = i
        elif i in raceArray:
            crace = i
        elif i in classArray:
            cclass = i
        else:
            flag = True
    if flag:
        orderedArray = array
    else:
        if ('prime' in locals()) and ('crace' in locals()):
            first = prime
            second = crace
        elif ('prime' in locals()) and ('cclass' in locals()):
            first = prime
            second = cclass
        else:
            first = crace
            second = cclass
        orderedArray = [first, second]
    #print orderedArray
    return " - %s" %orderedArray[0]+' %s' %orderedArray[1]

def getCardInfo(setID, card):
    logging.info('Fetching the card data.')
    # For each card in the set, get the Collector Number, Name,
    # ... Rarity, Color and Type.
    # Get the card Type.
    ctype = getType(card)
    # Get the Supertype of the card.
    supertype = getSupertype(card)
    # Get the Subtype of the card.
    if u'subtypes' in card:
        subtype = getSubtype(card)
    else:
        subtype = ''
    # Get the Color identity of the card.
    color = getColor(card, ctype)
    # Get the Collector Number and Rarity.
    for x in card[u'editions']:
        if x['set_id'] == setID:
            num = x['number']
            rar = x['rarity'][0].upper()
            return num, rar, color, supertype, ctype, subtype

def getPrice(setID, card):
    logging.info('Fetching the card price.')
    # This function provides price information, returning the
    # ... current median price.
    # It is a separate function so it can be called independently.
    price = "Error"
    if card[u'name'] in ['Plains', 'Island', 'Swamp', 'Mountain', 'Forest']:
        price = '0.10'
    else:
        for x in card[u'editions']:
            if x[u'set_id'] == setID.upper():
                med = float(x['price'].get('median')) / 100
                price = '{:0,.2f}'.format(med)
    #print card[u'name']+' '+price
    return price

def getCard(name):
    logging.info('Getting the individual card data.')
    # Get the card object from the name of the card.
    name = name.replace(' ', '-')
    name = name.replace("'", '')
    name = re.sub('[!@#$%^&*()[\]{};:,./<>?\\|`\'\"~=_+]', "", name.lower())
    url = "https://api.deckbrew.com/mtg/cards/"+name
    req = requests.get(url)
    card = req.json()
    return card

def createData(setID, cardCount, updateType):
    # deckbrew.com is the main data source, providing set AND price information.
    # This API limits returns to 100 items per page.  Use the cardCount (set size)
    # ... to determine the number of pages needed to fully display the set.
    # ... Page starts at 0.
    numPages = int(math.ceil(float(cardCount) / 100))
    # Now, update the Cards, Prices or Both, depending on user selection.
    cardList = list()
    for i in range(0, numPages):
        url = "https://api.deckbrew.com/mtg/cards?set=" + setID + "&page=" + str(i)
        req = requests.get(url)
        logging.info('Getting data from page %s' %i)
        data = req.json()
        for i in range(0, len(data)):
            card = data[i]
            # Get the name of the card.
            name = card['name']
            logging.info('CARD NAME: '+name)
            #print name
            if updateType == 'CARDS':
                logging.info('Starting the update of the '+updateType+'.')
                num, rar, color, supertype, ctype, subtype = getCardInfo(setID, card)
                cardList.append( num+'|'+name+'|'+rar+'|'+color+'|'+supertype+ctype+subtype )
                logging.info('Finished updating the '+updateType+'.')
            elif updateType == 'PRICES':
                logging.info('Starting the update of the '+updateType+'.')
                price = getPrice(setID, card)
                cardList.append( name+'|$%s' %price )
                logging.info('Finished updating the '+updateType+'.')
            elif updateType == 'BOTH':
                logging.info('Starting the FULL update.')
                num, rar, color, supertype, ctype, subtype = getCardInfo(setID, card)
                price = getPrice(setID, card)
                cardList.append( num+'|'+name+'|'+rar+'|'+color+'|'+supertype+ctype+subtype+'|$%s' %price )
                logging.info('Finished the FULL update.')
            else:
                logging.warning('ERROR: Something very bad has happened.')
                return "ERROR: Something very bad has happened."
    logging.info('Returning the dataset.')
    return [x.encode('UTF8') for x in cardList]


def getCardCount(setID):
    # mtgapi.com provides the set size information.
    mtgapiURL = "http://api.mtgapi.com/v2/sets?code=" + setID
    cardCount = requests.get(mtgapiURL).json()[u'sets'][0][u'cardCount']
    return cardCount

def parseStuff():
    parser = argparse.ArgumentParser(description='Create or update MTG card inventories.')
    parser.add_argument('-s', '--set', metavar='SET', dest='setID', required=True,
                        help='''REQUIRED: Which MtG SET do you want to update?
                          Please provide the unique, three-digit identifier.''')
    parser.add_argument('-u', '--update', metavar='UPDATE', dest='updateType',
                        choices=['cards', 'prices', 'both'], default='prices',
                        help='Do you want to update the CARDS, PRICES or BOTH?')
    args = parser.parse_args()
    return args

### Main ###
def main():
    # Set logging level.
    logging.basicConfig(filename='mtg.log', level=logging.INFO, format='%(levelname)s:%(message)s')
    logging.info('Initialzing parameters...')
    # User provides the set to act upon.  Must be in three-digit code format.
    # ... User declares update type, choosing just the cards, just the prices,
    # ... or both.
    args = parseStuff()
    setID = args.setID.upper()
    updateType = args.updateType.upper()
    logging.info('Updating '+updateType)
    # Get set size.
    cardCount = getCardCount(setID)

    # Create data.
    logging.info('Creating dataset.')
    createData(setID, cardCount, updateType)

    logging.info('Complete.')

if __name__ == '__main__':
    main()
