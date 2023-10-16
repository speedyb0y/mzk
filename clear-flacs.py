#!/usr/bin/python
#
# WARNING: MAKE SURE THEY ARE ALL OK FIRST
# flac -t /mnt/CONVERTED/*.flac
#

import sys
import os

hashes = {}

directories = tuple(d.replace('///', '/').replace('//', '/').rstrip('/') for d in sys.argv[1:])

assert len(directories) == len(set(directories))

for d in directories:
    for f in os.listdir(d):
        if f.endswith('.flac'):
            fpath = f'{d}/{f}'
            hashi = '|'.join(os.popen(f'metaflac --show-md5sum --show-channels --show-bps --show-sample-rate --show-total-samples -- {fpath}').read(4096).split())
#            print(hashi, fpath)
            assert len(hashi) >= len('2a563695866b4f594ee9021976162082|2|8|44100|100'), (fpath, hashi)
            if len(set(hashi.split('|', 1)[0])) >= 5:
                try:
                    hashes[hashi].append(fpath)
                except KeyError:
                    hashes[hashi] = [fpath]
            else:
                print('WARNING: BAD HASH', hashi)

print('--- DELETING:')

for hashi, outros in hashes.items():
    keep, *outros = outros
    assert keep
    if outros:
        print(f'KEEPING {keep} ({hashi})')
        for fpath in outros:
            print(fpath)
            assert fpath != keep
            try:
                os.unlink(fpath)
            except OSError as e:
                assert e.errno == 30 # Read-only file system
        print('')
