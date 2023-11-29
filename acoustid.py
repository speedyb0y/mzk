#!/usr/bin/python

import sys
import os
import time
import json
import cbor2 as cbor
import requests

TOKEN = "b'lfvGgAYa"

session = requests.session()

fd = os.open(f'TAGS-FETCHED.{time.time()}', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o0444)

results = []

try:

    for f in sys.argv[1:]:

        for line in open(f).read().split('\n'):

            if line == '':
                continue

            # XID DURATION=282 FINGERPRINT=AQADtEueJUrCJIF_hLan4Dn05EH2
            xid, duration, fingerprint = line.split()

            _, duration    = duration   .split('=', 1)
            _, fingerprint = fingerprint.split('=', 1)

            duration = int(duration)

            print(len(results), xid)

            try:
                response = session.get(f'https://api.acoustid.org/v2/lookup?client={TOKEN}&meta=recordings+releasegroups+releases+tracks+usermeta&duration={duration}&fingerprint={fingerprint}', headers = {
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.5',
                })
                response = response.text.upper()
                response = json.loads(response)
            except KeyboardInterrupt:
                raise
            except BaseException:
                continue

            results.append((xid, duration, fingerprint, response))

except BaseException:
    pass

results = cbor.dumps(results)

assert os.write(fd, results) == len(results)


'''
mkdir FINGERPRINTS ERRORS

blockdev --setra 2048 /dev/sdd

DIRS_0="CONVERTED sdd1 sdd3/CONVERTED"
DIRS_1="sdd1 CONVERTED sdd3/CONVERTED"
DIRS_2="sdd3/CONVERTED sdd1 CONVERTED"

find ${DIRS_0} -type f -iname '[ABC@1]*' -printf '\0%p ' -exec fpcalc  '{}' \; > FINGERPRINTS/0  2> ERRORS/0  &
find ${DIRS_1} -type f -iname '[DEF9]*'  -printf '\0%p ' -exec fpcalc  '{}' \; > FINGERPRINTS/1  2> ERRORS/1  &
find ${DIRS_2} -type f -iname '[GHI8]*'  -printf '\0%p ' -exec fpcalc  '{}' \; > FINGERPRINTS/2  2> ERRORS/2  &
find ${DIRS_0} -type f -iname '[JKL7]*'  -printf '\0%p ' -exec fpcalc  '{}' \; > FINGERPRINTS/3  2> ERRORS/3  &
find ${DIRS_1} -type f -iname '[MNO6]*'  -printf '\0%p ' -exec fpcalc  '{}' \; > FINGERPRINTS/4  2> ERRORS/4  &
find ${DIRS_2} -type f -iname '[PQR5]*'  -printf '\0%p ' -exec fpcalc  '{}' \; > FINGERPRINTS/5  2> ERRORS/5  &
find ${DIRS_0} -type f -iname '[STU4]*'  -printf '\0%p ' -exec fpcalc  '{}' \; > FINGERPRINTS/6  2> ERRORS/6  &
find ${DIRS_1} -type f -iname '[VXZ3]*'  -printf '\0%p ' -exec fpcalc  '{}' \; > FINGERPRINTS/7  2> ERRORS/7  &
find ${DIRS_2} -type f -iname '[WY02]*'  -printf '\0%p ' -exec fpcalc  '{}' \; > FINGERPRINTS/8  2> ERRORS/8  &

fg ; fg ; fg ; fg ; fg ; fg ; fg ; fg ; fg ; fg ; fg ; fg

wait ; wait ; wait ; wait ; wait ; wait ; wait ; wait ; wait ; wait

cat FINGERPRINTS/* | tr  '\n' ' ' | tr '\0' '\n' | awk -F / '{print $NF}' | sort -n > FINGERPRINTS.txt
'''
