import os
import discord
import bank
import helper
import fifty
import loaner
import trinkets

from discord.flags import Intents
from random import randrange, choice, random
from discord.ext import commands
from dotenv import load_dotenv


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

#Enable intents so the member list can be accessed
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents, case_insensitive=True)

botBank = bank.Bank()
botLoaner = loaner.Loaner()
botFifty = fifty.FiftyFifty()
botTrinkets = trinkets.Trinkets()

#Setup variables
flipPayoutRate = 1
rollPayoutRate = 6
suitPayoutRate = 4
xyzPayoutRate = 3

#===============================================
#   ON READY
#===============================================
@bot.event
async def on_ready():
    print(f'---------  {bot.user} has started   ---------')


#===============================================
#   ON_COMMAND_ERROR 
#===============================================
@bot.event
async def on_command_error(ctx, exception):
    #Checks for any errors in the command syntax
    if isinstance(exception, commands.MissingRequiredArgument) or isinstance(exception, commands.UserInputError):
        cmds = ctx.command.aliases
        cmds.append(ctx.command.name)

        await ctx.channel.send('**The proper command usage is:**  ![' + ' | '.join(cmds) + '] ' + ctx.command.help)

    #Checks to make sure the required permissions are had
    if isinstance(exception, commands.CheckFailure):
        await ctx.channel.send('You do not have the required role to execute that command')


#===============================================
#   Validation checks for any type of betting
#===============================================
def validation(userId, amount):
    resultMsg = ''

    #Create new balance if user doesn't exist yet
    botBank.createNewUserStats(userId)

    #Check to make sure the amount is positive
    if amount <= 0:
        resultMsg = 'The amount supplied must be over 0$'

    #Check to make sure the user has enough money
    elif botBank.balances[str(userId)]['balance'] < amount:
        resultMsg = 'You do not have enough money'

    return resultMsg


#===============================================
#   Gets the payout based on if the guess was correct
#===============================================
def getPayoutResult(userId, amount, multiplier, result):
    #Calculate the payout to the user
    if result == True:
        payout = amount * multiplier
    else:
        payout = -amount

    #Add the payout to the users balance
    botBank.updateBalance(userId, payout)

    return payout


#===============================================
#   Returns the users unique ID based on given display name or -1 if not found
#===============================================
async def getIdFromDisplayName(ctx, displayName):
    async for member in ctx.guild.fetch_members(limit=None):
        if displayName.lower() == member.display_name.lower():
            return member.id  
    return -1


#===============================================
#   Returns the user object based on given user id
#===============================================
async def getUserFromId(ctx, userId):
    id = int(userId)

    async for member in ctx.guild.fetch_members(limit=None):
        if id == member.id:
            return member
    return -1


#===============================================
#   Randomly generates a number and checks the win condition
#===============================================
def isWinner(userId, balances, chanceToWin):
    result = random()

    #Get the players additional chance of winning
    bonus = botTrinkets.getBonusFromTrinkets(userId, balances)

    #Check if the user scored above the chance of winning
    if result <= (chanceToWin + bonus):
        return True
    return False


#===============================================
#   Processes the fifty game mode outcome
#===============================================
async def processFiftyFifty(ctx, userId, opponentName, result, amount, isPoster):
    payout = amount * result
    outcome = 'WON'

    #If its a loss - only the challenger loses money
    if result == -1:
        outcome = 'LOST'

        if not isPoster:
            botBank.updateBalance(userId, payout)
    #If its a win - the poster gets double the payout
    else:
        if not isPoster:
            botBank.updateBalance(userId, payout)
        else:
            botBank.updateBalance(userId, payout * 2)

    botBank.updateModeStats(userId, 'fifty', result)

    #Send the results to the poster as they may not be online
    if isPoster:
        userObj = await getUserFromId(ctx, userId)
        await ctx.channel.send(userObj.mention + ' You have **' + outcome + '** against **' + opponentName.capitalize() + '**   (**BET: ' + str(helper.moneyFormat(abs(amount))) + '**)')


#===============================================
#   FLIP
#===============================================
@bot.command(name='flip', aliases=["f"], help='[h | t] [bet amount]', brief='[h | t] [bet amount] - Flips a coin (1/2 chance, 2 * payout)',  ignore_extra=True) 
async def flipCoin(ctx, guess : str, amount : int):
    userId = ctx.author.id
    name = str(ctx.author.display_name)

    choices = ['h','t']

    #Check to make sure the player supplied either a 'h' or a 't'
    if guess not in choices:
        await ctx.channel.send(name + ', you must supply either ''h'' (heads) or ''t'' (tails)')
        return

    #Checks for any errors of the input
    resultMsg = validation(userId, amount)

    if resultMsg != '':
        await ctx.channel.send(resultMsg)
        return

    result = isWinner(userId, botBank.balances, 0.5)

    if result == False:
        choices.remove(guess)

    payout = getPayoutResult(userId, amount, flipPayoutRate, result)

    #Send the user the message of the payout and whether they won
    if payout < 0:
        botBank.updateModeStats(userId, 'flip', -1)
        await ctx.channel.send(':regional_indicator_' + choices[0] + ':  ' + name + ', you **LOST**... **' + str(helper.moneyFormat(abs(payout))) + '** has been removed from your balance')
    else:
        botBank.updateModeStats(userId, 'flip', 1)
        await ctx.channel.send(':regional_indicator_' + guess + ':  ' + name + ', you **WON**! **' + str(helper.moneyFormat(abs(payout))) + '** has been added to your balance')


#===============================================
#   ROLL
#===============================================
@bot.command(name='roll', aliases=["r","ro"], help='[1 - 6] [bet amount]', brief='[1-6] [bet amount] Rolls a dice (1/6 chance, 6 * payout)', ignore_extra=True) 
async def rollDice(ctx, guess : int, amount : int):
    #Check to make sure the player supplied either a valid die side
    if guess < 1 or guess > 6:
        await ctx.channel.send('You must supply a number between 1-6')
        return

    userId = ctx.author.id
    name = str(ctx.author.display_name)

    #Checks for any errors of the input
    resultMsg = validation(userId, amount)

    if resultMsg != '':
        await ctx.channel.send(resultMsg)
        return

    result = result = isWinner(userId, botBank.balances, 0.16666)

    payout = getPayoutResult(userId, amount, rollPayoutRate, result)

    #Send the user the message of the payout and whether they won
    if payout < 0:
        botBank.updateModeStats(userId, 'roll', -1)
        await ctx.channel.send(helper.getRollNumberWord(False, guess) + '  ' + name + ', you guessed ' + str(guess) + ' and **LOST**... **' + str(helper.moneyFormat(abs(payout))) + '** has been removed from your balance')
    else:
        botBank.updateModeStats(userId, 'roll', 1)
        await ctx.channel.send(helper.getRollNumberWord(True, guess) + '  ' + name + ', you guessed ' + str(guess) + ' and **WON**! **' + str(helper.moneyFormat(abs(payout))) + '** has been added to your balance')


#===============================================
#   SUIT
#===============================================
@bot.command(name='suit', aliases=["s"], help='[h|s|d|c] [bet amount]', brief='[h|s|d|c] [bet amount] - Chooses a random suit from a deck of cards (1/4 chance, 4 * payout)',  ignore_extra=True) 
async def chooseSuit(ctx, guess : str, amount : int):
    userId = ctx.author.id
    name = str(ctx.author.display_name)

    choices = ['h','s','d','c']

    #Check to make sure the player supplied either a 'h' or a 't'
    if guess not in choices:
        await ctx.channel.send(name + ', you must supply either ''h'' (hearts), ''s'' (spades), ''d'' (diamonds), or ''c'' (clubs)')
        return

    #Checks for any errors of the input
    resultMsg = validation(userId, amount)

    if resultMsg != '':
        await ctx.channel.send(resultMsg)
        return

    result = isWinner(userId, botBank.balances, 0.25)

    if result == False:
        choices.remove(guess)

    payout = getPayoutResult(userId, amount, suitPayoutRate, result)

    #Send the user the message of the payout and whether they won
    if payout < 0:
        botBank.updateModeStats(userId, 'suit', -1)
        suit = helper.getCardSuit(False, guess)
        await ctx.channel.send(helper.getNumberEmojiFromInt(randrange(1,14)) + ' of ' + suit + '  ' + name + ', you guessed ' + suit + ' and **LOST**... **' + str(helper.moneyFormat(abs(payout))) + '** has been removed from your balance')
    else:
        botBank.updateModeStats(userId, 'suit', 1)
        suit = helper.getCardSuit(True, guess)
        await ctx.channel.send(helper.getNumberEmojiFromInt(randrange(1,14)) + ' of ' + suit + '  ' + name + ', you guessed ' + suit + ' and **WON**! **' + str(helper.moneyFormat(abs(payout))) + '** has been added to your balance')


#===============================================
#   XYZ
#===============================================
@bot.command(name='x', aliases=["y","z"], help='[bet amount]', brief='[bet amount] - Chooses X, Y, or Z (1/3 chance, 3 * payout)',  ignore_extra=True) 
async def chooseXYZ(ctx, amount : int):
    userId = ctx.author.id
    name = str(ctx.author.display_name)

    choices = ['x','y','z']
    guess = ctx.invoked_with[0]

    #Checks for any errors of the input
    resultMsg = validation(userId, amount)

    if resultMsg != '':
        await ctx.channel.send(resultMsg)
        return

    result = isWinner(userId, botBank.balances, 0.33333)

    if result == False:
        choices.remove(guess)

    payout = getPayoutResult(userId, amount, xyzPayoutRate, result)

    #Send the user the message of the payout and whether they won
    if payout < 0:
        botBank.updateModeStats(userId, 'xyz', -1)
        await ctx.channel.send(':regional_indicator_' + choice(choices) + ':  ' + name + ', you **LOST**... **' + str(helper.moneyFormat(abs(payout))) + '** has been removed from your balance')
    else:
        botBank.updateModeStats(userId, 'xyz', 1)
        await ctx.channel.send(':regional_indicator_' + choice(choices) + ':  ' + name + ', you **WON**! **' + str(helper.moneyFormat(abs(payout))) + '** has been added to your balance')


#===============================================
#   50create - Creates a new 50/50 posting
#===============================================
@bot.command(name='50create', aliases=['fc'], help='[bet amount]', brief='[bet amount] - Creates a new 50/50 posting',  ignore_extra=True) 
async def fiftyCreate(ctx, amount : int):
    userId = ctx.author.id
    name = str(ctx.author.display_name)

    #Checks for any errors of the input
    resultMsg = validation(userId, amount)

    if resultMsg != '':
        await ctx.channel.send(resultMsg)
        return

    #Check if there is already a posting for this user
    hasPosting = botFifty.doesUserHavePosting(userId)
    if hasPosting:
        await ctx.channel.send(name + ', you already have a posting. Do "!50remove" to cancel it.')
        return

    #Try to create the posting
    success = botFifty.createPosting(userId, name, amount)
    if success == False:
        await ctx.channel.send(name + ', you already have a posting. Do "!50remove" to cancel it.')
        return

    #Take the money from the user
    botBank.updateBalance(userId, -amount)

    await ctx.channel.send(name + ', you have created a 50/50 posting for ' + str(helper.moneyFormat(amount)))


#===============================================
#   50see - Checks all 50/50 postings available
#===============================================
@bot.command(name='50see', aliases=['fs'], help='Shows all available 50/50 postings',  ignore_extra=True) 
async def fiftySee(ctx):
    await ctx.channel.send(botFifty.displayPostings())


#===============================================
#   50accept - Accepts a 50/50 posting
#===============================================
@bot.command(name='50accept', aliases=['fa'], help='[name]', brief='[name] - Accepts and starts a 50/50 game',  ignore_extra=True) 
async def fiftyCreate(ctx, displayName : str):
    userId = ctx.author.id
    name = str(ctx.author.display_name)

    #Checks to make sure the given name actually has a posting
    postingAmount = botFifty.getPostingAmountIfExists(displayName)
    if postingAmount == -1:
        await ctx.channel.send(name + ', there is no posting by the username you supplied')
        return

    #Checks for any errors of the input
    resultMsg = validation(userId, postingAmount)

    if resultMsg != '':
        await ctx.channel.send(resultMsg)
        return

    #Flip a coin and store the result (0 = poster, 1 = challenger)
    result = choice([0, 1])

    #Get the user id of the poster
    posterId = botFifty.getPostingUserIdIfExists(displayName)
    if posterId == '':
        await ctx.channel.send(name + ', there is no posting by the username you supplied')
        return

    #Remove the posting
    botFifty.removePosting(posterId)

    if result == 0: #Poster won
        await processFiftyFifty(ctx, userId, displayName, -1, postingAmount, False)
        await processFiftyFifty(ctx, posterId, name, 1, postingAmount, True)
    else: #Challenger won
        await processFiftyFifty(ctx, userId, displayName, 1, postingAmount, False)
        await processFiftyFifty(ctx, posterId, name, -1, postingAmount, True)


#===============================================
#   50remove - Cancels your own 50/50 posting
#===============================================
@bot.command(name='50remove', aliases=['fr'], help='Removes your own 50/50 posting',  ignore_extra=True) 
async def fiftyRemove(ctx):
    userId = ctx.author.id
    name = str(ctx.author.display_name)

    #Check if there is already a posting for this user
    hasPosting = botFifty.doesUserHavePosting(userId)
    if hasPosting:
        #Give the money back to the user
        botBank.updateBalance(userId, botFifty.getPostingAmountIfExists(name))

        #Remove the posting
        botFifty.removePosting(userId)

        await ctx.channel.send(name + ', your 50/50 posting has been removed successfully.')
    else:
        await ctx.channel.send(name + ', you do not have a posting to remove')


#===============================================
#   LOAN
#===============================================
@bot.command(name='loan', aliases=["lo"], help=f'The bank will loan you every {loaner.secondsToWait} seconds', ignore_extra=True, case_insensitive=False) 
async def getLoan(ctx):
    return #Disable the command for now

    userId = ctx.author.id
    name = str(ctx.author.display_name)

    #Get the loan amount the bank offers - if no loan is allowed, it will be negative
    loanAmount = botLoaner.askForLoan(userId)

    if loanAmount < 0:
        timeLeft = botLoaner.checkTimeLeft(userId)
        await ctx.channel.send(timeLeft)
    else:
        botBank.updateBalance(userId, loanAmount)
        botBank.updateLoanStat(userId)
        await ctx.channel.send(name + ', you have been loaned: ' + str(helper.moneyFormat(loanAmount)))


#===============================================
#   BALANCE
#===============================================
@bot.command(name='balance', aliases=["bal"], help='(optional: name) Shows the balance of yourself or another', ignore_extra=True) 
async def checkBalance(ctx, name = ''):
    userId = ctx.author.id
    outputText = 'Your balance is: '

    if name != '':
        userId = await getIdFromDisplayName(ctx, name)

        if userId == -1:
            await ctx.channel.send('No one in the discord has a display name that matches what you supplied')
            return

        outputText = 'Their balance is: '

    #Create new balance if user doesn't exist yet
    botBank.createNewUserStats(userId)

    balance = helper.moneyFormat(botBank.balances[str(userId)]['balance'])

    await ctx.channel.send(outputText + str(balance))


#===============================================
#   STATS
#===============================================
@bot.command(name='stats', aliases=["st"], help='(optional: name) Shows the stats of yourself or another', ignore_extra=True) 
async def checkStats(ctx, name = ''):
    userId = ctx.author.id
    displayName = name.capitalize()

    if displayName != '':
        userId = await getIdFromDisplayName(ctx, displayName)

        if userId == -1:
            await ctx.channel.send('No one in the discord has a display name that matches what you supplied')
            return
    else:
        displayName = ctx.author.display_name

    #Get the stats of the player with the specified id
    await ctx.channel.send(botBank.getPlayerStats(userId, displayName))


#===============================================
#   GLOBAL STATS
#===============================================
@bot.command(name='globalStats', aliases=["gs"], help='Shows the stats of everyone in the channel', ignore_extra=True) 
async def checkGlobalStats(ctx):
    
    #Get the stats of everyone in the channel
    await ctx.channel.send(botBank.getGlobalStats())


#===============================================
#   TRINKET NEXT
#===============================================
@bot.command(name='trinketNext', aliases=["tn"], help='Shows the next trinket you can buy', ignore_extra=True) 
async def trinketNext(ctx):
    userId = ctx.author.id
    name = str(ctx.author.display_name)

    #Get the players current level
    level = botTrinkets.getTrinketLevel(userId, botBank.balances)

    #Check to see if they are at the maximum amount of trinkets
    if level == botTrinkets.getMaxTrinketLevel():
        await ctx.channel.send(name + ', you already have the maximum amount of trinkets (' + str(level) + ')')
        return

    if level == -1:
        await ctx.channel.send(name + ', you do not have a trinkets value. Contact an administrator')

    #Get the price of the next level trinket
    price = botTrinkets.getNextTrinketPrice(userId, botBank.balances)

    await ctx.channel.send(name + ', you have ' + str(level) + ' trinkets. The next one costs ' + str(helper.moneyFormat(price)))


#===============================================
#   TRINKET CHECK
#===============================================
@bot.command(name='trinketCheck', aliases=["tc"], help='Shows current bonuses from your trinkets', ignore_extra=True) 
async def trinketCheck(ctx):
    userId = ctx.author.id
    name = str(ctx.author.display_name)

    #Get the bonus based on the current level
    bonus = botTrinkets.getBonusFromTrinkets(userId, botBank.balances)

    await ctx.channel.send(name + ', you have an additional ' + str(100 * bonus) + '% chance to win in games against the House')


#===============================================
#   TRINKET BUY
#===============================================
@bot.command(name='trinketBuy', aliases=["tb"], help='Buys the next available trinket', ignore_extra=True) 
async def trinketBuy(ctx):
    userId = ctx.author.id
    name = str(ctx.author.display_name)

    #Get the new level
    level = botTrinkets.getTrinketLevel(userId, botBank.balances)

    #Check to see if they are at the maximum amount of trinkets
    if level == botTrinkets.getMaxTrinketLevel():
        await ctx.channel.send(name + ', you already have the maximum amount of trinkets (' + str(level) + ')')
        return

    #Get the price of the next trinket
    price = botTrinkets.getNextTrinketPrice(userId, botBank.balances)

    #Checks for any errors of the input
    resultMsg = validation(userId, price)

    if resultMsg != '':
        await ctx.channel.send(resultMsg)
        return

    #Increment the trinket level of the user
    botTrinkets.incrementTrinketAmount(userId, botBank.balances)

    #Get the new level
    level = botTrinkets.getTrinketLevel(userId, botBank.balances)

    #Update the balance of the user
    botBank.updateBalance(userId, -price)

    await ctx.channel.send(name + ', you bought trinket ' + str(level) + ' for ' + str(helper.moneyFormat(price)))


#===============================================
#   TRINKET TOP
#===============================================
@bot.command(name='trinketTop', aliases=["tt"], help='Shows who has the most trinkets', ignore_extra=True) 
async def trinketTop(ctx):
    userId = ctx.author.id

    #Get the latest member list
    members = []
    async for member in ctx.guild.fetch_members(limit=None):
        members.append((member.id,member.display_name))
    
    #Create the leaderboard string
    message = botTrinkets.getTopTrinkets(userId, members, botBank.balances)

    await ctx.channel.send(message)


#===============================================
#   GOONS CLAIM
#===============================================
@bot.command(name='goonsClaim', aliases=["gc"], help='Claims all offline income from your goons', ignore_extra=True) 
async def goonsClaim(ctx):
    

    await ctx.channel.send()


#===============================================
#   GOONS NEXT
#===============================================
@bot.command(name='goonsNext', aliases=["gn"], help='Shows the next goon you can buy', ignore_extra=True) 
async def goonsNext(ctx):
    

    await ctx.channel.send()


#===============================================
#   GOONS BUY
#===============================================
@bot.command(name='goonsBuy', aliases=["gb"], help='Buys the next available goon', ignore_extra=True) 
async def goonsBuy(ctx):
    

    await ctx.channel.send()


#===============================================
#   GOONS INFO
#===============================================
@bot.command(name='goonsInfo', aliases=["gi"], help='Shows all goon info and upgrade costs') 
async def goonsInfo(ctx):
    

    await ctx.channel.send()


#===============================================
#   GOONS UPGRADE
#===============================================
@bot.command(name='goonsUpgrade', aliases=["gu"], help='[goon #]', brief='[goon #] - Upgrades the specified goon', ignore_extra=True) 
async def goonsUpgrade(ctx, goonNumber : int):
    

    await ctx.channel.send()


#===============================================
#   GOONS TOP
#===============================================
@bot.command(name='goonsTop', aliases=["gt"], help='[goon #]', brief='[goon #] - Shows the top levels of a goon', ignore_extra=True) 
async def goonsTop(ctx):
    

    await ctx.channel.send()


#===============================================
#   LEADERBOARD
#===============================================
@bot.command(name='ranking', aliases=["rank","ra"], help='Ranks users based on their balance', ignore_extra=True) 
async def ranking(ctx):
    userId = ctx.author.id

    #Get the latest member list
    members = []
    async for member in ctx.guild.fetch_members(limit=None):
        members.append((member.id,member.display_name))
    
    #Create the leaderboard string
    message = botBank.getTopBalances(userId, members)

    await ctx.channel.send(message)


#===============================================
#
#   ADMIN COMMANDS - When a new one is added, 
#                    add it to the list below
#
#===============================================

#===============================================
#   ADMIN
#===============================================
@bot.command(name='admin', help='Shows admin commands', ignore_extra=True) 
@commands.has_permissions(administrator=True)
async def checkAdmin(ctx):
    adminCommands = ['mod','reset']
    output = '===== ADMIN COMMANDS =====\n'

    for i in adminCommands:
        cmd = bot.get_command(i)
        output += '• ' + cmd.name + ' - ' + cmd.help + '\n'

    await ctx.author.send(output)


#===============================================
#   MOD
#===============================================
@bot.command(name='mod', hidden=True, help='[displayName] [amount] - Modifies a players balance') 
@commands.has_permissions(administrator=True)
async def modifyBalance(ctx, displayName : str, amount : int):
    userId = await getIdFromDisplayName(ctx, displayName)
    
    if userId == -1:
        await ctx.author.send('No one in the discord has a display name that matches what you supplied to the add command')
    else:
        botBank.updateBalance(userId, amount)

    await ctx.channel.send(displayName.capitalize() + ' has been given ' + str(amount) + ' by the bank! How lucky!')


#===============================================
#   RESET STATS
#===============================================
@bot.command(name='reset', hidden=True, help='[displayName] - Resets a players stats') 
@commands.has_permissions(administrator=True)
async def resetPlayerStats(ctx, displayName : str):
    userId = await getIdFromDisplayName(ctx, displayName)
    
    if userId == -1:
        await ctx.author.send('No one in the discord has a display name that matches what you supplied to the add command')
    else:
        botBank.resetPlayerStats(userId)

    await ctx.channel.send(displayName.capitalize() + ' has had their stats reset')


#Start the bot
bot.run(TOKEN)