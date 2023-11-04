#!/usr/bin/python

import sys
import os
import time
import random

_, L, N = sys.argv

L = int(L)
N = int(N)

assert 1 <= L <= 4096
assert 1 <= N <= 1000*1000

RANDOMFD = os.open('/dev/urandom', os.O_RDONLY)
assert 0 <= RANDOMFD <= 10

ALPHABET = '0123456789@ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

def mhash (length):

    f  = int.from_bytes(os.read(RANDOMFD, 8), byteorder = 'little', signed=False)
    f += int(time.monotonic() * 1000)
    f += f >> 32
    f %= len(ALPHABET) ** length

    code = ''

    while f:
        code += ALPHABET[f % len(ALPHABET)]
        f //= len(ALPHABET)

    code += ALPHABET[0] * (length - len(code))

    return code

for _ in range(N):
    print(mhash(L))
