from Card import *
from Player import *

class Hand_Ranking(Enum):
    HIGHCARD = 0
    ONEPAIR = 1
    TWOPAIR = 2
    THREEOFAKIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULLHOUSE = 6
    FOUROFAKIND = 7
    STRAIGHTFLUSH = 8
    ROYALFLUSH = 9

hand_ranking_dict = {
    Hand_Ranking.HIGHCARD: 'High Card',
    Hand_Ranking.ONEPAIR: 'One Pair',
    Hand_Ranking.TWOPAIR: 'Two Pair',
    Hand_Ranking.THREEOFAKIND: 'Three of a Kind',
    Hand_Ranking.STRAIGHT: 'Straight',
    Hand_Ranking.FLUSH: 'Flush', 
    Hand_Ranking.FULLHOUSE: 'Full House', 
    Hand_Ranking.FOUROFAKIND: 'Four of a Kind', 
    Hand_Ranking.STRAIGHTFLUSH: 'Straight Flush', 
    Hand_Ranking.ROYALFLUSH: 'Royal Flush', 
}

class Poker_game:
    def __init__(self, players, deck):
        self.players = players
        self.deck = deck
        #self.turn = 0
    
    def print_players(self):
        for i, player in enumerate(self.players):
            print(f"Player {i+1}:  {player.name}")
    
    def deal_cards(self):
        for i in range(5):
            for player in self.players:
                player.hand.append(self.deck.pop())

    # TODO def evaluate_hand(self, hand):
    
    def play(self):
        self.print_players()
        
        best_hand = None
        winning_player = None
        
        self.deal_cards()
        
        #for player in self.players:
        #    evaluated_hand = self.evaluate_hand(player.hand)
        #    
        #    if best_hand is None or evaluated_hand > best_hand:
        #        best_hand = evaluated_hand
        #        winning_player = player

        if winning_player != None:
            print(f"WINNER: {winning_player.name}")
        else:
            print("DRAW")
        
        for player in self.players:
            player.show_hand()