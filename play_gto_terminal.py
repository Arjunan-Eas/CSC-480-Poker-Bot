import random
from GTO import GTOBot
from poker_main import evaluate_hand, choose_winner

RANKS = "23456789TJQKA"
SUITS = "DCHS"
DECK = [r + s for r in RANKS for s in SUITS]

def show(cards):
    return " ".join(sorted(cards))

def deal(deck, n):
    hand = set()
    for _ in range(n):
        hand.add(deck.pop())
    return hand

def user_action(valid, current_bet, min_bet, pot):
    while True:
        print(f"Valid actions: {valid}")
        act = input("Your move: ").strip().lower()
        if act in valid:
            if act in ("bet", "raise"):
                amt = input(f"Enter amount to {act} (minimum {min_bet}, pot is {pot}): ")
                try:
                    amt = int(amt)
                    if amt >= min_bet:
                        return act, amt
                except ValueError:
                    print("Enter a valid number.")
            elif act == "call":
                return act, current_bet
            else:
                return act, 0
        print("Invalid action.")

def print_status(stage, user_hand, comm, pot):
    print(f"\n--- {stage.upper()} ---")
    print(f"Your hand: {show(user_hand)}")
    print(f"Board: {show(comm)}")
    print(f"Pot: {pot}")

def main():
    print("Play Texas Hold'em Heads-Up vs GTO Bot!")
    position = input("Do you want to be SB or BB? (SB/BB): ").strip().upper()
    bot_pos = "BB" if position == "SB" else "SB"

    # Deal
    deck = DECK[:]
    random.shuffle(deck)
    user_hand = deal(deck, 2)
    bot_hand = deal(deck, 2)
    community = set()
    pot = 3   # SB posts 1, BB posts 2
    min_bet = 1
    user_bank, bot_bank = 200, 200
    user_bank -= 1
    bot_bank -= 2
    current_bet = 2  # BB's forced bet

    print_status("Preflop", user_hand, community, pot)

    # --- Preflop Betting ---
    if position == "SB":
        valid = ["fold", "call", "raise"]
        act, amt = user_action(valid, current_bet, min_bet, pot)
        if act == "fold":
            print("You folded. Bot wins the pot!")
            return
        elif act == "call":
            user_bank -= current_bet
            pot += current_bet
        elif act == "raise":
            user_bank -= amt
            pot += amt
            current_bet = amt

        # Bot's turn
        bot = GTOBot(bot_hand, community, bot_bank, bot_pos)
        bot_move, bot_amt = bot.choose_move("PF", min_bet, current_bet, pot, user_bank)
        print(f"GTO Bot action: {bot_move} {bot_amt}")
        if bot_move == "fold":
            print("Bot folded. You win the pot!")
            return
        elif bot_move == "call":
            bot_bank -= current_bet
            pot += current_bet
        elif bot_move in ("raise", "bet"):
            bot_bank -= bot_amt
            pot += bot_amt
            current_bet = bot_amt
            # User response
            valid = ["fold", "call"]
            act, amt = user_action(valid, current_bet, min_bet, pot)
            if act == "fold":
                print("You folded. Bot wins the pot!")
                return
            elif act == "call":
                user_bank -= current_bet
                pot += current_bet

    else:  # User is BB (acts after bot)
        bot = GTOBot(bot_hand, community, bot_bank, bot_pos)
        bot_move, bot_amt = bot.choose_move("PF", min_bet, current_bet, pot, user_bank)
        print(f"GTO Bot action: {bot_move} {bot_amt}")
        if bot_move == "fold":
            print("Bot folded. You win the pot!")
            return
        elif bot_move == "call":
            bot_bank -= current_bet
            pot += current_bet
        elif bot_move in ("raise", "bet"):
            bot_bank -= bot_amt
            pot += bot_amt
            current_bet = bot_amt
        valid = ["fold", "call", "raise"]
        act, amt = user_action(valid, current_bet, min_bet, pot)
        if act == "fold":
            print("You folded. Bot wins the pot!")
            return
        elif act == "call":
            user_bank -= current_bet
            pot += current_bet
        elif act == "raise":
            user_bank -= amt
            pot += amt
            current_bet = amt

    # --- FLOP ---
    community |= deal(deck, 3)
    print_status("Flop", user_hand, community, pot)
    bot.community_cards = community.copy()
    bot.bank = bot_bank

    # User acts first after flop unless all-in, but for this demo user always acts first
    valid = ["check", "bet", "fold"]
    act, amt = user_action(valid, 0, min_bet, pot)
    if act == "fold":
        print("You folded. Bot wins the pot!")
        return
    elif act == "bet":
        user_bank -= amt
        pot += amt
        current_bet = amt
    else:
        current_bet = 0

    # Bot's flop response
    bot.community_cards = community.copy()
    bot.bank = bot_bank
    bot_move, bot_amt = bot.choose_move("F", min_bet, current_bet, pot, user_bank)
    print(f"GTO Bot action: {bot_move} {bot_amt}")
    if bot_move == "fold":
        print("Bot folded. You win the pot!")
        return
    elif bot_move == "call":
        bot_bank -= current_bet
        pot += current_bet
    elif bot_move in ("raise", "bet"):
        bot_bank -= bot_amt
        pot += bot_amt
        current_bet = bot_amt
        # User response
        valid = ["fold", "call"]
        act, amt = user_action(valid, current_bet, min_bet, pot)
        if act == "fold":
            print("You folded. Bot wins the pot!")
            return
        elif act == "call":
            user_bank -= current_bet
            pot += current_bet

    # --- TURN ---
    community |= deal(deck, 1)
    print_status("Turn", user_hand, community, pot)
    bot.community_cards = community.copy()
    bot.bank = bot_bank

    valid = ["check", "bet", "fold"]
    act, amt = user_action(valid, 0, min_bet, pot)
    if act == "fold":
        print("You folded. Bot wins the pot!")
        return
    elif act == "bet":
        user_bank -= amt
        pot += amt
        current_bet = amt
    else:
        current_bet = 0

    bot_move, bot_amt = bot.choose_move("T", min_bet, current_bet, pot, user_bank)
    print(f"GTO Bot action: {bot_move} {bot_amt}")
    if bot_move == "fold":
        print("Bot folded. You win the pot!")
        return
    elif bot_move == "call":
        bot_bank -= current_bet
        pot += current_bet
    elif bot_move in ("raise", "bet"):
        bot_bank -= bot_amt
        pot += bot_amt
        current_bet = bot_amt
        valid = ["fold", "call"]
        act, amt = user_action(valid, current_bet, min_bet, pot)
        if act == "fold":
            print("You folded. Bot wins the pot!")
            return
        elif act == "call":
            user_bank -= current_bet
            pot += current_bet

    # --- RIVER ---
    community |= deal(deck, 1)
    print_status("River", user_hand, community, pot)
    bot.community_cards = community.copy()
    bot.bank = bot_bank

    valid = ["check", "bet", "fold"]
    act, amt = user_action(valid, 0, min_bet, pot)
    if act == "fold":
        print("You folded. Bot wins the pot!")
        return
    elif act == "bet":
        user_bank -= amt
        pot += amt
        current_bet = amt
    else:
        current_bet = 0

    bot_move, bot_amt = bot.choose_move("R", min_bet, current_bet, pot, user_bank)
    print(f"GTO Bot action: {bot_move} {bot_amt}")
    if bot_move == "fold":
        print("Bot folded. You win the pot!")
        return
    elif bot_move == "call":
        bot_bank -= current_bet
        pot += current_bet
    elif bot_move in ("raise", "bet"):
        bot_bank -= bot_amt
        pot += bot_amt
        current_bet = bot_amt
        valid = ["fold", "call"]
        act, amt = user_action(valid, current_bet, min_bet, pot)
        if act == "fold":
            print("You folded. Bot wins the pot!")
            return
        elif act == "call":
            user_bank -= current_bet
            pot += current_bet

    # --- Showdown ---
    print("\n--- SHOWDOWN ---")
    print(f"Your hand: {show(user_hand)}")
    print(f"Bot hand: {show(bot_hand)}")
    print(f"Board: {show(community)}")
    user_eval = evaluate_hand(user_hand | community)
    bot_eval = evaluate_hand(bot_hand | community)
    result = choose_winner(list(user_eval), list(bot_eval))
    if result == 1:
        print("You win the pot!")
    elif result == -1:
        print("Bot wins the pot!")
    else:
        print("It's a tie!")

if __name__ == "__main__":
    main()
