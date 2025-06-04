# Minimax.py

import math
import time

class MinimaxBot:
    """
    Two-player minimax with α–β pruning and iterative deepening (time-limited).
    If show_tree=True, prints the α–β tree after 1 s, then again fully for the last depth.
    """
    def __init__(self, hand, community, bank, max_depth=None, show_tree=True):
        # stash hole cards, community cards, and bank
        self.hole_cards = set(hand)
        self.community_cards = set(community)
        self.bank = bank

        # if True, we'll print the α–β tree after we finish iterative deepening
        self.show_tree = show_tree

        # one-second time cutoff per move
        self.time_limit = 1.0
        self.start_time = None

        # keep track of the best (score, move) found so far
        self.best_score_so_far = 0.0
        self.best_move_so_far = None

    def change_bank(self, amount):
        self.bank += amount

    def choose_move(self, game_phase, minimum_bet, current_bet, pot, opponent_bank):
        initial_state = (
            game_phase,
            frozenset(self.hole_cards),
            frozenset(self.community_cards),
            minimum_bet,
            current_bet,
            pot,
            opponent_bank,
            self.bank
        )

        # remember if the user wanted the tree printed
        want_tree = self.show_tree

        # reset timing and best-so-far
        self.start_time = time.time()
        self.best_score_so_far = 0.0
        self.best_move_so_far = None

        depth = 1
        last_completed_depth = 0

        # ───── ITERATIVE DEEPENING (1 s cutoff) ─────
        while True:
            if time.time() - self.start_time > self.time_limit:
                break

            # suppress tree printing during intermediate passes
            self.show_tree = False

            score, move = self._minimax(
                state=initial_state,
                depth=depth,
                maximizing=True,
                alpha=-math.inf,
                beta=math.inf,
                indent=""
            )

            # if we finished this depth in time, record it
            if time.time() - self.start_time <= self.time_limit:
                self.best_score_so_far = score
                self.best_move_so_far = move
                last_completed_depth = depth
                depth += 1
            else:
                # we ran out of time partway through, so ignore this result
                break

        # if user wants the tree and we have at least one completed depth:
        if want_tree and self.best_move_so_far is not None:
            # disable cutoff so the final tree prints fully
            old_time_limit = self.time_limit
            self.time_limit = float("inf")
            self.show_tree = True

            # re-run at last_completed_depth to print the full tree
            self._minimax(
                state=initial_state,
                depth=last_completed_depth,
                maximizing=True,
                alpha=-math.inf,
                beta=math.inf,
                indent=""
            )

            # restore settings
            self.show_tree = False
            self.time_limit = old_time_limit

        # decide what to return
        if self.best_move_so_far is None:
            # never completed any depth, so just evaluate once
            final_score = self.evaluate_state(initial_state)
            final_move = ("check", 0)
        else:
            final_score = self.best_score_so_far
            final_move = self.best_move_so_far

        # map score in [-1,1] to win probability [0,1]
        win_rate = max(0.0, min(1.0, (final_score + 1) / 2))
        print(f"\nMinimax heuristic: {win_rate*100:.1f}% chance at {game_phase}")

        # pick bet size based on EV
        decision, amount = self.bet_strategy(
            game_phase, current_bet, pot, win_rate, minimum_bet, opponent_bank
        )
        print(f"Decision: {decision}, Bet: ${amount}\n")
        return decision, amount

    def _minimax(self, state, depth, maximizing, alpha, beta, indent):
        # 1) time cutoff
        if time.time() - self.start_time > self.time_limit:
            val = self.evaluate_state(state)
            if self.show_tree:
                print(f"{indent}└─ [Time cutoff eval] score={val:.4f}")
            return val, None

        phase, hole, community, min_bet, curr_bet, pot, opp_bank, bank = state

        # 2) depth limit or terminal state
        if depth == 0 or self.is_terminal(state):
            val = self.evaluate_state(state)
            if self.show_tree:
                print(f"{indent}└─ [Leaf eval] phase={phase} score={val:.4f}")
            return val, None

        # 3) otherwise this is a decision node
        if self.show_tree:
            node_type = "Max" if maximizing else "Min"
            print(f"{indent}{node_type} Node: phase={phase} depth={depth} α={alpha:.4f} β={beta:.4f}")

        best_move = None
        best_val = -math.inf if maximizing else math.inf

        successors = self.get_successors(state)
        for i, (move, next_state) in enumerate(successors):
            is_last = (i == len(successors) - 1)
            branch = "└─" if is_last else "├─"
            if self.show_tree:
                print(f"{indent}{branch} Try move {move}")

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
        phase, hole, community, min_bet, curr_bet, pot, opp_bank, bank = state
        successors = []

        # fold is always an option
        successors.append((('fold', 0), self._apply_move(state, ('fold', 0))))

        if curr_bet == 0:
            # nobody has bet yet, so we can open the betting
            for mul in (1, 2, 3):
                amt = min(bank, min_bet * mul)
                successors.append((('bet', amt), self._apply_move(state, ('bet', amt))))
            successors.append((('check', 0), self._apply_move(state, ('check', 0))))
        else:
            # facing a bet: either call or raise
            successors.append((('call', curr_bet), self._apply_move(state, ('call', curr_bet))))
            for raise_amt in (curr_bet + min_bet, curr_bet + 2 * min_bet):
                if raise_amt <= bank:
                    successors.append((('raise', raise_amt), self._apply_move(state, ('raise', raise_amt))))

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
        return (phase == 'terminal') or (phase == 'R')

    def evaluate_state(self, state):
        from poker_main import evaluate_hand, RANK_TO_VALUE

        _, hole, community, *_ = state
        combined = set(hole) | set(community)

        if len(combined) < 5:
            # use a quick heuristic when we don't have full board yet
            vals = [RANK_TO_VALUE[c[0]] for c in combined]
            avg = sum(vals) / len(vals)
            same_suit = (len({c[1] for c in combined}) == 1)
            counts = {v: vals.count(v) for v in set(vals)}
            pair_bonus = max(counts.values())

            score = avg / max(RANK_TO_VALUE.values())
            if same_suit:
                score *= 1.25
            if pair_bonus > 1:
                score *= (1 + pair_bonus / 2)
            raw = min(1, score)
            return 2 * (raw - 0.5)

        # full evaluator once we have 5+ cards
        rank, _ = evaluate_hand(combined)
        strength = (11 - rank) / 10  # rank=1 => 1.0, rank=10 => 0.1
        return 2 * (strength - 0.5)

    def bet_strategy(self, game_phase, current_bet, pot, win_rate, min_bet, opponent_bank):
        from poker_main import evaluate_hand, RANK_TO_VALUE

        w = min(win_rate, 0.99)
        total = pot + current_bet
        odds = current_bet / total if total > 0 else 0
        if w < odds:
            return "fold", 0

        combined = self.hole_cards | self.community_cards
        rank = None
        if len(combined) >= 5:
            rank, _ = evaluate_hand(combined)

        HIGH_R, LOW_R = 0.25, 0.05
        R = HIGH_R if (rank is not None and rank <= 2) else LOW_R
        f = w / (1 - w) if w < 1 else float('inf')
        b_ev = f * pot
        b_bank = self.bank * w * R
        b_star = int(math.floor(min(self.bank, b_ev, b_bank)))

        if current_bet == 0:
            if b_star < min_bet and win_rate > 0.6:
                return "bet", min_bet
            elif b_star < min_bet:
                return "check", 0
            return "bet", b_star

        if b_star <= current_bet:
            return "call", current_bet
        return "raise", min(self.bank, max(b_star, current_bet + min_bet))
