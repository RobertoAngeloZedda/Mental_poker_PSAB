from Poker_game import *
import random

p1 = Player('p1')
p2 = Player('p2')
players = [p1, p2]

deck = [Card(suit, rank) for suit in Suit for rank in Rank]
random.shuffle(deck)

game = Poker_game(players, deck)
game.play()