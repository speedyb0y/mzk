#!/usr/bin/python

import sys
import os
import re
import time
import random

def mzk_name():

	checksum  = int(time.time()      * 1000000)
	checksum ^= int(time.monotonic() * 1000000)
	checksum += random.randint(0x1000000000000000, 0xFFFFFFFFFFFFFFFF)
	checksum += random.randint(0x1000000000000000, 0xFFFFFFFFFFFFFFFF)
	checksum += random.randint(0x1000000000000000, 0xFFFFFFFFFFFFFFFF)

	return ''.join('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'[(checksum // (36**i)) % 36] for i in range(12))

for fpath in sys.argv[1:]:

    for fpath in os.popen(f"find '{fpath}/' -type f -print0").read().split('\x00'):

        if not fpath.endswith('].opus'):
            continue

        *_, fname = fpath.rsplit('/', 1)

        ext = fpath.rsplit('.', 1)[1]

        title, url  = fname.rsplit('[', 1)

        title = ' '.join(title.replace("'", '`').split()).strip('-').strip('_')

        url = url.split(']')[0]

        new = f'{mzk_name()}.{ext}'

        print(f'{new} | {url} | {title} | {fpath}')

        os.rename(fpath, new)

        os.system(f"operon set -- YOUTUBE 'https://youtu.be/{url}' {new}")
        os.system(f"operon set -- TITLE '{title}' {new}")
