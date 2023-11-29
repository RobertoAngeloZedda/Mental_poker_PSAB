from Contract_communication_handler import *
from Poker import *
from SRA import *
from UI import *
import random

N_BITS = 256
DEBUG = True

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
    # choosing only quadratic residues to map the cards to represent the deck
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
    cch.catch_shuffle_event(assigned_index, max_players)

    n = sra_setup(N_BITS)
    if DEBUG: print('n =', n)

    deck_coding = generate_deck_encryption(n)
    deck_map = {key: value for key, value in zip(deck_coding, [Card(suit, rank) for rank in Rank for suit in Suit])}
    if DEBUG: print('deck coding =\n', deck_coding)

    e, d = sra_generate_key(n-1)

    enc = [sra_encrypt(card, e, n) for card in deck_coding]

    random.shuffle(enc)

    if DEBUG: print('encrypted_deck =\n', enc)

    cch.shuffle_dealer(n, deck_coding, enc)

    # waiting for the shuffle phase to end
    cch.catch_shuffle_event(max_players, max_players)

    return n, e, d, deck_map

def shuffle(assigned_index):
    if DEBUG: print('Listening for shuffle events')
    turn_index = cch.catch_shuffle_event(assigned_index, max_players)
    
    if turn_index >= max_players:
        return (None, None, None, None)

    n = cch.get_n()
    # checking if n length is appropriate
    if n < 2**(N_BITS-2):
        cch.report_n()
        return (None, None, None, None)
    
    if DEBUG: print('n =', n)

    deck_coding = cch.get_deck_coding()
    # checking if deck_coding is valid
    for index, code in enumerate(deck_coding):
        if is_quadratic_residue(code, n) != 1:
            cch.report_deck_coding(index)
            return (None, None, None, None)
    
    deck_map = {key: value for key, value in zip(deck_coding, [Card(suit, rank) for rank in Rank for suit in Suit])}
    if DEBUG: print('deck coding =\n', deck_coding)

    deck = cch.get_deck()

    e, d = sra_generate_key(n-1)

    enc = [sra_encrypt(card, e, n) for card in deck]

    random.shuffle(enc)

    if DEBUG: print('encrypted_deck =\n', enc)

    cch.shuffle(enc)

    # waiting for the shuffle phase to end
    cch.catch_shuffle_event(max_players, max_players)

    return n, e, d, deck_map

def deal_cards(assigned_index, max_players, n, d, deck_map):
    player_hand = []

    for _ in range(max_players):
        if DEBUG: print('Listening for draw events')
        draw_index, topdeck_index, hand_size = cch.catch_draw_event(assigned_index)

        # the contract communicates the phase is over when num_cards = 0
        if hand_size == 0:
            break

        deck = cch.get_deck()

        encrypted_hand = deck[topdeck_index : (topdeck_index + hand_size)]

        hand = [sra_decrypt(card, d, n) for card in encrypted_hand]

        # if client has to draw
        if draw_index == assigned_index:
            # reading and checking if cards drawn are valid
            player_hand = []
            for card_coding in hand:
                if card_coding in deck_map:
                    cch.report_draw()
                    return player_hand
            
            cch.draw()

        # if someone else has to draw
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
            print_pot(cch.get_pot())

        # when stake phase is over 'turn_index = max_players'
        if turn_index >= max_players:
            if phase == 1:
                print_pot(cch.get_pot())
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
    
    for _ in range(max_players):
        if DEBUG: print('Listening for draw events')
        draw_index, topdeck_index, num_cards = cch.catch_draw_event(assigned_index)

        # the contract communicates the phase is over when num_cards = 0
        if num_cards == 0:
            break

        deck = cch.get_deck()

        # if client has to draw
        if draw_index == assigned_index:
            hand_size = cch.get_hand_size()
            cards_owner = cch.get_cards_owner()

            # recreating player's hand and checking if cards are valid
            new_hand = []
            for card_index, owner in enumerate(cards_owner):
                if owner == assigned_index:
                    card_coding = sra_decrypt(deck[card_index], d, n)
                    if card_coding in deck_map:
                        new_hand.append(deck_map[card_coding])
                    else:
                        cch.report_draw()
                        return new_hand
                    
                    if len(new_hand) == hand_size:
                        break
            
            cch.draw()
        
        # if someone else has to draw
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

    hand_size = cch.get_hand_size()
    enc_keys = cch.get_enc_keys()
    dec_keys = cch.get_dec_keys()
    fold_flags = cch.get_fold_flags()
    hands = calculate_hands(max_players)
    
    # testing each player's key to check if they are legitimate
    for i in range(max_players):
        if i != assigned_index:
            random_num = random.randrange(N_BITS)
            if sra_decrypt(sra_encrypt(random_num, enc_keys[i], n), dec_keys[i], n) != random_num:
                if cch.get_reporter_index() == max_players:
                    cch.report_keys(i, random_num)
                return (None, None)

    for i in range(max_players):
        for j in range(hand_size):
            decrypted_card = sra_decrypt(hands[i][j], dec_keys[i], n)
            if decrypted_card in deck_map:
                hands[i][j] = deck_map[decrypted_card]
            else:
                if cch.get_reporter_index() == max_players:
                    cch.report_keys(i, 1)
                return (None, None)  
        
        if i == assigned_index:
            print('\nYour hand:')
        else:
            print(f'\nPlayer {i}\'s hand:')
        
        print_hand(hands[i])
    
    # determine winner
    winner, best_hand = hand_results(hands, fold_flags, max_players)

    if DEBUG: print(f'\nYour winner: {winner}')
    
    cch.optimistic_verify(winner)

    if DEBUG: print('Listening for verify events')
    cch.catch_optimistic_verify_event()
    
    return (winner, best_hand)

def award(assigned_index, winner=None, winner_hand=None):
    if DEBUG: print('Listening for award events')
    cch.catch_award_event()
    if winner is not None and winner_hand is not None:
        print_winner(assigned_index, winner, winner_hand)
    else:
        print('\nANOMALY DETECTED\nContract will proceed to refund all clients')

if __name__ == '__main__':

    wallet_address, wallet_password = get_wallet_info()

    cch = Contract_communication_handler(addresses_file_path='./addresses.txt', 
                                     abi_file_path='./abi.json',
                                     user_wallet_address=wallet_address,
                                     user_wallet_password=wallet_password)
    
    max_players = cch.get_max_players()
    deposit = cch.get_deposit()
    if DEBUG: print('Deposit:', deposit, '\nMax Players:', max_players)

    cch.participate(deposit)
    assigned_index = cch.get_my_turn_index()
    if DEBUG: print('Assigned index:', assigned_index)
    print('Waiting for other players...')

    # if client is dealer he has to choose n and generate deck coding
    if assigned_index == 0:
        n, e, d, deck_map = shuffle_dealer(assigned_index)
    # if client is not dealer (he reads n and deck coding)
    else:
        n, e, d, deck_map = shuffle(assigned_index)

    if cch.get_reporter_index() != max_players:
        award(assigned_index)
        exit()
    
    player_hand = deal_cards(assigned_index, max_players, n, d, deck_map)

    if cch.get_reporter_index() != max_players:
        key_reveal(e, d)
        award(assigned_index)
        exit()

    stake_round(assigned_index, max_players, 1)
    
    card_change(max_players)
    
    player_hand = deal_replacement_cards(assigned_index, max_players, n, d, deck_map)

    if cch.get_reporter_index() != max_players:
        key_reveal(e, d)
        award(assigned_index)
        exit()
    
    stake_round(assigned_index, max_players, 2)

    key_reveal(e, d)
    
    if cch.get_reporter_index() != max_players:
        award(assigned_index)
        exit()

    (winner_index, winner_hand) = verify(assigned_index, max_players, deck_map)

    if cch.get_reporter_index() != max_players:
        award(assigned_index)
    else:
        award(assigned_index, winner_index, winner_hand)