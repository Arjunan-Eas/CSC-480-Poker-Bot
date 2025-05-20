#my guy loves to fold pre flop please dont make fun of him
#hes a bit unoptimized but I wanted to make it easier to expand upon for our personal poker bot project
#so a terrible base case makes our good ones seem better

#there are 3 adjustable parameters the constant in ucb1 and 2 factors that limit the number of children expanded
#unforunately they are hardcoded in the code so you will have to change them manually

import random
import time
import math

suits = ['H', 'D', 'C', 'S']
ranks = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]



class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    #i forget the difference between str and repr
    def __str__(self):
        string = str(self.rank)
        if self.rank == 11:
            string = 'J'
        elif self.rank == 12:
            string = 'Q'
        elif self.rank == 13:
            string = 'K'
        elif self.rank == 14:
            string = 'A'
        return string + " of " + self.suit
    
    def __repr__(self):
        string = str(self.rank)
        if self.rank == 11:
            string = 'J'
        elif self.rank == 12:
            string = 'Q'
        elif self.rank == 13:
            string = 'K'
        elif self.rank == 14:
            string = 'A'
        return string + " of " + self.suit
    
    def __eq__(self, other):
        if isinstance(other, Card):
            return self.suit == other.suit and self.rank == other.rank
        return False

class Deck:
    global suits, ranks
    def __init__(self):
        self.cards = []
        for suit in suits:
            for rank in ranks:
                self.cards.append(Card(suit, rank))

    def shuffle(self):
        self.cards = []
        for suit in suits:
            for rank in ranks:
                self.cards.append(Card(suit, rank))
        for i in range(len(self.cards) - 1, 0, -1):
            j = random.randint(0, i)
            self.cards[i], self.cards[j] = self.cards[j], self.cards[i]

    def deal(self):
        return self.cards.pop()
    
class Tree:
    def __init__(self, state, bothand, community, parent=None):
        self.children = []
        self.bothand = bothand
        self.community = community
        self.state = state
        self.wins = 0
        self.visits = 0
        self.parent = parent
        self.ucb = 0

    def add_child(self, child):
        child.parent = self
        child.state = self.state + 1
        self.children.append(child)

class Monte_Carlo:
    def __init__(self):
        self.possibilities = []
        for suit in suits:
            for rank in ranks:
                self.possibilities.append(Card(suit, rank))

    def random_card(self, hand, num_cards=1):
        possibilities2 = self.possibilities.copy()
        for card in hand:
            if card in possibilities2:
                possibilities2.remove(card)
        cards = []
        for i in range(num_cards):
            cards.append(random.choice(possibilities2))
            possibilities2.remove(cards[i])
        return cards



    def should_bot_fold(self, bot, community):
        start_time = time.time()
        hand1 = bot.copy()
        communitycopy = community.copy()
        if len(communitycopy) == 0:
            state = 0
        elif len(communitycopy) == 3:
            state = 1
        elif len(communitycopy) == 4:
            state = 2
        elif len(communitycopy) == 5:
            state = 3
        root = Tree(state, hand1, communitycopy)
        Node = root

        while time.time() - start_time < 10:
            self.expand(Node, start_time)
        print(str(root.visits) + " iterations and " + str(root.wins) + " wins")
        if root.wins / root.visits > 0.5:
            return False
        else:
            return True

    #this is the ucb1 formula
    #u = w/n + c * sqrt(log(N)/n)
    def ucb(self, node, parent):
        if parent != None:
            if node.visits == 0:
                node.ucb = 999999999
            node.ucb = node.wins / node.visits + (2 * (math.log2(parent.visits) / node.visits) ** 0.5)

    def expand(self, Node, start_time):
        if time.time() - start_time > 10:
            return
        #if leaf evaluate and propogate
        if Node.state == 3:
            hand2 = self.random_card(Node.bothand.copy() + Node.community.copy(), 2)
            value = who_won_you_decide(Node.bothand.copy(), hand2.copy(), Node.community.copy())
            Node.wins += value
            Node.visits += 1
            while Node.parent != None:
                Node.parent.wins += value
                Node.parent.visits += 1
                Node = Node.parent
            return
        #if no children expand
        if len(Node.children) == 0:
            child = Tree(Node.state+1, Node.bothand, Node.community.copy(), Node)
            if Node.state == 0:
                child.community = child.community + self.random_card(child.bothand  + child.community, 3) 
            elif Node.state == 1 or Node.state == 2:
                child.community = child.community + self.random_card(child.bothand  + child.community, 1)
            Node.add_child(child)
            self.expand(child, start_time)
            return
        #if children exist, sort by ucb and expand the best one
        elif len(Node.children) > 0.5 * Node.visits ** 0.75: #factor to control exploration
            for child in Node.children:
                self.ucb(child, Node)
            Node.children.sort(key=lambda x: x.ucb, reverse=True)
            Node = Node.children[0]
            self.expand(Node, start_time)
            return
        #if children exist but we want to explore more do this
        else:
            child = Tree(Node.state + 1, Node.bothand, Node.community.copy(), Node)
            if Node.state == 0:
                child.community = child.community + self.random_card(child.bothand  + child.community, 3)
            elif Node.state == 1 or Node.state == 2:
                child.community = child.community + self.random_card(child.bothand  + child.community, 1)
            #states 1 and 2 are the pre turn and pre river and dont have so many children states
            if (Node.state == 1 or Node.state == 2):
                if len(Node. children) == 52 - len(Node.bothand) - len(Node.community):
                    Node.children.sort(key=lambda x: x.ucb, reverse=True)
                    Node = Node.children[0]
                    self.expand(Node, start_time)
                    return
            #pre flop has an incredible large amount of children ~100k so we dont worry about accidentally 
            # duplicating a child as checking for duplicates is expensive
            Node.add_child(child)
            self.expand(child, start_time)
            return


def poker():
    deck = Deck()
    deck.shuffle()
    bot = []
    player2 = []
    community = []
    for i in range(2):
        bot.append(deck.deal())
        player2.append(deck.deal())

    print("Bot's hand: ", bot)
    print("Player 2's hand: ", player2)

    MC = Monte_Carlo()
    if (MC.should_bot_fold(bot.copy(), community.copy())):
        print("Bot folded")
        for i in range(5):
            community.append(deck.deal())
        value = who_won_you_decide(bot, player2, community)
        if value == 1:
            print("Bot would have won")
        elif value == 0:
            print("Player 2 would have won")
        else:
            print("Would have Drew")
    else:    
        for i in range(3):
            community.append(deck.deal())
        print("Flop: ", community)
        if (MC.should_bot_fold(bot.copy(), community.copy())):
            print("Bot folded")
            community.append(deck.deal())
            community.append(deck.deal())
            value = who_won_you_decide(bot, player2, community)
            if value == 1:
                print("Bot would have won")
            elif value == 0:
                print("Player 2 would have won")
            else:
                print("Would have Drew")
        else:
            community.append(deck.deal())
            print("Turn: ", community)
            if (MC.should_bot_fold(bot.copy(), community.copy())):
                print("Bot folded")
                community.append(deck.deal())
                value = who_won_you_decide(bot, player2, community)
                if value == 1:
                    print("Bot would have won")
                elif value == 0:
                    print("Player 2 would have won")
                else:
                    print("Would have Drew")
            else:
                community.append(deck.deal())
                print("River: ", community)
                if (MC.should_bot_fold(bot.copy(), community.copy())):
                    print("Bot folded")
                    value = who_won_you_decide(bot, player2, community)
                    if value == 1:
                        print("Bot would have won")
                    elif value == 0:
                        print("Player 2 would have won")
                    else:
                        print("Would have Drew")
                else:
                    value = who_won_you_decide(bot, player2, community)
                    if value == 1:
                        print("Bot wins")
                    elif value == 0:
                        print("Player 2 wins")
                    else:
                        print("Draw")

    bot = []
    player2 = []
    community = []

def who_won_you_decide(hand1, hand2, community):
    #compare hands

    value1 = hand_value(hand1)
    value2 = hand_value(hand2)
    if value1[0] > value2[0]:
        return 1
    elif value1[0] < value2[0]:
        return 0
    else:
        if value1[1] > value2[1]:
            return 1
        elif value1[1] < value2[1]:
            return 0
        else:
            return 0.5

HIGH_CARD = 0
PAIR = 1
TWO_PAIR = 2
THREE_OF_A_KIND = 3
STRAIGHT = 4
FLUSH = 5
FULL_HOUSE = 6
FOUR_OF_A_KIND = 7
STRAIGHT_FLUSH = 8
ROYAL_FLUSH = 9

#pass in player + community cards
def hand_value(hand):
    global HIGH_CARD, PAIR, TWO_PAIR, THREE_OF_A_KIND, STRAIGHT, FLUSH, FULL_HOUSE, FOUR_OF_A_KIND, STRAIGHT_FLUSH, ROYAL_FLUSH
    values = [0] * 10 #boolean for all possible hands
    rank = [0] * 10 #boolean for all possible hands
    hand.sort(key=lambda x: x.rank) #sort hand by rank lowkey took this from google ai

    rank[HIGH_CARD] = max([card.rank for card in hand])

    #recursive four loops look daunting but the size is very small and often for loops will be skipped

    #pair, 3 of a kind, and four of a kind
    for i in range(len(hand)):
        for j in range(i + 1, len(hand)):
            if hand[i].rank == hand[j].rank:
                values[PAIR] = PAIR
                rank[PAIR] = max(rank[PAIR], (hand[i].rank))
                #check for 3 of a kind
                for k in range(j + 1, len(hand)):
                    if hand[k].rank == hand[i].rank:
                        values[THREE_OF_A_KIND] = THREE_OF_A_KIND
                        rank[THREE_OF_A_KIND] = max(rank[THREE_OF_A_KIND], (hand[i].rank))
                        #check for four of a kind
                        for l in range(k + 1, len(hand)):
                            if hand[l].rank == hand[i].rank:
                                values[FOUR_OF_A_KIND] = FOUR_OF_A_KIND
                                rank[FOUR_OF_A_KIND] = max(rank[FOUR_OF_A_KIND], (hand[i].rank))
    
    #2 pair, and full house
    #i dont know how to resolve ties for two pair and full house, ive seen it done in a few different ways
    if len(hand) >= 4:
        for i in range(len(hand)):
            for j in range(i + 1, len(hand)):
                if hand[i].rank == hand[j].rank:
                    #check for another different pair
                    for k in range(i + 1, len(hand)):
                        if hand[k].rank != hand[i].rank:
                            for l in range(k + 1, len(hand)):
                                if hand[k].rank == hand[l].rank:
                                    values[TWO_PAIR] = TWO_PAIR
                                    rank[TWO_PAIR] = max(rank[TWO_PAIR], max(hand[k].rank, hand[i].rank))
                                    #check for full house
                                    for m in range(i + 1, len(hand)):
                                        if m != i and m != j and m != k and m != l:
                                            if hand[m].rank == hand[i].rank or hand[m].rank == hand[k].rank:
                                                values[FULL_HOUSE] = FULL_HOUSE
                                                rank[FULL_HOUSE] = max(rank[FULL_HOUSE], max(hand[k].rank, hand[i].rank))
                            
    
    #flush, straight flush, and royal flush
    if len(hand) >= 5:
        for i in range(len(hand)):
            for j in range(i + 1, len(hand)):
                if hand[i].suit == hand[j].suit:
                    #check for flush
                    for k in range(j + 1, len(hand)):
                        if hand[k].suit == hand[i].suit:
                            for l in range(k + 1, len(hand)):
                                if hand[l].suit == hand[i].suit:
                                    for m in range(l + 1, len(hand)):
                                        if hand[m].suit == hand[i].suit:
                                            values[FLUSH] = FLUSH
                                            rank[FLUSH] = max(rank[FLUSH], max(hand[i].rank, hand[j].rank, hand[k].rank, hand[l].rank, hand[m].rank))
                                            #check for straight flush
                                            if (hand[m].rank == hand[l].rank + 1 or (hand[m].rank == 14 and hand[i].rank == 2)) and hand[l].rank == hand[k].rank + 1 and hand[k].rank == hand[j].rank + 1 and hand[j].rank == hand[i].rank + 1:
                                                values[STRAIGHT_FLUSH] = STRAIGHT_FLUSH
                                                rank[STRAIGHT_FLUSH] = max(rank[STRAIGHT_FLUSH], hand[l].rank)
                                                #check for royal flush
                                                if hand[i].rank == 10 and hand[j].rank == 11 and hand[k].rank == 12 and hand[l].rank == 13 and hand[m].rank == 14:
                                                    values[ROYAL_FLUSH] = ROYAL_FLUSH
                                                    
                                    
                            

    #straight
    if len(hand) >= 5:
        for i in range(len(hand)):
            for j in range(i + 1, len(hand)):
                if hand[i].rank == hand[j].rank + 1:
                    for k in range(j + 1, len(hand)):
                        if hand[k].rank == hand[j].rank + 1:
                            for l in range(k + 1, len(hand)):
                                if hand[l].rank == hand[k].rank + 1:
                                    for m in range(l + 1, len(hand)):
                                        if (hand[m].rank == hand[l].rank + 1 or (hand[m].rank == 14 and hand[i].rank == 2)):
                                            values[STRAIGHT] = STRAIGHT
                                            rank[STRAIGHT] = max(rank[STRAIGHT], hand[l].rank)
    return (max(values), rank[max(values)])
    

if __name__ == "__main__":
    poker()
