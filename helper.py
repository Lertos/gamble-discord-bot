import math
import time
from random import choice

#Returns the amount back with proper formatting (such as commas)
def moneyFormat(money):
    return f'${int(money):,}'


#Returns a formatted header for any list, given the main text
def listHeaders(text):
    return ':arrow_right:  **' + str(text) + '**  :arrow_left:\n\n'


#Used to show dice rolls as discord emojis given an integer dice result
def getRollNumberWord(isWinner, guess):
    sides = [1,2,3,4,5,6]

    if isWinner == False:
        sides.remove(int(guess))
        roll = choice(sides)
    else:
        roll = guess

    return getNumberEmojiFromInt(roll)


#Used to get a random card suit
def getCardSuit(isWinner, guess):
    suits = ['h','s','d','c']

    if isWinner == False:
        suits.remove(guess)
        suit = choice(suits)
    else:
        suit = guess

    if suit == 'h':
        return ':hearts:'
    elif suit == 's':
        return ':spades:'
    elif suit == 'd':
        return ':diamonds:'
    elif suit == 'c':
        return ':clubs:'


#Used to get a random card suit
def getNumberEmojiFromInt(number):
    if number == 1:
        return ':one:'
    elif number == 2:
        return ':two:'
    elif number == 3:
        return ':three:'
    elif number == 4:
        return ':four:'
    elif number == 5:
        return ':five:'
    elif number == 6:
        return ':six:'
    elif number == 7:
        return ':seven:'
    elif number == 8:
        return ':eight:'
    elif number == 9:
        return ':nine:'
    elif number == 10:
        return ':one::zero:'
    elif number == 11:
        return ':regional_indicator_j:'
    elif number == 12:
        return ':regional_indicator_q:'
    elif number == 13:
        return ':regional_indicator_k:'
    elif number == 14:
        return ':regional_indicator_a:'


#Find the users id in the members list and returns the display name 
def getDisplayName(userId, members, id):
    for x,y in members:
        if str(x) == str(id):
            if str(userId) == str(id):
                return '**' + str(y) + '**'
            else:
                return y


#Returns the time in hours, minutes, seconds until a cooldown is done
def checkTimeLeft(userId, dictToCheck, cooldownMsg):
    id = str(userId)

    #Check if the user is in the list
    if id not in dictToCheck:
        return cooldownMsg

    #Get the total time in seconds and parse it
    cooldownDone = dictToCheck[id]
    totalTime = cooldownDone - round(time.time())
    
    return 'You can loan in ' + formatTime(totalTime)


#Given time in seconds, returns the formatted time in hours/minutes/seconds
def formatTime(timeInSeconds):
    hours = math.floor(timeInSeconds / 3600)
    totalTime = timeInSeconds - (hours * 3600)

    minutes = math.floor(totalTime / 60)
    totalTime = totalTime - (minutes * 60)

    return f'{hours} hour(s), {minutes} minute(s), {totalTime} second(s)'