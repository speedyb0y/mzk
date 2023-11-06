#!/usr/bin/python

import sys
import os
import io
import mmap
import time
import fcntl
import random

#
DISK_BLOCK = 65536

#
ISO_BLOCK = 2048

_, opath, volumeName, *inputs = sys.argv

assert opath.startswith('/')

# TODO:
assert 1 <= len(volumeName) <= 30

DIRS0 = sorted('0123456789@ABCDEFGHIJKLMNOPQRSTUVWXYZ')
DIRS1 = [f'{a}/{b}' for a in DIRS0 for b in DIRS0]

def dhash (i):
    # QUANTOS POR DIRETORIO
    return DIRS1[i // ((len(reais) // len(DIRS1)) + ((len(reais) % len(DIRS1)) != 0))]

def fhash (i):
    i %= ((len(reais) // len(DIRS1)) + ((len(reais) % len(DIRS1)) != 0))
    if i:
        code = ''
        while i:
            code += '0123456789@ABCDEFGHIJKLMNOPQRSTUVWXYZ'[i % 37]
            i //= 37
    else:
        code = '0'
    return code

reais = []

def directory (append, d):
    try:
        for f in os.listdir(d):
            directory(append, f'{d}/{f}')
    except NotADirectoryError:
        append(d)

for d in inputs:
    directory(reais.append, d)

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
    return int(st.st_dev), start * block, st, f

reais = sorted(map(FIOMAP, reais))

reais = [(orig, st) for _, _, st, orig in reais]

# RESERVE THE MAP
'''
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
'''

# TOTAL
MSIZE = (1 + len(reais)) * 64
# CONFORME ISOFS
MSIZE = ((MSIZE + ISO_BLOCK - 1) // ISO_BLOCK) * ISO_BLOCK

fd = os.open('...', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o0444)
os.truncate(fd, MSIZE)
assert os.write(fd, b'ISOFS64\x00') == 8
os.close(fd)

# CREATE THE DIRECTORIES
for d in (DIRS0, DIRS1):
    for d in d:
        os.mkdir(d)

# PUT THE FILES IN THE DIRECTORIES
for i, (r, _) in enumerate(reais):
    os.symlink(r, f'{dhash(i)}/{fhash(i)}')

# TODO: REMDIR TODOS OS DIRETIORIOS PARE ELIMINAR OS VAZIOS
for d in (DIRS1, DIRS0):
    for d in d:
        try:
            os.rmdir(d)
        except BaseException as e:
            assert e.errno == 39 # DIRECTORY NOT EMPTY

#############################################################
# CREATE AND MAP THE OUTPUT FILE (WITH A BIGGER SIZE)

# TODO: AQUELE PADDING QUE O MKISOFS FAZ
PADDING = 128*ISO_BLOCK

osize = ((8*1024*1024 + len(DIRS1)*256 + (128 + MSIZE + ISO_BLOCK) + sum((128 + st.st_size + ISO_BLOCK) for _, st in reais) + PADDING + DISK_BLOCK - 1) // DISK_BLOCK) * DISK_BLOCK
#osize = -print-size

print('OSIZE:', osize)

ofd = os.open(opath, os.O_RDWR | os.O_DIRECT)
assert 0 <= ofd #  | os.O_DIRECT

obuff = mmap.mmap(-1, 1*1024*1024*1024, mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS, mmap.PROT_READ | mmap.PROT_WRITE, 0)
oview = memoryview(obuff)

#############################################################
# GENERATE THE ISOFS, BUT GET ONLY THE HEADER + MAP

# ORDEM DOS DADOS NO SISTEMA DE ARQUIVOS
with open('/tmp/sort', 'w') as fd:
    fd.write('\n'.join(('./... 1', *(f'./{dhash(i)}/{fhash(i)} -{1+i}' for i in range(len(reais))), '')))

# -hidden glob
pipe = os.popen(f'mkisofs -quiet -input-charset ASCII -hide ... -J -hide-joliet ... -follow-links -posix-L -V {volumeName} -p speedyb0y -untranslated-filenames -o - -sort /tmp/sort .')
pipeIO = io.FileIO(pipe.fileno(), 'r', closefd=False)

end = 0

# ACHA O NOSSO READER
while (h := obuff.find(b'ISOFS64\x00', 0, end)) == -1:
    c = pipeIO.readinto(oview[end:end+4*1024*1024])
    if c == 0:
        break
    end += c

assert 8192 <= h

# TERMINA DE LER ELE
end_ = h + MSIZE
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
done = end

total = 0

for i, (real, st) in enumerate(reais):

    print(f'{(done*100)//osize}% {st.st_size} {dhash(i)}/{fhash(i)} {real}')

    # CADA ARQUIVO COMECA EM UM BLOCO
    end_ = ((end + ISO_BLOCK - 1) // ISO_BLOCK) * ISO_BLOCK
    while end != end_:
        oview[end:end+1] = b'\x00'
        end += 1

    if size := st.st_size:
        done += size
        # TODO: FIXME: READ WITH DIRECT_IO DIRECTLY FROM THE DISK
        with io.FileIO(real, 'r') as fd:
            while size:
                # TEM QUE ESCREVER DE FORMA ALINHADA
                if (end + 128*1024*1024) >= len(oview):
                    end_ = (end//4096) * 4096
                    assert os.write(ofd, oview[:end_]) == end_
                    oview[:end-end_] = oview[end_:end]
                    total += end_
                    end -= end_
                c = fd.readinto(oview[end:end+size])
                assert 1 <= c
                end += c
                size -= c

# FLUSH ANY REMAINING, WITH PADDING, ALIGNED
end_ = ((end + PADDING + DISK_BLOCK - 1) // DISK_BLOCK) * DISK_BLOCK
while end != end_:
    oview[end:end+1] = b'\x00'
    end += 1

assert os.write(ofd, oview[:end]) == end

total += end

print('TOTAL:', total)

assert total <= osize

os.fsync(ofd)
os.close(ofd)

oview.release()
obuff.close()

# CLEANUP
for i in range(len(reais)):
    os.unlink(f'{dhash(i)}/{fhash(i)}')

os.unlink('...')

for d in (DIRS1, DIRS0):
    for d in d:
        try:
            os.rmdir(d)
        except FileNotFoundError:
            pass
