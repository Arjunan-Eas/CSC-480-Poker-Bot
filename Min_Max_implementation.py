from dataclasses import dataclass
from poker_main import evaluate_hand

@dataclass
class MinimaxBot:
    hole_cards: set[str]
    community_cards: set[str]
    bank: float

    def draw_card(self) -> set[str]:
        return set()

    def change_bank(self, amount: int):
        self.bank += amount

    def choose_move(self, game_phase: str, minimum_bet: int, current_bet: int, pot: int) -> tuple[str, int]:
        best_score, best_move = self.minimax(self.hole_cards, self.community_cards, current_bet, pot, True, 2)
        if best_move == "fold":
            return "fold", 0
        elif best_move == "call":
            return "call", current_bet
        elif best_move == "raise":
            return "raise", current_bet + minimum_bet
        return "check", 0 #pushing

    def minimax(self, hole_cards, community_cards, current_bet, pot, maximizing, depth):
        if depth == 0:
            score = self.evaluate_hand_strength(hole_cards, community_cards)
            return score, None

        actions = self.get_legal_actions(current_bet)
        best_move = None

        if maximizing:
            best_score = float('-inf')
            for action in actions:
                score = self.simulate_action(hole_cards, community_cards, action)
                next_score, _ = self.minimax(hole_cards, community_cards, current_bet, pot, False, depth - 1)
                if next_score > best_score:
                    best_score = next_score
                    best_move = action
            return best_score, best_move
        else:
            best_score = float('inf')
            for action in actions:
                score = self.simulate_action(hole_cards, community_cards, action)
                next_score, _ = self.minimax(hole_cards, community_cards, current_bet, pot, True, depth - 1)
                if next_score < best_score:
                    best_score = next_score
                    best_move = action
            return best_score, best_move

    def evaluate_hand_strength(self, hole_cards, community_cards):
        full_hand = hole_cards.union(community_cards)
        rank, _ = evaluate_hand(full_hand)
        return 10 - rank

    def get_legal_actions(self, current_bet):
        if current_bet == 0:
            return ["check", "raise"]
        else:
            return ["call", "fold"]

    def simulate_action(self, hole_cards, community_cards, action):
        return self.evaluate_hand_strength(hole_cards, community_cards)
