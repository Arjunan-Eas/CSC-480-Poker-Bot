from __future__ import annotations
import json, random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, Set



RANK_TO_VALUE = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}

_DATA = Path(__file__).parent / "data" / "preflop_hunl.json"
if _DATA.exists():
    CHART: Dict[str, Dict[str, Dict[str, float]]] = json.loads(_DATA.read_text())
else:
    CHART = {"SB": {}, "BB": {}}
    print("[GTO] Warning – preflop_hunl.json missing, bot will auto‑fold.")

def key_of(cards: Set[str]) -> str:
    """Convert two‑card set to 169‑grid key: 'AKo', 'QJs', '77', …"""
    a, b = sorted(cards, key=lambda c: RANK_TO_VALUE[c[0]], reverse=True)
    if a[0] == b[0]:
        return a[0] * 2
    return a[0] + b[0] + ("s" if a[1] == b[1] else "o")

def sample(dist: Dict[str, float]) -> str:
    r, s = random.random(), 0.0
    for k, p in dist.items():
        s += p
        if r <= s:
            return k
    return list(dist)[-1]   # fallback

@dataclass
class GTOBot:
    hole_cards: Set[str]
    community_cards: Set[str]
    bank: float
    position: str             

    def draw_card(self) -> Set[str]:
        return set()       

    def change_bank(self, amt: int):
        self.bank += amt

    def choose_move(
        self,
        phase: str,
        min_bet: int,
        cur_bet: int,
        pot: int,
        opp_bank: int
    ) -> Tuple[str, int]:
        if phase == "PF":
            return self._preflop(min_bet, cur_bet)
        return self._postflop_stub(cur_bet, pot, min_bet)

    def _preflop(self, min_bet: int, cur_bet: int) -> Tuple[str, int]:
        strat = CHART[self.position].get(key_of(self.hole_cards), {"fold": 1.0})
        act   = sample(strat)

        # unopened pot
        if cur_bet == 0:
            if act == "open":
                return "bet", 3 * min_bet
            return "check", 0   
        # facing an open
        if act == "fold":
            return "fold", 0
        if act == "call":
            return "call", cur_bet
        if act in ("3bet", "4bet"):
            raise_to = max(cur_bet * 3, 9 * min_bet)
            return "raise", raise_to
        return "fold", 0      

    # place holder for post flop, turn, river, etc
    def _postflop_stub(
        self,
        cur_bet: int,
        pot: int,
        min_bet: int
    ) -> Tuple[str, int]:


        if cur_bet == 0:
            return "check", 0
        return random.choice([("call", cur_bet), ("fold", 0)])
