from enum import Enum

class Suit(Enum):
    HEARTS = 0
    DIAMONDS = 1
    CLUBS = 2
    SPADES = 3

class Rank(Enum):
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
    ACE = 14

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
