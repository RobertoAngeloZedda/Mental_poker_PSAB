from Card import *

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

def is_royal_flush(hand):
    return is_straight_flush(hand) and (hand[0].rank == Rank.ACE or hand[4].rank == Rank.ACE)

def is_straight_flush(hand):
    return is_straight(hand) and is_flush(hand)

def is_four_of_a_kind(hand): #hand needs to be sorted
    return hand[0].rank == hand[3].rank or hand[1].rank == hand[4].rank

def is_full_house(hand): #hand needs to be sorted
    return (hand[0].rank == hand[2].rank and hand[3].rank == hand[4].rank) or (hand[2].rank == hand[4].rank and hand[0].rank == hand[1].rank)
    
def is_flush(hand):
    return all(card.suit == hand[0].suit for card in hand)

def is_straight(hand):
    return all(hand[i].rank.value - hand[i+1].rank.value == 1 for i in range(len(hand) - 1)) or all(hand[i].rank.value - hand[i+1].rank.value == -1 for i in range(len(hand) - 1))

def is_three_of_a_kind(hand): #hand needs to be sorted
    return hand[0].rank == hand[2].rank or hand[1].rank == hand[3].rank or hand[2].rank == hand[4].rank

def is_two_pair(hand): #hand needs to be sorted
    return (hand[0].rank == hand[1].rank and hand[2].rank == hand[3].rank) or (hand[0].rank == hand[1].rank and hand[3].rank == hand[4].rank) or (hand[1].rank == hand[2].rank and hand[3].rank == hand[4].rank)

def is_one_pair(hand): #hand needs to be sorted
    return any(hand[i].rank == hand[i+1].rank for i in range(len(hand) - 1))

def order_four_of_a_kind_hand(hand):
    ordered_hand = []
    rank_counts = {rank: [] for rank in Rank}

    for card in hand:
        rank_counts[card.rank].append(card)
    
    for rank in Rank:
        if len(rank_counts[rank]) == 4:
            ordered_hand.insert(0, rank_counts[rank][0])
            ordered_hand.insert(0, rank_counts[rank][1])
            ordered_hand.insert(0, rank_counts[rank][2])
            ordered_hand.insert(0, rank_counts[rank][3])
        elif len(rank_counts[rank]) == 1:
            ordered_hand.append(rank_counts[rank][0])

    return ordered_hand

def order_full_house_hand(hand):
    ordered_hand = []
    rank_counts = {rank: [] for rank in Rank}

    for card in hand:
        rank_counts[card.rank].append(card)
    
    for rank in Rank:
        if len(rank_counts[rank]) == 3:
            ordered_hand.insert(0, rank_counts[rank][0])
            ordered_hand.insert(0, rank_counts[rank][1])
            ordered_hand.insert(0, rank_counts[rank][2])
        elif len(rank_counts[rank]) == 2:
            ordered_hand.append(rank_counts[rank][0])
            ordered_hand.append(rank_counts[rank][1])

    return ordered_hand

def order_three_of_a_kind_hand(hand):
    ordered_hand = []
    rank_counts = {rank: [] for rank in Rank}

    for card in hand:
        rank_counts[card.rank].append(card)
    
    for rank in Rank:
        if len(rank_counts[rank]) == 3:
            ordered_hand.insert(0, rank_counts[rank][0])
            ordered_hand.insert(0, rank_counts[rank][1])
            ordered_hand.insert(0, rank_counts[rank][2])
        elif len(rank_counts[rank]) == 1:
            ordered_hand.append(rank_counts[rank][0])

    tmp = ordered_hand[3]
    ordered_hand[3] = ordered_hand[4]
    ordered_hand[4] = tmp
    
    return ordered_hand

def order_two_pair_hand(hand):
    ordered_hand = []
    rank_counts = {rank: [] for rank in Rank}

    for card in hand:
        rank_counts[card.rank].append(card)

    for rank in Rank:
        if len(rank_counts[rank]) == 2:
            ordered_hand.insert(0, rank_counts[rank][0])
            ordered_hand.insert(0, rank_counts[rank][1])
        elif len(rank_counts[rank]) == 1:
            ordered_hand.append(rank_counts[rank][0])
    
    return ordered_hand

def order_one_pair_hand(hand):
    ordered_hand = []
    rank_counts = {rank: [] for rank in Rank}

    for card in hand:
        rank_counts[card.rank].append(card)
    
    for rank in Rank:
        if len(rank_counts[rank]) == 2:
            ordered_hand.insert(0, rank_counts[rank][0])
            ordered_hand.insert(0, rank_counts[rank][1])
        elif len(rank_counts[rank]) == 1:
            ordered_hand.append(rank_counts[rank][0])
    
    tmp = ordered_hand[2]
    ordered_hand[2] = ordered_hand[4]
    ordered_hand[4] = tmp

def sort_hand(hand):
    return sorted(hand, key=lambda x: x.rank.value, reverse=True)

def evaluate_hand(hand):
    sorted_hand = sort_hand(hand)

    if is_royal_flush(hand):
        return (Hand_Ranking.ROYALFLUSH, sorted_hand)

    if is_straight_flush(hand):
        return (Hand_Ranking.STRAIGHTFLUSH, sorted_hand)
    
    if is_four_of_a_kind(sorted_hand):
        return (Hand_Ranking.FOUROFAKIND, order_four_of_a_kind_hand(sorted_hand))
    
    if is_full_house(sorted_hand):
        return (Hand_Ranking.FULLHOUSE, order_full_house_hand(sorted_hand))
    
    if is_flush(sorted_hand):
        return (Hand_Ranking.FLUSH, sorted_hand)
    
    if is_straight(hand):
        return (Hand_Ranking.STRAIGHT, sorted_hand)
    
    if is_three_of_a_kind(sorted_hand):
        return (Hand_Ranking.THREEOFAKIND, order_three_of_a_kind_hand(sorted_hand))
    
    if is_two_pair(sorted_hand):
        return (Hand_Ranking.TWOPAIR, order_two_pair_hand(sorted_hand))
    
    if is_one_pair(sorted_hand):
        return (Hand_Ranking.ONEPAIR, order_one_pair_hand(sorted_hand))
    
    return (Hand_Ranking.HIGHCARD, sorted_hand)

def compare_ordered_hands(hand1, hand2):
        if hand1 == hand2:
            return None
        else:
            for i in range(5):
                if hand1[i].rank.value > hand2[i].rank.value:
                    return hand1
                if hand1[i].rank.value < hand2[i].rank.value:
                    return hand2
