#!/usr/bin/python

import sys
import os
import time
import fcntl
import random

_, volumeName, volumeID, *inputs = sys.argv

# TODO:
assert 1 <= len(volumeName) <= 30

volumeID = int(volumeID)
assert 0 <= volumeID <= 0xFF

ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

def mhash (ext):

    f  = int.from_bytes(os.read(RANDOMFD, 8), byteorder = 'little', signed=False)
    f += int(time.time() * 1000000)
    f += int(time.monotonic() * 1000000)
    f += int(random.random() * 0xFFFFFFFFFFFFFFFF)
    f += f >> 48
    f %= len(ALPHABET) ** 12

    code = ''

    while f:
        code += ALPHABET[f % len(ALPHABET)]
        f //= len(ALPHABET)

    code += ALPHABET[0] * (12 - len(code))
    code += ext

    return code

RANDOMFD = os.open('/dev/urandom', os.O_RDONLY)
assert 0 <= RANDOMFD <= 10

reais = []

for d in inputs:
    try:
        for f in os.listdir(d):
            reais.append(f'{d}/{f}')
    except TimeoutError:
        reais.append(d)

# REORDENA CONFORME A POSICAO NO DISCO
def FIOMAP (f):
    start = bytearray(b'\x00'*8)
    block = bytearray(b'\x00'*8)
    fd = os.open(f, os.O_RDONLY)
    assert 0 <= fd
    st = os.stat(fd)
    fcntl.ioctl(fd, 1, start, True)
    fcntl.ioctl(fd, 2, block, True)
    os.close(fd)
    start = int.from_bytes(start, byteorder='little', signed=False)
    block = int.from_bytes(block, byteorder='little', signed=False)
    return ((st.st_dev >> 8), (st.st_dev) & 0xFF), start * block, st.st_size, f

reais = sorted(map(FIOMAP, reais))

'''
DEVICES = {}

def devfd (mj):
    try:
        fd = DEVICES[mj]
    except KeyError:
        fd = DEVICES[mj] = os.open(f'/dev/block/{mj[0]}:{mj[1]}', os.O_RDONLY | os.O_CLOEXEC)
    return fd

[print(os.pread(devfd(mj), 8, start)) for mj, start, size, f in reais]
'''

reais = [(r, mhash(r[r.index('.'):])) for _, _, _, r in reais]

# RESERVE THE MAP
fd = os.open('.ISOFS64', os.O_WRONLY | os.O_CREAT | os.O_CREAT, 0o0444)

m = ( b'ISOFS64\x00' +
            volumeName.encode() + b'\x00' * (4*8 - 2 - len(volumeName)) +
            volumeID.to_bytes(length=2, byteorder='little', signed=False) +
    int(time.time()).to_bytes(length=4, byteorder='little', signed=False) +
          len(reais).to_bytes(length=4, byteorder='little', signed=False) +
                 (0).to_bytes(length=8, byteorder='little', signed=False) +
                 (0).to_bytes(length=8, byteorder='little', signed=False) +
    b''.join(name.encode() + b'\x00' * (64 - len(name)) for r, name in reais)
)

assert len(m) == (1 + len(reais)) * 64

# ALIGNED SIZE
m += b'\x00' * ( (((len(m) + 65536 - 1) // 65536) * 65536) - len(m) )
assert len(m) % 65536 == 0
assert os.write(fd, m) == len(m)
os.close(fd)

#
for r, n in reais:
    os.symlink(r, n)

###
reais = *reais[:25], *reais[100:100+25], *reais[-25:]
###

open('/tmp/mk.list', 'w').write('.ISOFS64\n'   + '\n'.join(   n        for     r, n  in reais) + '\n')
open('/tmp/mk.sort', 'w').write('.ISOFS64 1\n' + '\n'.join(f'{n} -{i}' for i, (r, n) in enumerate(reais, 1)) + '\n')

# mkisofs  -o /tmp/teste.iso --follow-links -path-list /tmp/mk.list -sort /tmp/mk.sort
