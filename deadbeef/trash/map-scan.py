#!/usr/bin/python

import sys
import os
import mmap

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

diskCur = diskFD = None

chunks = memoryview(bytearray(32 * 500000))
c=0
cacheExts = {}

# TO DETECT REPETITIONS
files = set()

for partition, disk in sorted(( (int(x[3:]), x[:3])  for x in os.listdir(f'/mnt/MZK'))):

    if diskCur != disk:
        diskCur = disk

        print(f'# {disk}')

        if diskFD is not None:
            os.close(diskFD)

        diskFD = os.open(f'/dev/{disk}', os.O_RDONLY | os.O_DIRECT)

        # UM BLOCO A MENOS
        size = ((os.lseek(diskFD, 0, os.SEEK_END) - 65536) // 65536) * 65536

        assert 1*1024*1024 <= size

        buff = mmap.mmap(diskFD, size, mmap.MAP_SHARED, mmap.PROT_READ, 0, 0)
        buff.madvise(mmap.MADV_SEQUENTIAL)

        chunks[c:c+32] = disk.encode() + b'\x00' * (32 - len(disk))
        c += 32

        offset = 0

    #
    directory = f'/mnt/MZK/{disk}{partition}'

    for f in os.listdir(directory):

        # PRINT STATUS
        if len(files) % 200 == 0:
            print(f'{f} #{len(files)} @{offset}')

        assert 1 <= len(f) <= 15
        assert f not in files

        files.add(f)

        try:
            fd = os.open(f'{directory}/{f}', os.O_RDONLY | os.O_DIRECT)
        except:
            fd = os.open(f'{directory}/{f}', os.O_RDONLY)

        size  = os.stat(fd).st_size
        start = os.read(fd, 65536)

        os.close(fd)

        if size < 8192:
            # TOO SMALL TO LOOK SEARCH
            continue

        assert len(start) >= 8192

        start = buff.find(start, offset, offset + 16*1024*1024)

        if start == -1:
            # NOT FOUND
            continue

        assert offset <= start

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

        offset = start + size

chunks[c:c+32] = b'\x00' * 32
c += 32

# chunks = b''.join(chunks)
# assert len(chunks) % 32 == 0
open('map.bin', 'wb').write(chunks[:c])
