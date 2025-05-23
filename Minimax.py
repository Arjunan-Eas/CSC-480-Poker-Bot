import math
import random
import time

class MinimaxBot:
    """
    Minimax-based poker bot with depth-limited search and alpha-beta pruning.
    Uses a simple heuristic on the combined hole+community cards.
    """
    def __init__(self, hand, community, bank, max_depth=10):
        # game state
        self.hole_cards = set(hand)
        self.community_cards = set(community)
        self.bank = bank
        self.max_depth = max_depth
        # full deck for sampling
        self.deck = [r + s for r in "23456789TJQKA" for s in "DCHS"]

    def change_bank(self, amount):
        """Adjust the bot's bank by a given amount."""
        self.bank += amount

    def choose_move(self, game_phase, minimum_bet, current_bet, pot, opponent_bank):
        """
        Decide next action. Runs minimax to get a heuristic score.
        """
        score, move = self._minimax(
            state=(
                game_phase,
                frozenset(self.hole_cards),
                frozenset(self.community_cards),
                minimum_bet,
                current_bet,
                pot,
                opponent_bank,
                self.bank
            ),
            depth=self.max_depth,
            maximizing=True,
            alpha=-math.inf,
            beta=math.inf
        )
        win_rate = max(0.0, min(1.0, (score + 1) / 2))
        print(f"Minimax heuristic: {win_rate*100:.1f}% chance at {game_phase}")
        decision, amount = self.bet_strategy(
            game_phase, current_bet, pot, win_rate, minimum_bet, opponent_bank
        )
        print(f"Decision: {decision}, Bet: ${amount}\n")
        return decision, amount

    def _minimax(self, state, depth, maximizing, alpha, beta):
        (phase, hole, community, min_bet, curr_bet, pot, opp_bank, bank) = state
        if depth == 0 or self.is_terminal(state):
            return self.evaluate_state(state), None

        best_move = None
        if maximizing:
            value = -math.inf
            for move, next_state in self.get_successors(state):
                score, _ = self._minimax(next_state, depth-1, False, alpha, beta)
                if score > value:
                    value, best_move = score, move
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value, best_move
        else:
            value = math.inf
            for move, next_state in self.get_successors(state):
                score, _ = self._minimax(next_state, depth-1, True, alpha, beta)
                if score < value:
                    value, best_move = score, move
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value, best_move

    def get_successors(self, state):
        phase, hole, community, min_bet, curr_bet, pot, opp_bank, bank = state
        successors = []
        # Fold option
        successors.append((('fold', 0), self._apply_move(state, ('fold', 0))))
        # Call or check option
        act = ('call', curr_bet) if curr_bet > 0 else ('check', 0)
        successors.append((act, self._apply_move(state, act)))
        return successors

    def _apply_move(self, state, move):
        phase, hole, community, min_bet, curr_bet, pot, opp_bank, bank = state
        next_phase = phase
        if move[0] in ('call', 'check', 'bet', 'raise'):
            amount = move[1]
            bank -= amount
            pot += amount
            curr_bet = amount
        elif move[0] == 'fold':
            next_phase = 'terminal'
        return (next_phase, hole, community, min_bet, curr_bet, pot, opp_bank, bank)

    def is_terminal(self, state):
        phase = state[0]
        return phase == 'terminal' or phase == 'R'

    def evaluate_state(self, state):
        """
        Evaluate current state: use simple heuristic pre-flop/early (fewer than 5 cards),
        otherwise use full 5-card hand evaluator from poker_main.
        """
        _, hole, community, *_ = state
        combined = set(hole) | set(community)
        if len(combined) < 5:
            raw = self.evaluate_hole_cards(combined)
            return 2 * (raw - 0.5)
        from poker_main import evaluate_hand
        rank, _ = evaluate_hand(combined)
        strength = (11 - rank) / 10
        return 2 * (strength - 0.5)

    def evaluate_hole_cards(self, cards):
        from poker_main import RANK_TO_VALUE
        vals = [RANK_TO_VALUE[c[0]] for c in cards]
        avg = sum(vals) / len(vals)
        same_suit = len({c[1] for c in cards}) == 1
        counts = {v: vals.count(v) for v in set(vals)}
        pair_bonus = max(counts.values())
        score = avg / max(RANK_TO_VALUE.values())
        if same_suit:
            score *= 1.25
        if pair_bonus > 1:
            score *= (1 + pair_bonus/2)
        return min(1, score)

    def bet_strategy(self, game_phase, current_bet, pot, win_rate, min_bet, opponent_bank):
        """
        EV-based bet-sizing with dynamic risk fractions:
        - Only aggressively bet (higher R) on top-tier hands (royal or straight flush)
        - For all other hands, use a conservative risk fraction

        1. Clamp win_rate to avoid certainty
        2. Pot odds: O = C / (P + C)
        3. Fold if w < O
        4. Determine actual hand rank if board complete
        5. Select risk fraction R: high_R for rank ≤2, low_R otherwise
        6. Compute EV-optimal fraction f = w/(1-w)
        7. b_ev = f * P
        8. b_bank = B * w * R
        9. Final b* = min(B, b_ev, b_bank)
        10. No bet: bet b* or check
        11. Facing bet: call if b* ≤ C, else raise
        """
        # 1. Avoid 100% certainty
        w = min(win_rate, 0.99)
        # 2. Pot odds
        total = pot + current_bet
        odds = current_bet / total if total > 0 else 0
        if w < odds:
            return "fold", 0
        # 4. Actual hand rank (if flop or later)
        from poker_main import evaluate_hand
        combined = self.hole_cards | self.community_cards
        # If fewer than 5 cards, rank = None
        rank = None
        if len(combined) >= 5:
            rank, _ = evaluate_hand(combined)
        # 5. Dynamic risk fraction
        HIGH_R = 0.75   # allow up to 50% of bank on very strong hands
        LOW_R = 0.05   # limit to 5% otherwise
        R = HIGH_R if rank is not None and rank <= 2 else LOW_R
        # 6. EV fraction
        f = w / (1 - w)
        # 7. EV-based bet
        b_ev = f * pot
        # 8. Bank-based cap
        b_bank = self.bank * w * R
        # 9. Final bet size
        b_star = min(self.bank, b_ev, b_bank)
        b_star = int(math.floor(b_star))
        # 10. No current bet
        if current_bet == 0:
            if b_star < min_bet:
                return "check", 0
            return "bet", b_star
        # 11. Facing bet
        if b_star <= current_bet:
            return "call", current_bet
        raise_amt = min(self.bank, max(b_star, current_bet + min_bet))
        return "raise", raise_amt
