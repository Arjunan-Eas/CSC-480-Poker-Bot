#my guy loves to fold pre flop please dont make fun of him
#hes a bit unoptimized but I wanted to make it easier to expand upon for our personal poker bot project
#so a terrible base case makes our good ones seem better

#there are 3 adjustable parameters the constant in ucb1 and 2 factors that limit the number of children expanded
#unforunately they are hardcoded in the code so you will have to change them manually

import random
import time
import math
import poker_main


class MCTS:
    def __init__(self, hand, community, money):
        self.possibilities = ["2D", "3D", "4D", "5D", "6D", "7D", "8D", "9D", "TD", "JD", "QD", "KD", "AD",
                                "2C", "3C", "4C", "5C", "6C", "7C", "8C", "9C", "TC", "JC", "QC", "KC", "AC",
                                "2H", "3H", "4H", "5H", "6H", "7H", "8H", "9H", "TH", "JH", "QH", "KH", "AH",
                                "2S", "3S", "4S", "5S", "6S", "7S", "8S", "9S", "TS", "JS", "QS", "KS", "AS"]
        self.hole_cards = hand
        self.community_cards = community
        self.bank = money

    """
    You can implement this function however you see fit, but at a base level
    you should have some way of speculatively drawing cards based on the
    hole cards you have and what community cards are visible
    """
    def draw_card(self) -> set[str]:
        pass
    
    def random_card(self, hand, num_cards=1):
        possibilities2 = self.possibilities.copy()
        for card in hand:
            if card in possibilities2:
                possibilities2.remove(card)
        cards = set()
        for i in range(num_cards):
            new_card = random.choice(possibilities2)
            cards.add(new_card)
            possibilities2.remove(new_card)
        return cards

    """
    Different stages are:
        "PF" = Pre flop
        "F" = Flop
        "T" = Turn
        "R" = River

    The general format is (move, bet)
    Possible moves: (idk poker so feel free to update this)
        ("check", 0)        # Only if current bet is 0
        ("bet", $ amount)   # Only if current bet is 0
        ("call", $ amount)  # Only if current bet != 0
        ("raise", $ amount) # Only if current bet != 0 ($ amount is total bet, not just the increase)
        ("fold", 0)         # Anytime

    Your bot has a maximum of 1000000000 seconds to decide what its next move will be
    """
    def choose_move(self, game_phase: str, minimum_bet: int, current_bet: int, pot: int) -> tuple[str, int]:
        should_bot_fold = self.should_bot_fold()
        if should_bot_fold:
            return "fold", 0
        if current_bet == 0:
            return "check", 0
        elif current_bet > 0 and self.bank >= current_bet:
            return "call", current_bet
        elif current_bet > 0 and self.bank < current_bet:
            return "call", self.bank
        # do this shit later gang
        # elif current_bet > 0 and self.bank >= minimum_bet:
        #     return "raise", $$$$

    
    # Setter for modifying player bank
    def change_bank(self, amount: int):
        self.bank += amount
    # Feel free to include any other utility methods you want


    def should_bot_fold(self):
        start_time = time.time()
        communitycopy = self.community_cards.copy()
        if len(communitycopy) == 0:
            state = 0
        elif len(communitycopy) == 3:
            state = 1
        elif len(communitycopy) == 4:
            state = 2
        elif len(communitycopy) == 5:
            state = 3
        root = Tree(state, self.hole_cards.copy(), communitycopy)
        Node = root

        while time.time() - start_time < 15:
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
        if time.time() - start_time > 15:
            return
        #if leaf evaluate and propogate
        if Node.state == 3:
            hand2 = self.random_card(Node.bothand.copy().union(Node.community.copy()), 2)
            value = poker_main.choose_winner(poker_main.evaluate_hand(Node.bothand.copy().union(Node.community.copy())), poker_main.evaluate_hand(hand2.copy().union(Node.community.copy())))
            if value == -1:
                value = 1/2
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
                child.community = child.community.union(self.random_card(child.bothand.union(child.community), 3)) 
            elif Node.state == 1 or Node.state == 2:
                child.community = child.community.union(self.random_card(child.bothand.union(child.community), 1))
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
                child.community = child.community.union(self.random_card(child.bothand.union(child.community), 3))
            elif Node.state == 1 or Node.state == 2:
                child.community = child.community.union(self.random_card(child.bothand.union(child.community), 1))
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
