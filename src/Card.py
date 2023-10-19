from enum import Enum

class Suit(Enum):
    HEARTS = 0
    DIAMONDS = 1
    CLUBS = 2
    SPADES = 3

class Rank(Enum):
    ACE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13

class Card:
    def __init__(self, suit, rank):
        if not isinstance(suit, Suit):
            raise ValueError("Invalid suit")
        if not isinstance(rank, Rank):
            raise ValueError("Invalid rank")
        self.suit = suit
        self.rank = rank

    def __str__(self):
        return f"{self.rank.name} OF {self.suit.name}"
    
    #def get_suit(self):
    #    return self.suit
    
    #def get_rank(self):
    #    return self.rank
    
    #def get_suit_value(self):
    #    return self.suit.value
    
    #def get_rank_value(self):
    #    return self.rank.value
