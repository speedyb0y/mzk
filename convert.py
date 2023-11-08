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
        'XYOUTUBE',
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
    'YOUTUBE': 'XYOUTUBE',
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

# HOW MANY PROCESSES TO RUN SIMULTANEOUSLY
CPUS_MAX = 16

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

def mhash ():

    f  = int.from_bytes(os.read(RANDOMFD, 8), byteorder = 'little', signed=False)
    f += int(time.monotonic() * 10000000)
    f += int(random.random() * 0xFFFFFFFFFFFFFFFF)
    f += f >> 32
    f &= 0xFFFFFFFFFFFFFFFF

    code = ''

    while True:
        code += '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ@'[f % 37]
        f //= 37
        if f == 0:
            return code

PID = os.getpid()
assert 1 <= PID <= 0xFFFFFFFF

#
RANDOMFD = os.open('/dev/urandom', os.O_RDONLY)
assert 0 <= RANDOMFD <= 10

TNAME = f'xmzk-conversor-{PID}'
assert len(TNAME) >= 4

CPUS = open('/proc/cpuinfo').read().count('processor\t:')
assert 1 <= CPUS <= 512

print('CPUS HAS:', CPUS)
print('CPUS MAX:', CPUS_MAX)

CPUS *= 1.5
CPUS = int(CPUS)

# LIMIT AS REQUESTED
if CPUS > CPUS_MAX:
    CPUS = CPUS_MAX

print('CPUS USE:', CPUS)
print('TNAME:', TNAME)
print('GOOD DIR:', GOOD_DIR)

#
for d in (GOOD_DIR, ):
    #
    if not stat.S_ISDIR(os.stat(f'{d}/').st_mode):
        print('ERROR: OUTPUT DIRECTORY IS NOT A DIRECTORY')
        exit(1)
    #
    if os.getcwd().strip('/').startswith(d.strip('/')):
        print('ERROR: CANNOT WORK ON OUTPUT DIR')
        exit(1)

#
if False:
    if execute('/bin/chrt', ('chrt', '--batch', '-p', '0', str(PID))):
        print('ERROR: FAILED TO SET PROCESS PRIORITY')
        exit(1)

#
assert 0 <= os.open(f'/tmp/{TNAME}', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)

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
        for f in (f'/tmp/{TNAME}-{tid}', f'{GOOD_DIR}/{TNAME}-{tid}.tmp'):
            try:
                os.unlink(f)
            except FileNotFoundError:
                pass

    os.unlink(f'/tmp/{TNAME}')

    exit(0)

try: # THREAD
    print(f'[{tid}] LAUNCHED')

    # WE ARE THE READER
    os.close(pipeOut)

    #
    tmpRAM, tmpDISK  = f'/tmp/{TNAME}-{tid}', f'{GOOD_DIR}/{TNAME}-{tid}.tmp'

    i = o = imap = ibuff = None

    while True:

        if ibuff is not None: ibuff.release()
        if imap  is not None: imap.close()
        if i     is not None: os.close(i)
        if o     is not None: os.close(o)

        i = o = imap = ibuff = fp = fpStream = cmd = None

        XID = XTIME = XPATH = XCHANNELS = XCHANNELS_LAYOUT = XBITS = XBITS_FMT = XBITS_RAW = XHZ = None
        XDURATION = XFORMAT = XFORMAT_NAME = XCODEC = XCODEC_NAME = XBITRATE = XYOUTUBE = None

        original = os.read(pipeIn, 2048).decode()

        if not original:
            print(f'[{tid}] NO MORE FILES')
            break

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

            # TODO:
            canais = int(XCHANNELS)

        except BaseException:
            print(f'[{tid}] {original}: ERROR: FFPROBE FAILED')
            traceback.print_exc()
            continue

        #
        XFORMAT      = XFORMAT      .upper()
        XFORMAT_NAME = XFORMAT_NAME .upper()
        XCODEC       = XCODEC       .upper()
        XCODEC_NAME  = XCODEC_NAME  .upper()

        #
        XPATH, XID, XTIME, XSIZE = original, mhash(), int(time.time()), originalSize

        #
        for t in tags.values():
            t.clear()

        convert = True

        for T in (ORIGINAL_TAGS, ORIGINAL_TAGS2):

            if T is None:
                continue

            #
            T = { '_'.join(k[:80].replace('_', ' ').replace('-', ' ').split()).upper().replace('XMZK_TIME', 'CONVERSION_TIME').replace('XMZK_', 'ORIGINAL_'): ' '.join(v.split())[:300].rstrip().upper()
                for k, v in T.items()
                    if k and v
            }

            #
            if any(map(T.__contains__, ('CONVERSION_TIME', 'ORIGINAL_BITS', 'XID', 'XPATH', 'XTIME', 'XBITS'))):

                #
                convert = XCODEC in ('FLAC',)

                # FORGET THIS      TODO: SE ESTIVER OK ENTAO MANTEM ELE
                T.pop('XID', None)

                #
                ( XTIME,   XPATH ,  XCHANNELS_LAYOUT ,  XBITS ,  XBITS_RAW ,  XBITS_FMT ,  XFORMAT,   XFORMAT_NAME,   XCODEC,   XDURATION,   XCODEC_NAME,   XCHANNELS,   XHZ,   XSIZE,   XYOUTUBE) = ( T.pop(t, None) for t in
                ('XTIME', 'XPATH', 'XCHANNELS_LAYOUT', 'XBITS', 'XBITS_RAW', 'XBITS_FMT', 'XFORMAT', 'XFORMAT_NAME', 'XCODEC', 'XDURATION', 'XCODEC_NAME', 'XCHANNELS', 'XHZ', 'XSIZE', 'XYOUTUBE'))

                for t, vals in tags.items():
                    if v := T.pop(t, None):
                        vals.update(v.split('|'))

                # FORMATO VELHO
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
                XCHANNELS_LAYOUT = T.pop('XCHANNEL_LAYOUT',           XCHANNELS_LAYOUT)
                XCODEC_NAME      = T.pop('XCODEC_LONG_NAME',          XCODEC_NAME)
                XFORMAT_NAME     = T.pop('XFORMAT_NAME_LONG',         XFORMAT_NAME)
                XBITS_FMT        = T.pop('XSAMPLE_FMT',               XBITS_FMT)
                XHZ              = T.pop('XSAMPLE_RATE',              XHZ)
                XHZ              = T.pop('XSAMPLERATE',               XHZ)

                if _ := T.pop('XSAMPLE', None):
                    XBITS_FMT, XBITS, XBITS_RAW = _.split('|')

                if XBITS_FMT is None:
                    assert XBITS_RAW is None
                    XBITS_FMT, XBITS, XBITS_RAW = XBITS.split('|')

                if XFORMAT and XFORMAT_NAME is None:
                    XFORMAT, XFORMAT_NAME = XFORMAT.split('|', 1)

                if XCODEC and XCODEC_NAME is None:
                    XCODEC, XCODEC_NAME = XCODEC.split('|', 1)

                if XFORMAT is None:
                    XFORMAT = ('FLAC',)[('RAW FLAC').index(XFORMAT_NAME)]

                if XCODEC is None:
                    XCODEC = ('FLAC',)[(('FLAC', 'FLAC (FREE LOSSLESS AUDIO CODEC)'),).index((XFORMAT, XCODEC_NAME))]

                if XCHANNELS and '|' in XCHANNELS and XCHANNELS_LAYOUT is None:
                    XCHANNELS_LAYOUT, XCHANNELS = XCHANNELS.split('|', 1)

                # NOTE: MAY DON'T HAVE XBITS
                # NOTE: MAY DON'T HAVE XCHANNELS_LAYOUT
                assert all((XPATH, XTIME, XCHANNELS, XFORMAT, XFORMAT_NAME, XCODEC, XCODEC_NAME, XDURATION, XHZ)), (original,
                           (XPATH, XTIME, XCHANNELS, XFORMAT, XFORMAT_NAME, XCODEC, XCODEC_NAME, XDURATION, XHZ), T)

            #
            assert not 'XID'               in T
            assert not 'XPATH'             in T
            assert not 'XTIME'             in T
            assert not 'XBITS'             in T
            assert not 'CONVERSION_TIME'   in T
            assert not 'ORIGINAL_FILEPATH' in T
            assert not 'ORIGINAL_PATH'     in T
            assert not 'ORIGINAL_BITS'     in T
            assert not 'ORIGINAL_CHANNELS' in T
            assert not 'ORIGINAL_CHANNEL_LAYOUT' in T
            # assert not 'ORIGINAL_FILENAME' in T      !!! TODO :S

            assert XID

            # ORIGINAL TAGS
            for k, v in T.items():
                if 'MUSICBRAINZ' in k:
                    continue
                # EXACT MATCH, THEN PARTIAL MATCH
                if (t := TAGS_EXACTLY.get(k, None)) is None:
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
        XCHANNELS    = int       (XCHANNELS)
        XHZ          = int       (XHZ)
        XBITS_FMT    = str.upper (XBITS_FMT)
        XCODEC       = str.upper (XCODEC)
        XCODEC_NAME  = str.upper (XCODEC_NAME)
        XFORMAT      = str.upper (XFORMAT)
        XFORMAT_NAME = str.upper (XFORMAT_NAME)

        XBITS            = (0   if XBITS            is None else int       (XBITS))
        XBITS_RAW        = (0   if XBITS_RAW        is None else int       (XBITS_RAW))
        XCHANNELS_LAYOUT = ('-' if XCHANNELS_LAYOUT is None else str.upper (XCHANNELS_LAYOUT))
        XDURATION        = (0   if XDURATION        is None else float     (XDURATION))

        # VERIFY
        if not (XBITS in (0, 8, 16, 24, 32)):
            print(f'[{tid}] {original}: ERROR: BAD BITS: {XBITS}')
            continue

        if not (XBITS_RAW in (0, 8, 16, 24, 32)):
            print(f'[{tid}] {original}: ERROR: BAD BITS RAW: {XBITS_RAW}')
            continue

        # WMA, S16P, 0, 0
        if not (XBITS or XBITS_RAW): # -> 0, 0
            if XBITS_FMT not in ('FLTP', 'S16P'):
                print(f'[{tid}] {original}: ERROR: NO BITS ({XBITS_FMT})')
                continue

        if not (1 <= XCHANNELS <= 8):
            print(f'[{tid}] {original}: ERROR: BAD CHANNELS: {XCHANNELS}')
            continue

        if not (XBITS_FMT in ('S16', 'S16P', 'S32', 'S32P', 'FLT', 'FLTP')):
            print(f'[{tid}] {original}: ERROR: BAD SAMPLE FMT: {XBITS_FMT}')
            continue

        if not (20 <= XDURATION <= 7*24*60*60):
            print(f'[{tid}] {original}: WARNING: BAD DURATION: {XDURATION}')

        if not (8000 <= XHZ <= 192000):
            print(f'[{tid}] {original}: ERROR: BAD SAMPLE RATE: {XHZ}')
            continue

        assert XFORMAT and XFORMAT_NAME
        assert XCODEC  and XCODEC_NAME

        #
        for f in (tmpRAM, tmpDISK):
            try:
                os.unlink(f)
            except FileNotFoundError:
                pass

        if XYOUTUBE is not None:
            if 'youtu.be' in XYOUTUBE:
                XYOUTUBE = XYOUTUBE.rsplit('/', 1)[1][0].split('?')[0]
            elif '/watch?v=' in XYOUTUBE:
                XYOUTUBE = XYOUTUBE.split('=')[1]
            # https://www.youtube.com/watch?v=4LHYCXaI_CI
            # https://youtu.be/4LHYCXaI_CI?
        elif re.match(r'^.*youtube.*\[[0-9a-z_-]{5,16}\][.](m4a|opus|ogg|mp4|webm)$', original.lower()):
            XYOUTUBE, = re.findall(r'^.*\[([0-9A-Za-z_-]{5,})\][.].*$', original)
        elif re.match(r'^.*youtube.*\[[0-9a-z_-]{5,16}\][.](m4a|opus|ogg|mp4|webm)$', XPATH.lower()):
            XYOUTUBE, = re.findall(r'^.*\[([0-9A-Za-z_-]{5,})\][.].*$', XPATH)

        assert XYOUTUBE is None or re.match(r'^[0-9A-Za-z_-]{5,16}$', XYOUTUBE)

        #
        cmd  = [ 'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-bitexact', '-threads', '1', '-i', original, '-f', 'opus', '-map_metadata', '-1', '-map_metadata:s', '-1' ]

        # TAGS
        for t in ('XID', 'XTIME', 'XPATH', 'XCHANNELS', 'XCHANNELS_LAYOUT', 'XBITS', 'XBITS_FMT', 'XBITS_RAW', 'XHZ', 'XDURATION', 'XFORMAT', 'XFORMAT_NAME', 'XCODEC', 'XCODEC_NAME', 'XBITRATE', 'XSIZE', 'XYOUTUBE'):
            if v := eval(t):
                cmd.extend(('-metadata', f'{t}={v}'))
        for t, v in tags.items():
            if v := '|'.join(sorted(v)):
                cmd.extend(('-metadata', f'{t}={v}'))

        if XYOUTUBE is not None:
            assert (XFORMAT, XCODEC) in (('OGG', 'OPUS'), ('MOV,MP4,M4A,3GP,3G2,MJ2', 'AAC')), (XFORMAT, XCODEC)
            convert = False
 
        # CONVERSION
        if convert:
            if XHZ != 48000 and False:
                cmd.extend(('-af', 'aresample=resampler=soxr:precision=30:out_sample_rate=48000:osr=48000:dither_method=none')) # , '-ar', '48000'
                #@ffmpeg.exe -report -hide_banner -v 32 -stats -y -i "%filename%" -vn -af aresample=resampler=soxr:osr=48000:cutoff=0.990:dither_method=none,aformat=sample_fmts=s32:channel_layouts=0x60f -strict -2 -c:a dca -b:a 1536k -f wav "%~n1_dts.wav"
                # cmd.extend(('-af', 'aresample=resampler=soxr:precision=30:osf=flt:out_sample_fmt=flt:out_sample_rate=48000:osr=48000', '-ar', '48000', '-sample_fmt', 'flt'))
                # cmd.extend(('-af', 'aresample=48000:resampler=soxr:precision=30:osf=flt')) # :dither_method=triangular
            if mono := (canais == 1 or not any( ('BINAURAL' in w) for W in ((original.upper(), XPATH.upper()), tags['XARTIST'], tags['XALBUM'], tags['XTITLE'], tags['XFILENAME']) for w in W)):
                cmd.extend(('-ac', '1'))
            cmd.extend(('-c:a', 'libopus', '-qscale:a', '0', '-packet_loss', '0', '-application', 'audio', '-compression_level', '10'))
            if mono: # IF SET TO 0, DISABLES THE USE OF PHASE INVERSION FOR INTENSITY STEREO, IMPROVING THE QUALITY OF MONO DOWNMIXES
                cmd.extend(('-apply_phase_inv', '0'))
            cmd.extend(('-vbr', 'on', '-b:a', '256k'))
        else:
            cmd.extend(('-map', '0:a', '-acodec', 'copy'))

        # THE OUTPUT FILE
        cmd.extend(('-fflags', '+bitexact', '-flags:a', '+bitexact', tmpRAM))

        # EXECUTE THE CONVERSOR
        if execute('/usr/bin/ffmpeg', cmd):
            print(f'[{tid}] {original}: ERROR: ENCODE FAILED.')
            continue

        # NOW COPY FROM TEMP
        o = os.open(tmpDISK, os.O_WRONLY | os.O_DIRECT | os.O_SYNC | os.O_CREAT | os.O_EXCL, 0o644)
        i = os.open(tmpRAM, os.O_RDWR | os.O_DIRECT)

        # PROTECT AGAINST FILE DESCRIPTORS LEAKING
        assert 0 <= i <= 10
        assert 0 <= o <= 10

        newSize = os.fstat(i).st_size

        if not (65536 <= newSize <= 1*1024*1024*1024):
            print(f'[{tid}] {original}: ERROR: BAD ENCODED SIZE {newSize}')
            continue

        newSize_ = ((newSize + 4096 - 1) // 4096) * 4096

        # ALIGN THE FILE IN /tmp
        if newSize_ != newSize:
            try:
                os.truncate(i, newSize_)
            except BaseException:
                print(f'[{tid}] {original}: ERROR: FAILED TO TRUNCATE {tmpRAM} AS {newSize_} BYTES')
                continue

        # ALIGN AND RESERVE IN THE FILESYSTEM
        if execute('/bin/fallocate', ('fallocate', '--length', str(newSize_), tmpDISK)):
            print(f'[{tid}] {original}: ERROR: FAILED TO FALLOCATE {tmpDISK} AS {newSize_} BYTES')
            continue

        imap = mmap.mmap(i, newSize_, mmap.MAP_SHARED | mmap.MAP_POPULATE, mmap.PROT_READ, 0, 0)

        ibuff = memoryview(imap)
        offset = 0

        while newSize_:
            c = os.write(o, ibuff[offset:newSize_])
            offset   += c
            newSize_ -= c

        # NOW FIX THE SIZE
        os.fsync(o)
        os.truncate(o, newSize)
        os.fsync(o)
        os.close(o)
        o = None

        #
        new = f'{GOOD_DIR}/{XID}'

        try:
            os.stat(new)
        except FileNotFoundError:
            os.rename(tmpDISK, new)
        else:
            print(f'[{tid}] --- NEW ALREADY EXISTS: {new}')
            continue

        # COMPARE SIZES
        if convert:
            print(f'[{tid}] {(newSize*100) // originalSize}% {original} ======> {new}')
        else:
            print(f'[{tid}] --- {original} ======> {new}')

        # DELETE THE ORIGINAL
        os.unlink(original)

except KeyboardInterrupt:
    print(f'[{tid}] INTERRUPTED')
except BaseException:
    print(f'[{tid}] ---------------- EXCEPTION -----------')
    traceback.print_exc()

print(f'[{tid}] EXITING')

exit(0)
