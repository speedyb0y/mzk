#!/usr/bin/python

import sys
import os
import time
import hashlib
import re

ALIGNMENT = 65536

WRITE_SIZE = 128*1024*1024
PIPE_SIZE = 256*1024*1024

_, DIR, OUTPUT, NAME, AUTHOR = sys.argv

#
print('DIR:', DIR)
print('OUTPUT:', OUTPUT)
print('NAME:', NAME)
print('AUTHOR:', AUTHOR)
print('ALIGNMENT:', ALIGNMENT)
print('PIPE SIZE:', PIPE_SIZE)
print('WRITE SIZE:', WRITE_SIZE)

#
os.chdir(DIR)

assert '/' in OUTPUT
assert all((l in '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for l in NAME  ) and 1 <= len(NAME)   <= 28
assert all((l in '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for l in AUTHOR) and 1 <= len(AUTHOR) <= 31

#
open('/proc/sys/fs/pipe-max-size', 'w').write(str(PIPE_SIZE))

#
HASH = ''.join('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'[x % 36] for x in hashlib.sha256(open('/dev/urandom', 'rb').read(256) + int(time.time()*1000).to_bytes(length=8, byteorder='little', signed=False)).digest())

LABEL = '-'.join((NAME, HASH))[:32]

print('LABEL:', LABEL)

assert len(LABEL) == 32

files = os.listdir('.')

print('FILES:', len(files))

# VERIFY FILE NAMES
assert all(map(re.compile('^[0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz]{10}[.](flac|opus|ogg)$').match, files))
# NO REPEATED FILE NAMES
assert len(files) == len(set(map(str.upper, files)))

# COMPUTE ESTIMATED SIZE
ESTIMATED = sum((16 + os.stat(f).st_size) for f in files)

print('ESTIMATED:', ESTIMATED)

assert 1024 <= ESTIMATED

os.system(' '.join(map(str, ( 'spipe', PIPE_SIZE, '/bin/mkisofs', 'mkisofs', '-quiet', '-V', LABEL, '-p', AUTHOR,
    # SE NAO TEM INFO UNIX ENTAO NAO PRECISA DISSO
    # -uid 0 -gid 0 -dir-mode 0555 -file-mode 0444
    #-max-iso9660-filenames
    '-full-iso9660-filenames',
    # OMIT VERSION NUMBERS FROM ISO-9660 FILE NAMES.
    '-omit-version-number',
    #
    '-omit-period',
    # ALLOWS ISO-9660 FILENAMES TO INCLUDE DIGITS, UPPER CASE CHARACTERS AND ALL OTHER 7 BIT ASCII CHARACTERS
    # (RESP. ANYTHING EXCEPT LOWER-CASE CHARACTERS).
    #-relaxed-filenames
    #
    #-allow-lowercase
    #-allow-leading-dots
    #-allow-multidot
    # DO NOT TRANSLATE THE CHARACTERS '#' AND '~' WHICH ARE INVALID FOR ISO-9660 FILENAMES.
    #-no-iso-translate
    # ALLOWS "UNTRANSLATED" FILENAMES, COMPLETELY VIOLATING THE ISO-9660 STANDARDS DESCRIBED ABOVE.
    # IT ALLOWS MORE THAN ONE '.' CHARACTER IN THE FILENAME, AS WELL AS MIXED CASE FILENAMES.
    # THIS IS USEFUL ON HP-UX SYSTEM, WHERE THE BUILT-IN CDFS FILESYSTEM DOES NOT RECOGNIZE ANY EXTENSIONS.
    '-untranslated-filenames',
    #-iso-level 4
    '-input-charset ASCII',
    '-follow-links',
    '-posix-L',
    #
    '.',
    # 'oflag=direct,dsync' 'conv=fdatasync',iflag=fullblock
    '|', 'dd', f'ibs={64*1024*1024}', f'obs={WRITE_SIZE}', f'of={OUTPUT}', 'oflag=direct', 'status=progress'
))))

assert 128 <= ALIGNMENT <= 1*1024*1024

TOTAL = int(os.popen(f'isosize {OUTPUT}').read().strip())
ROUND = ((TOTAL + ALIGNMENT - 1) // ALIGNMENT) * ALIGNMENT

print('TOTAL:', TOTAL)
print('ROUND:', ROUND)

assert ESTIMATED <= TOTAL <= ROUND
assert ROUND % ALIGNMENT == 0

os.system(f'truncate --size={ROUND} {OUTPUT}')

#
with open(OUTPUT, 'rb') as fd:
    assert os.pread(fd.fileno(), 32, 32808).decode() == LABEL

# sudo mount /mnt/BAD.iso -t iso9660 -o loop,ro,norock,nojoliet,check=strict,uid=0,gid=0,mode=0444,map=off,block=2048 /data/
