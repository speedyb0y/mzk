#!/usr/bin/python

import sys
import os
import re
import json
import cbor2 as cbor
import html

import mutagen
import mutagen.flac
import mutagen.mp3
import mutagen.ogg
import mutagen.mp4

FLAC = mutagen.flac.FLAC
MP3  = mutagen.mp3.MP3
OGG  = mutagen.File
M4A  = mutagen.mp4.MP4

ALPHABET = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

FEX = b''

try:
    PATHS_, MUSICS = cbor.loads(open('MUSICS.cbor', 'rb').read())
except FileNotFoundError:
    PATHS_, MUSICS = [], {}

PATHS = { tuple(k): i for i, k in enumerate(PATHS_) }

def name_to_code (name):
    assert len(name) == 10
    code = sum(ALPHABET.index(l)*(len(ALPHABET)**i) for i, l in enumerate(name))
    assert 1 <= code <= 0xFFFFFFFFFFFFFFFF, code
    return code

def code_to_name (code):
    assert 1 <= code <= 0xFFFFFFFFFFFFFFFF, code
    name = ''.join(ALPHABET[(code // (len(ALPHABET)**i)) % len(ALPHABET)] for i in range(10))
    assert len(name) == 10
    return name

def music_path (code):
    return code_to_name(code).join(PATHS_[MUSICS[code][0]])

def music_load (fpath, prefix='/'):

    if fpath.startswith('file:/'):
        fpath = fpath[len('file:'):]

    *folder, name = (d for d in fpath.split('/') if d and d != '.')

    folder = prefix + '/'.join(folder) + '/'

    name, ext = name.rsplit('.')

    code = name_to_code(name)
    assert code_to_name(code) == name

    fex = folder, '.' + ext

    #
    try:
        pcode = PATHS[fex]
    except KeyError:
        pcode = PATHS[fex] = len(PATHS_)
        PATHS_.append(fex)

    #
    fpath = prefix + fpath

    st = os.stat(fpath)

    size  = st.st_size
    mtime = st.st_mtime

    #
    try:
        pcode_, size_, mtime_, bits_, channels_, sample_rate_, total_samples_, info = MUSICS[code]
    except KeyError:
        pcode_, size_, mtime_, bits_, channels_, sample_rate_, total_samples_, info = pcode, 0, 0, 0, 0, 0, 0, {}

    assert pcode == pcode_

    channels = 0
    total_samples = total_samples_
    sample_rate = sample_rate_
    bits = bits_
    channels = channels_

    if size != size_ or mtime != mtime_:
        tagged = (FLAC, MP3, OGG, OGG, M4A)[('flac', 'mp3', 'ogg', 'opus', 'm4a').index(ext)](fpath)

        if isinstance(tagged, FLAC):
            channels      = tagged.info.channels
            bits          = tagged.info.bits_per_sample
            total_samples = tagged.info.total_samples
            sample_rate   = tagged.info.sample_rate
        else:
            sample_rate = 48000
            total_samples =    int(tagged.info.length * sample_rate)
            bits = 16
            channels = 0

        #
        if tagged.tags is not None:
            info = {
                '-'.join(str(k).split()).upper() :
                ' '.join(''.join(v).split()).upper()
                for k, v in tagged.items()
                    if k
            }

    # SALVA COM O PATH ATUALIZADO
    MUSICS[code] = pcode, size, mtime, bits, channels, sample_rate, total_samples, info

    return code, pcode, size, mtime, bits, channels, sample_rate, total_samples, info

def some_tag (tags, labels):
    val = ''
    for label in labels:
        try:
            val = info[label]
        except KeyError:
            pass
        else:
            break
    return val

VLC_DIR = '/home/speedyb0y/.local/share/vlc'

#
try:
    os.mkdir(f'{VLC_DIR}/pls/')
except FileExistsError:
    pass

for pls in os.listdir('/home/speedyb0y/.config/quodlibet/playlists'):

    x = open(f'/home/speedyb0y/.config/quodlibet/playlists/{pls}', 'r').read()

    pls = pls[:-len('.xspf')]

    fd = open(f'{VLC_DIR}/pls/{pls}.xspf', 'w')
    fd.write(f'<?xml version="1.0" encoding="UTF-8"?><playlist><title>{pls}</title><trackList>\n')

    for fpath in re.findall(r'<location>([^<]*)<', x):

        code, pcode, size, mtime, bits, channels, sample_rate, total_samples, info = music_load(fpath)

        #
        fpath = music_path(code)

        #
        duration = total_samples // sample_rate

        artist = some_tag(info, ('ARTIST', 'ARTISTS', 'PERFORMER', 'PERFORMERS', 'ALBUMARTIST', 'ALBUMARTISTS'))
        title  = some_tag(info, ('TITLE', 'NAME', 'SONG'))
        album  = some_tag(info, ('ALBUM',))

        album, artist, title = map(html.escape, (album, artist, title))

        #
        xx = '%02d:%02d:%02d | %2d-BIT %d CHN %06d HZ' % (duration//3600, (duration%3600)//60, duration%60, bits, channels, sample_rate)

        fd.write(
            f'<track>'
                f'<location>file://{fpath}</location>'
                f'<album>{album}</album>'
                f'<creator>{artist}</creator>'
                f'<title>{title}</title>'
                f'<duration>{duration}</duration>'
                f'<annotation>{xx} | {artist} | {title}</annotation>'
            '</track>'
        )

    fd.write('</trackList></playlist>\n')
    fd.close()

db = cbor.dumps((PATHS_, MUSICS))

assert open('MUSICS.cbor', 'wb').write(db) == len(db)
