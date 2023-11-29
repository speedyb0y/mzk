#!/usr/bin/python

import sys
import os
import time
import orjson as json
import cbor2 as cbor
import requests

TOKEN = "b'lfvGgAYa"

session = requests.session()

for f in sys.argv[1:]:

    for line in open(f).read().split('\n'):

        if line == '':
            continue

        # XID DURATION=282 FINGERPRINT=AQADtEueJUrCJIF_hLan4Dn05EH2
        xid, duration, fingerprint = line.split()

        _, duration    = duration   .split('=', 1)
        _, fingerprint = fingerprint.split('=', 1)

        duration = int(duration)

        try:
            response = session.get(f'https://api.acoustid.org/v2/lookup?client={TOKEN}&meta=recordings+releasegroups+releases+tracks+usermeta&duration={duration}&fingerprint={fingerprint}', headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.5',
            }).text
        except KeyboardInterrupt:
            raise
        except BaseException as e:
            continue

        print((xid, duration, fingerprint, response))
