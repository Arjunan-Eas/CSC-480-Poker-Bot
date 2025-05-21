from dataclasses import dataclass

@dataclass
class exampleBot:
    hole_cards: set[str]
    community_cards: set[str]
    bank: float

    """
    You can implement this function however you see fit, but at a base level
    you should have some way of speculatively drawing cards based on the
    hole cards you have and what community cards are visible
    """
    def draw_card(self) -> set[str]:
        pass
    

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

    Your bot has a maximum of 10 seconds to decide what its next move will be
    """
    def choose_move(self, game_phase: str, minimum_bet: int, current_bet: int, pot: int, opponent_bank: int) -> tuple[str, int]:
        pass
    
    # Setter for modifying player bank
    def change_bank(self, amount: int):
        self.bank += amount
    # Feel free to include any other utility methods you want