#!/usr/bin/python

import sys
import os
import traceback
import base64
import requests
import json
import cbor2 as cbor
import re

DB_PATH      = 'mzk-acoustid.cbor'
DB_PATH_TEMP = 'mzk-acoustid.cbor.tmp'

apiKey = "b'lfvGgAYa"

fdx = os.open('/dev/null', os.O_RDONLY)
os.close(fdx)

cmd = f'fpcalc -json /proc/{os.getpid()}/fd/{fdx}'

#
session = requests.Session()

# FILE_CODE -> FINGERPRINT_ID
files = {}

fingersMap    = {}
fingers       = []
fingersTracks = []

tracksMap  = {}
tracks     = []
tracksRecs = []
tracksRels = []

artistsMap = {}
artists    = []

try:
    files, fingers, fingersTracks, tracks, tracksRecs, tracksRels, artists = cbor.loads(open(DB_PATH, 'rb').read())
except:
    # exit(1)
    pass

fingersMap = { (d, f): i for i, (d, f) in enumerate(fingers) }
tracksMap  = { t: i for i, t in enumerate(tracks)  }
artistsMap = { a: i for i, a in enumerate(artists) }

assert isinstance(files,         dict)
assert isinstance(fingersMap,    dict)
assert isinstance(fingers,       list)
assert isinstance(fingersTracks, list)
assert isinstance(tracksMap,     dict)
assert isinstance(tracks,        list)
assert isinstance(tracksRecs,    list)
assert isinstance(tracksRels,    list)
assert isinstance(artistsMap,    dict)
assert isinstance(artists,       list)

assert len(fingersMap) == len(fingers)
assert len(fingersMap) == len(fingersTracks)
assert len(tracksMap)  == len(tracks)
assert len(tracksMap)  == len(tracksRecs)
assert len(tracksMap)  == len(tracksRels)
assert len(artistsMap) == len(artists)

def IDENTIFY_FINGERPRINT (duration, fingerprint):
    df = duration, fingerprint
    try:
        fid = fingersMap[df]
    except KeyError:
        fid = fingersMap[df] = len(fingersMap)
        fingers.append(df)
        fingersTracks.append(())
    return fid

def IDENTIFY_TRACK (trackid):
    try:
        tid = tracksMap[trackid]
    except KeyError:
        tid = tracksMap[trackid] = len(tracksMap)
        tracks.append(trackid)
        tracksRecs.append(())
        tracksRels.append(())
    return tid

def IDENTIFY_ARTIST (artist):
    artist = ' '.join(artist.split())
    try:
        aid = artistsMap[artist]
    except KeyError:
        aid = artistsMap[artist] = len(artistsMap)
        artists.append(artist)
    return aid

try:
    for f in sys.argv[1:]:

        fname, extension = f.rsplit('/', 1)[-1].split('.')

        assert len(fname) == 10

        fcode = int.from_bytes(base64.b64decode(f'{fname}=='), byteorder='little', signed=False)

        print(fname, fcode, f)

        if fcode not in files:

            fd = os.open(f, os.O_RDONLY)
            assert fd == fdx
            fpcalc = json.loads(os.popen(cmd).read(1*1024*1024))
            os.close(fdx)

            duration = int(fpcalc['duration'])
            fingerprint = fpcalc['fingerprint']

            assert 1 <= duration <= 24*60*60, duration
            assert 64 <= len(fingerprint) <= 1*1024*1024, (f, len(fingerprint))

            files[fcode] = IDENTIFY_FINGERPRINT(duration, fingerprint)

    for (duration, fingerprint), fid in fingersMap.items():

        if not fingersTracks[fid]:

            print(f'FETCH ACOUSTID #{fid}...')

            response = session.get(f'https://api.acoustid.org/v2/lookup?client={apiKey}&meta=&duration={duration}&fingerprint={fingerprint}')
            response = json.loads(response.text)

            status = response['status']

            if status != 'ok':
                print('STATUS NOT OK:', repr(response))
                continue

            response = response['results']

            fingersTracks[fid] = [(b, a) for a, b in sorted(set(( int(float(result['score'])*1000), IDENTIFY_TRACK(result['id'])) for result in response))]

    for trackid, tid in tracksMap.items():

        if not tracksRecs[tid]:
            #recordings,recordingids,releases,releaseids,releasegroups,releasegroupids,tracks,compress,usermeta,sources
            print(f'FETCH RECORDING #{tid}...')

            response = session.get(f'https://api.acoustid.org/v2/lookup?client={apiKey}&meta=recordings&trackid={trackid}')

            response = json.loads(response.text)

            status = response['status']

            if status != 'ok':
                print('STATUS NOT OK:', repr(response))
                continue

            tracksRecs[tid] = sorted({ (tuple(sorted({IDENTIFY_ARTIST(a['name']) for a in (rec['artists'] if 'artists' in rec else ())})), rec['title'].strip())
                for result in response['results']
                    if 'recordings' in result
                        for rec in result['recordings']
                            if 'title' in rec
            })

except KeyboardInterrupt:
    pass
except:
    print('ERROR!!!')
    traceback.print_exc()

db = cbor.dumps((files, fingers, fingersTracks, tracks, tracksRecs, tracksRels, artists))

#
assert open(DB_PATH_TEMP, 'wb').write(db) == len(db)

os.rename(DB_PATH_TEMP, DB_PATH)


for fcode, fid in files.items():
    for tid, score in fingersTracks[fid]:
        for arts, title in tracksRecs[tid]:
            print((fcode, fid, score, '; '.join(artists[a] for a in arts), title))
    print()
