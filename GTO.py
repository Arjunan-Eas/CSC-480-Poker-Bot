import json, random
from dataclasses import dataclass
from pathlib import Path
from typing import Set, Dict, Tuple

RANK_TO_VALUE = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
                 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
DATA_DIR = Path(__file__).parent / "data"

def load_json_chart(filename: str) -> dict:
    p = DATA_DIR / filename
    if not p.exists():
        print(f"[GTO] Warning: {filename} missing.")
        return {}
    return json.loads(p.read_text())

PRE_CHART  = load_json_chart("preflop_hunl.json")
FLOP_CHART = load_json_chart("flop_hunl.json")
TURN_CHART = load_json_chart("turn_hunl.json")
RIVER_CHART= load_json_chart("river_hunl.json")

def hand_key(cards: Set[str]) -> str:
    # Returns key for preflop
    a, b = sorted(cards, key=lambda c: RANK_TO_VALUE[c[0]], reverse=True)
    if a[0] == b[0]:
        return a[0] * 2
    return a[0] + b[0] + ('s' if a[1] == b[1] else 'o')

def equity_bucket(equity: float) -> str:
    # For bucketing on flop/turn/river
    if equity >= 0.85: return "very_strong"
    if equity >= 0.65: return "strong"
    if equity >= 0.4:  return "medium"
    if equity >= 0.2:  return "weak"
    return "very_weak"

def sample(dist: Dict[str, float]) -> str:
    r, s = random.random(), 0.0
    for k, p in dist.items():
        s += p
        if r <= s:
            return k
    return list(dist)[-1]

@dataclass
class GTOBot:
    hole_cards: Set[str]
    community_cards: Set[str]
    bank: float
    position: str = "SB" 

    def draw_card(self) -> Set[str]:
        # Not needed for GTO
        return set()

    def change_bank(self, amount: int):
        self.bank += amount

    def choose_move(self, game_phase: str, minimum_bet: int, current_bet: int, pot: int, opponent_bank: int) -> Tuple[str, int]:
        if game_phase == "PF":
            return self.preflop_action(minimum_bet, current_bet)
        elif game_phase == "F":
            return self.postflop_action("flop", minimum_bet, current_bet, pot)
        elif game_phase == "T":
            return self.postflop_action("turn", minimum_bet, current_bet, pot)
        elif game_phase == "R":
            return self.postflop_action("river", minimum_bet, current_bet, pot)
        else:
            return "fold", 0

    def preflop_action(self, min_bet, cur_bet):
        chart = PRE_CHART.get(self.position, {})
        hand = hand_key(self.hole_cards)
        strat = chart.get(hand, {"fold": 1.0})
        action = sample(strat)
        if cur_bet == 0:
            if action == "open":
                return "bet", 3 * min_bet
            return "check", 0
        # Facing action
        if action == "fold":
            return "fold", 0
        if action == "call":
            return "call", cur_bet
        if action in ("3bet", "4bet"):
            raise_to = max(cur_bet * 3, 9 * min_bet)
            return "raise", raise_to
        return "fold", 0

    def postflop_action(self, street, min_bet, cur_bet, pot):
        # Bucketing by hand strength
        eq = self.estimate_equity()
        bucket = equity_bucket(eq)
        if street == "flop":
            chart = FLOP_CHART.get(self.position, {})
        elif street == "turn":
            chart = TURN_CHART.get(self.position, {})
        elif street == "river":
            chart = RIVER_CHART.get(self.position, {})
        else:
            return "fold", 0
        strat = chart.get(bucket, {"fold": 1.0})
        action = sample(strat)
        if cur_bet == 0:
            if action == "bet":
                return "bet", int(0.66 * pot) if pot > 0 else min_bet
            return "check", 0
        if action == "call":
            return "call", cur_bet
        if action == "raise":
            raise_to = cur_bet + int(0.66 * pot)
            return "raise", raise_to
        if action == "fold":
            return "fold", 0
        return "check", 0

    def estimate_equity(self) -> float:
        # Monte Carlo simulation, quick-and-dirty (sample 100 random hands)
        from poker_main import evaluate_hand, choose_winner
        deck = [r + s for r in "23456789TJQKA" for s in "DCHS"]
        used = self.hole_cards | self.community_cards
        remaining = list(set(deck) - used)
        wins, total = 0, 0
        n_needed = max(0, 5 - len(self.community_cards))
        my_hand = self.hole_cards | self.community_cards
        for _ in range(60):
            sample_cards = random.sample(remaining, n_needed + 2)
            board = self.community_cards | set(sample_cards[:n_needed])
            opp = set(sample_cards[n_needed:])
            mine = self.hole_cards | board
            opp_full = opp | board
            my_eval = evaluate_hand(mine)
            opp_eval = evaluate_hand(opp_full)
            res = choose_winner(list(my_eval), list(opp_eval))
            if res == 1:
                wins += 1
            elif res == -1:
                wins += 0.5
            total += 1
        return wins / total if total else 0.5

