from Card import *
from Poker import *
import os

suit_symbols_dict = {
    Suit.HEARTS: '♥',
    Suit.DIAMONDS: '♦',
    Suit.CLUBS: '♣',
    Suit.SPADES: '♠'
    }

rank_symbols_dict = {
    Rank.ACE: 'A',
    Rank.TWO: '2',
    Rank.THREE: '3',
    Rank.FOUR: '4',
    Rank.FIVE: '5',
    Rank.SIX: '6',
    Rank.SEVEN: '7',
    Rank.EIGHT: '8',
    Rank.NINE: '9',
    Rank.TEN: '10',
    Rank.JACK: 'J',
    Rank.QUEEN: 'Q',
    Rank.KING: 'K'
    }

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_card(card):
    # Print the card design
    print(' _______ ')
    print('|       |')
    if (card.rank == Rank.TEN):
        print(f'|  {rank_symbols_dict[card.rank]}   |')
    else:
        print(f'|   {rank_symbols_dict[card.rank]}   |')
    print('|       |')
    print(f'|   {suit_symbols_dict[card.suit]}   |')
    print('|_______|')

def print_hand(hand):
    # Print each card side by side
    for _ in hand:
        print(' _______ ', end=' ')
    print()
    for _ in hand:
        print('|       |', end=' ')
    print()
    for card in hand:
        if card.rank == Rank.TEN:
            print(f'|  {rank_symbols_dict[card.rank]}   |', end=' ')
        else:
            print(f'|   {rank_symbols_dict[card.rank]}   |', end=' ')
    print()
    for _ in hand:
        print('|       |', end=' ')
    print()
    for card in hand:
        print(f'|   {suit_symbols_dict[card.suit]}   |', end=' ')
    print()
    for _ in hand:
        print('|_______|', end=' ')
    print()

def print_bets(max_players, assigned_index, last_raise_index, bets, fold_flags):
    col_width = 16

    print('\nBets:\n')
    for i in range(max_players):
        if i == assigned_index:
            print(f"{'Player ' + str(i)+' (you)':^{col_width}}||", end = ' ')
        else:
            print(f"{'Player ' + str(i):^{col_width}}||", end = ' ')
    print()
    for _ in range(max_players):
        print(f"{'':^{col_width}}||", end = ' ')
    print()
    for i in range(max_players):
        print(f"{'Bet: ' + str(bets[i]):^{col_width}}||", end = ' ')
    print()
    for i in range(max_players):
        if fold_flags[i]:
            print(f"{'Folded':^{col_width}}||", end = ' ')
        elif i == last_raise_index and bets[i] > 0:
            print(f"{'Last raise':^{col_width}}||", end = ' ')
        else:
            print(f"{'':^{col_width}}||", end = ' ')
    print()

def print_options(assigned_index, last_raise_index, bets):
    while (True):
        if all(bet == 0 for bet in bets):
            stringa = '\nChoose an action:\n 1: Raise\n 2: Check\n 3: Fold'
        else:
            stringa = '\nChoose an action:\n 1: Raise\n 2: Call\n 3: Fold'
        print(stringa)

        choice = input()
        match choice:
            case '1':
                bet = ''
                while not (bet.isdigit()):
                    bet = input(f'How much do you want to bet? (min {bets[last_raise_index] - bets[assigned_index] + 1})\n')
                    if bet.isdigit():
                        if int(bet) > bets[last_raise_index] - bets[assigned_index]:
                            return (choice, int(bet))
                        else:
                            print('The amount you chose is not enough to raise')
                            bet = ''
                    else:
                        print('Not a number, try again')
            case '2':
                return (choice, 0)
            case '3':
                return (choice, 0)
            case _:
                print('Input not accepted, try again\n')

def print_card_change():
    cards_to_change = [False] * 5

    while (True):
        print('\nDo you want to change one or more cards?')
        print('0. Yes')
        print('1. No')

        match input():
            case '0':
                choices = []
                i = 0
                while i < 4:
                    print('\nInsert a value between 1 and 5 to change the corresponding card (insert q to quit)')
                    if i == 3:
                        print('Last possible change')
                    else:
                        print(f'{4-i} changes left')
                    choice = input()
                    if choice == 'q':
                        break
                    elif int(choice) > 0 and int(choice) <= 5:
                        if int(choice) not in choices:
                            choices.append(int(choice))
                            i += 1
                        else:
                            print(f'You already chose to change the card n° {int(choice)}\n')
                    else:
                        print('Input not accepted, try again\n')

                for choice in choices:
                    cards_to_change[choice-1] = True
                
                return cards_to_change
            
            case '1':
                print('\nYou chose to keep all your cards')
                return cards_to_change
                
            case _:
                print('Input not accepted, try again\n')


def print_winner(winner, winner_hand, assigned_index):
    if winner == assigned_index:
        print('\nYou win')
    else:
        print(f'\nWinner: {winner}')
    print(hand_ranking_dict[winner_hand[0]])
