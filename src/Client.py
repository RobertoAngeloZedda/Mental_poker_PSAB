from Contract_communication_handler import *
from SRA import *

cch = Contract_communication_handler(addresses_file_path='./addresses.txt', 
                                     abi_file_path='./abi.json',
                                     user_wallet_address='0xAC2444B1e48b6024f6d11c2a67584fe706C4FF9B',
                                     user_wallet_password='0x66957c694c0ff3661f6716a5befa7ba2466f159fa2b4a040780dfa263a90e96e')

cch.participate()
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

print('Listening for draw events')
draw_index, topdeck_index, hand_size = cch.catch_draw_event(assigned_index)

deck = cch.get_encrypted_deck()

encrypted_hand = deck[topdeck_index : (topdeck_index + hand_size)]

hand = [sra_decrypt(card, d, n) for card in encrypted_hand]

print(hand)

# If client has to draw
if draw_index == assigned_index:
    cch.draw()

# If someoneelse has to draw
else:
    cch.reveal_cards(hand)