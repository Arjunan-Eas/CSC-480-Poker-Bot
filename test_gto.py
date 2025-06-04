from GTO import GTOBot
from poker_main import evaluate_hand

def test_preflop_open():
    bot = GTOBot({"AS", "AD"}, set(), 200, "SB")
    move, amt = bot.choose_move("PF", 1, 0, 0, 200)
    assert move in {"bet", "check", "fold", "call", "raise"}, f"Invalid move: {move}"
    print(f"Preflop AA, SB: {move}, {amt}")

def test_flop_bucket():
    bot = GTOBot({"AS", "KD"}, {"2H", "8C", "QS"}, 200, "SB")
    move, amt = bot.choose_move("F", 1, 0, 10, 200)
    print(f"Flop, AK, {move}, {amt}")

def test_vs_minimax():
    from Minimax import MinimaxBot
    from poker_main import STARTING_MONEY
    bot1 = GTOBot({"AS", "AD"}, set(), STARTING_MONEY, "SB")
    bot2 = MinimaxBot({"KH", "KS"}, set(), STARTING_MONEY)
    move1, amt1 = bot1.choose_move("PF", 1, 0, 0, STARTING_MONEY)
    move2, amt2 = bot2.choose_move("PF", 1, amt1, amt1, STARTING_MONEY)
    print(f"GTO: {move1}, {amt1} | Minimax: {move2}, {amt2}")

if __name__ == "__main__":
    test_preflop_open()
    test_flop_bucket()
    test_vs_minimax()
    print("All GTOBot tests passed.")
