from Crypto.Util import number

def sra_setup(bits: int):
    n = 0
    while n < 2 ** (bits-2):
       n = number.getPrime(bits)
    return n

def sra_generate_key(phi: int):
    e = number.getPrime(phi.bit_length() - 1)
    d = pow(e, -1, phi)
    return (e, d)

def sra_encrypt(plain_text: int, e: int, n: int):
    return pow(plain_text, e, n)

def sra_decrypt(cypher_text: int, d: int, n: int):
    return pow(cypher_text, d, n)

def shuffle(deck, permutation):
    new_deck = []
    for index in permutation:
        new_deck.append(deck[index])

    return new_deck

def is_quadratic_residue(num: int, mod: int):
    if num % mod == 0:
        return 0
    elif pow(num, (mod - 1) // 2, mod) == 1:
        return 1
    else:
        return -1