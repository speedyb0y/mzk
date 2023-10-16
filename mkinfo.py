#!/usr/bin/python

import sys
import os
import time
import re
import cbor2 as cbor

# find testa/ -type f -printf '\n\v\r\n%f\n' -exec soxi '{}' \; > LISTAAA

for lista in sys.argv[1:]:

    print('LISTA:', lista)

    musics = {}

    for fi in open(lista, 'rb').read().split(b'\n\v\r\n'):

        fi = fi.split(b'\n')

        if len(fi) <= 2:
            continue

        ( fname, _,
            _fname,
            channs,
            sampleRate,
            bits,
            duration,
            _size,
            bitrate,
            encoding,
            __,
            *tags,
        ) = fi

        assert not _ and __.startswith(b'Comments       : '), (_, __)

        # FILE NAME
        fname = fname.rsplit(b'/')[-1].decode()

        assert re.match('^[0-9A-Z]{12}[.](flac|opus|aac|mp3|ogg)$', fname), fname
        assert fname not in musics, fname

        # ENCODING FORMAT
        encoding = {
            b'Sample Encoding: Vorbis'      : 'VORBIS',
            b'Sample Encoding: Opus'        : 'OPUS',
            b'Sample Encoding: 16-bit FLAC' : 'FLAC',
            b'Sample Encoding: 24-bit FLAC' : 'FLAC',
            b'Sample Encoding: 32-bit FLAC' : 'FLAC',
        } [encoding]

        # BIT DEPTH
        bits = {
            b'Precision      : 16-bit': 16,
            b'Precision      : 24-bit': 24,
            b'Precision      : 32-bit': 32,
        } [bits]

        #
        (channs, sampleRate, bitrate) = ( b' '.join(x.split(b':', 1)[1].split()).decode() for x in
        (channs, sampleRate, bitrate))

        channs = int(channs)
        sampleRate = int(sampleRate)

        assert 1 <= channs <= 16
        assert 1 <= sampleRate <= 800000

        # b'Duration       : 00:03:58.68 = 22913373 samples ~ 17901.1 CDDA sectors'
        (duration, samples, cdda), = re.findall(r'^Duration       : ([^\s]*) = ([^\s]*) samples . ([^\s]*) CDDA sectors$', duration.decode())

        samples = int(samples)
        cdda = int(float(cdda))

        assert 1 <= samples <= 1000000000
        assert 1 <= cdda <= 1000000000

        TAGS = {}

        for key, val in { (b'-'.join(k.upper().replace(b'_', b' ').replace(b'-', b' ').split()).decode(), b' '.join(v.split()).decode())
            for k, v in (kv.split(b'=', 1) for kv in tags if b'=' in kv)
                if k
        }:
            if key in ('ORIGINAL-SAMPLERATE', 'ORIGINAL-SAMPLES', 'ORIGINAL-CHANNELS', 'ORIGINAL-BITS', 'CONVERSION-TIME'):
                val = int(val)
            try:
                TAGS[key].add(val)
            except KeyError:
                TAGS[key] = { val }

        tags = { k: (v.pop() if len(v) == 1 else sorted(v)) for k, v in TAGS.items() }

        musics[fname] = encoding, channs, bits, sampleRate, bitrate, samples, tags

    print('LISTA:', lista, len(musics))

    musics = cbor.dumps(musics)

    # SAVE AS TEMPORARY
    assert open(f'{lista}.cbor.tmp', 'wb').write(musics) == len(musics)

    # RENAME TEMPORARY
    os.rename(f'{lista}.cbor.tmp',
              f'{lista}.cbor')
