#!/usr/bin/python

import sys
import os
import io
import mmap
import time
import fcntl
import random

_, opath, volumeName, *inputs = sys.argv

assert opath.startswith('/')

# TODO:
assert 1 <= len(volumeName) <= 30

ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

DIRS_N = 256

def dhash (i):
    i %= DIRS_N
    return '/'.join((
        ALPHABET[i %  len(ALPHABET)],
        ALPHABET[i // len(ALPHABET)]
    ))

def mhash ():

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

# REORDENA CONFORME O DISCO E A POSICAO NO DISCO
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
    return ((st.st_dev >> 8), (st.st_dev) & 0xFF), start * block, st, f

# reais = reais[:5]
reais = sorted(map(FIOMAP, reais))
reais = [(orig, st, new + orig[orig.index('.'):]) for (mm, start, st, orig), new in zip(reais, sorted(mhash() for _ in reais))]

# RESERVE THE MAP
m = ( b'ISOFS64\x00'                                                       # MAGIC
   +              (0).to_bytes(length=8, byteorder='little', signed=False) # CHECKSUM (HDR + FILES HDR)
   +              (0).to_bytes(length=8, byteorder='little', signed=False) # TOTAL SIZE
   + int(time.time()).to_bytes(length=4, byteorder='little', signed=False) # CREATION TIME
   +       len(reais).to_bytes(length=4, byteorder='little', signed=False) # NUMBER OF FILES
   +         volumeName.encode() + b'\x00' * (32 - len(volumeName))        # LABEL
   + b''.join( (
        (0).to_bytes(length=8, byteorder='little', signed=False) # OFFSET
   +    st.st_size.to_bytes(length=8, byteorder='little', signed=False) # SIZE
   + int(0).to_bytes(length=4, byteorder='little', signed=False) # CREATION TIME
   + int(st.st_mtime).to_bytes(length=4, byteorder='little', signed=False) # MODIFIED TIME
   +    (0).to_bytes(length=8, byteorder='little', signed=False) # CHECKSUM OF FILE
   +    name.encode() + b'\x00' * (32 - len(name))               # NAME
   )  for r, st, name in reais)
)

assert len(m) == (1 + len(reais)) * 64

ALIGNMENT = 2048

# ALIGNED SIZE
m += b'\x00' * ( (((len(m) + ALIGNMENT - 1) // ALIGNMENT) * ALIGNMENT) - len(m) )
assert len(m) % ALIGNMENT == 0

fd = os.open('.MAP', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o0444)
assert os.write(fd, m) == len(m)
os.close(fd)

# CREATE THE DIRECTORIES
for a in ALPHABET:
    os.mkdir(a)
    for b in ALPHABET:
        os.mkdir(f'{a}/{b}')

# PUT THE FILES IN THE DIRECTORIES
for i, (r, st, n) in enumerate(reais):
    os.symlink(r, f'{dhash(i)}/{n}')

#############################################################
# CREATE AND MAP THE OUTPUT FILE (WITH A BIGGER SIZE)

# TODO: AQUELE PADDING QUE O MKISOFS FAZ
PADDING = 128*2048

osize = ((8*1024*1024 + DIRS_N*256 + (128 + len(m) + 2048) + sum((128 + st.st_size + 2048) for r, st, n in reais) + PADDING + 65536 - 1) // 65536) * 65536
#osize = -print-size

print('OSIZE:', osize)

ofd = os.open(opath, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o0444)
assert 0 <= ofd #  | os.O_DIRECT

try:
    os.fallocate(ofd, osize)
except AttributeError:
    assert os.system(f'fallocate -l {osize} /proc/{os.getpid()}/fd/{ofd}') == 0

omap = mmap.mmap(ofd, osize, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, 0)
# mmap.mmap.madvise
oview = memoryview(omap)

#############################################################
# GENERATE THE ISOFS, BUT GET ONLY THE HEADER + MAP

# ORDEM DOS DADOS NO SISTEMA DE ARQUIVOS
with open('/tmp/sort', 'w') as fd:
    fd.write('\n'.join(('./.MAP 1', *(f'./{dhash(i)}/{n} -{1+i}' for i, (r, st, n) in enumerate(reais)), '')))

#os.system('mkisofs -untranslated-filenames -o /mnt/sda2/TESTE.iso.tmp --follow-links -sort /tmp/sort .')

pipe = os.popen('mkisofs -quiet -untranslated-filenames -o - --follow-links -sort /tmp/sort .')
pipeIO = io.FileIO(pipe.fileno(), 'r', closefd=False)

end = 0

# ACHA O NOSSO READER
while (h := omap.find(b'ISOFS64\x00', 0, end)) == -1:
    c = pipeIO.readinto(oview[end:end+4*1024*1024])
    if c == 0:
        break
    end += c

assert 8192 <= h

# TERMINA DE LER ELE
end_ = h + len(m)
while end < end_:
    c = pipeIO.readinto(oview[end:end_])
    assert 1 <= c
    end += c

# PODE TER LIDO MAIS
end = end_

pipeIO.close()
pipe.close()

#############################################################
# PUT ALL THE FILES

for real, st, new in reais:

    # CADA ARQUIVO COMECA EM UM BLOCO
    end_ = ((end + 2048 - 1) // 2048) * 2048
    while end != end_:
        oview[end:end+1] = b'\x00'
        end += 1

    ate = end + st.st_size
    # TODO: FIXME: READ WITH DIRECT_IO DIRECTLY FROM THE DISK
    with io.FileIO(real, 'r') as rfd:
        while c := rfd.readinto(oview[end:]):
            assert 1 <= c
            end += c
    assert end == ate

# FLUSH ANY REMAINING, WITH PADDING, ALIGNED
end = ((end + PADDING + 65536 - 1) // 65536) * 65536

oview[end] = b'\x00'

print('CLOSING...', end)
oview.release()
omap.flush()
omap.close()

os.fsync(ofd)
os.ftruncate(ofd, end)
os.fsync(ofd)
os.close(ofd)
