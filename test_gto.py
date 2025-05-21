from poker_main import Deck
from GTO import GTOBot
from basic_bot import basicBot

deck = Deck()
sb_hand, bb_hand = deck.deal_pre_flop()

sb = GTOBot(sb_hand, set(), 100, position="SB")
bb = basicBot(bb_hand, set(), 100)

print("SB (GTO) hand:", sb_hand)
print("BB (basic) hand:", bb_hand)
sb_move = sb.choose_move("PF", 1, 0, 0, bb.bank)
print("SB action:", sb_move)