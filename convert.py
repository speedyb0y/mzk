#!/usr/bin/python

# ARQUIVOS NA VERSÃO FINAL: @1699130361

import sys
import os
import io
import stat
import time
import json
import re
import traceback
import mmap
import random

tags = { t: set()
    for t in (
        'XALBUM',
        'XARTIST',
        'XCOMMENT',
        'XCOMPILATION',
        'XCOMPOSER',
        'XDATE',
        'XENCODED_BY',
        'XENCODER',
        'XFILENAME',
        'XGENRE',
        'XGROUP',
        'XLANG',
        'XPEOPLE',
        'XPERFORMER',
        'XPUBLISHER',
        'XREMIXER',
        'XTITLE',
        'XTRACK',
        'XYEAR',
    )
}

TAGS_EXACTLY = {
    # COMMON
    'ALBUM_SORT':        'XALBUM',
    'ALBUM':             'XALBUM',
    'ARTIST_SORT':       'XARTIST',
    'ARTIST':            'XARTIST',
    'ARTISTS':           'XARTIST',
    'ALBUM_ARTIST':      'XARTIST',
    'ALBUM_ARTIST_SORT': 'XARTIST',
    'TITLE':             'XTITLE',
    'TRACK':             'XTRACK',
    'TRACKNO':           'XTRACK',
    'TRACKNUMBER':       'XTRACK',
    'YEAR':              'XYEAR',
    'DATE':              'XDATE',
    'PERFORMER':         'XPERFORMER',
    'PERFORMERS':        'XPERFORMER',
    'COMPOSER':          'XCOMPOSER',
    'COMPOSERS':         'XCOMPOSER',
    'COMMENT':           'XCOMMENT',
    'COMMENTS':          'XCOMMENT',
    'DESCRIPTION':       'XCOMMENT',
    'ENCODER':           'XENCODER',
    'ENCODER_OPTIONS':   'XENCODER',
    'ENCODED_BY':        'XENCODED_BY',
    # ID3
    'TAL':  'XALBUM',
    'TCM':  'XCOMPOSER',
    'TCO':  'XGENRE',
    'TCP':  'XCOMPILATION',
    'TDA':  'XDATE',
    'TEN':  'XENCODED_BY',
    'TENC': 'XENCODED_BY',
    'XSOT': 'XTITLE', # TitleSortOrder
    'XSOP': 'XPERFORMER', # PerformerSortOrder
    'XSOA': 'XALBUM', #     AlbumSortOrder
    'TLA':  'XLANG',
    'TOA':  'XARTIST',
    'TOF':  'XFILENAME',
    'TP1':  'XARTIST',
    'TP2':  'XARTIST',
    'TP3':  'XPEOPLE',
    'TP4':  'XPEOPLE',
    'TPB':  'XPEOPLE',
    'TRD':  'XDATE',
    'TRK':  'XTRACK',
    'TS2':  'XARTIST',
    'TSA':  'XALBUM',
    'TSC':  'XCOMPOSER',
    'TSP':  'XPERFORMER',
    'TSS':  'XENCODER',
    'TST':  'XTITLE',
    'TT1':  'XGROUP',
    'TT2':  'XTITLE',
    'TT3':  'XTITLE',
    'TXX':  'XCOMMENT',
    'TYE':  'XYEAR',
    'WAF':  'XFILENAME',
    'COM':  'XCOMMENT',
}

TAGS_PARTIAL = (
    ('ARTIST',      'XARTIST'),
    ('TITLE',       'XTITLE'),
    ('ALBUM',       'XALBUM'),
    ('PEOPLE',      'XPEOPLE'),
    ('COMPOSER',    'XCOMPOSER'),
    ('PERFORMER',   'XPERFORMER'),
    ('REMIXER',     'XREMIXER'),
    ('COMMENT',     'XCOMMENT'),
    ('DESCRIPTION', 'XCOMMENT'),
)

#
assert not any (tags[t] for t in TAGS_EXACTLY.values())
assert not any (tags[t] for _, t in TAGS_PARTIAL)

#export LC_ALL=en_US.UTF-8

# WHERE TO SAVE THE CONVERTED FILES
GOOD_DIR = '/mnt/sda2/CONVERTED'
BAD_DIR = '/mnt/sda2/BAD'

#
TMP_DIR = '/tmp'

# HOW MANY PROCESSES TO RUN SIMULTANEOUSLY
CPUS_MAX = 12

def version (cmd, start):
    with os.popen(cmd) as fd:
        ret = fd.read(65536).startswith(start)
    return ret

# EXECUTE A COMMAND, WAIT FOR ALL IT'S CHILDS, AND RETURN ANY FAILURE FROM ANY OF THEM
def execute (executable, args, env=os.environ):
    if os.fork() == 0:
        os.execve(executable, args, env)
        exit(1)
    fail = 0
    try:
        while True:
            fail |= os.wait()[1]
    except ChildProcessError:
        pass
    return fail

#
assert version('ffmpeg    -version', 'ffmpeg')
assert version('operon   --version', 'operon')
assert version('opusenc  --version', 'opusenc')
assert version('opusdec  --version', 'opusdec')
assert version('flac     --version', 'flac')
assert version('metaflac --version', 'metaflac')
assert version('soxi',               'soxi')

def scandir (d):
    try:
        for f in os.listdir(d):
            yield from scandir(f'{d}/{f}')
    except FileNotFoundError:
        pass
    except PermissionError:
        pass
    except NotADirectoryError:
        yield d

ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ@'

def mhash ():

    f  = int.from_bytes(os.read(RANDOMFD, 8), byteorder = 'little', signed=False)
    f += int(time.monotonic() * 10000000)
    f += int(random.random() * 0xFFFFFFFFFFFFFFFF)
    f += f >> 32
    f &= 0xFFFFFFFFFFFFFFFF

    code = ''

    while True:
        code += ALPHABET[f % len(ALPHABET)]
        f //= len(ALPHABET)
        if f == 0:
            return code

PID = os.getpid()
assert 1 <= PID <= 0xFFFFFFFF

#
RANDOMFD = os.open('/dev/urandom', os.O_RDONLY)
assert 0 <= RANDOMFD <= 10

TNAME = mhash()
assert len(TNAME) >= 4

CPUS = open('/proc/cpuinfo').read().count('processor\t:')
assert 1 <= CPUS <= 512

# LIMIT AS REQUESTED
if CPUS >= CPUS_MAX:
    CPUS = CPUS_MAX

print('CPUS HAS:', CPUS)
print('CPUS USE:', CPUS_MAX)
print('TNAME:', TNAME)
print('GOOD DIR:', GOOD_DIR)
print('BAD DIR:', BAD_DIR)

#
for d in (GOOD_DIR, BAD_DIR):
    #
    if not stat.S_ISDIR(os.stat(f'{d}/').st_mode):
        print('ERROR: OUTPUT DIRECTORY IS NOT A DIRECTORY')
        exit(1)
    #
    if os.getcwd().strip('/').startswith(d.strip('/')):
        print('ERROR: CANNOT WORK ON OUTPUT DIR')
        exit(1)

#
if execute('/bin/chrt', ('chrt', '--batch', '-p', '0', str(PID))):
    print('ERROR: FAILED TO SET PROCESS PRIORITY')
    exit(1)

#
os.mkdir(f'{TMP_DIR}/{TNAME}')

#
pipeIn, pipeOut = os.pipe2(os.O_DIRECT)

# TODO: CPU AFFINITY
cpu0 = 0

for tid in range(CPUS + 1):
    if tid != CPUS: # THE LAST ONE WONT LAUNCH ANYTHING
        if os.fork() == 0:
            break # THE CHILD WILL STOP HERE

if tid == CPUS:

    # WE ARE THE WRITER
    os.close(pipeIn)

    try:
        for f in sys.argv[1:]:
            for f in scandir(f):
                if re.match('^.*[.](mp3|aac|flac|wav|m4a|ogg|opus|ape|wma|wv|alac|aif|aiff)$', f.lower()):
                    os.write(pipeOut, f.encode())
    except KeyboardInterrupt:
        pass

    os.close(pipeOut)

    # WAIT ALL CHILDS TO FINISH
    while True:
        try:
            os.wait()
        except ChildProcessError:
            break
        except KeyboardInterrupt:
            pass

    # CLEAR ALL FILES
    for tid in range(CPUS):
        for f in (
            # # # # # # # # # # f'{TMP_DIR}/{TNAME}/{tid}-decoded',
            f'{TMP_DIR}/{TNAME}/{tid}-encoded',
           f'{GOOD_DIR}/{TNAME}-{tid}.tmp',
            f'{BAD_DIR}/{TNAME}-{tid}.tmp',
        ):
            try:
                os.unlink(f)
            except FileNotFoundError:
                pass

    os.rmdir(f'{TMP_DIR}/{TNAME}')

    exit(0)

try: # THREAD
    print(f'[{tid}] LAUNCHED')

    # WE ARE THE READER
    os.close(pipeOut)

    #
    # # # # # # # # # # decoded = f'{TMP_DIR}/{TNAME}/{tid}-decoded'
    encoded = f'{TMP_DIR}/{TNAME}/{tid}-encoded'

    tmpGood = f'{GOOD_DIR}/{TNAME}-{tid}.tmp'
    tmpBad  =  f'{BAD_DIR}/{TNAME}-{tid}.tmp'

    good = GOOD_DIR, tmpGood
    bad  = BAD_DIR,  tmpBad

    while original := os.read(pipeIn, 2048):
        original = original.decode()

        i = o = imap = ibuff = fp = fpStream = cmd = None

        XID = XTIME = XPATH = XCHANNELS = XCHANNELS_LAYOUT = XBITS = XBITS_FMT = XBITS_RAW = XHZ = XDURATION = XFORMAT = XFORMAT_NAME = XCODEC = XCODEC_NAME = XBITRATE = None

        # ONLY IF EXISTS
        try:
            st = os.stat(original)
        except FileNotFoundError:
            print(f'[{tid}] {original}: SKIPPED (NOT FOUND)')
            continue

        # ONLY FILES
        if not stat.S_ISREG(st.st_mode):
            print(f'[{tid}] {original}: SKIPPED (NOT FILE)')
            continue

        originalSize = st.st_size

        # NOT SMALL FILES
        if originalSize < 128*1024:
            print(f'[{tid}] {original}: SKIPPED (TOO SMALL)')
            if 1 <= originalSize:
                os.unlink(original)
            continue

        #
        try:
            with open(original, 'rb') as xxx:
                with os.popen(f'ffprobe -v quiet -print_format json -show_format -show_streams -- /proc/{os.getpid()}/fd/{xxx.fileno()}') as fd:
                    fp = json.loads(fd.read(1*1024*1024))

            fpStream, = (s for s in fp['streams'] if s['codec_type'] == 'audio') # NOTE: ONLY SUPPORT FILES WITH 1 AUDIO STREAM

            ( # FORMAT
                XFORMAT, XFORMAT_NAME, ORIGINAL_TAGS,
                # STREAM
                XCODEC, XCODEC_NAME, XBITS_FMT, XHZ, XCHANNELS, XCHANNELS_LAYOUT, XBITS, XBITS_RAW, XDURATION, XBITRATE, ORIGINAL_TAGS2
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
            print(f'[{tid}] {original}: ERROR: FFPROBE FAILED')
            traceback.print_exc()
            continue

        if XDURATION is None:
            print(f'[{tid}] {original}: ERROR: DURATION IS NONE!')
            continue

        #
        XPATH, XID, XTIME = original, mhash(), int(time.time())

        #
        for t in tags.values():
            t.clear()

        for T in (ORIGINAL_TAGS, ORIGINAL_TAGS2):

            if T is None:
                continue

            #
            T = { k: ' '.join(v.split())[:300].upper()
                for k, v in ( ('_'.join(k_.replace('_', ' ').replace('-', ' ').split()).upper(), v_)
                    for k_, v_ in T.items()
                        if k_ and v_
                )
            }

            #
            if 'CONVERSION_TIME' in T:
                XTIME            = T.pop('CONVERSION_TIME',           XTIME)
                XPATH            = T.pop('ORIGINAL_FILEPATH',         XPATH)
                XPATH            = T.pop('ORIGINAL_FILENAME',         XPATH)
                XPATH            = T.pop('ORIGINAL_PATH',             XPATH)
                XCHANNELS_LAYOUT = T.pop('ORIGINAL_CHANNEL_LAYOUT',   XCHANNELS_LAYOUT)
                XCHANNELS        = T.pop('ORIGINAL_CHANNELS',         XCHANNELS)
                XBITS            = T.pop('ORIGINAL_BITS',             XBITS)
                XBITS_RAW        = T.pop('ORIGINAL_BITS_RAW',         XBITS_RAW)
                XBITS_FMT        = T.pop('ORIGINAL_SAMPLE_FMT',       XBITS_FMT)
                XHZ              = T.pop('ORIGINAL_SAMPLE_RATE',      XHZ)
                XFORMAT          = T.pop('ORIGINAL_FORMAT_NAME',      XFORMAT)
                XFORMAT_NAME     = T.pop('ORIGINAL_FORMAT_NAME_LONG', XFORMAT_NAME)
                XCODEC           = T.pop('ORIGINAL_CODEC_NAME',       XCODEC)
                XCODEC_NAME      = T.pop('ORIGINAL_CODEC_LONG_NAME',  XCODEC_NAME)
                XDURATION        = T.pop('ORIGINAL_DURATION',         XDURATION)
                XBITRATE         = T.pop('ORIGINAL_BITRATE',          XBITRATE)

            # ORIGINAL TAGS
            while T:
                k, v = T.popitem()
                # EXACT MATCH
                t = TAGS_EXACTLY.get(k, None)
                # PARTIAL MATCH
                if t is None:
                    for old, new in TAGS_PARTIAL:
                        if old in k:
                            t = new
                            break
                # TODO: FIXME: SUPORTAR MULTIPLOS
                if t is not None:
                    if isinstance(v, (list, tuple, set)):
                        tags[t].update(v)
                    else:
                        tags[t].add(v)

        # PARSE/DEFAULTS
        XCHANNELS   = int(XCHANNELS)
        XHZ  = int(XHZ)

        if XDURATION is None:
            XDURATION = 0
        else:
            XDURATION = float(XDURATION)

        #
        XBITS_FMT = XBITS_FMT.upper()

        if XBITS is None:
            XBITS = 0
        else:
            XBITS = int(XBITS)

        if XBITS_RAW is None:
            XBITS_RAW = 0
        else:
            XBITS_RAW = int(XBITS_RAW)

        if XCHANNELS_LAYOUT is None:
            XCHANNELS_LAYOUT = '-'

        # VERIFY
        if not (XBITS in (0, 8, 16, 24, 32)):
            print(f'[{tid}] {original}: ERROR: BAD BITS: {XBITS}')
            continue

        if not (XBITS_RAW in (0, 8, 16, 24, 32)):
            print(f'[{tid}] {original}: ERROR: BAD BITS RAW: {XBITS_RAW}')
            continue

        if not (XBITS or XBITS_RAW):
            print(f'[{tid}] {original}: ERROR: NO BITS')
            continue

        if not (1 <= XCHANNELS <= 2):
            print(f'[{tid}] {original}: ERROR: BAD CHANNELS: {XCHANNELS}')
            continue

        if not (XBITS_FMT in ('S16', 'S16P', 'S32')):
            print(f'[{tid}] {original}: ERROR: BAD SAMPLE FMT: {XBITS_FMT}')
            continue

        if not (20 <= XDURATION <= 7*24*60*60):
            if XDURATION < 15:
                os.unlink(original)
            print(f'[{tid}] {original}: ERROR: BAD DURATION: {XDURATION}')
            continue

        if not (44100 <= XHZ <= 192000):
            print(f'[{tid}] {original}: ERROR: BAD SAMPLE RATE: {XHZ}')
            continue

        assert XBITS_FMT
        assert XFORMAT
        assert XFORMAT_NAME
        assert XCODEC
        assert XCODEC_NAME

        #
        for f in (encoded, tmpGood, tmpBad): # , decoded
            try:
                os.unlink(f)
            except FileNotFoundError:
                pass

        # FFMPEG/LIBOPUS
        cmd  = [ 'ffmpeg', '-y', '-hide_banner', '-loglevel', 'quiet', '-bitexact', '-i', original, '-map_metadata', '-1', '-f', 'opus', '-c:a', 'libopus', '-packet_loss', '0', '-application', 'audio', '-compression_level', '10' ]

        # cutoff (N.A.)
        # mapping_family (mapping_family)

        #
        # IF SET TO 0, DISABLES THE USE OF PHASE INVERSION FOR INTENSITY STEREO, IMPROVING THE QUALITY OF MONO DOWNMIXES
        if any(('BINAURAL' in w) for g in ((original.upper(), XPATH.upper()), tags['XARTIST'], tags['XALBUM'], tags['XTITLE'], tags['XFILENAME']) for w in g):
            print(f'[{tid}] {original}: WARNING: IS BINAURAL')
            assert 1 <= XCHANNELS  <= 2
        else:
            cmd.extend(('-apply_phase_inv', '0', '-ac', '1'))

        # BIT RATE
        cmd.extend(('-b:a', f'256k'))
        # cmd.extend(('-b', f'{256*1024}'))

        # OUR TAGS
        for t in ('XID', 'XTIME', 'XPATH', 'XCHANNELS', 'XCHANNELS_LAYOUT', 'XBITS', 'XBITS_FMT', 'XBITS_RAW', 'XHZ', 'XDURATION', 'XFORMAT', 'XFORMAT_NAME', 'XCODEC', 'XCODEC_NAME', 'XBITRATE'):
            if v := eval(t):
                cmd.extend(('-metadata', f'{t}={v}'))

        # ORIGINAL TAGS
        for t, v in tags.items():
            if v := '|'.join(sorted(v)):
                cmd.extend(('-metadata', f'{t}={v}'))

        # THE OUTPUT FILE
        cmd.append(encoded)

        # EXECUTE THE CONVERSOR
        if execute('/usr/bin/ffmpeg', cmd):
            print(f'[{tid}] {original}: ERROR: ENCODE FAILED.')
            continue

        # DONT NEED IT ANYMORE
        # os.unlink(decoded)

        # VERIFY
        # assert channels == int(piped(f'soxi -c {encoded}'))

        #
        where, tmp = good

        #
        # dur = float(piped(f'soxi -D {encoded}'))
        # if not (-1 <= (XDURATION - dur) <= 1):
            # print(f'[{tid}] {original}: ERROR: DURATION MISMATCH: {XDURATION} VS {dur}')
            # where, tmp = bad

        # NOW COPY FROM TEMP
        new = f'{where}/{XID}'

        #
        o = os.open(tmp, os.O_WRONLY | os.O_DIRECT | os.O_CREAT | os.O_EXCL, 0o644)
        i = os.open(encoded, os.O_RDWR | os.O_DIRECT)

        encodedSize  = os.fstat(i).st_size

        if not (65536 <= encodedSize <= 1*1024*1024*1024):
            print(f'[{tid}] {original}: ERROR: BAD ENCODED SIZE {encodedSize}')
            continue

        encodedSize_ = ((encodedSize + 4096 - 1) // 4096) * 4096
        assert encodedSize_ % 4096 == 0

        # ALIGN THE FILE IN /tmp
        if encodedSize_ != encodedSize:
            try:
                os.truncate(i, encodedSize_)
            except BaseException:
                print(f'[{tid}] {original}: ERROR: FAILED TO TRUNCATE {encoded} AS {encodedSize_} BYTES')
                os.close(i)
                os.close(o)
                continue

        # ALIGN AND RESERVE IN THE FILESYSTEM
        if execute('/bin/fallocate', ('fallocate', '--length', str(encodedSize_), tmp)):
            print(f'[{tid}] {original}: ERROR: FAILED TO FALLOCATE {tmp} AS {encodedSize_} BYTES')
            os.close(i)
            os.close(o)
            continue

        imap = mmap.mmap(i, encodedSize_, mmap.MAP_SHARED | mmap.MAP_POPULATE, mmap.PROT_READ, 0, 0)

        ibuff = memoryview(imap)
        offset = 0

        while encodedSize_:
            c = os.write(o, ibuff[offset:encodedSize_])
            assert c % 4096 == 0
            offset += c
            encodedSize_ -= c

        ibuff.release()
        imap.close()
        os.close(i)

        # NOW FIX THE SIZE
        os.fsync(o)
        os.truncate(o, encodedSize)
        os.fsync(o)
        os.close(o)

        #
        os.rename(tmp, new)

        # DELETE THE ORIGINAL
        os.unlink(original)
        os.unlink(encoded)

        # COMPARE SIZES
        print(f'[{tid}] {(encodedSize*100) // originalSize}% {original} ======> {new}')

except KeyboardInterrupt:
    print(f'[{tid}] INTERRUPTED')
except BaseException:
    print(f'[{tid}] ---------------- EXCEPTION -----------')
    traceback.print_exc()

print(f'[{tid}] EXITING')

exit(0)
