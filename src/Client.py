from Contract_communication_handler import *
from SRA import *

cch = Contract_communication_handler(addresses_file_path='./addresses.txt', 
                                     abi_file_path='./abi.json',
                                     user_wallet_address='0xAC2444B1e48b6024f6d11c2a67584fe706C4FF9B',
                                     user_wallet_password='0x66957c694c0ff3661f6716a5befa7ba2466f159fa2b4a040780dfa263a90e96e')

def calculate_next_stake_turn(turn_index, fold_flags, max_players):
    new_turn_index = (turn_index + 1) % max_players

    if fold_flags[new_turn_index]:
        return calculate_next_stake_turn(new_turn_index, fold_flags, max_players)
        
    else:
        return new_turn_index

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

for _ in range(2):
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
while turn_index < 2:
    print('Listening for stake events')
    turn_index = cch.catch_stake_event(turn_index, 2)

    last_raise_index = cch.get_last_raise_index()
    bets = cch.get_bets()
    fold_flags = cch.get_fold_flags()

    print(last_raise_index)
    print(bets)
    print(fold_flags)

    if turn_index >= 2:
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
    
    turn_index = calculate_next_stake_turn(turn_index, fold_flags, 2)
    print(turn_index)

print('Listening for key reveal events')
turn_index = cch.catch_key_reveal_event(assigned_index)

cch.key_reveal(e, d)

enc_keys = cch.get_enc_keys()
dec_keys = cch.get_dec_keys()

print(enc_keys)
print(dec_keys)