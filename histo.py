"""
***************************************************
*********** THE RULES OF BLACKJACK ****************
***************************************************
1: DEALING:

First, deal one card face down to the dealer. Then, deal one card face-up to the dealer.
Deal each player two cards.
If the dealer's upCard is an Ace:
    Each player has the option to "buy insurance", a bet that pays two to one if the 
        dealer has a blackjack. The size of the insurance bet is at most half the player's
        initial bet.
    Then, the dealer checks the hole card
    If the hole Card is a ten:
        Players who purchased insurance are paid two to one,
        Players with blackjack push, and
        Players without blackjack lose their initial bet
        ************************
        **** ROUND IS OVER. ****
        ************************
    Else:
        Players who bought insurance lose their insurance bet.
        Round continues


2: PLAYER PLAY:


If the player has a blackjack, then their bet is paid 3:2, and the 
************************
**** ROUND IS OVER. ****
************************

The player can choose to surrender their hand. If they surrender, then they lose 
    half their initial bet, but get to keep half as well. This ENDS THE ROUND

The player can choose to split their hand into two distinct hands. If they split, 
    then they will be dealt an additional card to each hand, and they will play the hands in order.
    In this game, split hands may be resplit, and we allow double down after split.

The player can choose to double down on their hand. If they double down, they take one final
    card and double their wager. 

The player can choose to hit. If they hit, they lose the ability to double down and split, 
    and they receive an additional card. Players may hit until they reach a hard 21. 

The player can choose to stand. If they stand, the player stops playing and his hand is frozen.

If the Player busts, they automatically lose their initial bet, and the ROUND IS OVER.

3: DEALER PLAY
The dealer's play is simple: He takes additional cards until the best value is over 17, or until
    the lowest value is greater than 21.
If the dealer busts, the player wins their bet.
If the dealer's value is equal to the player's, then it's a push, and no money is won or lost.
If the dealer's value is better than the player's, then the player loses his wager.
If the dealer's value is worse than the player's, then the player is paid equal to their wager.
Now, let's code that up.
"""

"""
This gives the main structure of play
"""
#TODO: implement autoplay (at the bottom)

# Useful Modules
from functools import reduce
import random
import math
import numpy as np
import matplotlib.pyplot as plt

# Global variables
NUM_DECKS = 6
DECK_SIZE = 52
BANKROLL = 1000
BETTING_UNIT = 1
LOW_CARDS = [2,3,4,5,6]
HIGH_CARDS = ["A", 10]


def histogram(numIters):
    data = []
    for i in range(numIters):
        profit = np.floor(newGame() - 1000)
        data.append(profit)
        print(i)
    upper = max(data)
    lower = min(data)
    plt.hist(data, range = (lower, upper), bins = int((upper - lower)/5), rwidth = 0.9)
    plt.show()

def newGame():
    # Create and shuffle the shoe of cards
    suits = ["A", 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10]
    deck = 4*suits
    shoeList = NUM_DECKS*deck
    random.shuffle(shoeList)
    shoe = Shoe(shoeList, 0)
    # create the player and the dealer 
    p1 = Player("auto")
    dealer = Player(True)
    # begin play
    rounds = 0
    while rounds < 1000:
        if p1.money < 0:
            break
        if shoe.getNumCards() < 26:
            shoeList = NUM_DECKS*deck
            random.shuffle(shoeList)
            shoe = Shoe(shoeList, 0)

        bet = takeBets(p1, shoe)
        dealCards(shoe, p1, dealer, bet)
        upCard = dealer.getHand().getCards()[0]
        roundOver = checkInsurance(p1, dealer, shoe)
        if not roundOver:
            playerPlay(shoe, p1, upCard)
            dealerPlay(shoe, dealer)
        settleDebts(dealer, p1)
        resetHands(dealer, p1)
        rounds += 1
    return p1.money
"""
A pile of cards equipped with a count
"""
class Shoe:
    def __init__(self, cardList, rCount = 0):
        self.cards = cardList
        self.rCount = rCount

    def getNumCards(self):
        return len(self.cards)
    
    def deal(self):
        topCard = self.cards[0]
        self.cards = self.cards[1:]
        if topCard in LOW_CARDS:
            self.rCount += 1
        if topCard in HIGH_CARDS:
            self.rCount -= 1
        return topCard

    def getCount(self):
        return self.rCount
    
    def getTrue(self):
        numDecks = self.getNumCards()/DECK_SIZE
        return self.getCount()/numDecks

class Hand:
    def __init__(self, cardList, bet):
        self.cards = cardList
        self.bet = bet
    
    def addCard(self, newCard):
        self.cards += [newCard]
    
    def changeBetTo(self, newBet):
        self.bet = newBet

    def getBet(self):
        return self.bet

    def getCards(self):
        return self.cards

    def getValue(self, someCards):
        if someCards == []:
            return 0
        #copy needs to be a deepCopy, since we change things
        copy = [element for element in someCards]
        numAces = 0
        while "A" in copy:
            numAces += 1
            copy.remove("A")
        if numAces == 0:
            return copy[0] + self.getValue(copy[1:])
        else:
            hardValue = numAces - 1 + self.getValue(copy)
            highValue = hardValue + 11
            lowValue = hardValue + 1
            if highValue <= 21:
                return highValue
            else:
                return lowValue

"""
we want to be able to make a player split, hit, and double down.
"""  
class Player:
    def __init__(self, playerType, hands = []):
        self.playerType = playerType
        self.playable = hands
        self.frozen = []
        self.money = BANKROLL
        self.bettingUnit = BETTING_UNIT

    """
    removes hand from playing queue
    """
    def deleteHand(self, hand):
        if hand in self.playable:
            self.playable.remove(hand)

    """
    takes hand out of the queue of play and inserts
    hand into evaluation queue.
    """
    def stand(self):
        hand = self.playable[0]
        self.frozen.append(hand)
        self.deleteHand(hand)
    """
    adds a new hand to the front of the playable hands
    """
    def addHandtoFront(self, cardList, bet):
        newHand = Hand(cardList, bet)
        self.playable = [newHand] + self.playable
    """
    clears all hands and bets
    """
    def clearhands(self):
        self.playable = []
        self.frozen = []

    def getHand(self):
        return self.playable[0]

    """
    increments/decrements the money by delta
    """
    def changeMoney(self, delta):
        self.money += delta

    def hit(self, shoe):
        newCard = shoe.deal()
        currentHand = self.getHand()
        currentHand.addCard(newCard)

    def doubleDown(self, shoe):
        newCard = shoe.deal()
        currentHand = self.getHand()
        currentBet = currentHand.getBet()
        currentHand.addCard(newCard)
        currentHand.changeBetTo(2*currentBet)
        self.changeMoney(-currentBet)
        self.stand()

    def split(self, shoe):
        currentHand = self.playable[0]
        currentCards = currentHand.getCards()
        if len(currentCards) == 2:
            if currentCards[0] == currentCards[1]:
                self.deleteHand(currentHand)
                for i in range(0,2):
                    newCards = [currentCards[i], shoe.deal()]
                    bet = currentHand.getBet()
                    self.addHandtoFront(newCards, bet)
    def surrender(self):
        firstHand = self.getHand()
        self.changeMoney(firstHand.getBet()/2)
        self.deleteHand(firstHand)


def takeBets(player, shoe):
    prop = BETTING_UNIT/BANKROLL
    bet = prop*player.money
    # if shoe.getTrue() > 1:
    #     bet *= shoe.getTrue()
    bet = round(bet)
    player.changeMoney(-bet)
    return bet
    

def dealCards(shoe, player, dealer, bet):
    player.addHandtoFront([shoe.deal(), shoe.deal()], bet)
    dealer.addHandtoFront([shoe.deal(), shoe.deal()], 0)

def checkInsurance(player, dealer, shoe):
    upCard = dealer.getHand().getCards()[0]
    holeCard = dealer.getHand().getCards()[1]
    if upCard == "A":
        if player.playerType == "human":
            print("the dealer's upcard is an Ace")
            insurance = 0
            if "y" in input("Would you like to take insurance?"):
                insurance = player.getHand().getBet()/2
                player.changeMoney(-insurance)
            if holeCard == 10:
                player.changeMoney(3*insurance)
                player.stand()
                return True
            else:
                return False
        elif player.playerType == "auto":
            if holeCard == 10:
                player.stand()
                return True
            else:
                return False

def playerPlay(shoe, player, upCard):
    if player.playerType == "human":
        humanPlay(shoe, player,upCard)
    elif player.playerType == "auto":
        autoPlay(shoe, player, upCard)

def humanPlay(shoe, player, upCard):
    print('the dealer\'s upcard is ' + str(upCard))
    print("")
    print("your current hand is:")
    print(player.getHand().getCards())
    print("")
    decision = input("will you surrender? (y/n)")
    if "y" in decision:
        player.surrender()
    elif "m" in decision:
        print(player.money)
    while player.playable != []:
        #First, check if the hand is bust:
        currentHand = player.getHand()
        if currentHand.getValue(currentHand.getCards()) > 21:
            player.stand()
        # Now, we play
        else:
            print('the dealer\'s upcard is ' + str(upCard))
            print("")
            print("your current hand is:")
            print(player.getHand().getCards())
            print("")
            decision = input("will you hit (h), double down (dd), stand (st) or split (sp)?")
            if decision == "h":
                player.hit(shoe)
            elif decision == "dd":
                player.doubleDown(shoe)
            elif decision == "st":
                player.stand()
            elif decision == "sp":
                player.split(shoe)

def dealerPlay(shoe, dealer):
    dHand = dealer.getHand()
    while dHand.getValue(dHand.getCards()) < 17:
        dealer.hit(shoe)

def settleDebts(dealer, player):
    dCards = dealer.getHand().getCards()
    dScore = value(dCards)
    for hand in player.frozen:
        pCards = hand.getCards()
        pScore = value(pCards)
        if pScore == 21.5:
            if dScore != 21.5:
                #Blackjack!
                player.money += 2.5*hand.getBet()
                # print("")
                # print("BLACKJACK - you win $" + str(1.5*hand.getBet()))
            else:
                #return the player's money
                player.money += hand.getBet()
                # print("")
                # print("PUSH - no money won or lost")
        elif value(pCards) == -1:
            # print("")
            # print("BUST - YOU LOSE $" + str(hand.getBet()))
            continue
        elif pScore > dScore:
            player.money += 2* hand.getBet()
            # print("")
            # print("YOU WON $" + str(hand.getBet()))
        elif pScore == dScore:
            player.money += hand.getBet()   
            # print("")
            # print("PUSH - no money won or lost") 
        else:
            # print("")
            # print("Dealer wins - you lose $" + str(hand.getBet()))
            continue

def sumCards(cardList):
    copy = [card for card in cardList]
    numAces = 0
    while "A" in copy:
        numAces += 1
        copy.remove("A")
    partialSum = sum(copy)
    if numAces == 0:
        return partialSum

    partialSum += numAces - 1
    if partialSum < 11:
        return partialSum + 11
    else:
        return partialSum + 1

def value(cardList):
    if cardList == ["A", 10] or cardList == [10, "A"]:
        return 21.5
    naiveSum = sumCards(cardList)
    if naiveSum > 21:
        return -1
    return naiveSum

def resetHands(dealer, player):
    player.clearhands()
    dealer.clearhands()
"""
plays according to Basic Strategy - A mess of conditionals
"""
def autoPlay(shoe, player, upCard):
    pCards = player.getHand().getCards()
    #surrender conditions - for initial Hand ONLY
    if value(pCards) == 16 and isSoft(pCards) == False:
        if upCard in [9,10, "A"]:
            player.surrender()
    if value(pCards) == 15 and isSoft(pCards) == False:
        if upCard == 10:
            player.surrender()


    #Makes decisions until all hands are frozen
    while player.playable != []:
        pCards = player.getHand().getCards()
        # check if busted surtout
        if value(pCards) < 0:
            player.stand()
            continue
        # PAIR SPLITTING
        if len(pCards) == 2 and pCards[0] == pCards[1]:
            card = pCards[0]
            if card == "A":
                player.split(shoe)
                continue
            if card == 10:
                if upCard in [4,5,6]:
                    if upCard + shoe.getCount() >= 10:
                        player.split(shoe)
            if card == 9:
                if upCard in [2,3,4,5,6,8,9]:
                    player.split(shoe)
                    continue
            if card == 8:
                player.split(shoe)
                continue
            if card in [6,7]:
                if value([upCard]) <= card:
                    player.split(shoe)
                    continue
            if card == 4:
                if upCard in [4,5]:
                    player.split(shoe)
                    continue
            if card in [2,3]:
                if value([upCard]) < 8:
                    player.split(shoe)
                    continue
        #SOFT TOTALS
        if isSoft(pCards):
            total = value(pCards)
            if total > 19:
                player.stand()
            elif total == 19:
                if upCard == 6:
                    player.doubleDown(shoe)
                else:
                    player.stand()
            elif total == 18:
                if value([upCard]) > 8:
                    player.hit(shoe)
                elif upCard > 6:
                    player.stand()
                elif len(pCards) > 2:
                    player.stand()
                else:
                    player.doubleDown(shoe)
            elif total == 17:
                if upCard in [3,4,5,6]:
                    player.doubleDown(shoe)
                else:
                    player.hit(shoe)
            elif total in [15,16]:
                if upCard in [4,5,6]:
                    player.doubleDown(shoe)
                else:
                    player.hit(shoe)
            elif total in [13,14]:
                if upCard in [5,6]:
                    player.doubleDown(shoe)
                else:
                    player.hit(shoe)
        #HARD TOTALS
        else:
            total = value(pCards)
            if total > 16:
                player.stand()
            elif total > 12:
                if value([upCard]) > 6:
                    player.hit(shoe)
                else:
                    player.stand()
            elif total == 12:
                if upCard in [4,5,6]:
                    player.stand()
                else:
                    player.hit(shoe)
            elif total == 11:
                player.doubleDown(shoe)
            elif total == 10:
                if value([upCard]) > 9:
                    player.hit(shoe)
                else:
                    player.doubleDown(shoe)
            elif total == 9:
                if upCard in [3,4,5,6]:
                    player.doubleDown(shoe)
                else:
                    player.hit(shoe)
            else:
                player.hit(shoe)

def isSoft(pCards):
    copy = [card for card in pCards]
    if "A" in copy:
        copy.remove("A")
        score = 0
        while "A" in copy:
            score += 1
            copy.remove("A")
        score += sum(copy)
        return score < 11
    return False
        
