"""
Definitions:
Bucket - a situation defined by the following information:
    (a) Dealer's upCard
    (b) Player's Hand (defined by the attributes value, isSoft, canHit, canDouble, canSplit
    (c) current True Count

Introduction:
Without going into the derivation, there are 9146 possible buckets, and 6960 situations that we need to choose a move in.
The moves we can choose are a subset of {stand, hit, double Down, split, surrender}

In order to say with any confidence what the best playing decision is for any given bucket, we need to generate lots of 
examples. The good news is that we can kind of ignore the ones we miss, since they don't come up very often.

(1) generate examples to populate the buckets
(2) classify examples with a function

Finally, it would be best if we could save our computational work
so we don't repeat it. 

(3) Write out buckets to a txt file?
"""
#TODO: write the function currentValue so it assigns a value of 21.5 to a natural
import numpy as np
import random
import matplotlib.pyplot as plt

SUITS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
DECK = 4*["A", 2, 3,4,5,6,7,8,9,10,10,10,10]
DECKS_PER_SHOE = 6
# In any given round, the dealer hits to at most 26 and the player hits to at most 31
MAX_ROUND_VALUE = 57
MIN_COUNT = -3
MAX_COUNT = 8


class Hand:
    def __init__(self, handList, wager = 0,  mustStand = False):
        self.bet = wager
        self.cardList = handList
        self.value = currentValue(handList)
        self.isBJ = self.value == 21.5
        self.canHit = not(mustStand) and self.value > 0 and not(self.isBJ)
        self.canDouble = (self.canHit and len(handList) == 2)
        self.canSplit = self.canDouble and (handList[0] == handList[1])
        self.isSoft = isSoft(handList) and self.canHit

    def __repr__(self):
        string = "a"
        if self.canSplit:
            string += " Splittable"
        elif self.canDouble:
            string += " Doubleable"
        elif self.canHit:
            string += " Hittable"
        if self.isSoft:
            string += " Soft"
        else:
            string+= " Hard"
        if self.value == -1:
            string += " Bust"
        elif self.value == 21.5:
            string += " Blackjack"
        else:
            string += " " + str(self.value)
        return string

    def deepCopy(self):
        mustStand = not(self.canHit)
        return Hand([card for card in self.cardList], self.bet, mustStand)

    def __eq__(self, other):
        #the following conditions must hold:
        c1 = self.value == other.value
        c2 = self.canHit == other.canHit
        # NOTE: canDouble and canSplit are to be ignored right now.
        c3 = self.canDouble == other.canDouble
        c4 = self.canSplit == other.canSplit
        c5 = self.isSoft == other.isSoft
        return c1 and c2 and c5 
    
    def __lt__(self, other):
        return self.value < other.value
    
    def stand(self):
        self.canHit = False
        self.canDouble = False
        self.canSplit = False
        self.isSoft = False

    def hit(self, newCard):
        if self.canHit:
            self.cardList.append(newCard)
            self.value = currentValue(self.cardList)
            if self.value == -1:
                self.canHit = False
            self.isSoft = isSoft(self.cardList)
            self.canDouble = False
            self.canSplit = False
        else:
            print("not allowed to hit this hand")

    def double(self, newCard):
        if self.canDouble:
            self.bet = 2*self.bet
            self.hit(newCard)
            self.canHit = False
            self.canDouble = False
            self.canSplit = False
        else:
            print("not allowed to double down on this hand")
    
    def split(self, newCards):
        if self.canSplit:
            if self.cardList == ["A", "A"]:
                self.cardList = ["A", newCards[0]]
                self.canHit = False
        else:
            print("not allowed to split this hand")
    
class Block:
    def __init__(self, hand, upCard, dCard, extraCards, runningCount, numCardsDealt):
        self.hand = hand
        self.upCard = upCard
        self.dCard = dCard
        self.extraCards = extraCards
        self.rc = runningCount
        self.numCardsDealt = numCardsDealt
        self.stChild = None
        self.hChild = None
        self.key = self.getKey()

    def __repr__(self):
        string = "Dealer's upCard: "+ str(self.upCard) + "\n"
        string += "Your Hand: " + str(self.hand) + "\n"
        string += "True Count: "+ str(self.getTC()) + "\n "
        return string
    
    def getKey(self):
        #return (self.hand.value, self.hand.isSoft, self.hand.canHit, hardValue([self.upCard]))
        #return (self.hand.value, self.hand.isSoft, self.hand.canHit, hardValue([self.upCard]), self.getTC())
        if self.hand.value == -1:
            return (-1, False, False, False, False, None, None) # this makes 120 keys into one.
        elif self.hand.value == 21.5:
            if self.upCard == "A":
                return (21.5, False, False, False, False, 1, self.getTC())
            elif self.upCard == 10:
                return (21.5, False, False, False, False, 10, self.getTC())
            else:
                return (21.5, False, False, False, False, None, None)
        else:
            return (self.hand.value, self.hand.canSplit, self.hand.isSoft, self.hand.canDouble, self.hand.canHit, hardValue([self.upCard]), self.getTC())

    def getTC(self):
        cardsPerShoe = 52*DECKS_PER_SHOE
        numDecksLeft = (cardsPerShoe - self.numCardsDealt)/52
        TrueCount = int(self.rc//numDecksLeft)
        if TrueCount > MAX_COUNT:
            TrueCount = MAX_COUNT
        elif TrueCount < MIN_COUNT:
            TrueCount = MIN_COUNT
        return TrueCount

    def deepCopy(self):
        newHand = self.hand.deepCopy()
        newCards = [card for card in self.extraCards]
        newBlock = Block(newHand, self.upCard, self.dCard, newCards, self.rc, self.numCardsDealt)
        return newBlock
    
    def stand(self):
        self.hand.stand()
        self.key = self.getKey()

    def hit(self):
        if self.hand.canHit:
            newCard = self.extraCards[0]
            self.hand.hit(newCard)
            self.extraCards = self.extraCards[1:]
            self.rc += countValue(newCard)
            self.numCardsDealt += 1
            self.key = self.getKey()
           
class Bucket: 
    def __init__(self, block):
        self.hand = block.hand
        self.upCard = block.upCard
        self.count = block.getTC()
        self.blocks = [block]
        self.key = block.key
        self.expectation = None
        self.bestChoice = None
    
    def __eq__(self, other):
        #these are the conditions:
        c1 = self.hand == other.hand
        c2 = self.upCard == other.upCard
        c3 = self.count == other.count
        return c1 and c2 and c3
    
    def __repr__(self):
        return str(self.blocks[0])

    def append(self, newBlock):
        self.blocks.append(newBlock)

    def size(self):
        return len(self.blocks)

def isSoft(handList):
    copy = [element for element in handList]
    if "A" in copy:
        copy.remove("A")
        num_extra_Aces = 0
        while "A" in copy:
            num_extra_Aces += 1
            copy.remove("A")
        softValue = 11 + num_extra_Aces + sum(copy)
        return softValue <= 21
    else:
        return False

def currentValue(hand):
    if hand in [["A", 10], [10, "A"]]:
        return 21.5
    if isSoft(hand):
        return 10 + hardValue(hand)
    if hardValue(hand) > 21:
        return -1
    else:
        return hardValue(hand)

def hardValue(hand):
    copy = [element for element in hand]
    numAces = 0
    while "A" in copy:
        numAces += 1
        copy.remove("A")
    return numAces + sum(copy)

def makeBuckets(numShoes):
    buckets = {}
    for i in range(numShoes):
        hitQueue = []
        shoe = DECKS_PER_SHOE*DECK
        random.shuffle(shoe)
        shoeTotal = DECKS_PER_SHOE*hardValue(DECK)
        runningCount = 0
        cardsDealt = 0
        while shoeTotal >= MAX_ROUND_VALUE:
            cardList = carveBlock(shoe)
            shoe = shoe[len(cardList):]
            shoeTotal -= hardValue(cardList)

            tempRC = runningCount
            tempCD = cardsDealt
            runningCount += sum([countValue(card) for card in cardList])
            cardsDealt += len(cardList)
            playerHand = Hand(cardList[0:2])
            upCard = cardList[2]
            dCard = cardList[3]
            remaining = cardList[4:]
            tempRC += sum([countValue(card) for card in cardList[0:3]])
            tempCD += 3
            newBlock = Block(playerHand, upCard, dCard, remaining, tempRC, tempCD)
            hitQueue.append(newBlock)
            addBlocktoBuckets(newBlock, buckets)
        while len(hitQueue) > 0:
            parent = hitQueue[0]
            hitQueue = hitQueue[1:]
            if parent.hand.canHit:
                stChild = parent.deepCopy()
                stChild.stand()
                addBlocktoBuckets(stChild, buckets)
                parent.stChild = stChild

                hChild = parent.deepCopy()
                hChild.hit()
                addBlocktoBuckets(hChild, buckets)
                parent.hChild = hChild
                if hChild.hand.canHit:
                    hitQueue.append(hChild)
    return buckets

def addBlocktoBuckets(newBlock, buckets):
    if newBlock.key in buckets:
        buckets[newBlock.key].append(newBlock)
    else:
        buckets[newBlock.key] = Bucket(newBlock)

def carveBlock(shoe):
    finalIndex = 0
    while hardValue(shoe[:finalIndex]) < MAX_ROUND_VALUE:
        finalIndex += 1
    return shoe[:finalIndex]

""" 
Assigns cards values according to the Hi-Lo system.
"""
def countValue(card):
    if card in ["A", 10]:
        return -1
    elif card in [7, 8, 9]:
        return 0
    else: # card in [2,3,4,5,6]
        return 1

"""
Divide classifies the buckets into 4 categories: stand, soft, high hard, and low hard.
"""
def divide(buckets):

    stBuckets = {}
    hardBucketsHigh = {}
    softBuckets = {}
    hardBucketsLow = {}
    doubleBuckets = {}
    splitBuckets = {}

    for key in buckets:
        h = buckets[key].hand

        if h.canSplit:
            splitBuckets[key] = buckets[key]
        elif h.canDouble:
            doubleBuckets[key] = buckets[key]   
        elif h.canHit:
            if h.isSoft:
                softBuckets[key] = buckets[key]
            elif h.value > 10:
                hardBucketsHigh[key] = buckets[key]
            else:
                hardBucketsLow[key] = buckets[key]
        else:
            stBuckets[key] = buckets[key]
    return (stBuckets, hardBucketsHigh, softBuckets, hardBucketsLow, doubleBuckets, splitBuckets)

"""
dealerPlay defaults to a S17 game (i.e., dealer stands on Soft 17)
"""
def dealerPlay(initialCards, hitList):
    dealerCards = [card for card in initialCards]
    i = 0
    while currentValue(dealerCards) in range(0,17):
        dealerCards += [hitList[i]]
        i += 1
    return currentValue(dealerCards)

"""
attaches a simplified estimate of expectation to each situation
assuming two choices: hit or stand.
"""
def makeExpectations(buckets):
    stand, high, soft, low, double, split = divide(buckets)
    standExpectations(stand)
    highExpectations(high, stand)
    softExpectations(soft, high, stand)
    lowExpectations(low, soft, high, stand)
    doubleExpectations(double, low, soft, high, stand)
    splitExpectations(split, double, low, soft, high, stand)


"""
Evaluates expected profit of inert hands 
based on the likelihood of winning, losing and pushing
with the dealer
"""        
def standExpectations(stand):
    for key in stand:
        b = stand[key]

        payoff = 1
        if b.key[0] == 21.5:
            payoff = 1.5

        if b.key[0] == -1:
            b.expectation = -1

        else:
            numWon = 0
            numLost = 0
            for block in b.blocks:
                dealerHand = [block.upCard, block.dCard]
                remaining = block.extraCards
                dTotal = dealerPlay(dealerHand, remaining)
                pTotal = block.hand.value

                if pTotal > dTotal: numWon += 1
                elif pTotal < dTotal: numLost += 1

            numBlocks = len(b.blocks)
            b.expectation = (payoff*numWon - numLost)/numBlocks

"""
Evaluates expected profit for high hard hands
based on the likelihood of winning if we stand or hit
"""
#TODO: incorportate double and splitting procedures to setExpectation
def setExpectation(split, double, low, soft, high, stand, value, canSplit, isSoft, canDouble, myHome, upCard, count):
    
    currentKey = (value, canSplit, isSoft, canDouble, True, hardValue([upCard]), count)
    if currentKey not in myHome:
        # print("ignoring:")
        # print(currentKey)
        return
    currentBucket = myHome[currentKey]

    standKey = currentBucket.blocks[0].stChild.key
    stExp = stand[standKey].expectation

    hChildKeyFreqs = {}

    for block in currentBucket.blocks:
        occurrence = block.hChild.key
        if occurrence in hChildKeyFreqs:
            hChildKeyFreqs[occurrence] += 1
        else:
            hChildKeyFreqs[occurrence] = 1

    def contribution(key, frequencies):
        location = None
        if key in stand: location = stand
        elif key in high: location = high
        elif key in soft: location = soft
        elif key in low: location = low
        elif key in double: location = double
        elif key in split: location = split
        return frequencies[key]*location[key].expectation

    hitExp = sum([contribution(key,hChildKeyFreqs) for key in hChildKeyFreqs])/len(currentBucket.blocks)

    doubleExp = -2
    splitExp = -2
    # the processes for splitting and doubling are a little complicated:
    if canDouble:
        dChildKeyFreqs = {}
        for block in currentBucket.blocks:
            if block.hChild.stChild:
                occurrence = block.hChild.stChild.key
            else:
                occurrence = block.hChild.key
            if occurrence in dChildKeyFreqs:
                dChildKeyFreqs[occurrence] += 1
            else:
                dChildKeyFreqs[occurrence] = 1
        doubleExp = 2*sum([contribution(key,dChildKeyFreqs) for key in dChildKeyFreqs])/len(currentBucket.blocks)

    if canSplit:
        legacyCard = currentBucket.hand.value // 2
        if isSoft:
            legacyCard = "A"

        splChildFreqs = {}
        numKeys = 0
        for block in currentBucket.blocks:
            # Note: we are guaranteed at least two extraCards, for a splittable hand
            nextCards = [block.extraCards[0], block.extraCards[1]]
            hand1 = Hand([legacyCard,nextCards[0]])
            hand2 =  Hand([legacyCard, nextCards[1]])
            countShift = countValue(nextCards[0]) + countValue(nextCards[1])
            key1 = Block(hand1, block.upCard, block.dCard, None, block.rc + countShift, block.numCardsDealt + 2).key
            key2 = Block(hand2, block.upCard, block.dCard, None, block.rc + countShift, block.numCardsDealt + 2).key
            for key in (key1, key2):
                if key == currentKey: # if we split into the same hand, we should ignore the child.
                    continue
                if key not in double: # only occurs if our coverage is not total
                    # print("don't have data on:")
                    # print(key)
                    continue

                if legacyCard == "A": # typically, must stand after splitting aces
                    key = double[key].blocks[0].stChild.key
                if key in splChildFreqs:
                    splChildFreqs[key] += 1
                else:
                    splChildFreqs[key] = 1
                numKeys += 1
        if numKeys == 0:
            splitExp = -10
        else:
            splitExp = 2*sum([contribution(key, splChildFreqs) for key in splChildFreqs])/numKeys

    currentBucket.expectation = max(splitExp, doubleExp, hitExp, stExp)

    if currentBucket.expectation == hitExp:
        currentBucket.bestChoice = "hit"
    elif currentBucket.expectation == stExp:
        currentBucket.bestChoice = "stand"
    elif currentBucket.expectation == doubleExp:
        currentBucket.bestChoice = "double"
    else:
        currentBucket.bestChoice = "split"

def highExpectations(high, stand):
    for upCard in SUITS:
        for i in range(21, 10, -1):
            for count in range(MIN_COUNT, MAX_COUNT + 1):
                isSoft = False
                myHome = high
                setExpectation(None, None, None, None, high, stand,i, False, isSoft, False, myHome, upCard, count)
            
def softExpectations(soft, high, stand):
    for upCard in SUITS:
        for i in range(21, 12, -1): # we operate in reverse because we want to build from simple (21) to complex (12)
            for count in range(MIN_COUNT, MAX_COUNT + 1):
                isSoft = True
                myHome = soft
                setExpectation(None, None, None, soft, high, stand, i, False, isSoft, False, myHome, upCard, count)

def lowExpectations(low, soft, high, stand):
    for upCard in SUITS:
        for i in range(10, 5, -1):
            for count in range(MIN_COUNT, MAX_COUNT + 1):
                isSoft = False
                myHome = low
                setExpectation(None, None, low, soft, high, stand, i, False, isSoft, False, myHome, upCard, count)

def doubleExpectations(double, low, soft, high, stand):
    for key in double:
        value = double[key].hand.value
        isSoft = double[key].hand.isSoft
        upCard = double[key].upCard
        count = double[key].count
        setExpectation(None, double, low, soft, high, stand, value, False, isSoft, True, double, upCard, count)

def splitExpectations(split, double, low, soft, high, stand):
    for key in split:
        value = split[key].hand.value
        isSoft = split[key].hand.isSoft
        upCard = split[key].upCard
        count = split[key].count
        setExpectation(split, double, low, soft, high, stand, value, True, isSoft, True, split, upCard, count)

"""
right now, this is just a testing function
"""

def main(n):
    buckets = makeBuckets(n)
    makeExpectations(buckets)
    strategy = {}
    for key in buckets:
        if buckets[key].hand.canHit:
            strategy[key] = (buckets[key].bestChoice, buckets[key].expectation)
    return (buckets, strategy)