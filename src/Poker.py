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
}

def sort_hand(hand):
    return sorted(sorted(hand, key=lambda x: x.suit.value, reverse=False), key=lambda x: x.rank.value, reverse=False)

def evaluate_hand(hand):
    sorted_hand = sort_hand(hand)

    card1 = None
    card2 = None

    flush_flag = True
    straight_flag = True
    first_pair_count = 1
    second_pair_count = 0

    for i in range(1, 5):
        if i == 4 and straight_flag and sorted_hand[i].rank == Rank.ACE and sorted_hand[i-1].rank == Rank.FIVE:
            straight_flag = True
        elif straight_flag and sorted_hand[i].rank.value != sorted_hand[i-1].rank.value +1:
            straight_flag = False
        
        if flush_flag and sorted_hand[i].suit.value != sorted_hand[i-1].suit.value:
            flush_flag = False
        
        if sorted_hand[i].rank.value == sorted_hand[i-1].rank.value:
            if second_pair_count < 1: 
                card1 = sorted_hand[i]
                first_pair_count += 1
            else: 
                card2 = sorted_hand[i]
                second_pair_count += 1
        else:
            if first_pair_count > 1 and second_pair_count == 0:
                second_pair_count = 1
    
    if first_pair_count == 1: card1 = sorted_hand[4]
    
    if first_pair_count == 4: 
        return (Hand_Ranking.FOUROFAKIND, card1, card2)
    
    elif first_pair_count == 3:
        if second_pair_count == 2: 
            return (Hand_Ranking.FULLHOUSE, card1, card2)
        else: 
            return (Hand_Ranking.THREEOFAKIND, card1, card2)
    
    elif first_pair_count == 2:
        if second_pair_count == 3: 
            return (Hand_Ranking.FULLHOUSE, card1, card2)
        elif second_pair_count == 2: 
            return (Hand_Ranking.TWOPAIR, card2, card1)
        else: 
            return (Hand_Ranking.ONEPAIR, card1, card2)
    
    elif flush_flag and straight_flag: return (Hand_Ranking.STRAIGHTFLUSH, card1, card2)
    elif flush_flag: return (Hand_Ranking.FLUSH, card1, card2)
    elif straight_flag: return (Hand_Ranking.STRAIGHT, card1, card2)
    
    else: return (Hand_Ranking.HIGHCARD, card1, card2)

def same_hand_ranking_result(index1, index2, hand_ranking, best_card1, best_card2, card1, card2):
    match hand_ranking:
        case Hand_Ranking.HIGHCARD:
            if best_card1.rank.value > card1.rank.value:
                return index1
            elif best_card1.rank.value < card1.rank.value:
                return index2
            else:
                if best_card1.suit.value > card1.suit.value:
                    return index1
                elif best_card1.suit.value < card1.suit.value:
                    return index2
            
        case Hand_Ranking.ONEPAIR:
            if best_card1.rank.value > card1.rank.value:
                return index1
            elif best_card1.rank.value < card1.rank.value:
                return index2
            else:
                if best_card1.suit.value > card1.suit.value:
                    return index1
                elif best_card1.suit.value < card1.suit.value:
                    return index2
        
        case Hand_Ranking.TWOPAIR:
            if best_card1.rank.value > card1.rank.value:
                return index1
            elif best_card1.rank.value < card1.rank.value:
                return index2
            else:
                if best_card2.rank.value > card2.rank.value:
                    return index1
                elif best_card2.rank.value < card2.rank.value:
                    return index2
                else:
                    if best_card1.suit.value > card1.suit.value:
                        return index1
                    elif best_card1.suit.value < card1.suit.value:
                        return index2
        
        case Hand_Ranking.THREEOFAKIND:
            if best_card1.rank.value > card1.rank.value:
                return index1
            elif best_card1.rank.value < card1.rank.value:
                return index2
            
        case Hand_Ranking.STRAIGHT:
            if best_card1.rank.value > card1.rank.value:
                return index1
            elif best_card1.rank.value < card1.rank.value:
                return index2
            else:
                if best_card1.suit.value > card1.suit.value:
                    return index1
                elif best_card1.suit.value < card1.suit.value:
                    return index2
            
        case Hand_Ranking.FLUSH:
            if best_card1.suit.value > card1.suit.value:
                return index1
            elif best_card1.suit.value < card1.suit.value:
                return index2
            else:
                if best_card1.rank.value > card1.rank.value:
                    return index1
                elif best_card1.rank.value < card1.rank.value:
                    return index2
        
        case Hand_Ranking.FULLHOUSE:
            if best_card1.rank.value > card1.rank.value:
                return index1
            elif best_card1.rank.value < card1.rank.value:
                return index2
        
        case Hand_Ranking.FOUROFAKIND:
            if best_card1.rank.value > card1.rank.value:
                return index1
            elif best_card1.rank.value < card1.rank.value:
                return index2
        
        case Hand_Ranking.STRAIGHTFLUSH:    
            if best_card1.suit.value > card1.suit.value:
                return index1
            elif best_card1.suit.value < card1.suit.value:
                return index2
            else:
                if best_card1.rank.value > card1.rank.value:
                    return index1
                elif best_card1.rank.value < card1.rank.value:
                    return index2

def hand_results(hands, fold_flags, max_players):
    winner = None
    best_hand = None
    best_card1 = None
    best_card2 = None
    
    for i in range(max_players):
        if not fold_flags[i]:
            evaluated_hand, card1, card2 = evaluate_hand(hands[i])

            if best_hand is None or evaluated_hand.value > best_hand.value:
                winner = i
                best_hand = evaluated_hand
                best_card1 = card1
                best_card2 = card2
            elif best_hand == evaluated_hand:
                if same_hand_ranking_result(winner, i, best_hand, best_card1, best_card2, card1, card2) == i:
                    winner = i
                    best_card1 = card1
                    best_card2 = card2
    
    return winner, best_hand