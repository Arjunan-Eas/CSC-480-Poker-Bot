"""
Main game file to pit two models together in a game of poker.
Each model should be imported and instantiated before running the file (we can change how that works later)

For now, I included a UML diagram of all the functions your poker bot class should have.
This way, they are more plug and play.

Also, all bots have to use the same card format, which for now I have chosen as set[str].
Ex: pocket aces hand: {"AS", "AC"}.
Each model is responsible for keeping track of which cards it has, and simulating drawing future cards
The overall file will deal the necessary cards at each turn.
"""
from basic_bot import basicBot
from MCTS import MCTS
from Min_Max_implementation import MinimaxBot
import random
from typing import Optional, Union
from GTO import GTOBot
import statistics
import matplotlib.pyplot as plt
import time

# For blind bets
MIN_BET = 1
# Starting money for each player
STARTING_MONEY = 100
# Maps the string representing the card rank to its numerical value
RANK_TO_VALUE = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
# Reverse mapping
VALUE_TO_RANK = {1: 'A', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: 'T', 11: 'J', 12: 'Q', 13: 'K', 14: 'A'}
# Collection of suits
SUITS = ('D', 'C', 'H', 'S')
# Maps generated result to a human understandable name
RESULT_TO_HAND = {1 : "Royal flush", 2 : "Straight Flush", 3 : "Four of a kind", 4 : "Full House", 5 : "Flush", 6 : "Straight", 7 : "Three of a kind", 8 : "Two pair", 9 : "Pair", 10 : "High card"}
# Maps class name to string version
CLASS_TO_NAME = {MCTS : "mcts", basicBot : "basic", MinimaxBot : "minimax", GTOBot : "gto"}

# Deck class
class Deck:
    def __init__(self):
        # Randomly shuffles deck on instantiation
        self.deck: list[str] = ["2D", "3D", "4D", "5D", "6D", "7D", "8D", "9D", "TD", "JD", "QD", "KD", "AD",
                                "2C", "3C", "4C", "5C", "6C", "7C", "8C", "9C", "TC", "JC", "QC", "KC", "AC",
                                "2H", "3H", "4H", "5H", "6H", "7H", "8H", "9H", "TH", "JH", "QH", "KH", "AH",
                                "2S", "3S", "4S", "5S", "6S", "7S", "8S", "9S", "TS", "JS", "QS", "KS", "AS"]
        random.shuffle(self.deck)
                                 
    
    # Dealing at each phase modifies deck, so no duplicate checking needed
    def deal_pre_flop(self) -> tuple[set[str], set[str]]:
        hand1 = set()
        hand2 = set()
        for i in range(2):
            hand1.add(self.deck.pop())
            hand2.add(self.deck.pop())
        return hand1, hand2

    def deal_flop(self) -> set[str]:
        flop_cards = set()
        for i in range(3):
            flop_cards.add(self.deck.pop())
        return flop_cards  

    def deal_turn(self) -> set[str]:
        turn_card = set()
        turn_card.add(self.deck.pop())
        return turn_card  

    def deal_river(self) -> set[str]:
        river_card = set()
        river_card.add(self.deck.pop())
        return river_card  

def royal_flush(values: dict, suits: dict, cards: set[str]) -> Optional[tuple[int, list[int]]]:
    # Royal flush must have 5 different cards values
    if len(values.keys()) < 5:
        return None
    
    # Checks if there is a suit with 5 different cards
    royal_suit = 0
    for suit in suits.keys():
        if suits[suit] >= 5:
            royal_suit = suit
    
    # No suits had 5 cards
    if royal_suit == 0:
        return None

    royal_values = set([10, 11, 12, 13, 14])
    # Checks if there a possible royal flush
    if len(set(values.keys()).intersection(royal_values)) == 5:
        royal_hand = set([f"T{royal_suit}", f"J{royal_suit}", f"Q{royal_suit}", f"K{royal_suit}", f"A{royal_suit}"])
        if len(royal_hand.intersection(cards)) == 5:
            return (1, [])
        else:
            return None

def straight_flush(values: dict, suits: dict, cards: set) -> Optional[tuple[int, list[int]]]:
    straight = False

    # Sorts the values
    sorted_values = sorted(values.keys())

    # Checks for straight
    in_a_row = 1
    straight_cards = set()
    
    for i in range(len(sorted_values) - 1):
        if(sorted_values[i + 1] == sorted_values[i] + 1):
            in_a_row += 1
            straight_cards.add(sorted_values[i])
            straight_cards.add(sorted_values[i+1])
        elif(in_a_row < 5):
            in_a_row = 1
            straight_cards = set()
            
    if(in_a_row < 5):
        # If ace
        if sorted_values[-1] == 14:
            in_a_row = 1
            # Retries with ace as 1
            sorted_values = [1] + sorted_values[:-1]
            for i in range(len(sorted_values) - 1):
                if(sorted_values[i + 1] == sorted_values[i] + 1):
                    in_a_row += 1
                    straight_cards.add(sorted_values[i])
                    straight_cards.add(sorted_values[i+1])
                elif(in_a_row < 5):
                    in_a_row = 1
                    straight_cards = set()
    
    # Confirms a straight is possible
    if(in_a_row >= 5):
        straight = True

    # Checks flush
    flush_suit = 0
    for suit in suits.keys():
        if suits[suit] == 5:
            # Flush is possible
            flush_suit = suit
            break
    # No flush
    if flush_suit == 0:
        if straight:
            # Just a straight
            return (6, list(straight_cards)[-5:])
        else:
            return None
    else:
        straight_flush_cards = set()
        for card in straight_cards:
            straight_flush_cards.add(f'{VALUE_TO_RANK[card]}{flush_suit}')
        # Checks straight and flush
        hand = (straight_flush_cards.intersection(cards))
        if len(hand) >= 5:
            h = sorted([RANK_TO_VALUE[card[0]] for card in hand])
            # Checks to make same suit
            in_a_row = 1
            for i in range(len(h) - 1):
                if(h[i + 1] == h[i] + 1):
                    in_a_row += 1
                else:
                    in_a_row = 1
            # Straight flush
            if(in_a_row == 5):
                return (2, h[-5:])
            
            else:
                # Just a flush
                return (5, sorted([RANK_TO_VALUE[card[0]] for card in cards if card[1] == suit]))

def duplicates(values: dict) -> Optional[tuple[int, list[int]]]:
    
    sorted_values = sorted(values.keys())
    
    three_of_a_kind = False
    three_value = []
    pair_count = 0
    pair_values = []

    for value in values.keys():
        # Four of a kind
        if(values[value] == 4):
            sorted_values.remove(value)
            return (3, sorted_values[-1:] + [value])
        # Three of a kind
        if(values[value] == 3):
            three_value.append(value)
            three_of_a_kind = True
        # Pairs
        if(values[value] == 2):
            pair_count += 1
            pair_values.append(value)
    
    if(three_of_a_kind):
        # Full house
        if( pair_count > 0):
            return (4, [max(pair_values)] + three_value)
        else:
            # Just three of a kind
            sorted_values.remove(three_value[0])
            return (7, sorted_values[-2:] + three_value)

    # Two pairs
    if pair_count >= 2:
        pair_values.sort()
        # Takes the highest two pairs
        pair_values = pair_values[-2:]
        sorted_values.remove(pair_values[0])
        sorted_values.remove(pair_values[1])
        return (8, sorted_values[-1:] + pair_values)
    
    # Pair
    if pair_count == 1:
        sorted_values.remove(pair_values[0])
        return(9, sorted_values[-3:] + pair_values)
    
    # High card
    else:
        return(10, sorted_values[-5:])

def evaluate_hand(cards: set[str]) -> tuple[int, list[int]]:
    # Dictionary to hold the counts of each value of card
    value_counter = {}
    
    # Dictionary to hold the counts of each suit of card
    suit_counter = {}
    
    # Counts cards
    for card in cards:
        if RANK_TO_VALUE[card[0]] in value_counter.keys():
            value_counter[RANK_TO_VALUE[card[0]]] += 1
        else:
            value_counter[RANK_TO_VALUE[card[0]]] = 1
        
        if card[1] in suit_counter.keys():
            suit_counter[card[1]] += 1
        else:
            suit_counter[card[1]] = 1

    # Checks royal flush
    rf = royal_flush(value_counter, suit_counter, cards)
    if not rf is None:
        return rf

    # Checks four of a kind, three of a kind, full house, two pairs, pair, and high card
    dup = duplicates(value_counter)

    # Checks straight, flush, and straight flush    
    sf = straight_flush(value_counter, suit_counter, cards)
    if sf is None or dup[0] == 3:
        return dup
    else:
        return sf

def breakdown_result(result: tuple[int, list[int]]) -> str:      
    rank = RESULT_TO_HAND[result[0]]
    if result[0] == 1:
        return rank
    if result[0] in [2, 4, 5, 6]:
        return rank + f" ({str(result[1])})"
    if result[0] == 3:
        return rank + f" ({result[1][-1]}), Kicker: {result[1][-2]}"
    if result[0] == 7:
        return rank + f" ({result[1][-1]}), Kickers: {result[1][-3:-1]}"
    if result[0] == 8:
        return rank + f" ({result[1][-2]}, {result[1][-1]}), Kicker: {result[1][-3]}"
    if result[0] == 9:
        return rank + f" ({result[1][-1]}), Kickers: {result[1][-4:-1]}"
    else:
        return rank + f" ({result[1][-1]}), Kickers: {result[1][-5:-1]}"
    
"""
Takes in two evaluated hands.
Returns 1 if the first player wins
Return 0 if the second player wins
Returns -1 if tie
"""
def choose_winner(p0: tuple[int, list[int]], p1: tuple[int, list[int]]) -> int:
    # If hands have the same rank
    if(p0[0] == p1[0]):
        # Compare kickers
        while len(p0[1]) > 0 and len(p1[1]) > 0:
            kicker0 = p0[1].pop()
            kicker1 = p1[1].pop()
            # Goes to the next kicker if they are the same
            if kicker0 == kicker1:
                continue
            else:
                # Otherwise compares kickers to determine winner
                return kicker1 < kicker0
        
        # Ties
        if len(p0[1]) == 0 and len(p1[1]) == 0:
            return -1
        # p0 had higher duplicate kicker
        elif len(p0[1]) == 0 and len(p1[1]) != 0:
            return 1
        # p1 had higher duplicate kicker
        elif len(p0[1]) != 0 and len(p1[1]) == 0:
            return 0
            
    # Whoever has highest ranking hand wins
    # Note, 1 is the highest rank and 10 is the lowest.
    else:
        return p0[0] < p1[0]

# Simulates the ending of the game in case of fold
def simulate_ending(p1: Union[basicBot, MinimaxBot, MCTS, GTOBot], p2: Union[basicBot, MinimaxBot, MCTS, GTOBot], deck: Deck, stage: str) -> int:
    match(stage):
        case "PF":
            community_cards = set()
            community_cards.union(deck.deal_flop())
            community_cards.union(deck.deal_turn())
            community_cards.union(deck.deal_river())
        case "F":
            community_cards = p1.community_cards.copy()
            community_cards.union(deck.deal_turn())
            community_cards.union(deck.deal_river())           
        case "T":
            community_cards = p1.community_cards.copy()
            community_cards.union(deck.deal_river())
        case "R":
            community_cards = p1.community_cards.copy()
        case _: return

    return choose_winner(evaluate_hand(p1.hole_cards.union(community_cards)), evaluate_hand(p2.hole_cards.union(community_cards)))

# Main function, plays a single poker game, returns players banks
def main(p1: Union[basicBot, MinimaxBot, MCTS, GTOBot], p2: Union[basicBot, MinimaxBot, MCTS, GTOBot], folding_counter1: int, folding_tracker1: dict, folding_counter2: int, folding_tracker2: dict, p1_wins: int, p2_wins: int, bot1: str, bot2: str):
    # Initializes pot
    pot = 0

    # Initializes start bank amount for delta comparison
    p1_start_bank = p1.bank
    p2_start_bank = p2.bank

    """
    Blind stage
    """
    # Blind bets
    pot += 3*MIN_BET
    # Small blind
    p1.change_bank(MIN_BET * -1)
    # Big Blind
    p2.change_bank(2 * MIN_BET * -1)

    """
    Pre-flop stage
    """
    current_bet = 0
    p1_bet = None
    p2_bet = None

    while True:
        # Player 1 goes first
        p1_action, p1_bet = p1.choose_move("PF", MIN_BET, current_bet, pot, p2.bank)
        match p1_action:
            case "check":
                pass
            case "call":
                if(p1.bank >= p1_bet):
                    pot += p1_bet
                    p1.change_bank(current_bet * -1)
                break
            case "bet":
                current_bet = p1_bet
                pot += p1_bet
                p1.change_bank(current_bet * -1)
            case "fold":
                print("Player 1 folded")
                p2.change_bank(pot)
                # Update folding tracker with if the player folded correctly. Ties count as a correct fold
                if(CLASS_TO_NAME[p1.__class__] == bot1):
                    p2_wins += 1
                    if(simulate_ending(p1, p2, deck, "PF") == 0):
                        folding_counter1 += 1    # Correct fold
                    folding_tracker1["PF"] += 1
                elif(CLASS_TO_NAME[p1.__class__] == bot2):
                    p1_wins += 1
                    if(simulate_ending(p1, p2, deck, "PF") == 0):
                        folding_counter2 += 1    # Correct fold
                    folding_tracker2["PF"] += 1                    
                return p1.bank, p2.bank, p1_start_bank - p1.bank, p2_start_bank - p2.bank, folding_counter1, folding_tracker1, folding_counter2, folding_tracker2, p1_wins, p2_wins
            case _:
                # Illegal action, do something?
                print(f"Illegal action: {p1_action} from Player 1") 

        # Continues the betting loop until players have the same bet
        if(not p2_bet is None):
            if((p1_bet == current_bet and p2_bet == current_bet or (p1.bank == 0 or p2.bank == 0)) and everyone_has_bet):
                break       
                    
        p2_action, p2_bet = p2.choose_move("PF", MIN_BET, current_bet, pot, p1.bank)
        match p2_action:
            case "check":
                break
            case "call":
                if(p2.bank >= p2_bet):
                    pot += p2_bet
                    p2.change_bank(current_bet * -1)
                break
            case "raise":
                current_bet = p2_bet
                pot += p2_bet
                p2.change_bank(current_bet * -1)
            case "bet":
                current_bet = p2_bet
                pot += p2_bet
                p2.change_bank(current_bet * -1)     
            case "fold":
                print("Player 2 folded")
                p1.change_bank(pot)
                # Update folding tracker with if the player folded correctly. Ties count as a correct fold
                if(CLASS_TO_NAME[p2.__class__] == bot1):
                    p2_wins += 1
                    if(simulate_ending(p1, p2, deck, "PF") == 1):
                        folding_counter1 += 1    # Correct fold
                    folding_tracker1["PF"] += 1
                elif(CLASS_TO_NAME[p2.__class__] == bot2):
                    p1_wins += 1
                    if(simulate_ending(p1, p2, deck, "PF") == 1):
                        folding_counter2 += 1    # Correct fold
                    folding_tracker2["PF"] += 1                 
                return p1.bank, p2.bank, p1_start_bank - p1.bank, p2_start_bank - p2.bank, folding_counter1, folding_tracker1, folding_counter2, folding_tracker2, p1_wins, p2_wins
            case _:
                # Illegal action, do something?
                print(f"Illegal action: {p2_action} from Player 2")

        # Goes true after everyone has done their initial bets
        everyone_has_bet = True

        # Continues the betting loop until players have the same bet
        if((p1_bet == current_bet and p2_bet == current_bet) or (p1.bank == 0 or p2.bank == 0)):
            break

    """
    Flop Stage
    """
    # Deals 3 community cards
    community_cards = deck.deal_flop()
    p1.community_cards = p1.community_cards.union(community_cards)
    p2.community_cards = p2.community_cards.union(community_cards)

    # Resets current bet to 0
    current_bet = 0
    p1_bet = None
    p2_bet = None

    while True:
        # Player 1 goes first
        p1_action, p1_bet = p1.choose_move("F", MIN_BET, current_bet, pot, p2.bank)
        match p1_action:
            case "check":
                pass
            case "call":
                if(p1.bank >= p1_bet):
                    pot += p1_bet
                    p1.change_bank(current_bet * -1)
                break
            case "bet":
                current_bet = p1_bet
                pot += p1_bet
                p1.change_bank(current_bet * -1)
            case "fold":
                print("Player 1 folded")
                p2.change_bank(pot)
                if(CLASS_TO_NAME[p1.__class__] == bot1):
                    p2_wins += 1
                    if(simulate_ending(p1, p2, deck, "F") == 0):
                        folding_counter1 += 1    # Correct fold
                    folding_tracker1["F"] += 1
                elif(CLASS_TO_NAME[p1.__class__] == bot2):
                    p1_wins += 1
                    if(simulate_ending(p1, p2, deck, "F") == 0):
                        folding_counter2 += 1    # Correct fold
                    folding_tracker2["F"] += 1 
                return p1.bank, p2.bank, p1_start_bank - p1.bank, p2_start_bank - p2.bank, folding_counter1, folding_tracker1, folding_counter2, folding_tracker2, p1_wins, p2_wins
            case _:
                # Illegal action, do something?
                print(f"Illegal action: {p1_action} from Player 1") 
            
        # Continues the betting loop until players have the same bet
        if(not p2_bet is None):
            if((p1_bet == current_bet and p2_bet == current_bet or (p1.bank == 0 or p2.bank == 0)) and everyone_has_bet):
                break         

        p2_action, p2_bet = p2.choose_move("F", MIN_BET, current_bet, pot, p1.bank)
        match p2_action:
            case "check":
                pass
            case "call":
                if(p2.bank >= p2_bet):
                    pot += p2_bet
                    p2.change_bank(current_bet * -1)
                break
            case "raise":
                current_bet = p2_bet
                pot += p2_bet
                p2.change_bank(current_bet * -1)
            case "bet":
                current_bet = p2_bet
                pot += p2_bet
                p2.change_bank(current_bet * -1)                     
            case "fold":
                print("Player 2 folded")
                p1.change_bank(pot)
                if(CLASS_TO_NAME[p2.__class__] == bot1):
                    p2_wins += 1
                    if(simulate_ending(p1, p2, deck, "F") == 1):
                        folding_counter1 += 1    # Correct fold
                    folding_tracker1["F"] += 1
                elif(CLASS_TO_NAME[p2.__class__] == bot2):
                    p1_wins += 1
                    if(simulate_ending(p1, p2, deck, "F") == 1):
                        folding_counter2 += 1    # Correct fold
                    folding_tracker2["F"] += 1    
                return p1.bank, p2.bank, p1_start_bank - p1.bank, p2_start_bank - p2.bank, folding_counter1, folding_tracker1, folding_counter2, folding_tracker2, p1_wins, p2_wins
            case _:
                # Illegal action, do something?
                print(f"Illegal action: {p2_action} from Player 2")
                
        # Goes true after everyone has done their initial bets
        everyone_has_bet = True

        # Continues the betting loop until players have the same bet
        if((p1_bet == current_bet and p2_bet == current_bet) or (p1.bank == 0 or p2.bank == 0)):
            break          
    """
    Turn Stage
    """
    # Deals 3 community cards
    community_cards = deck.deal_turn()
    p1.community_cards = p1.community_cards.union(community_cards)
    p2.community_cards = p2.community_cards.union(community_cards)

    # Resets current bet to 0
    current_bet = 0
    p1_bet = None
    p2_bet = None

    while True:
        # Player 1 goes first
        p1_action, p1_bet = p1.choose_move("T", MIN_BET, current_bet, pot, p2.bank)
        match p1_action:
            case "check":
                pass
            case "call":
                if(p1.bank >= p1_bet):
                    pot += p1_bet
                    p1.change_bank(current_bet * -1)
                break
            case "bet":
                current_bet = p1_bet
                pot += p1_bet
                p1.change_bank(current_bet * -1)
            case "fold":
                print("Player 1 folded")
                p2.change_bank(pot)
                if(CLASS_TO_NAME[p1.__class__] == bot1):
                    p2_wins += 1
                    if(simulate_ending(p1, p2, deck, "T") == 0):
                        folding_counter1 += 1    # Correct fold
                    folding_tracker1["T"] += 1
                elif(CLASS_TO_NAME[p1.__class__] == bot2):
                    p1_wins += 1
                    if(simulate_ending(p1, p2, deck, "T") == 0):
                        folding_counter2 += 1    # Correct fold
                    folding_tracker2["T"] += 1 
                return p1.bank, p2.bank, p1_start_bank - p1.bank, p2_start_bank - p2.bank, folding_counter1, folding_tracker1, folding_counter2, folding_tracker2, p1_wins, p2_wins
            case _:
                # Illegal action, do something?
                print(f"Illegal action: {p1_action} from Player 1") 

        # Continues the betting loop until players have the same bet
        if(not p2_bet is None):
            if((p1_bet == current_bet and p2_bet == current_bet or (p1.bank == 0 or p2.bank == 0)) and everyone_has_bet):
                break           

        p2_action, p2_bet = p2.choose_move("T", MIN_BET, current_bet, pot, p1.bank)
        match p2_action:
            case "check":
                pass
            case "call":
                if(p2.bank >= p2_bet):
                    pot += p2_bet
                    p2.change_bank(current_bet * -1)
                break
            case "raise":
                current_bet = p2_bet
                pot += p2_bet
                p2.change_bank(current_bet * -1)
            case "bet":
                current_bet = p2_bet
                pot += p2_bet
                p2.change_bank(current_bet * -1)                     
            case "fold":
                print("Player 2 folded")
                p1.change_bank(pot)
                if(CLASS_TO_NAME[p2.__class__] == bot1):
                    p2_wins += 1
                    if(simulate_ending(p1, p2, deck, "T") == 1):
                        folding_counter1 += 1    # Correct fold
                    folding_tracker1["T"] += 1
                elif(CLASS_TO_NAME[p2.__class__] == bot2):
                    p1_wins += 1
                    if(simulate_ending(p1, p2, deck, "T") == 1):
                        folding_counter2 += 1    # Correct fold
                    folding_tracker2["T"] += 1    
                return p1.bank, p2.bank, p1_start_bank - p1.bank, p2_start_bank - p2.bank, folding_counter1, folding_tracker1, folding_counter2, folding_tracker2, p1_wins, p2_wins
            case _:
                # Illegal action, do something?
                print(f"Illegal action: {p2_action} from Player 2")

        # Goes true after everyone has done their initial bets
        everyone_has_bet = True

        # Continues the betting loop until players have the same bet
        if((p1_bet == current_bet and p2_bet == current_bet) or (p1.bank == 0 or p2.bank == 0)):
            break

    """
    River Stage
    """
    # Deals 3 community cards
    community_cards = deck.deal_river()
    p1.community_cards = p1.community_cards.union(community_cards)
    p2.community_cards = p2.community_cards.union(community_cards)

    # Resets current bet to 0
    current_bet = 0
    p1_bet = None
    p2_bet = None

    while True:
        # Player 1 goes first
        p1_action, p1_bet = p1.choose_move("R", MIN_BET, current_bet, pot, p2.bank)
        match p1_action:
            case "check":
                pass
            case "call":
                if(p1.bank >= p1_bet):
                    pot += p1_bet
                    p1.change_bank(current_bet * -1)
                break
            case "bet":
                current_bet = p1_bet
                pot += p1_bet
                p1.change_bank(current_bet * -1)
            case "fold":
                print("Player 1 folded")
                p2.change_bank(pot)
                if(CLASS_TO_NAME[p1.__class__] == bot1):
                    p2_wins += 1
                    if(simulate_ending(p1, p2, deck, "R") == 0):
                        folding_counter1 += 1    # Correct fold
                    folding_tracker1["R"] += 1
                elif(CLASS_TO_NAME[p1.__class__] == bot2):
                    p1_wins += 1
                    if(simulate_ending(p1, p2, deck, "R") == 0):
                        folding_counter2 += 1    # Correct fold
                    folding_tracker2["R"] += 1 
                return p1.bank, p2.bank, p1_start_bank - p1.bank, p2_start_bank - p2.bank, folding_counter1, folding_tracker1, folding_counter2, folding_tracker2, p1_wins, p2_wins
            case _:
                # Illegal action, do something?
                print(f"Illegal action: {p1_action} from Player 1") 
        
        # Continues the betting loop until players have the same bet
        if(not p2_bet is None):
            if((p1_bet == current_bet and p2_bet == current_bet or (p1.bank == 0 or p2.bank == 0)) and everyone_has_bet):
                break        

        p2_action, p2_bet = p2.choose_move("R", MIN_BET, current_bet, pot, p1.bank)
        match p2_action:
            case "check":
                pass
            case "call":
                if(p2.bank >= p2_bet):
                    pot += p2_bet
                    p2.change_bank(current_bet * -1)
                break
            case "raise":
                current_bet = p2_bet
                pot += p2_bet
                p2.change_bank(current_bet * -1)
            case "bet":
                current_bet = p2_bet
                pot += p2_bet
                p2.change_bank(current_bet * -1)                
            case "fold":
                print("Player 2 folded")
                p1.change_bank(pot)
                if(CLASS_TO_NAME[p2.__class__] == bot1):
                    p2_wins += 1
                    if(simulate_ending(p1, p2, deck, "R") == 1):
                        folding_counter1 += 1    # Correct fold
                    folding_tracker1["R"] += 1
                elif(CLASS_TO_NAME[p2.__class__] == bot2):
                    p1_wins += 1
                    if(simulate_ending(p1, p2, deck, "R") == 1):
                        folding_counter2 += 1    # Correct fold
                    folding_tracker2["R"] += 1    
                return p1.bank, p2.bank, p1_start_bank - p1.bank, p2_start_bank - p2.bank, folding_counter1, folding_tracker1, folding_counter2, folding_tracker2, p1_wins, p2_wins
            case _:
                # Illegal action, do something?
                print(f"Illegal action: {p2_action} from Player 2")
        
        # Goes true after everyone has done their initial bets
        everyone_has_bet = True
        
        # Continues the betting loop until players have the same bet
        if((p1_bet == current_bet and p2_bet == current_bet) or (p1.bank == 0 or p2.bank == 0)):
            break
    
    """
    Showdown stage
    """
    # If it reaches this point in the game, both players are still in
    winner = choose_winner(evaluate_hand(p1.hole_cards.union(p1.community_cards)), evaluate_hand(p2.hole_cards.union(p2.community_cards)))

    if(winner == 1):
        # Player 1 wins
        p1.change_bank(pot)
        if(CLASS_TO_NAME[p1.__class__] == bot1):
            p1_wins += 1
        elif(CLASS_TO_NAME[p1.__class__] == bot2):
            p2_wins += 1
        print(f"Player 1 wins ${pot}!")
        
    elif(winner == 0):
        # Player 2 wins
        p2.change_bank(pot)
        if(CLASS_TO_NAME[p2.__class__] == bot1):
            p1_wins += 1
        elif(CLASS_TO_NAME[p2.__class__] == bot2):
            p2_wins += 1
        print(f"Player 2 wins ${pot}!")

    elif(winner == -1):
        # Tie
        p1.change_bank(pot / 2)
        p2.change_bank(pot / 2)

    print(f"Community cards: {p1.community_cards}")
    print(f"Player 1 hold cards: {p1.hole_cards} Hand: {breakdown_result(evaluate_hand(p1.hole_cards.union(p1.community_cards)))} Bank: {p1.bank}")
    print(f"Player 2 hold cards: {p2.hole_cards} Hand: {breakdown_result(evaluate_hand(p2.hole_cards.union(p2.community_cards)))} Bank: {p2.bank}")

    # Returns bank and delta
    return p1.bank, p2.bank, p1_start_bank - p1.bank, p2_start_bank - p2.bank, folding_counter1, folding_tracker1, folding_counter2, folding_tracker2, p1_wins, p2_wins

if __name__ == "__main__":
    start_time = time.time()
    # Number of games to play
    while True:
        try:
            rounds = int(input("How many full games would you like to play (goes until one player loses)? "))
            if(rounds > 0):
                break
            else:
                print("Please enter a positive number of rounds")
        except:
            print("Enter an integer number of rounds")

    # Starting bank for both players
    p1_bank, p2_bank = STARTING_MONEY, STARTING_MONEY

    # Initializing profit trackers
    p1_profit = []
    p2_profit = []
    delta1 = 0
    delta2 = 0

    # Initialize fold trackers
    folding_counter1 = 0
    folding_tracker1 = {"PF" : 0, "F" : 0, "T" : 0, "R" : 0}
    folding_counter2 = 0
    folding_tracker2 = {"PF" : 0, "F" : 0, "T" : 0, "R" : 0}

    # Win trackers
    p1_wins = 0
    p2_wins = 0

    # Choose type of each bot.
    while True:
        try:
            bot1 = input("Which bot is player 1? (Basic, Minimax, MCTS, or GTO) ").lower()
            match(bot1):
                case "basic" : break
                case "minimax" : break
                case "mcts" : break
                case "gto" : break
                case _: 
                    print("Please enter a valid bot type")
                    continue
        except:
            print("Please enter one of the bot types")

    while True:
        try:
            bot2 = input("Which bot is player 2? (Basic, Minimax, MCTS, or GTO) ").lower()
            match(bot2):
                case "basic" : break
                case "minimax" : break
                case "mcts" : break
                case "gto" : break
                case _: 
                    print("Please enter a valid bot type")
                    continue
        except:
            print("Please enter one of the bot types")

    total_hands = 0
    hand = 0
    p1_game_wins = 0
    p2_game_wins = 0
    for i in range(rounds):
        # Counter for number of hands played per game
        hand = 0
        p1_bank = STARTING_MONEY
        p2_bank = STARTING_MONEY
        # Plays until one player is bankrupt    
        while True:
            # Shuffle deck on instantiation
            deck = Deck()

            # Deals hole cards to each player
            p1_hand, p2_hand = deck.deal_pre_flop()

            # Swaps who is player 1 and player 2 each round. Ultimately bot1 started as player 1 and will be tracked as so
            if(hand % 2 == 0):
                match(bot1):
                    case "basic" : 
                        p1 = basicBot(p1_hand, set(), p2_bank)
                        print("Player 1 is basic bot")
                    case "minimax" : 
                        p1 = MinimaxBot(p1_hand, set(), p2_bank)
                        print("Player 1 is Minimax Bot")
                    case "mcts" : 
                        p1 = MCTS(p1_hand, set(), p2_bank)
                        print("Player 1 is MCTS bot")
                    case "gto" : 
                        p1 = GTOBot(p1_hand, set(), p2_bank)
                        print("Player 1 is GTO bot")

                match(bot2):
                    case "basic" : 
                        p2 = basicBot(p2_hand, set(), p1_bank)
                        print("Player 2 is basic bot")
                    case "minimax" : 
                        p2 = MinimaxBot(p2_hand, set(), p1_bank)
                        print("Player 2 is Minimax bot")
                    case "mcts" : 
                        p2 = MCTS(p2_hand, set(), p1_bank)
                        print("Player 2 is MCTS bot")
                    case "gto" : 
                        p2 = GTOBot(p2_hand, set(), p1_bank)
                        print("Player 2 is GTO bot")
            else:
                match(bot1):
                    case "basic" : 
                        p2 = basicBot(p1_hand, set(), p1_bank)
                        print("Player 2 is basic bot")
                    case "minimax" : 
                        p2 = MinimaxBot(p1_hand, set(), p1_bank)
                        print("Player 2 is Minimax bot")
                    case "mcts" : 
                        p2 = MCTS(p1_hand, set(), p1_bank)
                        print("Player 2 is MCTS bot")
                    case "gto" :
                        p2 = GTOBot(p1_hand, set(), p1_bank) 
                        print("Player 2 is GTO bot")

                match(bot2):
                    case "basic" : 
                        p1 = basicBot(p2_hand, set(), p2_bank)
                        print("Player 1 is basic bot")
                    case "minimax" : 
                        p1 = MinimaxBot(p2_hand, set(), p2_bank)
                        print("Player 1 is Minimax Bot")
                    case "mcts" : 
                        p1 = MCTS(p2_hand, set(), p2_bank)
                        print("Player 1 is MCTS bot")
                    case "gto" : 
                        p1 = GTOBot(p2_hand, set(), p2_bank)
                        print("Player 1 is GTO bot")

            # Plays a round             
            p1_bank, p2_bank, delta1, delta2, folding_counter1, folding_tracker1, folding_counter2, folding_tracker2, p1_wins, p2_wins = main(p1, p2, folding_counter1, folding_tracker1, folding_counter2, folding_tracker2, p1_wins, p2_wins, bot1, bot2)

            # Attributes profit to correct player
            if(hand % 2 == 0):
                p1_profit.append(delta2)
                p2_profit.append(delta1)
            else:
                p1_profit.append(delta1)
                p2_profit.append(delta2)

            # Increments number of hands played for this game
            hand += 1
            total_hands += 1
            if p1_bank <= 0:
                print("P2 wins!")
                if(hand % 2 == 0):
                    p1_game_wins += 1
                else:
                    p2_game_wins += 1
                break
            elif p2_bank <= 0:
                print("P1 wins!")
                if(hand % 2 == 0):
                    p2_game_wins += 1
                else:
                    p1_game_wins += 1
                break
            else:
                print(f"After hand {hand}, P1 bank: {p1_bank}  P2 bank: {p2_bank}\n")
    
    # Average profit per hand
    print(f"Player 1 was {bot1} implementation, and had an average profit per hand of {sum(p1_profit) / len(p1_profit)} over {total_hands} hands (Std dev: {statistics.stdev(p1_profit)})")
    print(f"Player 2 was {bot2} implementation, and had an average profit per hand of {sum(p2_profit) / len(p2_profit)} over {total_hands} hands (Std dev: {statistics.stdev(p2_profit)})\n")
    # Game win rate and hand win rate
    print(f"Games played: {rounds}. {bot1} game win rate: {p1_game_wins/rounds*100} %  Hand win rate: {p1_wins/total_hands*100} %")
    print(f"Games played: {rounds}. {bot2} game win rate: {p2_game_wins/rounds*100} %  Hand win rate: {p2_wins/total_hands*100} %\n")
    
    # Fold accuracy
    try:
        total_folds1 = sum(folding_tracker1.values())
        print(f"Fold accuracy for {bot1} model: {folding_counter1 / total_folds1 * 100} % of {total_folds1} folds were accurate. Folds per stage: {folding_tracker1}")
    except:
        print(f"{bot1} model did not fold")
    try:
        total_folds2 = sum(folding_tracker2.values())
        print(f"Fold accuracy for {bot2} model: {folding_counter2 / total_folds2 * 100} % of {total_folds2} folds were accurate. Folds per stage: {folding_tracker2}")
    except:
        print(f"{bot2} model did not fold")

    # Plots profit of player 1
    x_values = [i for i in range(1, total_hands + 1)]
    p1_rolling_profit = [p1_profit[0]]
    for i in range(1, total_hands):
        p1_rolling_profit.append(p1_rolling_profit[i - 1] + p1_profit[i])

    # Create subplots: 2 rows, 1 column
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # Player 1 plot
    x_values = [i for i in range(1, total_hands + 1)]
    p1_rolling_profit = [p1_profit[0]]
    for i in range(1, total_hands):
        p1_rolling_profit.append(p1_rolling_profit[i - 1] + p1_profit[i])

    axes[0].plot(x_values, p1_rolling_profit)
    axes[0].set_ylabel("Rolling profit/loss ($)")
    axes[0].set_title("Profit over time of Player 1")

    # Player 2 plot
    p2_rolling_profit = [p2_profit[0]]
    for i in range(1, total_hands):
        p2_rolling_profit.append(p2_rolling_profit[i - 1] + p2_profit[i])

    axes[1].plot(x_values, p2_rolling_profit)
    axes[1].set_xlabel("Round")
    axes[1].set_ylabel("Rolling profit/loss ($)")
    axes[1].set_title("Profit over time of Player 2")
    
    end_time = time.time()
    print(f"Total testing time was: {end_time - start_time} for {rounds} game and {total_hands} hands")
    
    # Adjust layout to avoid overlap
    plt.tight_layout()
    plt.show()


