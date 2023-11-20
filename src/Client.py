from Contract_communication_handler import *
from Poker import *
from SRA import *
from UI import *
import random

DEBUG = False

def get_wallet_info():
    wallet_address = ''
    wallet_password = ''
    
    while (wallet_address == '' or wallet_password == ''):
        file_path = input('Link the path of the file containing your wallet info\n')

        try:
            with open(file_path) as file:
                lines = [line.strip() for _, line in enumerate(file)]

                if len(lines) != 2:
                    raise Exception('Wallet file does not meet the right format.')
                
                split = lines[0].split(': ')
                if len(split) == 2 or split[0] == 'wallet_address':
                    wallet_address = split[1]
                else:
                    raise Exception('Error in Wallet file line 1.')
                
                split = lines[1].split(': ')
                if len(split) == 2 or split[0] == 'wallet_password':
                    wallet_password = split[1]
                else:
                    raise Exception('Error in Wallet file line 2.')
                
                return (wallet_address, wallet_password) 
        except FileNotFoundError:
            print('File not found.')
        except Exception as e:
            print(str(e))

def calculate_next_turn(turn_index, fold_flags, max_players):
    new_turn_index = (turn_index + 1) % max_players

    # skip players if they folded
    if fold_flags[new_turn_index]:
        return calculate_next_turn(new_turn_index, fold_flags, max_players)
    else:
        return new_turn_index

def generate_deck_encryption(n):
    # Choosing only quadratic residues to map the cards to represent the deck
    deck_coding = []
    deck_size = 52
    count = 0
    for i in range(2, n):
        if count >= deck_size:
            break
        if is_quadratic_residue(i, n) == 1:
            deck_coding.append(i)
            count += 1
    return deck_coding

def calculate_hands(max_players):
    deck = cch.get_deck()
    cards_owner = cch.get_cards_owner()
    hand_size = cch.get_hand_size
    hands = [[] for _ in range(max_players)]
        
    hands_filled = 0
    for i in range(len(cards_owner)):
        player_index = cards_owner[i]
        if player_index < max_players:
            hands[player_index].append(deck[i])
            if len(hands[player_index]) == hand_size:
                hands_filled +=1
                if hands_filled == max_players:
                    break
    
    return hands

def shuffle_dealer(assigned_index):
    if DEBUG: print('Listening for shuffle events')
    cch.catch_shuffle_event(assigned_index)

    n = sra_setup(16)
    if DEBUG: print('n =', n)

    deck_coding = generate_deck_encryption(n)
    deck_map = {key: value for key, value in zip(deck_coding, [Card(suit, rank) for suit in Suit for rank in Rank])}
    if DEBUG: print('deck coding =\n', deck_coding)

    e, d = sra_generate_key(n-1)

    enc = [sra_encrypt(card, e, n) for card in deck_coding]

    random.shuffle(enc)

    if DEBUG: print('encrypted_deck =\n', enc)

    cch.shuffle_dealer(n, deck_coding, enc)

    return n, e, d, deck_map

def shuffle(assigned_index):
    if DEBUG: print('Listening for shuffle events')
    cch.catch_shuffle_event(assigned_index)

    n = cch.get_n()
    if DEBUG: print('n =', n)

    deck_coding = cch.get_deck_coding()
    # CHECK
    deck_map = {key: value for key, value in zip(deck_coding, [Card(suit, rank) for suit in Suit for rank in Rank])}
    if DEBUG: print('deck coding =\n', deck_coding)

    deck = cch.get_deck()

    e, d = sra_generate_key(n-1)

    enc = [sra_encrypt(card, e, n) for card in deck]

    random.shuffle(enc)

    if DEBUG: print('encrypted_deck =\n', enc)

    cch.shuffle(enc)

    return n, e, d, deck_map

def deal_cards(assigned_index, max_players, n, d, deck_map):
    player_hand = []

    for _ in range(max_players):
        if DEBUG: print('Listening for draw events')
        draw_index, topdeck_index, hand_size = cch.catch_draw_event(assigned_index)

        deck = cch.get_deck()

        encrypted_hand = deck[topdeck_index : (topdeck_index + hand_size)]

        hand = [sra_decrypt(card, d, n) for card in encrypted_hand]

        # If client has to draw
        if draw_index == assigned_index:
            player_hand = [deck_map[card] for card in hand]
            cch.draw()

        # If someone else has to draw
        else:
            cch.reveal_cards(hand)
        
    return player_hand

def stake_round(assigned_index, max_players, phase):
    turn_index = cch.get_last_raise_index()

    # the contract communicates the stake phase is over using turn_index = max_players
    while turn_index < max_players:
        if DEBUG: print('Listening for stake events')
        turn_index = cch.catch_stake_event(turn_index, max_players)

        last_raise_index = cch.get_last_raise_index()
        bets = cch.get_bets()
        fold_flags = cch.get_fold_flags()
        
        clear_screen()
        print('Your hand:')
        print_hand(player_hand)
        print_bets(assigned_index, max_players, last_raise_index, bets, fold_flags, phase)
        if phase == 2:
            print_number_of_changed_cards(max_players, cch.get_number_of_changed_cards())
            print_pot(cch.get_pot() - cch.get_participation_fee())

        # when stake phase is over 'turn_index = max_players'
        if turn_index >= max_players:
            if phase == 1:
                print_pot(cch.get_pot() - cch.get_participation_fee())
            break
        
        # if it's this client's turn
        if turn_index == assigned_index:
            choice = print_options(assigned_index, last_raise_index, bets)
            match choice[0]:
                case '1':
                    cch.bet(choice[1])
                case '2':
                    if all(bet == 0 for bet in bets):
                        cch.check()
                    else:
                        cch.call(bets[last_raise_index] - bets[assigned_index])
                case '3':
                    cch.fold()
                
            clear_screen()

        # if it's another client's turn
        else:
            print(f'\nWaiting for Player {turn_index}\'s action...')
        
        turn_index = calculate_next_turn(turn_index, fold_flags, max_players)

def card_change(max_players):
    turn_index = cch.get_last_raise_index()

    # the card_change phase starts from where the stake round finished
    # the contract communicates the card_change phase is over using turn_index = max_players
    while turn_index < max_players:
        if DEBUG: print('Listening for card change events')
        turn_index = cch.catch_card_change_event(turn_index, max_players)
        
        # when card_change phase is over 'turn_index = max_players'
        if turn_index >= max_players:
            break
        
        fold_flags = cch.get_fold_flags()

        if turn_index == assigned_index:
            cards_to_change = print_card_change()
            cch.card_change(cards_to_change)
        else:
            print(f'\nWaiting for Player {turn_index}\'s action...')
        
        turn_index = calculate_next_turn(turn_index, fold_flags, max_players)

def deal_replacement_cards(assigned_index, max_players, n, d, deck_map):
    new_hand = player_hand
    
    if DEBUG: print('Deal cards')

    for _ in range(max_players):
        if DEBUG: print('Listening for draw events')
        draw_index, topdeck_index, num_cards = cch.catch_draw_event(assigned_index)

        # the contract communicates the phase is over when num_cards = 0
        if num_cards == 0:
            break

        deck = cch.get_deck()

        # If client has to draw
        if draw_index == assigned_index:
            hand_size = cch.get_hand_size()
            cards_owner = cch.get_cards_owner()

            # recreate player's hand
            new_hand = []
            for card_index, owner in enumerate(cards_owner):
                if owner == assigned_index:
                    new_hand.append(deck_map[sra_decrypt(deck[card_index], d, n)])
                    if len(new_hand) == hand_size:
                        break

            cch.draw()
        
        # If someone else has to draw
        else:
            encrypted_cards = deck[topdeck_index : (topdeck_index + num_cards)]
            cards = [sra_decrypt(card, d, n) for card in encrypted_cards]
            
            cch.reveal_cards(cards)
        
    return new_hand

def key_reveal(e, d):
    if DEBUG: print('Listening for key reveal events')
    cch.catch_key_reveal_event()
    cch.key_reveal(e, d)

    if DEBUG: print(cch.get_enc_keys())
    if DEBUG: print(cch.get_dec_keys())

def verify(assigned_index, max_players, deck_map):
    if DEBUG: print('Listening for verify events')
    cch.catch_optimistic_verify_event()

    # Determine winner
    hand_size = cch.get_hand_size()
    keys = cch.get_dec_keys()
    fold_flags = cch.get_fold_flags()
    hands = calculate_hands(max_players)

    for i in range(max_players):
        for j in range(hand_size):
            for k in range(max_players):
                if i == k: #remove
                    hands[i][j] = deck_map[sra_decrypt(hands[i][j], keys[k], n)]
        
        if i == assigned_index:
            print('\nYour hand:')
        else:
            print(f'\nPlayer {i}\'s hand:')
        
        print_hand(hands[i])

    winner = None
    best_hand = None
    for i in range(max_players):
        if not fold_flags[i]:
            evaluated_hand = evaluate_hand(hands[i])
        
            if best_hand is None or evaluated_hand[0].value > best_hand[0].value:
                best_hand = evaluated_hand
                winner = i
            elif evaluated_hand[0] == best_hand[0]:
                # if hand rank is equal, compare value of cards 
                higher_valued_hand = compare_ordered_hands(best_hand[1], evaluated_hand[1])
                if higher_valued_hand == evaluated_hand[1]:
                    winner = i
                    best_hand = evaluated_hand
                elif higher_valued_hand == None:
                    winner == None
                    best_hand = None

    if DEBUG: print(f'\nYour winner: {winner}')

    cch.optimistic_verify(winner)

    return (winner, best_hand)

def award(assigned_index, winner, winner_hand):
    if DEBUG: print('Listening for award events')
    cch.catch_award_event()
    print_winner(assigned_index, winner, winner_hand)

if __name__ == '__main__':

    wallet_address, wallet_password = get_wallet_info()

    cch = Contract_communication_handler(addresses_file_path='./addresses.txt', 
                                     abi_file_path='./abi.json',
                                     user_wallet_address=wallet_address,
                                     user_wallet_password=wallet_password)
    
    max_players = cch.get_max_players()
    participation_fee = cch.get_participation_fee()
    if DEBUG: print('Participation fee:', participation_fee, '\nMax Players:', max_players)

    cch.participate(participation_fee)
    assigned_index = cch.get_my_turn_index()
    if DEBUG: print('Assigned index:', assigned_index)
    print('Waiting for other players...')

    # If client is dealer he has to choose n and generate deck coding
    if assigned_index == 0:
        n, e, d, deck_map = shuffle_dealer(assigned_index)
    # If client is not dealer (he reads n and deck coding)
    else:
        n, e, d, deck_map = shuffle(assigned_index)
    
    player_hand = deal_cards(assigned_index, max_players, n, d, deck_map)
    
    stake_round(assigned_index, max_players, 1)
    
    card_change(max_players)
    
    player_hand = deal_replacement_cards(assigned_index, max_players, n, d, deck_map)
    
    stake_round(assigned_index, max_players, 2)

    key_reveal(e, d)

    (winner_index, winner_hand) = verify(assigned_index, max_players, deck_map)

    award(assigned_index, winner_index, winner_hand)