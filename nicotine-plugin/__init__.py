#!/usr/bin/python

import sys
import os
import time
import cbor2 as cbor
import re
import xxhash

import pynicotine

from pynicotine.pluginsystem import BasePlugin

# grep def /usr/lib/python*/site-packages/pynicotine/pluginsystem.py

class Plugin (BasePlugin):

    def __init__(self, *args, **kwargs):
        print('MUZIK: INITALIZING')
        super().__init__(*args, **kwargs)

    # TODO: FIXME: VAI FUNCIONAR MESMO SE O ARQUIVO NAO ESTIVER NO MESMO SISTEMA DE ARQUIVOS?
    # POIS PODE ANUNCIAR QUE TERMINOU O DOWNLOAD, MAS AINDA ESTAR MOVENDO O ARQUIVO...
    def download_finished_notification (self, user, vpath, rpath):
        fline = f'{user}\x00{vpath}\x00{os.stat(rpath).st_size}'.encode()
        KNOWNS.add(HASHER(fline))
        fline += b'\x01'
        assert os.write(fd, fline) == len(fline)

    def upload_finished_notification(self, user, virtual_path, real_path):
        print('MUZIK: upload_finished_notification()', user, virtual_path, real_path)

    # def incoming_public_chat_notification(self, room, user, line):
        # print('MUZIK: incoming_public_chat_notification()', room, user, line)

    # def incoming_private_chat_notification(self, user, line):
        # print('MUZIK: incoming_private_chat_notification()', user, line)

    def search_request_notification(self, *_):
        print('MUZIK: search_request_notification()', repr(_))

    def distrib_search_notification(self, term, user, token):
        # print(f'MUZIK: USER: {user} TOKEN: {token} TERM: {term}')
        pass

    # def outgoing_global_search_event(self, *_):
        # print('MUZIK: outgoing_global_search_event()', repr(_))

    # def outgoing_room_search_event(self, *_):
        # print('MUZIK: outgoing_room_search_event()', repr(_))

    # def outgoing_buddy_search_event(self, *_):
        # print('MUZIK: outgoing_buddy_search_event()', repr(_))

    # def outgoing_user_search_event(self, *_):
        # print('MUZIK: outgoing_user_search_event()', repr(_))

def add_result_list(self, results, user, country, inqueue, ulspeed, h_speed, h_queue, color, private=False):

    # self.num_results_found
    self.max_limit = 100000
    self.max_limited = False

    #
    # '~Music (Sorted) (G)\\Metal\\Opeth (Sweden)\\01. Studio Albums\\1995 (2008) - Orchid (Japanese Edition)\\01. In Mist She Was Standing.mp3',
    # fsize, None, {0: 320, 1: 849, 2: 0}
    #)

    return ADD_RESULT_LIST(self, [ (order, fpath, fsize, nada, dic)
        for order, fpath, fsize, nada, dic in results
            if (hsh_ := HASHER(f'{user}\x00{fpath}\x00{fsize}'.encode())) not in KNOWNS
                if HASHER(f'{user}\x00{fpath}'.encode()) not in KNOWNS
                    if fsize <= 350*1024*1024 and fpath.lower().endswith(('.flac', '.wav', '.wv', '.wvc', '.aif', '.aiff', '.opus', '.mp3', '.ogg', '.cue', '.ape', '.wma', '.m4a', '.aac',
    '.avi', '.mkv', '.mp4', '.flv', '.mpg', '.mpeg'))
                        if KNOWNS.add(hsh_) is None
    ], user, country, inqueue, ulspeed, h_speed, h_queue, color, private)

HASHER = xxhash.xxh128_intdigest
HASHER = bytes.__hash__

try:
    KNOWNS = set(map(HASHER, open(f'/home/speedyb0y/NICOTINE-DOWNLOADED', 'rb').read().split(b'\x01')))
except:
    print('FAILED TO LOAD')
    exit(1)

print(f'HAS {len(KNOWNS)} FILES')

if os.system(f'cp -v -- /home/speedyb0y/NICOTINE-DOWNLOADED /home/speedyb0y/NICOTINE-DOWNLOADED-{int(time.time()*1000)}'):
    print('FAILED TO BACKUP')
    exit(1)

fd = os.open(f'/home/speedyb0y/NICOTINE-DOWNLOADED', os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o0644)

# PATCH
ADD_RESULT_LIST = pynicotine.gtkgui.search.Search.add_result_list
pynicotine.gtkgui.search.Search.add_result_list = add_result_list

# TODO: INCLUIR FILE SIZE USANDO O FSTAT APOS CONCLUIR O DOWNLOAD
