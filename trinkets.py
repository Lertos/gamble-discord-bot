import helper


bonusPerLevel = 0.0025
costPerLevel = 200
costMultiplier = 1.3
maxTrinketLevel = 60


class Trinkets:   
    def __init__(self):
        pass


    #Gets the trinket level given a user id
    def getTrinketLevel(self, userId, balances):
        id = str(userId)

        if id not in balances.keys():
            return -1

        return balances[id]['trinkets']


    #Gets the bonus for the number of trinkets the user has
    def getBonusFromTrinkets(self, userId, balances):
        level = self.getTrinketLevel(userId, balances)

        if level == -1:
            return 0
        else:
            return level * bonusPerLevel


    #Gets the price of the next trinket available
    def getNextTrinketPrice(self, userId, balances):
        level = self.getTrinketLevel(userId, balances)
        
        return round(costPerLevel * (costMultiplier ** (level + 1)))


    #Increments the trinket value for the user
    def incrementTrinketAmount(self, userId, balances):
        id = str(userId)

        if id not in balances.keys():
            return

        balances[id]['trinkets'] = balances[id]['trinkets'] + 1


    #Displays the top trinket amounts
    def getTopTrinkets(self, userId, members, balances):
        header = helper.listHeaders('TOP TRINKETS')

        sortedTrinkets = sorted(balances.items(), key=lambda x: x[1]['trinkets'], reverse=True)
        formatted = list(map(lambda x: str(x[1]['trinkets']) + ' - ' + helper.getDisplayName(userId, members, x[0]), sortedTrinkets))

        return header + '\n'.join(formatted)


    #Get the max level so players cannot go over
    def getMaxTrinketLevel(self):
        return maxTrinketLevel


