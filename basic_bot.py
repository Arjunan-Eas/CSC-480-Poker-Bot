from dataclasses import dataclass

@dataclass
class basicBot:
    hole_cards: set[str]
    community_cards: set[str]
    bank: int

    """
    Basic bot doesn't make any predictions based on cards
    """
    def draw_card(self) -> set[str]:
        pass
    
    """
    Basic bot always either checks or calls
    """
    def choose_move(self, game_phase: str, minimum_bet: int, current_bet: int, pot: int) -> tuple[str, int]:
        if current_bet == 0:
            return "check", 0
        else:
            return "call", current_bet
    
    # Setter for modifying player bank
    def change_bank(self, amount: int):
        self.bank += amount