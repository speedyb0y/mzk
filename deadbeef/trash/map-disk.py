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

# disks[dmajor, dminor][start][fname] = size
disks = {}

def MAJOR (dev):
    major = dev >> 8
    assert os.major(dev) == major
    return major

def MINOR (dev):
    minor = dev & 0xFF
    assert os.minor(dev) == minor
    return minor

for mpoint in sys.argv[1:]:

    partDev = os.stat(mpoint).st_dev

    partMajor = MAJOR(partDev)
    partMinor = MINOR(partDev)

    #
    fsizes = {}

    for fname in os.listdir(mpoint):
        st = os.stat(f'{mpoint}/{fname}')
        assert st.st_dev == partDev
        fsizes[fname] = st.st_size

    #
    diskDev = tuple(map(int, open(f'/sys/dev/block/{partMajor}:{partMinor}/../dev').read().split(':')))

    try:
        parts = disks[diskDev]
    except KeyError:
        parts = disks[diskDev] = {}

    #
    partStart = int(open(f'/sys/dev/block/{partMajor}:{partMinor}/start').read()) * 512

    assert partStart not in parts

    parts[partStart] = fsizes

for (major, minor), parts in disks.items():

    diskPath = f'/dev/block/{major}:{minor}'

    # ABRE O DISCO
    fd = os.open(diskPath, os.O_RDONLY | os.O_DIRECT)
    mm = mmap.mmap(fd, os.lseek(fd, 0, os.SEEK_END), mmap.MAP_SHARED, mmap.PROT_READ, 0, 0)
    mm.madvise(mmap.MADV_SEQUENTIAL)
    buff = memoryview(mm)

    for start, fsizes in parts.items():

        print(diskPath, '@', start)

        #
        assert buff[start+32768:start+32768+8] == b'\x01CD001\x01\x00'
        assert buff[start+34817:start+34817+8] == b'CD001\x01\x00\x00'

        # LABEL
        label = bytes(buff[start+32808:start+32808+32]).decode()

        # buff.startswith(b'ewgwe')
        print(label)

        # INICIO DOS ARQUIVOS PARTICAO
        FILES_START = start + 47205
        FILES_END = FILES_START + (len(fsizes) + 1024)*48

        fsizes = sorted((offset := mm.find(fname.encode(), FILES_START, FILES_END), fname, size) for fname, size in fsizes.items())

        offset = FILES_END - 256

        for o, fname, size in fsizes:

            assert start <= o, (fname, o, size)

            code, ext = fname.split('.')
            
            where = mm.find({ 'flac': b'fLaC', 'ogg': b'OggS', 'opus': b'OggS', }[ext.lower()], offset, offset + 128*1024*1204)            

            assert offset <= where, (where, diskPath, fname, start, offset, size)

            # print(where, fname, o, size, int.from_bytes(buff[where:where+6]))
            hdr = b'|'.join((ext.upper().encode(), buff[where:where+6]))

            assert hdr in {
                b'FLAC|fLaC\x00\x00',
                b'FLAC|fLaC\xcb\x83',
                 # b'OGG|OggS\x00\x00',
                b'OPUS|OggS\x00\x00',
                b'OPUS|OggS\x00\x01',
                b'OPUS|OggS\x00\x02',
                b'OPUS|OggS\x00\x04',
            }, (fname, where, hdr)
            
            offset = where + size

    buff.release()
    mm.close()
    os.close(fd)

# print(disks)
for x in ():

    fd = os.open(disk, os.O_RDONLY | os.O_DIRECT)

    # COM UM BLOCO A MENOS
    #size = ((os.lseek(diskFD, 0, os.SEEK_END) - 65536) // 65536) * 65536
    size = os.lseek(fd, 0, os.SEEK_END)

    assert 1*1024*1024 <= size

    buff = mmap.mmap(fd, size, mmap.MAP_SHARED, mmap.PROT_READ, 0, 0)
    buff.madvise(mmap.MADV_SEQUENTIAL)

    # chunks[c:c+32] = disk.encode() + b'\x00' * (32 - len(disk))
    # c += 32

    offset, end = 0, ((size - 65536) // 65536) * 65536

    while offset != end:

        found = buff.find(b"\x01\x43\x44\x30\x30\x31\x01\x00")

        offset = found

    continue

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
