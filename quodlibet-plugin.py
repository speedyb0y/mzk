#!/usr/bin/python

# sudo ln -s -f -n /home/speedyb0y/MUZIK/quodlibet-console.py /usr/lib/python3.11/site-packages/quodlibet/ext/songsmenu/console.py

import sys
import os
import re
from itertools import takewhile

from gi.repository import Gtk, GLib

from quodlibet import _, app, ngettext
from quodlibet import const
from quodlibet.plugins.events import EventPlugin
from quodlibet.plugins.gui import UserInterfacePlugin
from quodlibet.qltk import Icons
from quodlibet.plugins.songsmenu import SongsMenuPlugin
# from quodlibet.util.collection import Collection
# from quodlibet.util import print_

class PyConsole(SongsMenuPlugin):
    PLUGIN_ID = 'Python Console'
    PLUGIN_NAME = _('Python Console')
    PLUGIN_DESC = _('Interactive Python console. Opens a new window.')
    PLUGIN_ICON = Icons.UTILITIES_TERMINAL

    def plugin_songs(self, songs):
        print(songs[0])
        print(songs)

class PyConsoleSidebar(EventPlugin, UserInterfacePlugin):
    PLUGIN_ID = 'Python Console Sidebar'
    PLUGIN_NAME = _('Python Console Sidebar')
    PLUGIN_DESC = _('Interactive Python console sidebar, '
                    'that follows the selected songs in the main window.')
    PLUGIN_ICON = Icons.UTILITIES_TERMINAL

    def enabled(self):
        print('ENABLED')

    def plugin_on_songs_selected(self, songs):
        if songs:
            print(songs[0]._song['~filename'])

'''
    def create_sidebar(self):
        align = Align(self.console)
        self.sidebar = align
        self.sidebar.show_all()
        return align
'''

from struct import pack, unpack
from enum import Enum

class Flag(Enum):
    IS_SUBTRACK = 1 << 0  # file is not single-track, might have metainfo in external file
    IS_READONLY = 1 << 1  # check this flag to block tag writing (e.g. in iso.wv)
    HAS_EMBEDDED_CUESHEET = 1 << 2

    TAG_ID3V1 = 1 << 8
    TAG_ID3V22 = 1 << 9
    TAG_ID3V23 = 1 << 10
    TAG_ID3V24 = 1 << 11
    TAG_APEV2 = 1 << 12
    TAG_VORBISCOMMENTS = 1 << 13
    TAG_CUESHEET = 1 << 14
    TAG_ICY = 1 << 15
    TAG_ITUNES = 1 << 16

    TAG_MASK = 0x000fff00

class Track:

    def __init__(self):
        self.uri = None
        self.decoder = ''
        self.num = 0
        self.startsample = 0
        self.endsample = 0
        self.duration = 0
        self.filetype = ''
        self.replaygain_albumgain = 0
        self.replaygain_albumpeak = 0
        self.replaygain_trackgain = 0
        self.replaygain_trackpeak = 0
        self.flags = 0
        self.meta = {}

    def get_uri(self):
        return self.meta[':URI']

    def get_startsample(self):
        return self.meta[':STARTSAMPLE'] if ':STARTSAMPLE' in self.meta else self.startsample

    def set_startsample(self, value):
        self.startsample = value
        self.meta[':STARTSAMPLE'] = value

    def get_endsample(self):
        return self.meta[':ENDSAMPLE'] if ':ENDSAMPLE' in self.meta else self.endsample

    def set_endsample(self, value):
        self.endsample = value
        self.meta[':ENDSAMPLE'] = value

    def get_writable_meta(self):
        meta = {}
        for key, value in self.meta.items():
            if key[0] != '_' and key[0] != '!':
                meta[key] = value
        return meta

    def pack(self):
        buf = bytearray()

        uri_b = self.get_uri().encode()
        buf.extend(pack('H', len(uri_b)))
        buf.extend(uri_b)

        if self.decoder:
            decoder_b = self.decoder.encode()
            buf.append(len(decoder_b))
            buf.extend(decoder_b)
        else:
            buf.append(0)

        buf.extend(pack('h', self.num))
        buf.extend(pack('i', self.get_startsample()))
        buf.extend(pack('i', self.get_endsample()))
        buf.extend(pack('f', self.duration))

        ft_b = self.filetype.encode()
        buf.append(len(ft_b))
        if len(self.filetype):
            buf.extend(ft_b)

        buf.extend(pack('f', self.replaygain_albumgain))
        buf.extend(pack('f', self.replaygain_albumpeak))
        buf.extend(pack('f', self.replaygain_trackgain))
        buf.extend(pack('f', self.replaygain_trackpeak))
        buf.extend(pack('I', self.flags))

        meta = self.get_writable_meta()
        buf.extend(pack('h', len(meta)))

        for key, value in meta.items():
            value = str(value).encode()
            key = key.encode()
            key_len, value_len = len(key), len(value)

            buf.extend(pack('H', key_len))
            if key_len:
                buf.extend(key)

            buf.extend(pack('H', value_len))
            if value_len:
                buf.extend(value)

        return bytes(buf)

class Playlist:

    MINOR_VERSION = 2
    MAJOR_VERSION = 1

    def __init__(self, file):
        self.file = file
        self.major_version = None
        self.minor_version = None
        self.tracks = []
        self.meta = {}
        
    def add_track(self, track):
        self.tracks.append(track)

    def pack(self):
        pass

    def load(self):
        with open(self.file, 'rb') as f:

            # MAGIC
            assert f.read(4) == b'DBPL'

            # uint8_t
            self.major_version, self.minor_version = unpack('BB', f.read(2))

            assert self.major_version == 1
            assert self.minor_version >= 1

            # uint32_t
            tracks_count = unpack('I', f.read(4))[0]

            for i in range(tracks_count):
                track = Track()

                if self.minor_version <= 2:
                    # uint16_t
                    uri_len = unpack('H', f.read(2))[0]
                    track.uri = f.read(uri_len).decode()

                    # uint8_t
                    decoder_len = unpack('B', f.read(1))[0]
                    if decoder_len >= 20:
                        raise ValueError('invalid decoder length %d' % decoder_len)

                    if decoder_len:
                        track.decoder = f.read(decoder_len).decode()

                    # int16_t
                    track.num = unpack('h', f.read(2))[0]

                # int32_t
                ss, es = unpack('ii', f.read(8))
                track.set_startsample(ss)
                track.set_endsample(es)

                # float
                track.duration = unpack('f', f.read(4))[0]

                if self.minor_version <= 2:
                    # legacy filetype support, they say
                    # uint8_t
                    filetype_len = unpack('B', f.read(1))[0]
                    if filetype_len:
                        track.filetype = f.read(filetype_len).decode()

                    # floats
                    ag, ap, tg, tp = unpack('ffff', f.read(16))
                    if ag != 0:
                        track.replaygain_albumgain = ag
                    if ap != 0 and ap != 1:
                        track.replaygain_albumpeak = ap
                    if tg != 0:
                        track.replaygain_trackgain = tg
                    if tp != 0 and tp != 1:
                        track.replaygain_trackpeak = tp

                if self.minor_version >= 2:
                    # uint32_t
                    track.flags = unpack('I', f.read(4))[0]
                elif track.startsample > 0 or track.endsample > 0 or track.num > 0:
                    track.flags |= Flag.IS_SUBTRACK

                # int16_t
                meta_count = unpack('h', f.read(2))[0]
                for j in range(meta_count):
                    # uint16_t
                    value_len = unpack('H', f.read(2))[0]
                    if value_len >= 20000:
                        raise ValueError('invalid key length')

                    key = f.read(value_len).decode()

                    value_len = unpack('H', f.read(2))[0]
                    if value_len >= 20000:
                        f.seek(value_len, os.SEEK_CUR)
                    else:
                        value = f.read(value_len)
                        if key[0] == ':':
                            if key == ':STARTSAMPLE':
                                track.set_startsample(int(value))
                            elif key == ':ENDSAMPLE':
                                track.set_endsample(int(value))
                            else:
                                track.meta[key] = value.decode()
                        else:
                            track.meta[key] = value.decode()

                self.add_track(track)

            assert tracks_count == len(self.tracks)

            # playlist metadata
            # int16_t
            meta_count = unpack('H', f.read(2))[0]
            for i in range(meta_count):
                # int16_t
                key_len = unpack('h', f.read(2))[0]
                if key_len < 0 or key_len >= 20000:
                    raise ValueError('invalid length')

                key = f.read(key_len).decode()

                # int16_t
                value_len = unpack('h', f.read(2))[0]
                if value_len < 0 or value_len >= 20000:
                    f.seek(value_len, os.SEEK_CUR)
                else:
                    value = f.read(value_len)
                    self.meta[key] = value.decode()
            
    def save(self, file: str = None) -> None:
        if file is None:
            file = self.file

        with open(file, 'wb') as f:
            f.write(b'DBPL')
            f.write(pack('BB', Playlist.MAJOR_VERSION, Playlist.MINOR_VERSION))
            f.write(pack('I', len(self.tracks)))
            for track in self.tracks:
                f.write(track.pack())

            f.write(pack('h', len(self.meta)))
            for key, value in self.meta.items():
                value = str(value)
                key_len, value_len = len(key), len(value)

                f.write(pack('H', key_len))
                if key_len:
                    f.write(key.encode())

                f.write(pack('H', value_len))
                if value_len:
                    f.write(value.encode())

print('FIXING LIBRARY...')

fixes = (
    ('artist', {
        ('GABRIEL, O PENSADOR', 'GABRIEL O PENSADOR'),
        ('LEGIAO URBANA', 'LEGIÃO URBANA'),
        ('TITAS', 'TITÃS'),
        ('TIT?S', 'TITÃS'),
        ('XIMENA SARINANA', 'XIMENA SARIÑANA'),
        ('XIMENA SARI?ANA', 'XIMENA SARIÑANA'),
        ('ALANIS MORISSETTE ALANIS MORISSETTE ALANIS MORISSETTE', 'ALANIS MORISSETTE'),
    }),
    ('title', ()),
    ('album', ()),
)

def some_tag (info, labels):
    val = ''
    for label in labels:
        for label in (label, label.upper(), label.lower()):
            try:
                val = info[label]
            except KeyError:
                pass
            else:
                break
    return val

pls = Playlist('/home/speedyb0y/.config/deadbeef/playlists/0.dbpl')

# pls.load()
# for track in pls.tracks:
    # print(track.meta)
    # input('---')

for fpath, finfo in app.library._contents.items():
    
    for label, repls in fixes:
        try:
            value = finfo[label]
            assert isinstance(value, str)
            value = ' '.join(value.split()).upper()
            for bef, aft in repls:
                value = value.replace(bef, aft)
        except KeyError:
            value = '?'
        finfo[label] = value

    artist = some_tag(finfo, ('ARTIST', 'ARTISTS', 'PERFORMER', 'PERFORMERS', 'ALBUMARTIST', 'ALBUMARTISTS'))
    title  = some_tag(finfo, ('TITLE', 'NAME', 'SONG'))
    album  = some_tag(finfo, ('ALBUM',))

    track = Track()
    track.meta[':URI'] = fpath
    track.meta[':FILETYPE'] = 'FLAC' # ':FILETYPE': 'Ogg Opus'
    track.meta[':CHANNELS'] = 1
    track.meta[':SAMPLERATE'] = 44100
    track.meta[':BITRATE'] = 320
    track.meta[':FILE_SIZE'] = 4*1024*1024
    track.set_startsample(0)
    track.set_endsample(800000)
    track.meta['album'] = album
    track.meta['artist'] = artist
    track.meta['title'] = title
        
    pls.add_track(track)

pls.save()

app.library.save()
print('SAVED!')
