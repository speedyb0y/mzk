#!/usr/bin/python

import sys
import os
import mutagen
import mutagen.flac
import mutagen.mp3
import mutagen.ogg
import mutagen.mp4

FLAC = mutagen.flac.FLAC
MP3  = mutagen.mp3.MP3
OGG  = mutagen.File
M4A  = mutagen.mp4.MP4

TAGS_TO_KEEP = {
    'IPLS', #    Involved people list
    'LINK', #    Linked information
    'MCDI', #    Music CD identifier
    'TALB', #    Album/Movie/Show title
    'TFLT', #    File type
    'TIT1', #    Content group description
    'TIT2', #    Title/songname/content description
    'TIT3', #    Subtitle/Description refinement
    'TOAL', #    Original album/movie/show title
    'TOFN', #    Original filename
    'TOPE', #    Original artist(s)/performer(s)
    'TPE1', #    Lead performer(s)/Soloist(s)
    'TPE2', #    Band/orchestra/accompaniment
    'TPE3', #    Conductor/performer refinement
    'TPE4', #    Interpreted, remixed, or otherwise modified by
    'TRCK', #    Track number/Position in set
    'WXXX', #    User defined URL link

    'ALBUM',
    'ALBUMARTIST',
    'ALBUMARTIST2',
    'ALBUMARTISTSORT',
    'ALBUMSORT',
    'ARTIST',
    'ARTISTSORT',
    'ARTISTS',
    'DISCSUBTITLE',
    'PERFORMER',
    'TITLE',
    'TRACK',
    'TRACKN',
    'TRACKNO',
    'TRACKNUMBER',
    'TRACKTOTAL',
    'TOTALTRACKS',
    'DISCID',
    'DISCNUMBER',
    'DISCTOTAL',

    'TOTALDISCS',

    'DESCRIPTION',

    'ORIGINAL_FILENAME',
    'ORIGINAL_PATH',
    'ENCODER',
    'ENCODER_OPTIONS',
    'YOUTUBE',

    'ALBUM ARTIST',
    'ALBUMARTISTNOSORT',
    'ALBUMARTISTS',
    'ALBUMARTISTSORTORDER',
    'ALBUMARTIST_CREDIT',
    'ALBUMSORTORDER',
    'ALBUMTITLE',
    'ALBUM_ARTIST',
    'ALBUM_ARTISTS_SORT',
    'ARTISTNOSORT',
    'ARTISTSORTORDER',
    'ARTISTS_SORT',
    'ARTIST_CREDIT',
    'AUTHOR',
    'NAME',
    'ORIGINAL FILENAME',
    'ORIGINAL TITLE',
    'ORIGINALARTIST',
    'ORIGINALSAMPLERATE',
    'PART',
    'PERFORMER_SORT',
    'REMIXED BY',
    'SORTALBUM',
    'SORT_ALBUM',
    'SORT_ALBUM_ARTIST',
    'SORT_ARTIST',
    'SUBTITLE',
    'TITLESORT',
    'TITLESORTORDER',
    'TOTAL TRACKS',
    'TOTALTRACK',
    'TRACKARTIST',
    'TRACKARTISTSORT',
    'ALBUMARTISTSSORT',
# ?

'TXXX:COVER ARTIST',
'TXXX:QUODLIBET::ALBUMARTIST',
'TXXX:TOTAL TRACKS',
'TXXX:VA ARTIST',

'TCMP',
'TCOM',
'TCON',
'TCOP',
'TDOR',
'TDRC',
'TDRL',
'TDTG',
'TENC',
'TIPL',
'TKEY',
'TLAN',
'TLEN',
'TMED',
'TPOS',
'TPUB',
'TSO2',
'TSOA',
'TSOP',
'TSSE',

'ORIGINALTITLE',
'BITRATE',
'BIT_DEPTH',
}

#
TAGS_TO_REMOVE = set(open(sys.argv[0].rsplit('.')[0] + '.txt').read().strip().split('\n'))

assert 50 <= len(TAGS_TO_REMOVE) <= 5000

for f in sys.argv[1:]:

    print(f)

    tagged = (FLAC, MP3, OGG, OGG, M4A)[('flac', 'mp3', 'ogg', 'opus', 'm4a').index(f.rsplit('.', 1)[1])](f)

    if tagged.tags is not None:

        modificou = None

        # if isinstance(tagged, FLAC):
            # tagged.clear_pictures()
            # modificou = tagged.save

        # REMOVE ALL EXCEPT THOSE
        for k in tuple(map(str, tagged.keys())):
            TAAAG = k.upper().strip()
            if TAAAG not in TAGS_TO_KEEP:
                if TAAAG not in TAGS_TO_REMOVE and not TAAAG.startswith('PRIV:'):
                    if len(TAAAG) > 64:
                        print(TAAAG[:128], '# !!!!!!!!!!!!!!!!!!')
                    else:
                        print(TAAAG)
                    TAGS_TO_REMOVE.add(TAAAG)
                del tagged.tags[k]
                modificou = tagged.save

        if modificou:
            modificou()
        tagged = None
