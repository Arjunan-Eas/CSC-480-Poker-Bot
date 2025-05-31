import tkinter as tk
from tkinter import messagebox
import random
from typing import Set, Tuple, List
from basic_bot import basicBot
from MCTS import MCTS
from Minimax import MinimaxBot
from GTO import GTOBot
from poker_main import royal_flush, straight_flush, duplicates

SUITS = ['H', 'D', 'C', 'S']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
RANK_TO_VALUE = {r: i for i, r in enumerate(RANKS, start=2)}
RESULT_TO_HAND = {
    1: "Royal Flush", 2: "Straight Flush", 3: "Four of a Kind", 4: "Full House",
    5: "Flush", 6: "Straight", 7: "Three of a Kind", 8: "Two Pair", 9: "Pair", 10: "High Card"
}
DECK = [r + s for s in SUITS for r in RANKS]



def evaluate_hand(cards: Set[str]) -> Tuple[int, List[int]]:
    value_counter, suit_counter = {}, {}
    for card in cards:
        v, s = RANK_TO_VALUE[card[0]], card[1]
        value_counter[v] = value_counter.get(v, 0) + 1
        suit_counter[s] = suit_counter.get(s, 0) + 1
    rf = royal_flush(value_counter, suit_counter, cards)
    if rf: return rf
    dup = duplicates(value_counter)
    sf = straight_flush(value_counter, suit_counter, cards)
    return dup if sf is None or dup[0] == 3 else sf

def choose_winner(p0: Tuple[int, List[int]], p1: Tuple[int, List[int]]) -> int:
    if p0[0] == p1[0]:
        while p0[1] and p1[1]:
            k0, k1 = p0[1].pop(), p1[1].pop()
            if k0 != k1:
                return 1 if k0 > k1 else 0
        return -1
    return 1 if p0[0] < p1[0] else 0

def breakdown_result(result: Tuple[int, List[int]]) -> str:
    rank = RESULT_TO_HAND[result[0]]
    return f"{rank} with {result[1]}"

class PokerGUI:
    def __init__(self, master, bot):
        self.master = master
        self.bot = bot
        self.user_bank = 1000
        self.bot.bank = 1000
        self.pot = 0
        self.current_bet = 0
        self.phase = "PF"
        self.deck = DECK[:]
        random.shuffle(self.deck)
        self.awaiting_bot_action = False
        self.setup_ui()
        self.start_hand()

    def setup_ui(self):
        self.master.title("Poker Hand")

        tk.Label(self.master, text="Poker Hand GUI", font=("Helvetica", 16)).pack()
        self.community_label = tk.Label(self.master, text="Community Cards: ")
        self.community_label.pack()
        self.player_hand_label = tk.Label(self.master, text="Your Hand: ")
        self.player_hand_label.pack()
        self.bot_hand_label = tk.Label(self.master, text="Bot Hand: ")
        self.bot_hand_label.pack()
        self.bot_action_label = tk.Label(self.master, text="Bot Action: ")
        self.bot_action_label.pack()
        self.pot_label = tk.Label(self.master, text="Pot: $0")
        self.pot_label.pack()
        self.bank_label = tk.Label(self.master, text="Your Bank: $1000")
        self.bank_label.pack()

        self.bet_entry = tk.Entry(self.master)
        self.bet_entry.pack()

        self.actions_frame = tk.Frame(self.master)
        self.actions_frame.pack()
        tk.Button(self.actions_frame, text="Check", command=self.player_check).grid(row=0, column=0)
        tk.Button(self.actions_frame, text="Bet", command=self.player_bet).grid(row=0, column=1)
        tk.Button(self.actions_frame, text="Fold", command=self.player_fold).grid(row=0, column=2)

    def deal_cards(self):
        self.player_hand = {self.deck.pop(), self.deck.pop()}
        self.bot.hole_cards = {self.deck.pop(), self.deck.pop()}

    def start_hand(self):
        self.user_bank -= 25
        self.bot.bank -= 50
        self.pot = 75
        self.current_bet = 50
        self.deck = DECK[:]
        random.shuffle(self.deck)
        self.community_cards = set()
        self.phase = "PF"
        self.deal_cards()
        self.update_ui()

    def update_ui(self):
        self.community_label.config(text=f"Community Cards: {' '.join(self.community_cards)}")
        self.player_hand_label.config(text=f"Your Hand: {' '.join(self.player_hand)}")
        self.pot_label.config(text=f"Pot: ${self.pot}")
        self.bank_label.config(text=f"Your Bank: ${self.user_bank}")
        self.bot_action_label.config(text="Bot Action: Waiting...")
        self.bot_hand_label.config(text="Bot Hand: [Hidden]")

    def player_check(self):
        if self.current_bet == 0:
            self.bot_move()
        else:
            messagebox.showinfo("Error", "You cannot check. A bet has been made.")

    def player_bet(self):
        try:
            amount = int(self.bet_entry.get())
        except ValueError:
            messagebox.showinfo("Error", "Please enter a valid number.")
            return
        if amount > self.user_bank or amount <= 0:
            messagebox.showinfo("Error", "Invalid bet amount.")
            return
        self.pot += amount
        self.user_bank -= amount
        self.current_bet = amount
        self.update_ui()
        self.bot_move()

    def player_fold(self):
        self.bot_hand_label.config(text=f"Bot Hand: {self.bot.hole_cards}")
        self.end_game("You folded. Bot wins!")

    def bot_move(self):
        move, amount = self.bot.choose_move(self.phase, 0, self.current_bet, self.pot, self.user_bank)
        self.bot_action_label.config(text=f"Bot Action: {move} ${amount}")
        if move == "call":
            if self.bot.bank >= amount:
                self.pot += amount
                self.bot.bank -= amount
                self.next_phase()
            else:
                self.bot_hand_label.config(text=f"Bot Hand: {self.bot.hole_cards}")
                self.end_game("Bot tried to call but had insufficient funds. You win!")
        elif move == "check":
            if self.current_bet == 0:
                self.next_phase()
            else:
                self.bot_hand_label.config(text=f"Bot Hand: {self.bot.hole_cards}")
                self.end_game("Bot tried to check illegally. You win!")
        elif move == "fold":
            self.user_bank += self.pot
            self.bot_hand_label.config(text=f"Bot Hand: {self.bot.hole_cards}")
            self.end_game("Bot folded. You win!")
        elif move == "bet":
            self.bot.bank -= amount
            self.next_phase()

    def next_phase(self):
        self.update_ui()
        if self.phase == "PF":
            self.phase = "F"
            self.community_cards = {self.deck.pop(), self.deck.pop(), self.deck.pop()}
        elif self.phase == "F":
            self.phase = "T"
            self.community_cards.add(self.deck.pop())
        elif self.phase == "T":
            self.phase = "R"
            self.community_cards.add(self.deck.pop())
        elif self.phase == "R":
            self.showdown()
            return
        self.current_bet = 0
        self.update_ui()

    def showdown(self):
        self.bot_hand_label.config(text=f"Bot Hand: {' '.join(self.bot.hole_cards)}")
        player_eval = evaluate_hand(self.player_hand | self.community_cards)
        bot_eval = evaluate_hand(self.bot.hole_cards | self.community_cards)
        result = choose_winner(player_eval, bot_eval)
        if result == 1:
            self.user_bank += self.pot
            msg = f"You win! {breakdown_result(player_eval)} beats {breakdown_result(bot_eval)}"
        elif result == 0:
            self.bot.bank += self.pot
            msg = f"Bot wins! {breakdown_result(bot_eval)} beats {breakdown_result(player_eval)}"
        else:
            split = self.pot // 2
            self.user_bank += split
            self.bot.bank += split
            msg = "It's a tie!"
        self.bot_hand_label.config(text=f"Bot Hand: {self.bot.hole_cards}")
        self.end_game(msg)

    def end_game(self, msg):
        self.update_ui()
        messagebox.showinfo("Game Over", msg)
        self.disable_buttons()

    def disable_buttons(self):
        for widget in self.actions_frame.winfo_children():
            widget.config(state=tk.DISABLED)

def select_bot():
    def launch_game_with_bot(bot_class):
        bot_selection_window.destroy()
        root = tk.Tk()
        bot = bot_class(set(), set(), 1000)
        app = PokerGUI(root, bot)
        root.mainloop()

    bot_selection_window = tk.Tk()
    bot_selection_window.title("Select Poker Bot")

    tk.Label(bot_selection_window, text="Choose an opponent:", font=("Helvetica", 14)).pack(pady=10)
    tk.Button(bot_selection_window, text="Basic Bot", width=20, command=lambda: launch_game_with_bot(basicBot)).pack(pady=5)
    tk.Button(bot_selection_window, text="MCTS Bot", width=20, command=lambda: launch_game_with_bot(MCTS)).pack(pady=5)
    tk.Button(bot_selection_window, text="Minimax Bot", width=20, command=lambda: launch_game_with_bot(MinimaxBot)).pack(pady=5)
    tk.Button(bot_selection_window, text="GTO Bot", width=20, command=lambda: launch_game_with_bot(GTOBot)).pack(pady=5)

    bot_selection_window.mainloop()

if __name__ == "__main__":
    select_bot()
