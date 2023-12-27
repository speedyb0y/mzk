#!/usr/bin/python

import sys
import os
import time
import orjson
import json
import socket

'''
class Socket (socket.socket):

    def __init__ (self, *x, **k):
        super().__init__(*x, **k)
        self.connect(('192.0.0.1', 443))
        self.send(b''.join((
            (0x01).to_bytes(length=1, signed=False, byteorder='big'),
        len(b'api.acoustid.org').to_bytes(length=1, signed=False, byteorder='big'),
            (443).to_bytes(length=2, signed=False, byteorder='big'),
            b'api.acoustid.org',
            b'\x00'
            )))
        assert self.recv(4) == b'\x00'

    def connect(self, *_):
        pass

socket.socket = Socket
'''

json.dumps = orjson.dumps
json.loads = orjson.loads

import cbor2 as cbor
import requests

TOKEN = "b'lfvGgAYa"

session = requests.Session()

def cacheado (C, obj):
    if isinstance(obj, dict):
        return {cacheado(C, k) : cacheado(C, v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [cacheado(C, o) for o in obj]
    else:
        if isinstance(obj, (str, bytes)):
            obj = ' '.join(obj.upper().split())
        try:
            n = C[obj]
        except KeyError:
            n = C[obj] = len(C)
        return n

for f in sys.argv[1:]:

    cache = {}

    lista = []

    for xid, duration, fingerprint in (l.split() for l in open(f).read().split('\n') if l):

        duration = int(duration)

        try:
            response = session.get(f'https://api.acoustid.org/v2/lookup?client={TOKEN}&meta=recordings+releases+releasegroups&duration={duration}&fingerprint={fingerprint}', headers = {
                'User-Agent': 'MyCollectionTagger',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.5',
            }).json()
        except KeyboardInterrupt:
            raise
        except BaseException as e:
            continue

        # assert '\r' not in response
        # print(xid, duration, fingerprint, response)

        lista.append((xid, duration, fingerprint, cacheado(cache, response)))

    lista = cbor.dumps((cache, lista))

    cache.clear()

    fd = os.open(f'{f}.cbor', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    assert os.write(fd, lista) == len(lista)
    os.close(fd)


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

# vai = cbor.dumps([(xid, int(length.decode()), fp, json.loads(este := info)) for xid, length, fp, info in (line.split(b' ', 3) for line in open('PEGOS.txt', 'rb').read().split(b'\n') if line) if info and not info.startswith(b'upstream connect error')])
