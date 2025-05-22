from dataclasses import dataclass

@dataclass
class basicBot:
    hole_cards: set[str]
    community_cards: set[str]
    bank: float

    """
    Basic bot doesn't make any predictions based on cards
    """
    def draw_card(self) -> set[str]:
        pass
    
    """
    Basic bot always either checks or calls
    """
    def choose_move(self, game_phase: str, minimum_bet: int, current_bet: int, pot: int, opponent_bank: int) -> tuple[str, int]:
        if current_bet == 0:
            return "check", 0
        else:
            if(current_bet <= self.bank):
                return "call", current_bet
            else:
                if(self.bank >= 0):
                    return "call", self.bank
                else:
                    return "fold", 0
    
    # Setter for modifying player bank
    def change_bank(self, amount: int):
        self.bank += amount