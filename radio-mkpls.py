#!/usr/bin/python

import sys
import os
import io
import stat
import time
import json
import cbor2 as cbor
import traceback
import random

#export LC_ALL=en_US.UTF-8

for radio in sys.argv[1:]:

    assert radio and '/' not in radio

    try:
        fs = sorted(os.listdir(radio))
    except NotADirectoryError:
        continue

    songs = {}

    try:
        songsOld = cbor.loads(open(f'{radio}.cbor', 'rb').read())
    except FileNotFoundError:
        songsOld = {}

    assert isinstance(songsOld, dict)

    pls = [
        '#EXTM3U',
        f'#PLAYLIST:{radio}'
    ]

    for _song in fs:

        if _song.endswith('.txt'):
            continue

        song = f'{radio}/{_song}'

        print(song)

        st = songsOld.pop(_song, None)

        if st is None:

            # ONLY IF EXISTS
            try:
                st = os.stat(song)
            except FileNotFoundError:
                print(f'{song}: SKIPPED (NOT FOUND)')
                continue

            # ONLY FILES
            if not stat.S_ISREG(st.st_mode):
                print(f'{song}: SKIPPED (NOT FILE)')
                continue

            size = st.st_size

            # NOT SMALL FILES
            if size < 128*1024:
                print(f'{song}: SKIPPED (TOO SMALL)')
                continue

            #
            try:
                with open(song, 'rb') as xxx:
                    with os.popen(f'ffprobe -v quiet -print_format json -show_format -show_streams -- /proc/{os.getpid()}/fd/{xxx.fileno()}') as fd:
                        fp = json.loads(fd.read(4*1024*1024))

                fpStream, = (s for s in fp['streams'] if s['codec_type'] == 'audio') # NOTE: ONLY SUPPORT FILES WITH 1 AUDIO STREAM

                ( # FORMAT
                    format, formatName, ORIGINAL_TAGS,
                    # STREAM
                    codec, codecName, bitsFMT, hz, channels, channelsLayout, bits, bitsRaw, seconds, XBITRATE, ORIGINAL_TAGS2
                ) = ( (d[k] if k in d and d[k] != '' else None)
                    for d, K in (
                        ( fp['format'], (
                            'format_name',
                            'format_long_name',
                            'tags',
                        )),
                        ( fpStream, (
                            'codec_name',
                            'codec_long_name',
                            'sample_fmt',
                            'sample_rate',
                            'channels',
                            'channel_layout',
                            'bits_per_sample',
                            'bits_per_raw_sample',
                            'duration',
                            'bit_rate',
                            'tags',
                        )),
                    )
                    for k in K
                )

            except BaseException:
                print(f'{song}: ERROR: FFPROBE FAILED')
                traceback.print_exc()
                continue

            # DO ARQUIVO QUE TEMOS AGORA
            channels    = int       (channels)
            hz          = int       (hz)
            # bitsFMT     = str.upper (bitsFMT)
            format      = str.upper (format)
            codec       = str.upper (codec)

            # bits           = (0   if bits           is None else int       (bits))
            # bitsRaw        = (0   if bitsRaw        is None else int       (bitsRaw))
            # channelsLayout = ('-' if channelsLayout is None else str.upper (channelsLayout))
            seconds        = (0   if seconds        is None else float     (seconds))

            assert codec and format

            # '_'.join(k[:80].replace('_', ' ').replace('-', ' ').split()).upper()
            T = { k.strip().upper(): ' '.join(v.split())[:300].rstrip().upper() for T in (ORIGINAL_TAGS, ORIGINAL_TAGS2) if T for k, v in T.items() if k and v}

            artist = T.pop('ARTIST', None)
            title  = T.pop('TITLE',  None)
            album  = T.pop('ALBUM',  None)
            year   = T.pop('YEAR',   None)
            genre  = T.pop('GENRE',  None)

        else:
            size, seconds, hz, channels, artist, title, album, year, genre, format, codec = st

        seconds = int(seconds)

        songs[_song] = (size, seconds, hz, channels, artist, title, album, year, genre, format, codec)

        pls.extend((f'#EXTINF:{seconds},{artist} – {title}', song))

    songs = cbor.dumps(songs)

    assert open(f'{radio}.cbor', 'wb').write(songs) == len(songs)

    pls.append('')

    open(f'{radio}.m3u', 'w').write('\n'.join(pls))
