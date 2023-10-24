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

ALPHABET = []
# NORMAL
ALPHABET += '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
# OK
#ALPHABET += '@'
# SHELL INSECURE
#ALPHABET += '#$&!?=+,'
# SHELL INSECURE - COMMAND OPTIONS
#ALPHABET += '-'
# UGLY
#ALPHABET += '_'
# HTTP INSECURE
#ALPHABET += '%:'

random.shuffle(ALPHABET)

ALPHABET = ''.join(ALPHABET)

def mhash (length, alphabet=ALPHABET):
    assert isinstance(length, int) and 1 <= length <= 512
    f = sum(int(x()*10000000) for x in (os.getpid, time.time, time.time_ns, time.monotonic, time.monotonic_ns, random.random))
    f += f >> 32
    f %= len(alphabet)**length
    code  = ''.join(alphabet[(f := (f + x)) % len(alphabet)] for x in os.read(RANDOMFD, length))
    assert len(code) == length
    #return ''.join(('%16s %16d %16x' % (code, f, f)))
    return code

for _ in range(N):
    print(mhash(L))
