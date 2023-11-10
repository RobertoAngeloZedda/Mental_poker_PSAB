from Contract_communication_handler import *
from SRA import *
import random

DEBUG = True

def get_wallet_info():
    wallet_address = ''
    wallet_password = ''
    
    while (wallet_address == '' or wallet_password == ''):
        file_path = input('Link the path of the file containing your wallet info\n')

        try:
            with open(file_path) as file:
                lines = [line.strip() for i, line in enumerate(file)]

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

def shuffle_dealer(assigned_index):
    if DEBUG: print('Listening for shuffle events')
    cch.catch_shuffle_event(assigned_index)

    n = sra_setup(16)
    if DEBUG: print('n =', n)

    deck_coding = generate_deck_encryption(n)
    if DEBUG: print('deck coding =\n', deck_coding)

    e, d = sra_generate_key(n-1)

    enc = [sra_encrypt(card, e, n) for card in deck_coding]

    random.shuffle(enc)

    if DEBUG: print('encrypted_deck =\n', enc)

    cch.shuffle_dealer(n, deck_coding, enc)

    return n, e, d

def shuffle(assigned_index):
    if DEBUG: print('Listening for shuffle events')
    cch.catch_shuffle_event(assigned_index)

    n = cch.get_n()
    if DEBUG: print('n =', n)

    deck_coding = cch.get_deck_coding()
    if DEBUG: print('deck coding =\n', deck_coding)

    deck = cch.get_deck()

    e, d = sra_generate_key(n-1)

    enc = [sra_encrypt(card, e, n) for card in deck]

    random.shuffle(enc)

    if DEBUG: print('encrypted_deck =\n', enc)

    cch.shuffle(enc)

    return n, e, d

def deal_cards(n, d):
    for _ in range(max_players):
        if DEBUG: print('Listening for draw events')
        draw_index, topdeck_index, hand_size = cch.catch_draw_event(assigned_index)

        deck = cch.get_deck()

        if DEBUG: print(deck)

        encrypted_hand = deck[topdeck_index : (topdeck_index + hand_size)]

        hand = [sra_decrypt(card, d, n) for card in encrypted_hand]

        # If client has to draw
        if draw_index == assigned_index:
            print('\nYour hand:')
            for card in hand:
                print(card)
            cch.draw()

        # If someone else has to draw
        else:
            cch.reveal_cards(hand)

def stake_round():
    turn_index = 0
    while turn_index < max_players:
        if DEBUG: print('Listening for stake events')
        turn_index = cch.catch_stake_event(turn_index, max_players)

        last_raise_index = cch.get_last_raise_index()
        bets = cch.get_bets()
        fold_flags = cch.get_fold_flags()

        if not all(bet == 0 for bet in bets):
            if assigned_index != last_raise_index:
                print(f'\nLast player that raised: {last_raise_index}')
            else:
                print('\nLast player that raised: You')
        
        print(f'\nYour bet: {bets[assigned_index]}')
        for i, bet in enumerate(bets):
            if i != assigned_index:
                print(f'Player {i}\'s bet: {bet}')
        for i, flag in enumerate(fold_flags):
            if flag:
                if i != assigned_index:
                    print(f'Player {i} has folded')
                else:
                    print('You folded')

        # when stake phase is over 'turn_index = max_players'
        if turn_index >= max_players:
            break

        if turn_index == assigned_index:
            repeat_input = True
            while (repeat_input):
                if all(bet == 0 for bet in bets):
                    stringa = '\nChoose an action:\n 1: Raise\n 2: Check\n 3: Fold'
                else:
                    stringa = '\nChoose an action:\n 1: Raise\n 2: Call\n 3: Fold'
                print(stringa)

                match input():
                    case '1':
                        repeat_input = False
                        bet = ''
                        while not (bet.isdigit()):
                            bet = input(f'How much do you want to bet? (min {bets[last_raise_index] - bets[assigned_index] + 1})\n')
                            if bet.isdigit():
                                if int(bet) > bets[last_raise_index] - bets[assigned_index]:
                                    cch.bet(int(bet))
                                else:
                                    print('The amount you chose is not enough to raise')
                                    bet = ''
                            else:
                                print('Not a number, try again')
                    case '2':
                        repeat_input = False
                        if all(bet == 0 for bet in bets):
                            cch.check()
                        else:
                            cch.call(bets[last_raise_index] - bets[assigned_index])
                    case '3':
                        repeat_input = False
                        cch.fold()
                    case _:
                        repeat_input = True
                        print('Input not accepted, try again\n')
        else:
            print(f'\nWaiting for Player {turn_index}\'s action...')
        
        turn_index = calculate_next_turn(turn_index, fold_flags, max_players)
        #print(turn_index)

def key_reveal(e, d):
    if DEBUG: print('Listening for key reveal events')
    cch.catch_key_reveal_event()
    cch.key_reveal(e, d)

    if DEBUG: print(cch.get_enc_keys())
    if DEBUG: print(cch.get_dec_keys())

def verify():
    if DEBUG: print('Listening for verify events')
    cch.catch_optimistic_verify_event()

    # Determine winner
    deck = cch.get_deck()
    cards = []
    keys = cch.get_dec_keys()
    fold_flags = cch.get_fold_flags()
    
    print('\n')
    for i in range(max_players):
        cards.append(deck[i])
        
        for j in range(max_players):
            if (i == j):
                cards[i] = sra_decrypt(cards[i], keys[j], n)
        
        if i != assigned_index:
            print(f'Player {i}\'s hand: {cards[i]}')
        else:
            print(f'Your hand: {cards[i]}')

    winner = 0
    best_card = 0
    for i in range(max_players):
        if not fold_flags[i] and cards[i] > best_card:
            best_card = cards[i]
            winner = i

    if DEBUG: print(f'\nYour winner: {winner}')

    cch.optimistic_verify(winner)

    return winner

def award(winner):
    if DEBUG: print('Listening for award events')
    cch.catch_award_event()
    print(f'\nWinner: {winner}')

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
        n, e, d = shuffle_dealer(assigned_index)
    # If client is not dealer (he reads n and deck coding)
    else:
        n, e, d = shuffle(assigned_index)

    deal_cards(n, d)

    stake_round()

    key_reveal(e, d)

    winners_index = verify()

    award(winners_index)