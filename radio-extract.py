#!/usr/bin/python
#
# python ~/streamit.py /mnt/radios/*/1???????????[0-9]
# rm -r -f -- /mnt/radios/*/incomplete
#
#  for x in */*.{mp3,aac} ; do mv -n -- "${x}" "${x// /-}" ; done
#  for x in */*.{mp3,aac} ; do mv -n -- "${x}" "$(dirname "${x}")/$(basename ${x^^})" ; done
#

import sys
import os
import mmap
import time
import socket
import re

PORT = 10000 + int(time.time()) % 5000

#
listener = socket.socket()
listener.bind(('127.0.0.1', PORT))
listener.listen()

#
for ipath in sys.argv[1:]:

    print(f'FILE {ipath}')

    direc, T = ipath.rsplit('/', 1)

    try:
        T = int(T)
    except:
        continue

    radioName = direc.rsplit('/', 1)[-1]

    assert 3 <= len(radioName) <= 128
    assert 1000000000 <= T <= int(time.time() * 1000)

    # OPEN THE FILE
    ifd = open(ipath, 'rb')

    # LOAD THE FILE
    ibuff = ifd.read()

    # GET THE FILE SIZE
    isize = len(ibuff)

    # GET THE HTTP HEADER SIZE
    hsize = ibuff.find(b'\r\n\r\n', 8, 8192)

    print(f'FILE {ipath} SIZE {isize}')

    if isize < 512*1024:

        print(f'FILE {ipath} SIZE {isize}: TOO SMALL')

    elif not ibuff.startswith(b'HTTP/1.'):

        print(f'FILE {ipath} SIZE {isize}: NO HTTP HEADER START')

    elif hsize == -1:

        print(f'FILE {ipath} SIZE {isize}: NO HTTP HEADER END')

    elif (ibuff.find(b'Transfer-Encoding: chunked', 0, hsize) != -1 or
          ibuff.find(b'transfer-encoding: chunked', 0, hsize) != -1):

        print(f'FILE {ipath} SIZE {isize}: HTTP CHUNKED')

        assert False

    else:
        # TITLES
        titles = sorted({b' '.join(f.upper().split()) for f in re.findall(b"StreamTitle='([^']*)'", ibuff)})

        print(f'FILE {ipath} SIZE {isize}: TITLES {len(titles)}')

        # SAVE TITLES
        if titles:
            titles = open(f'{direc}/{T}.txt', 'wb').write(b'\n'.join(titles) + b'\n')

        # MIME TYPE -> EXTENSION
        ext = {
            b'audio/mpeg' : 'mp3',
            b'audio/aacp' : 'aac',
            b'audio/aac'  : 'aac',
            b'audio/flac' : 'flac',
            b'audio/opus' : 'opus',
            b'audio/ogg'  : 'ogg',
            b'audio/m4a'  : 'm4a',
        }[re.findall(b'[Cc]ontent-[Tt]ype:\s*([^\s]*)', ibuff[:hsize])[0]]

        # LAUNCH STREAM-RIPPER
        pipe = os.popen(f'streamripper http://127.0.0.1:{PORT}/{radioName}.{ext} -s -c -d {direc} -D "{T}-%q-%A-%T" --xs2 --quiet 2>&1')

        # WAIT FOR STREAM-RIPPER
        sock, *_ = listener.accept()

        # SEND TO STREAM-RIPPER
        offset = 0

        try:
            while offset < isize:
                offset += os.write(sock.fileno(), ibuff[offset:offset+8*1024*1024])
            assert offset == isize
            # TELL STREAM-RIPPER WE ENDED
            sock.shutdown(socket.SHUT_WR)
            # WAIT STREAM RIPPER TO CLOSE ITS CONNECTION
            while sock.recv(1*1024*1024):
                pass
        except BaseException as e:
            print('ERROR:', e, repr(e), str(e))
            assert e.errno in (
                104, # ?
                107, # Transport endpoint is not connected
            )

        # WAIT STREAMRIPPER TO EXIT
        while pipe.read(1*1024*1024):
            pass

        pipe.close()
        sock.close()

    ifd.close()

    #
    os.unlink(ipath)
