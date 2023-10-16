#!/usr/bin/python

import sys
import os
import fcntl

ALPHABET = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ' # @$%#!,_-=+~^:[]{}()/§

def name_to_code (name):
    exp = 1
    code = 0
    for L in name:
        code += ALPHABET.index(L) * exp
        exp *= len(ALPHABET)
    assert 0 <= code <= 0xFFFFFFFFFFFFFFFF
    return code

def code_to_name (code):
    assert 0 <= code
    name = ''
    while code:
        name += ALPHABET[code % len(ALPHABET)]
        code //= len(ALPHABET)
    if not name:
        name = ALPHABET[0]
    return name

assert name_to_code(code_to_name(0)) == 0
assert name_to_code(code_to_name(32423432)) == 32423432
assert name_to_code(code_to_name(0x465748406AE)) == 0x465748406AE
assert code_to_name(name_to_code('ewgAweg32')) == 'ewgAweg32'

diskCur = partOffset = None

chunks = memoryview(bytearray(32 * 500000))
c=0

# TO DETECT REPETITIONS
files = set()

for partition, disk in sorted(( (int(x[3:]), x[:3])  for x in os.listdir('/mnt/MZK'))):

    if diskCur != disk:
        diskCur = disk

        print(f'# {disk}')

        partOffset = int(open(f'/sys/block/{disk}/{disk}{partition}/start').read()) * 512

        #7814037168  *512

    #
    directory = f'/mnt/MZK/{disk}{partition}'

    for f in os.listdir(directory):

        assert 1 <= len(f) <= 15
        assert f not in files

        files.add(f)

        start, size = map(int, int(os.pipe(f'file-offset-size {directory}/{f}').read())

        if size < 8192:
            # TOO SMALL TO LOOK SEARCH
            continue

        #
        name, *ext = f.split('.')

        name = name_to_code(name)

        if ext:
            ext, = ext
            ext  = name_to_code(ext)
        else:
            ext = 0

        chunks[c+ 0:c+ 8] =  name.to_bytes(length=8, byteorder='little', signed=False)
        chunks[c+ 8:c+16] =   ext.to_bytes(length=8, byteorder='little', signed=False)
        chunks[c+16:c+24] = start.to_bytes(length=8, byteorder='little', signed=False)
        chunks[c+24:c+32] =  size.to_bytes(length=8, byteorder='little', signed=False)

        c += 32

        # PRINT STATUS
        if len(files) % 200 == 0:
            print(f'{f} #{len(files)} @{start}')

chunks[c:c+32] = b'\x00' * 32
c += 32

open('map.bin', 'wb').write(chunks[:c])
