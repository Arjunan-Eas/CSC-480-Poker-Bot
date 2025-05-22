#my guy loves to fold pre flop please dont make fun of him
#hes a bit unoptimized but I wanted to make it easier to expand upon for our personal poker bot project
#so a terrible base case makes our good ones seem better

#there are 3 adjustable parameters the constant in ucb1 and 2 factors that limit the number of children expanded
#unforunately they are hardcoded in the code so you will have to change them manually

import random
import time
import math

# Variable for amount of time the model is allowed to simulate
SIM_TIME = 10

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

    bot has a maximum of 15 seconds to decide what its next move will be
    """
    def choose_move(self, game_phase: str, minimum_bet: int, current_bet: int, pot: int, opponent_bank: int) -> tuple[str, int]:
        win_rate = self.simulate()
        print(f"Model winrate: {win_rate}% at {game_phase}")
        decision, bet = self.bet_strategy(game_phase, current_bet, pot, win_rate, minimum_bet, opponent_bank)
        print(f"Model decision: {decision}! Bot bets ${bet}\n")
        return decision, bet


    
    # Setter for modifying player bank
    def change_bank(self, amount: int):
        self.bank += amount
    # Feel free to include any other utility methods you want

    # Runs MCTS to simulate the game, returns the win rate
    def simulate(self):
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
        # print(str(root.visits) + " iterations and " + str(root.wins) + " wins")
        return root.wins / root.visits
        
    def evaluate_hole_cards(self):
        import poker_main
        same_suit = True
        suit = None
        value = None
        avg_value = 0
        pair = True
        for card in self.hole_cards:
            # Adds cumulative value
            avg_value += poker_main.RANK_TO_VALUE[card[0]]
            # Checks same suit
            if suit is None:
                suit = card[1]
            elif suit != card[1]:
                    same_suit = False
            # Checks pair
            if value is None:
                value = poker_main.RANK_TO_VALUE[card[0]]
            elif value != poker_main.RANK_TO_VALUE[card[0]]:
                pair = False
        
        # Score = average card value, with 1.25x multipler for same suit, and 2x multiplier for pair
        score = avg_value / 2
        score = score + score * same_suit * 0.25
        score = score + score * pair
        return score / 28
        


    # Heuristic function for determining how much to bet
    # TODO: take opponent bets into account and current stage/pot to minimize losses
    def bet_strategy(self, game_phase: str, current_bet: int, pot: int, win_rate: float, min_bet: int, opponent_bank: int) -> tuple[str, int]:
        import poker_main
        # Weight to balance between win % and hole card strength based on the turn. Higher = more reliance on hand strength
        RISK_FACTOR = 2 # Risk factor goes from 1 - 5. Higher means lower risk
        phase_weights = {"PF" : 0.75, "F" : 0.5, "T" : 0.25, "R" : 0.15}
        hole_strength = self.evaluate_hole_cards()
        opponent_confidence = current_bet / pot * opponent_bank / poker_main.STARTING_MONEY
        heuristic = (((win_rate + phase_weights[game_phase] * (hole_strength - win_rate)) - opponent_confidence * (1 - phase_weights[game_phase])) / 2) ** RISK_FACTOR
        if heuristic < 0:
            heuristic = 0
        elif heuristic > 1:
            heuristic = 1
        decision = "fold"
        bet = 0

        # Strong hand
        if win_rate > 0.5:
            if current_bet > 0:
                if self.bank > current_bet:
                    bet = min(int(self.bank * heuristic), max(int(pot * heuristic), current_bet))
                    if bet <= current_bet:
                        bet = current_bet
                        decision = "call"
                    else:
                        bet = max(bet, current_bet + min_bet)
                        decision = "raise"
                else:
                    bet = self.bank
                    decision = "call"  # All-in
            else:
                bet = int(self.bank * heuristic)
                if bet <= min_bet:
                    bet = 0
                    decision = "check"
                else:
                    decision = "bet"

        # Medium hand, but strong hole cards and early phase
        elif win_rate > 0.4 and hole_strength > 0.7 and (game_phase == "PF" or game_phase == "F"):
            if current_bet > 0:
                if self.bank > current_bet:
                    bet = current_bet
                    decision = "call"
                else:
                    bet = self.bank
                    decision = "call"  # All-in
            else:
                decision = "check"
                bet = 0

        # Weak hand
        else:
            decision = "fold"
            bet = 0

        print(f"Heuristic score at {game_phase} is {heuristic}")
        return decision, bet

    
    #this is the ucb1 formula
    #u = w/n + c * sqrt(log(N)/n)
    def ucb(self, node, parent):
        if parent != None:
            if node.visits == 0:
                node.ucb = 999999999
            node.ucb = node.wins / node.visits + (2 * (math.log2(parent.visits) / node.visits) ** 0.5)

    def expand(self, Node, start_time):
        if time.time() - start_time > SIM_TIME:
            return
        if Node.state == 0: 
            #preflop ##original code here / code below was modified to add a check for the number of children
            if len(Node.children) == 0:
                child = Tree(Node.state+1, Node.bothand, Node.community.copy(), Node)
                child.community = child.community.union(self.random_card(child.bothand.copy().union(child.community), 3)) 
                Node.add_child(child)
                self.expand(child, start_time)
                return
            #if children exist, sort by ucb and expand the best one
            elif len(Node.children) > 0.5 * Node.visits ** 0.75: #factor to control exploration
                for child in Node.children:
                    self.ucb(child, Node)
                max_ucb_child = None
                for child in Node.children:
                    if max_ucb_child == None:
                        max_ucb_child = child
                    elif child.ucb > max_ucb_child.ucb:
                        max_ucb_child = child
                Node = max_ucb_child 
                self.expand(Node, start_time)
                return
            #if children exist but we want to explore more do this
            else:
                child = Tree(Node.state + 1, Node.bothand, Node.community.copy(), Node)
                child.community = child.community.union(self.random_card(child.bothand.copy().union(child.community), 3))
                Node.add_child(child)
                self.expand(child, start_time)
                return
        
        #if leaf evaluate and propogate
        if Node.state == 3:
            import poker_main
            hand2 = self.random_card(Node.bothand.copy().union(Node.community), 2)
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
        
        #states 1 and 2 only 
        #if no children expand
        if len(Node.children) == 0:
            child = Tree(Node.state+1, Node.bothand, Node.community.copy(), Node)
            child.community = child.community.union(self.random_card(child.bothand.copy().union(child.community), 1))
            Node.add_child(child)
            self.expand(child, start_time)
            return
        #if children exist, sort by ucb and expand the best one
        elif len(Node.children) > 52 - len(Node.bothand) - len(Node.community):
            for child in Node.children:
                self.ucb(child, Node)
            max_ucb_child = None
            for child in Node.children:
                if max_ucb_child == None:
                    max_ucb_child = child
                if child.ucb > max_ucb_child.ucb:
                    max_ucb_child = child
            Node = max_ucb_child
            self.expand(Node, start_time)
            return
        #if children exist but we want to explore more do this
        else:
            child = Tree(Node.state + 1, Node.bothand, Node.community.copy(), Node)
            num_children = len(Node.children)
            child.community = child.community.union(self.random_card(child.bothand.copy().union(child.community), 1))
            Node.add_child(child)
            self.expand(child, start_time)
            return


class Tree:
    def __init__(self, state, bothand, community, parent=None):
        self.children = set()
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
        self.children.add(child)

    def __hash__(self):
        return hash((frozenset(self.bothand), frozenset(self.community)))

    def __eq__(self, other):
        if isinstance(other, Tree):
            return self.bothand == other.bothand and self.community == other.community
        return False
        

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
