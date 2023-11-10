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

    def sort_hand(self, hand):
        return sorted(hand, key=lambda x: x.rank.value, reverse=True)
    
    def is_royal_flush(self, hand):
        return self.is_straight_flush(hand) and (hand[0].rank == Rank.ACE or hand[4].rank == Rank.ACE)

    def is_straight_flush(self, hand):
        return self.is_straight(hand) and self.is_flush(hand)
    
    def is_four_of_a_kind(self, hand): #hand needs to be sorted
        return hand[0].rank == hand[3].rank or hand[1].rank == hand[4].rank
    
    def is_full_house(self, hand): #hand needs to be sorted
        return (hand[0].rank == hand[2].rank and hand[3].rank == hand[4].rank) or (hand[2].rank == hand[4].rank and hand[0].rank == hand[1].rank)
        
    def is_flush(self, hand):
        return all(card.suit == hand[0].suit for card in hand)

    def is_straight(self, hand):
        return all(hand[i].rank.value - hand[i+1].rank.value == 1 for i in range(len(hand) - 1)) or all(hand[i].rank.value - hand[i+1].rank.value == -1 for i in range(len(hand) - 1))
    
    def is_three_of_a_kind(self, hand): #hand needs to be sorted
        return hand[0].rank == hand[2].rank or hand[1].rank == hand[3].rank or hand[2].rank == hand[4].rank

    def is_two_pair(self, hand): #hand needs to be sorted
        return (hand[0].rank == hand[1].rank and hand[2].rank == hand[3].rank) or (hand[0].rank == hand[1].rank and hand[3].rank == hand[4].rank) or (hand[1].rank == hand[2].rank and hand[3].rank == hand[4].rank)

    def is_one_pair(self, hand): #hand needs to be sorted
        return any(hand[i].rank == hand[i+1].rank for i in range(len(hand) - 1))
    
    def order_four_of_a_kind_hand(self, hand):
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
    
    def order_full_house_hand(self, hand):
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

    def order_three_of_a_kind_hand(self, hand):
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

    def order_two_pair_hand(self, hand):
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

    def order_one_pair_hand(self, hand):
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

    def evaluate_hand(self, hand):
        sorted_hand = self.sort_hand(hand)

        if self.is_royal_flush(hand):
            return (Hand_Ranking.ROYALFLUSH, sorted_hand)

        if self.is_straight_flush(hand):
            return (Hand_Ranking.STRAIGHTFLUSH, sorted_hand)
        
        if self.is_four_of_a_kind(sorted_hand):
            return (Hand_Ranking.FOUROFAKIND, self.order_four_of_a_kind_hand(sorted_hand))
        
        if self.is_full_house(sorted_hand):
            return (Hand_Ranking.FULLHOUSE, self.order_full_house_hand(sorted_hand))
        
        if self.is_flush(sorted_hand):
            return (Hand_Ranking.FLUSH, sorted_hand)
        
        if self.is_straight(hand):
            return (Hand_Ranking.STRAIGHT, sorted_hand)
        
        if self.is_three_of_a_kind(sorted_hand):
            return (Hand_Ranking.THREEOFAKIND, self.order_three_of_a_kind_hand(sorted_hand))
        
        if self.is_two_pair(sorted_hand):
            return (Hand_Ranking.TWOPAIR, self.order_two_pair_hand(sorted_hand))
        
        if self.is_one_pair(sorted_hand):
            return (Hand_Ranking.ONEPAIR, self.order_one_pair_hand(sorted_hand))
        
        return (Hand_Ranking.HIGHCARD, sorted_hand)
    
    def evaluate_hand(self, hand):
        sorted_hand = self.sort_hand()

        card1 = Card()
        card2 = Card()

        flush_flag = True
        straight_flag = True
        first_pair_count = 1
        second_pair_count = 0

        for i in range(1, 5):
            if flush_flag and sorted_hand[i].rank.value != sorted_hand[i-1].rank.value +1:
                flush_flag = False
            
            if straight_flag and sorted_hand[i].suit.value != sorted_hand[i-1].suit.value:
                straight_flag = False
            
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
            

    def compare_ordered_hands(self, hand1, hand2):
        if hand1 == hand2:
            return None
        else:
            for i in range(5):
                if hand1[i].rank.value > hand2[i].rank.value:
                    return hand1
                if hand1[i].rank.value < hand2[i].rank.value:
                    return hand2
    
    def hand_results(self):
        winning_player = None
        best_hand = None

        for player in self.players:
            player.show_hand()
            evaluated_hand = self.evaluate_hand(player.hand)
            print(f"Hand ranking: {hand_ranking_dict[evaluated_hand[0]]}\n")
            
            if best_hand is None or evaluated_hand[0].value > best_hand[0].value:
                best_hand = evaluated_hand
                winning_player = player
            elif evaluated_hand[0] == best_hand[0]:
                # if hand rank is equal, compare value of cards 
                higher_valued_hand = self.compare_ordered_hands(best_hand[1], evaluated_hand[1])
                if higher_valued_hand == evaluated_hand[1]:
                    winning_player = player
                    best_hand = evaluated_hand
                elif higher_valued_hand == None:
                    winning_player == None
                    best_hand = None
    
        return (winning_player, best_hand)

    def hand_results(self):
            winners = []
            #winners_player = None
            best_hand = None
            best_card1 = None
            best_card2 = None

            for player in self.players:
                player.show_hand()
                evaluated_hand, card1, card2 = self.evaluate_hand(player.hand)
                print(f"Hand ranking: {hand_ranking_dict[evaluated_hand]}\n")
                
                if best_hand is None or evaluated_hand.value > best_hand.value:
                    winners.clear()
                    winners.append(player)
                    best_hand = evaluated_hand
                    best_card1 = card1
                    best_card2 = card2
                elif evaluated_hand == best_hand:
                    if card1 > best_card1:
                    
        
            return (winning_player, best_hand)

    def play(self):
        self.print_players()
        
        self.deal_cards()

        (winning_player, best_hand) = self.hand_results()

        if winning_player != None:
            print(f"WINNER: {winning_player.name}\n{hand_ranking_dict[best_hand[0]]}")
        else:
            print("DRAW")
        
        #for player in self.players:
        #    player.show_hand()