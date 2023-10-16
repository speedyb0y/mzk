#!/usr/bin/python

import sys
import os
import time
import random

_, L, N = sys.argv

L = int(L)
N = int(N)

assert 1 <= L <= 4096
assert 1 <= N <= 4096

checksum  = int(time.time()      * 10000000)
checksum += int(time.monotonic() * 10000000)
checksum += os.getpid()
checksum &= 0xFFFFFFFFFFFFFFFF

ALPHABET = [
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
    'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
    'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
    'U', 'V', 'W', 'X', 'Y', 'Z',
    'u', 'v', 'w', 'x', 'y', 'z',
] * 8

name = []

for _ in range(N):

    random.shuffle(ALPHABET)

    for _ in range(L):
        checksum += checksum >> 32
        checksum += random.randint(0, 0xFFFFFFFFFFFFFFFF)
        checksum &= 0xFFFFFFFFFFFFFFFF
        name.append(ALPHABET[checksum % len(ALPHABET)])

    print(''.join(name))

    name.clear()
