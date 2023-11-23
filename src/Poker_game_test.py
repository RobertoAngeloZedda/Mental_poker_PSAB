from Poker_game import *
import random

p1 = Player('p1')
p2 = Player('p2')
p3 = Player('p3')
p4 = Player('p4')
p5 = Player('p5')
p6 = Player('p6')
p7 = Player('p7')
p8 = Player('p8')
players = [p1, p2, p3, p4, p5, p6, p7, p8]

deck = [Card(suit, rank) for suit in Suit for rank in Rank]
random.shuffle(deck)

game = Poker_game(players, deck)
game.play()