from SRA import *

n = sra_setup(256)

# Choosing only quadratic residues to map the cards to represent the deck
deck = []
deck_size = 52
count = 0
for i in range(2, n):
    if count >= deck_size:
        break
    if is_quadratic_residue(i, n) == 1:
        deck.append(i)
        count += 1

A_e, A_d = sra_generate_key(n-1)
#print(A_e, A_d)

#A_permutation = [1, 3, 2, 0]
#A_shuffle = shuffle(deck, A_permutation)
#print(A_shuffle)

A_enc = [sra_encrypt(card, A_e, n) for card in deck]
#print(A_dec)

B_e, B_d = sra_generate_key(n-1)
#print(B_e, B_d)

#B_permutation = [0, 3, 1, 2]
#B_shuffle = shuffle(A_enc, B_permutation)
#print(B_shuffle)

B_enc = [sra_encrypt(card, B_e, n) for card in A_enc]
#print(B_enc)

print('n:', n)
print('deck encoding:', deck)
print(B_enc)

# B draws the 3rd card
A_dec = sra_decrypt(B_enc[2], A_d, n)
B_dec = sra_decrypt(A_dec, B_d, n)
print(B_dec)

# A draws the 2nd card
B_dec = sra_decrypt(B_enc[1], B_d, n)
A_dec = sra_decrypt(B_dec, A_d, n)
print(A_dec)