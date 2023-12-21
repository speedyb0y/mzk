#!/usr/bin/python

import sys
import os
import time
import hashlib
import re

def scandir (d):
    d = d.rstrip('/')
    try:
        for f in os.listdir(d):
            yield from scandir(f'{d}/{f}')
    except FileNotFoundError:
        pass
    except PermissionError:
        pass
    except NotADirectoryError:
        yield d

ALIGNMENT = 65536

WRITE_SIZE = 128*1024*1024
PIPE_SIZE = 256*1024*1024

_, OUTPUT, AUTHOR, LABEL, *DIRS = sys.argv

#
print('DIRS:', DIRS)
print('OUTPUT:', OUTPUT)
print('AUTHOR:', AUTHOR)
print('LABEL:', LABEL)
print('ALIGNMENT:', ALIGNMENT)
print('PIPE SIZE:', PIPE_SIZE)
print('WRITE SIZE:', WRITE_SIZE)

#
assert '/' in OUTPUT
assert all((l in '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-_') for l in LABEL  ) and 1 <= len(LABEL)   <= 28
assert all((l in '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ- ') for l in AUTHOR) and 1 <= len(AUTHOR) <= 31

#
open('/proc/sys/fs/pipe-max-size', 'w').write(str(PIPE_SIZE))

#
HASH = ''.join('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'[x % 36] for x in hashlib.sha256(open('/dev/urandom', 'rb').read(256) + int(time.time()*1000).to_bytes(length=8, byteorder='little', signed=False)).digest())

assert len(LABEL) <= 32
assert len(HASH) == 32

files = set()

any(map(files.update, map(scandir, DIRS)))

files = [f for _, f in sorted((f.rsplit('/', 1)[-1], f) for f in files)]

print('FILES:', len(files))

#print(files)

# VERIFY FILE NAMES
#assert all(map(re.compile('^[0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz]{10}[.](flac|opus|ogg)$').match, files))
# NO REPEATED FILE NAMES
assert len(files) == len(set(map(str.upper, files)))

# COMPUTE ESTIMATED SIZE
ESTIMATED = sum((128 + os.stat(f).st_size + 2048) for f in files)

print('ESTIMATED:', ESTIMATED)

assert 1024 <= ESTIMATED

open('/tmp/list', 'w').write('\n'.join(files) + '\n')
open('/tmp/sort', 'w').write('\n'.join(f'{f} -{i}' for i, f in enumerate(files, 1)) + '\n')

os.system(' '.join(map(str, ( 'spipe', PIPE_SIZE, '/bin/mkisofs', 'mkisofs', '-quiet',
	'-V', LABEL,
	'-appid', HASH,
	'-preparer', str(int(time.time())),
	'-publisher', AUTHOR,
    # SE NAO TEM INFO UNIX ENTAO NAO PRECISA DISSO
    # -uid 0 -gid 0 -dir-mode 0555 -file-mode 0444
    #-max-iso9660-filenames
    #'-full-iso9660-filenames',
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
    '-path-list', '/tmp/list',
    '-sort', '/tmp/sort',
    #'.',

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
    assert os.pread(fd.fileno(), 32, 32808).decode().startswith(LABEL)

# sudo mount /mnt/BAD.iso -t iso9660 -o loop,ro,norock,nojoliet,check=strict,uid=0,gid=0,mode=0444,map=off,block=2048 /data/
