from dataclasses import dataclass
import random

# Standard deck of cards
ALL_CARDS = [rank + suit for rank in "23456789TJQKA" for suit in "DCHS"]

@dataclass
class MinimaxBot:
    hole_cards: set[str]
    community_cards: set[str]
    bank: float

    def draw_card(self) -> set[str]:
        used = self.hole_cards | self.community_cards
        available = list(set(ALL_CARDS) - used)
        return set(random.sample(available, 1))

    def change_bank(self, amount: int):
        self.bank += amount

    def choose_move(self, game_phase: str, minimum_bet: int, current_bet: int, pot: int, opponent_bank: int) -> tuple[str, int]:
        _, best_move = self.minimax(self.hole_cards, self.community_cards, current_bet, pot, True, 2)

        if best_move == "fold":
            return "fold", 0
        elif best_move == "call":
            return "call", current_bet
        elif best_move == "raise":
            return "raise", current_bet + minimum_bet
        else:
            return "check", 0

    def minimax(self, hole_cards, community_cards, current_bet, pot, is_maximizing, depth):
        if depth == 0 or len(community_cards) == 5:
            return self.evaluate_hand_strength(hole_cards, community_cards), None

        actions = self.get_legal_actions(current_bet)
        best_score = float('-inf') if is_maximizing else float('inf')
        best_action = None

        for action in actions:
            score = self.simulate_action(hole_cards, community_cards, action, pot, current_bet)
            next_score, _ = self.minimax(hole_cards, community_cards, current_bet, pot, not is_maximizing, depth - 1)

            if is_maximizing:
                if next_score > best_score:
                    best_score = next_score
                    best_action = action
            else:
                if next_score < best_score:
                    best_score = next_score
                    best_action = action

        return best_score, best_action

    def evaluate_hand_strength(self, hole, community):
        from poker_main import evaluate_hand
        cards = hole | community
        rank, _ = evaluate_hand(cards)
        return 10 - rank  # Lower rank is stronger

    def get_legal_actions(self, current_bet):
        if current_bet == 0:
            return ["check", "raise"]
        else:
            return ["call", "fold"]

    def simulate_action(self, hole, community, action, pot, current_bet):
        from poker_main import evaluate_hand, choose_winner
        if action == "fold":
            return -pot  # Folding loses pot

        # Simulate opponent hand and full board
        opponent_hand = self.sample_opponent_hand(hole, community)
        full_community = self.simulate_community_cards(hole, community, opponent_hand)

        our_hand = hole | full_community
        opp_hand = opponent_hand | full_community

        our_score = evaluate_hand(our_hand)
        opp_score = evaluate_hand(opp_hand)

        result = choose_winner(our_score, opp_score)
        if result == 1:
            return pot  # win
        elif result == -1:
            return 0  # tie
        else:
            return -pot  # loss

    def sample_opponent_hand(self, our_hand, community):
        used = our_hand | community
        deck = list(set(ALL_CARDS) - used)
        random.shuffle(deck)
        return set(deck[:2])

    def simulate_community_cards(self, our_hand, community, opponent_hand):
        cards_needed = 5 - len(community)
        used = our_hand | community | opponent_hand
        deck = list(set(ALL_CARDS) - used)
        random.shuffle(deck)
        return community | set(deck[:cards_needed])
