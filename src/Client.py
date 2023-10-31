from Contract_communication_handler import *
from SRA import *

def get_wallet_info(file_path: str):
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
        return ('','')
    except Exception as e:
        print(str(e))
        return ('','')

wallet_address = ''
wallet_password = ''
while (wallet_address == '' or wallet_password == ''):
    file_path = input('Link the path of the file containing your wallet info\n')
    (wallet_address, wallet_password) = get_wallet_info(file_path)

cch = Contract_communication_handler(addresses_file_path='./addresses.txt', 
                                     abi_file_path='./abi.json',
                                     user_wallet_address=wallet_address,
                                     user_wallet_password=wallet_password)

def calculate_next_stake_turn(turn_index, fold_flags, max_players):
    new_turn_index = (turn_index + 1) % max_players

    if fold_flags[new_turn_index]:
        return calculate_next_stake_turn(new_turn_index, fold_flags, max_players)
        
    else:
        return new_turn_index

max_players = 2
fee = 5
cch.participate(fee)
assigned_index = cch.get_my_turn_index()
print('Assigned index:', assigned_index)

print('Listening for shuffle events')
cch.catch_shuffle_event(assigned_index)

# If client is dealer he gotta shuffle the deck
if assigned_index == 0:
    n = sra_setup(32)
    print('n =', n)

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
    print('deck coding =\n', deck_coding)

    e, d = sra_generate_key(n-1)

    #shuffle

    enc = [sra_encrypt(card, e, n) for card in deck_coding]
    print('encrypted_deck =\n', enc)

    cch.shuffle_dealer(n, deck_coding, enc)

# If client is not dealer (he reads n and deck coding)
else:
    n = cch.get_n()
    print('n =', n)

    deck_coding = cch.get_deck_coding()
    print('deck coding =\n', deck_coding)

    deck = cch.get_encrypted_deck()

    e, d = sra_generate_key(n-1)

    #shuffle

    enc = [sra_encrypt(card, e, n) for card in deck]
    print('encrypted_deck =\n', enc)

    cch.shuffle(enc)

for _ in range(max_players):
    print('Listening for draw events')
    draw_index, topdeck_index, hand_size = cch.catch_draw_event(assigned_index)

    deck = cch.get_encrypted_deck()

    encrypted_hand = deck[topdeck_index : (topdeck_index + hand_size)]

    hand = [sra_decrypt(card, d, n) for card in encrypted_hand]

    print(hand)

    # If client has to draw
    if draw_index == assigned_index:
        cch.draw()

    # If someone else has to draw
    else:
        cch.reveal_cards(hand)

turn_index = 0
while turn_index < max_players:
    print('Listening for stake events')
    turn_index = cch.catch_stake_event(turn_index, max_players)

    last_raise_index = cch.get_last_raise_index()
    bets = cch.get_bets()
    fold_flags = cch.get_fold_flags()

    print(last_raise_index)
    print(bets)
    print(fold_flags)

    if turn_index >= max_players:
        break

    if turn_index == assigned_index:
        repeat_input = True
        while (repeat_input):
            if all(bet == 0 for bet in bets):
                stringa = '\nChoose an action:\n 1: Raise\n 2: Check\n 3: Fold'
            else:
                stringa = 'Choose an action:\n 1: Raise\n 2: Call\n 3: Fold'
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
                                print(f'The amount you chose is not enough to raise')
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
    
    turn_index = calculate_next_stake_turn(turn_index, fold_flags, max_players)
    print(turn_index)

print('Listening for key reveal events')
turn_index = cch.catch_key_reveal_event(assigned_index)

cch.key_reveal(e, d)

print(cch.get_enc_keys())
print(cch.get_dec_keys())

print('Listening for verify events')
cch.catch_optimistic_verify_event()

# Determine winner
deck = cch.get_encrypted_deck()
cards = []
for i in range(max_players):
    cards.append(deck[i])
    
    for j in range(max_players):
        if (i == j):
            cards[i] = sra_decrypt(cards[i], cch.get_dec_keys()[j], n)
    
    print(f'Player {i}\'s hand: {cards[i]}')

winner = 0
best_card = cards[0]
for i in range(1, max_players):
    if (cards[i] > best_card):
        best_card = cards[i]
        winner = i

print(f'Player {assigned_index}\'s winner: {winner}')

cch.optimistic_verify(winner)

print('Listening for award events')
cch.catch_award_event()
print(f'Winner: {winner}')