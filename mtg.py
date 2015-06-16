#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import argparse
import math
import logging


### Functions ###
def getColor(card, ctype):
    logging.info('Getting the Color of the card.')
    # Get the color identity of the card.
    if card[u'colors'] != None:
        numColors = len(card[u'colors'])
        if numColors > 1:
            color = ''
            for i in card[u'colors']:
                if i == "Blue":
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
        color = 'Colorless'
    return color


def getSupertype(card):
    logging.info('Getting the Supertype of the card.')
    if card[u'supertypes'] == None:
        supertype = ''
    else:
        supertype = card[u'supertypes'][0].capitalize()+' '
    return supertype


def getType(card):
    logging.info('Getting the Type of the card.')
    # Get the Type of the card.
    typeArray = [x.capitalize() for x in card[u'types']]
    ctype = ""
    for i in typeArray:
        ctype += i+' '
    return ctype.rstrip()


def getSubtype(card):
    logging.info('Getting the Subtype of the card.')
    if card[u'subtypes'] == None:
        subtype = ''
    else:
        subtypeArray = [x.capitalize() for x in card[u'subtypes']]
        #print subtypeArray
        subtype = ""
        for i in subtypeArray:
            subtype += i+' '
        subtype = ' '+u'—'+' '+subtype.rstrip()
    return subtype


def getCardInfo(card):
    logging.info('Fetching the card data.')
    # For each card in the set, get the Collector Number, Name,
    # ... Rarity, Color and Type.
    # Get the card Type.
    ctype = getType(card)
    # Get the Supertype.
    supertype = getSupertype(card)
    # Get the Subtype.
    subtype = getSubtype(card)
    # Get the Color identity.
    color = getColor(card, ctype)
    # Get the Collector Number.
    num = card[u'number']
    # Get the Rarity.
    rar = card['rarity'][0].upper()
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


def createData(setID, cardCount, updateType):
    # mtgapi.com is the main data source, providing set AND price information.
    # This API limits returns to 20 items per page. Use the cardCount (set size)
    # ... to determine the number of pages needed to fully display the set.
    # ... Page starts at 1.
    numPages = int(math.ceil(float(cardCount) / 20))
    print numPages
    # Now, update the Cards, Prices or Both, depending on user selection.
    cardList = list()
    for i in range(1, numPages+1):
        url = "http://api.mtgapi.com/v2/cards?set=" + setID + "&page=" + str(i)
        req = requests.get(url)
        logging.info('Getting data from page '+str(i))
        data = req.json()
        for i in range(0, len(data["cards"])):
            card = data["cards"][i]
            # Get the name of the card.
            name = card['name']
            logging.info('CARD NAME: '+name)
            #print name
            if updateType == 'CARDS':
                logging.info('Starting the update of the '+updateType+'.')
                num, rar, color, supertype, ctype, subtype = getCardInfo(card)
                cardList.append(num+'|'+name+'|'+rar+'|'+color+'|'
                                +supertype+ctype+subtype)
                logging.info('Finished updating the '+updateType+'.')
            elif updateType == 'PRICES':
                logging.info('Starting the update of the '+updateType+'.')
                price = getPrice(setID, card)
                cardList.append(name+'|$%s' %price)
                logging.info('Finished updating the '+updateType+'.')
            elif updateType == 'BOTH':
                logging.info('Starting the FULL update.')
                num, rar, color, supertype, ctype, subtype = getCardInfo(card)
                price = getPrice(setID, card)
                cardList.append(num+'|'+name+'|'+rar+'|'+color+'|'
                                +supertype+ctype+subtype+'|$%s' %price)
                logging.info('Finished the FULL update.')
            else:
                logging.warning('ERROR: Something very bad has happened.')
                return "ERROR: Something very bad has happened."
    logging.info('Returning the dataset.')
    f = open(setID+'_cardlist.csv', 'w')
    for x in cardList:
        f.write(x.encode('UTF8'))
        f.write('\n')
    f.close()
    return [x.encode('UTF8') for x in cardList]


def getCardCount(setID):
    # mtgapi.com provides the set size information.
    mtgapiURL = "http://api.mtgapi.com/v2/sets?code=" + setID
    cardCount = requests.get(mtgapiURL).json()[u'sets'][0][u'cardCount']
    return cardCount


def parseStuff():
    parser = argparse.ArgumentParser(
        description='Create or update MTG card inventories.')
    parser.add_argument(
        '-s', '--set', metavar='SET', dest='setID', required=True,
        help='''REQUIRED: Which MtG SET do you want to update?
        Please provide the unique, three-digit identifier.''')
    parser.add_argument(
        '-u', '--update', metavar='UPDATE', dest='updateType',
        choices=['cards', 'prices', 'both'], default='prices',
        help='Do you want to update the CARDS, PRICES or BOTH?')
    args = parser.parse_args()
    return args


### Main ###
def main():
    # Set logging level.
    logging.basicConfig(
        filename='mtg.log',
        level=logging.INFO, format='%(levelname)s:%(message)s')
    logging.info('Initialzing parameters...')
    # User provides the set to act upon.  Must be in three-digit code format.
    # ... User declares update type, choosing just the cards, just the prices,
    # ... or both.
    args = parseStuff()
    setID = args.setID.upper()
    updateType = args.updateType.upper()
    # Get set size.
    cardCount = getCardCount(setID)

    # Create data.
    logging.info('Creating dataset for '+setID+'. There are '
                 +str(cardCount)+' cards in the set.')
    logging.info('Updating '+updateType+'.')
    createData(setID, cardCount, updateType)

    logging.info('Complete.')

if __name__ == '__main__':
    main()
