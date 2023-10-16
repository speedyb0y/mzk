#!/usr/bin/python

import sys
import cbor2 as cbor
import base64

'''
import time
import cbor2 as cbor

x = cbor.dumps(app.library._contents)
assert len(x) == open(f'/home/speedyb0y/quodlibet-{int(time.time())}.cbor', 'wb').write(x)
assert len(x) == open(f'/home/speedyb0y/quodlibet.cbor', 'wb').write(x)

app.library._contents = { fpath: { k.lower() : (v.upper() if isinstance(v, str) else v) for k, v in info.items() } for fpath, info in app.library._contents.items() }

'''

# '/arquivos/aiff/Ipo8k90D.aiff', {'~#length': 236.06333333333333,
#'~#bitrate': 1411, '~#channels': 2, '~#samplerate': 44100, 'genre': 'Rock', 'album': 'Metal Hammer #147: Razor: Music From the Cutting Edge: Xmas 2005', 'title': 'Nobody', 'artist': 'Skindred', '~filename': '/arquivos/aiff/Ipo8k90D.aiff', '~mountpoint': '/arquivos', '~#added': 1691371780, '~#mtime': 1691405581.1210637, '~#filesize': 41642864, '~#laststarted': 1691384838, '~#skipcount': 1, 'date': '2005-12', 'tracknumber': '9/19'})

def pega(finfo, Ks):
    for k in Ks:
        try:
            v = finfo[k]
        except:
            v = ''
        yield ' '.join(str(v).split())

for fentry, finfo in cbor.loads(open('quodlibet.cbor', 'rb').read()).items():

    ( ffilename,  falbum,  fartist,  ftracknumber,  ftitle,    fbitrate,    fchannels,    fsamplerate,    fmtime,    ffilesize,    flength) = pega(finfo,
    ('~filename', 'album', 'artist', 'tracknumber', 'title', '~#bitrate', '~#channels', '~#samplerate', '~#mtime', '~#filesize', '~#length'))

    # assert fentry == ffilename, print(repr(fpath), '\n', repr(ffilename))

    if isinstance(flength, float):
        flength = int(flength)
    elif flength != '':
        flength = int(float(flength))

    fdir, fname = ffilename.rsplit('/', 1)

    # assert fname.count('.') == 1

    fhash, fextension = fname.rsplit('.', 1)

    if fextension == 'wav':
        continue

    try:
        fid = int.from_bytes(base64.b64decode(fhash, '_,'), signed=False, byteorder='big')
    except:
        # print(fentry)
        # raise
        continue

    print('|'.join(map(str, (fid, fhash, fextension, fdir, fchannels, fsamplerate, fbitrate, ffilesize, flength, falbum, ftracknumber, fartist, ftitle))))


'''
 python ~/teste.py ~/quodlibet-1691444*.cbor | head -n 500 | tr ' ' '~' | tr '|' ' ' | column --table | tr '~' ' '
'''
