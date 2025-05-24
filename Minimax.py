import math
import random
import time

class MinimaxBot:
    """
    Minimax-based poker bot with depth-limited search and alpha-beta pruning.
    You can toggle ASCII tree printing with the show_tree flag.
    """
    def __init__(self, hand, community, bank, max_depth=100, show_tree=True):
        # Initialize game state
        self.hole_cards = set(hand)               # Player's hole cards
        self.community_cards = set(community)      # Shared community cards
        self.bank = bank                           # Player's remaining chips
        self.max_depth = max_depth                 # Max search depth
        self.show_tree = show_tree                 # Flag to print α–β tree
        # Prepare a full deck for sampling future cards if needed
        self.deck = [r + s for r in "23456789TJQKA" for s in "DCHS"]

    def change_bank(self, amount):
        """Adjust the bot's bank by a given amount."""
        self.bank += amount

    def choose_move(self, game_phase, minimum_bet, current_bet, pot, opponent_bank):
        """
        Decide next action, and optionally print an ASCII α–β search tree.
        Returns a tuple: (decision_str, bet_amount)
        """
        # Header for tree output
        if self.show_tree:
            print("\nAlpha-Beta Search Tree:")

        # Run the recursive minimax search
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
            beta=math.inf,
            indent=""
        )

        # Convert score in [-1,1] to win probability
        win_rate = max(0.0, min(1.0, (score + 1) / 2))
        if self.show_tree:
            print(f"\nMinimax heuristic: {win_rate*100:.1f}% chance at {game_phase}")

        # Decide final bet using EV-based strategy
        decision, amount = self.bet_strategy(
            game_phase, current_bet, pot, win_rate, minimum_bet, opponent_bank
        )
        if self.show_tree:
            print(f"Decision: {decision}, Bet: ${amount}\n")
        return decision, amount

    def _minimax(self, state, depth, maximizing, alpha, beta, indent):
        """
        Core recursive minimax with alpha-beta pruning.
        Prints tree nodes if show_tree=True.
        Returns (value, best_move).
        """
        phase, hole, community, min_bet, curr_bet, pot, opp_bank, bank = state

        # Terminal or depth limit: evaluate and return
        if depth == 0 or self.is_terminal(state):
            value = self.evaluate_state(state)
            if self.show_tree:
                print(f"{indent}└─ [Leaf eval] phase={phase} score={value:.4f}")
            return value, None

        # Print node header
        if self.show_tree:
            node_type = "Max" if maximizing else "Min"
            print(f"{indent}{node_type} Node: phase={phase} depth={depth} α={alpha:.4f} β={beta:.4f}")

        best_move = None
        best_val = -math.inf if maximizing else math.inf

        # Generate all legal continuations
        successors = self.get_successors(state)
        for i, (move, next_state) in enumerate(successors):
            is_last = (i == len(successors) - 1)
            branch = "└─" if is_last else "├─"
            if self.show_tree:
                print(f"{indent}{branch} Try move {move}")

            # Recurse
            child_val, _ = self._minimax(
                next_state,
                depth - 1,
                not maximizing,
                alpha,
                beta,
                indent + ("   " if is_last else "|  ")
            )
            if self.show_tree:
                print(f"{indent}{branch} Move {move} → score={child_val:.4f}")

            # Alpha-beta logic
            if maximizing:
                if child_val > best_val:
                    best_val, best_move = child_val, move
                alpha = max(alpha, best_val)
                if alpha >= beta:
                    if self.show_tree:
                        print(f"{indent}{branch} Prune (α={alpha:.4f} ≥ β={beta:.4f})")
                    break
            else:
                if child_val < best_val:
                    best_val, best_move = child_val, move
                beta = min(beta, best_val)
                if beta <= alpha:
                    if self.show_tree:
                        print(f"{indent}{branch} Prune (β={beta:.4f} ≤ α={alpha:.4f})")
                    break

        return best_val, best_move

    def get_successors(self, state):
        """
        Generate possible moves: fold, check/bet when facing no bet,
        or call/raise when facing a bet.
        """
        phase, hole, community, min_bet, curr_bet, pot, opp_bank, bank = state
        successors = []

        # Always can fold
        successors.append((('fold', 0), self._apply_move(state, ('fold', 0))))

        if curr_bet == 0:
            # Open bets of 1×,2×,3× min_bet
            for mul in (1, 2, 3):
                amt = min(bank, min_bet * mul)
                successors.append((('bet', amt), self._apply_move(state, ('bet', amt))))
            # Option to check
            successors.append((('check', 0), self._apply_move(state, ('check', 0))))
        else:
            # Facing a bet: can call
            successors.append((('call', curr_bet), self._apply_move(state, ('call', curr_bet))))
            # Or raise by 1× or 2× min_bet
            for raise_amt in (curr_bet + min_bet, curr_bet + 2*min_bet):
                if raise_amt <= bank:
                    successors.append((('raise', raise_amt), self._apply_move(state, ('raise', raise_amt))))

        return successors

    def _apply_move(self, state, move):
        """Apply a move to the state, updating bank, pot, and phase."""
        phase, hole, community, min_bet, curr_bet, pot, opp_bank, bank = state
        next_phase = phase
        if move[0] in ('call', 'check', 'bet', 'raise'):
            amount = move[1]
            bank -= amount    # Deduct bet from bank
            pot += amount     # Add bet to pot
            curr_bet = amount
        elif move[0] == 'fold':
            next_phase = 'terminal'  # Hand ends
        return (next_phase, hole, community, min_bet, curr_bet, pot, opp_bank, bank)

    def is_terminal(self, state):
        """Check if the state is terminal (fold or showdown)."""
        phase = state[0]
        return phase == 'terminal' or phase == 'R'

    def evaluate_state(self, state):
        """
        Heuristic evaluation:
        - Pre-flop/early: use hole-card heuristic
        - Post-flop+: use full hand evaluator
        """
        _, hole, community, *_ = state
        combined = set(hole) | set(community)
        if len(combined) < 5:
            raw = self.evaluate_hole_cards(combined)
            return 2 * (raw - 0.5)

        # Full 5+ card hand ranking
        from poker_main import evaluate_hand
        rank, _ = evaluate_hand(combined)
        strength = (11 - rank) / 10
        return 2 * (strength - 0.5)

    def evaluate_hole_cards(self, cards):
        """
        Simple hole-card heuristic:
        - Higher average rank is better
        - Suited bonus
        - Pair bonus
        """
        from poker_main import RANK_TO_VALUE
        vals = [RANK_TO_VALUE[c[0]] for c in cards]
        avg = sum(vals) / len(vals)
        same_suit = len({c[1] for c in cards}) == 1
        counts = {v: vals.count(v) for v in set(vals)}
        pair_bonus = max(counts.values())

        # Normalize average
        score = avg / max(RANK_TO_VALUE.values())
        if same_suit:
            score *= 1.25  # extra for suited cards
        if pair_bonus > 1:
            score *= (1 + pair_bonus / 2)
        return min(1, score)

    def bet_strategy(self, game_phase, current_bet, pot, win_rate, min_bet, opponent_bank):
        """
        EV-based bet-sizing with dynamic risk:
        1. Clamp win rate to <1
        2. Calculate pot odds
        3. Fold if w < odds
        4. Determine hand rank if 5+ cards
        5. Set risk fraction (high for strong hands)
        6. Compute EV-optimal bet
        7. Cap by bank-based risk
        8. Bet or call/raise accordingly
        """
        # 1. Avoid certainty
        w = min(win_rate, 0.99)
        # 2. Pot odds
        total = pot + current_bet
        odds = current_bet / total if total > 0 else 0
        if w < odds:
            return "fold", 0

        # 4. Evaluate full hand if possible
        from poker_main import evaluate_hand
        combined = self.hole_cards | self.community_cards
        rank = None
        if len(combined) >= 5:
            rank, _ = evaluate_hand(combined)

        # 5. Risk fraction
        HIGH_R, LOW_R = 0.50, 0.05
        R = HIGH_R if rank is not None and rank <= 2 else LOW_R
        # 6. EV-optimal
        f = w / (1 - w)
        b_ev = f * pot
        # 7. Bank cap
        b_bank = self.bank * w * R
        b_star = int(math.floor(min(self.bank, b_ev, b_bank)))

        # 8. Final decision
        if current_bet == 0:
            if b_star < min_bet and win_rate > 0.6:
                return "bet", min_bet
            elif b_star < min_bet:
                return "check", 0
            return "bet", b_star

        if b_star <= current_bet:
            return "call", current_bet
        return "raise", min(self.bank, max(b_star, current_bet + min_bet))