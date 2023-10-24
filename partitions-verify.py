#!/usr/bin/python
#
# VERIFY COLLECTION FILENAMES
#

import sys
import os

# BY DEFAULT, CHECK THE MOUNTED ONES
if len(sys.argv) == 1:
    files = [ f
        for p in os.listdir(f'/mnt/music')
        for f in os.listdir(f'/mnt/music/{p}')
    ]
else:
    files = [ f.rsplit('/', 1)[-1]
        for a in sys.argv[1:]
            for f in (os.listdir(a) if a.endswith('/') else (a,))
    ]

print('FILES:', len(files))

# NO REPEATED FILE NAMES
assert len(files) == len(set(files))
assert len(files) == len(set(map(str.upper, files)))

# ONLY THOSE NAME LENGTHS
# ONLY THOSE EXTENSIONS
# ONLY ONE EXTENSION PER FILE
# ONE DOT PER FILE
assert all( (len(name) == 10 and ext in ('flac', 'opus', 'ogg'))
    for name, ext in (f.split('.') for f in files)
)

# ONLY THOSE CHARACTERS
assert ''.join(sorted(set(''.join(files)))) == '.0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
