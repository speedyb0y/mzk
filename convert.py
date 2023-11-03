#!/usr/bin/python

'''

#for x in * ; do mv -vn "${x}" $(metaflac --show-md5sum "${x}") ; done

# UNIFY FLAC AS ORIGINAL_HASH
for x in * ; do
    OHASH=-
    if OHASH=$(spipe $[1*1024*1024] /bin/ffmpeg ffmpeg -y -hide_banner -loglevel quiet -i ${x} -f s24le - | b3sum --num-threads 1 --no-names --raw | base64 | tr / @ | tr + \$) ; then
        if [ ${#OHASH} = 44 ] ; then
            mv -vn -- ${x} /mnt/sda2/FLAC-OHASH/${OHASH}
        fi
    fi
done

# UNIFY LOSSY OPUS
for x in todo/*.opus ; do
    HASH=-
    if HASH=$(opusdec --quiet ${x} - | b3sum --num-threads 1 --no-names --raw | base64 | tr / '@') ; then
        if [ ${#HASH} = 44 ] ; then
            mv -v -- ${x} hashed/${HASH}
        fi
    fi
done
'''

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

_lossless = {

    (16, 44100): 165,
    (24, 44100): 180,
    (32, 44100): 190,

    (16, 48000): 170,
    (24, 48000): 190,
    (32, 48000): 210,

    (16, 96000): 256,
    (24, 96000): 280,
    (32, 96000): 395,

    (16, 176400): 290,
    (24, 176400): 220,
    (32, 176400): 235,

    (16, 192000): 300,
    (24, 192000): 350,
    (32, 192000): 365,
}

_lossy_44k_16b = 150
_lossy_44k_24b = 160
_lossy_44k_32b = 160

_lossy_48k_16b = 160
_lossy_48k_24b = 178
_lossy_48k_32b = 178

mapa = {

	('ALAC',      1, 176400, 'S16P', 0,  16) : _lossless[(16, 176400)],
	('ALAC',      1, 176400, 'S32P', 0,  24) : _lossless[(24, 176400)],
	('ALAC',      1, 176400, 'S32P', 0,  32) : _lossless[(32, 176400)],
	('ALAC',      1, 192000, 'S16P', 0,  16) : _lossless[(16, 192000)],
	('ALAC',      1, 192000, 'S32P', 0,  24) : _lossless[(24, 192000)],
	('ALAC',      1, 192000, 'S32P', 0,  32) : _lossless[(32, 192000)],
	('ALAC',      1, 44100,  'S16P', 0,  16) : _lossless[(16, 44100)],
	('ALAC',      1, 44100,  'S32P', 0,  24) : _lossless[(24, 44100)],
	('ALAC',      1, 44100,  'S32P', 0,  32) : _lossless[(32, 44100)],
	('ALAC',      1, 48000,  'S16P', 0,  16) : _lossless[(16, 48000)],
	('ALAC',      1, 48000,  'S32P', 0,  24) : _lossless[(24, 48000)],
	('ALAC',      1, 48000,  'S32P', 0,  32) : _lossless[(32, 48000)],
	('ALAC',      1, 96000,  'S16P', 0,  16) : _lossless[(16, 96000)],
	('ALAC',      1, 96000,  'S32P', 0,  24) : _lossless[(24, 96000)],
	('ALAC',      1, 96000,  'S32P', 0,  32) : _lossless[(32, 96000)],
	('APE',       1, 176400, 'S16P', 0,  16) : _lossless[(16, 176400)],
	('APE',       1, 176400, 'S32P', 0,  24) : _lossless[(24, 176400)],
	('APE',       1, 176400, 'S32P', 0,  32) : _lossless[(32, 176400)],
	('APE',       1, 192000, 'S16P', 0,  16) : _lossless[(16, 192000)],
	('APE',       1, 192000, 'S32P', 0,  24) : _lossless[(24, 192000)],
	('APE',       1, 192000, 'S32P', 0,  32) : _lossless[(32, 192000)],
	('APE',       1, 44100,  'S16P', 0,  16) : _lossless[(16, 44100)],
	('APE',       1, 44100,  'S32P', 0,  24) : _lossless[(24, 44100)],
	('APE',       1, 44100,  'S32P', 0,  32) : _lossless[(32, 44100)],
	('APE',       1, 48000,  'S16P', 0,  16) : _lossless[(16, 48000)],
	('APE',       1, 48000,  'S32P', 0,  24) : _lossless[(24, 48000)],
	('APE',       1, 48000,  'S32P', 0,  32) : _lossless[(32, 48000)],
	('APE',       1, 96000,  'S16P', 0,  16) : _lossless[(16, 96000)],
	('APE',       1, 96000,  'S32P', 0,  24) : _lossless[(24, 96000)],
	('APE',       1, 96000,  'S32P', 0,  32) : _lossless[(32, 96000)],
	('DTS',       1, 176400, 'FLTP', 0,  0)  : _lossless[(32, 176400)],
	('DTS',       1, 192000, 'FLTP', 0,  0)  : _lossless[(32, 192000)],
	('DTS',       1, 44100,  'FLTP', 0,  0)  : _lossless[(32, 44100)],
	('DTS',       1, 48000,  'FLTP', 0,  0)  : _lossless[(32, 48000)],
	('DTS',       1, 96000,  'FLTP', 0,  0)  : _lossless[(32, 96000)],
	('FLAC',      1, 176400, 'S16',  0,  16) : _lossless[(16, 176400)],
	('FLAC',      1, 176400, 'S32',  0,  24) : _lossless[(24, 176400)],
	('FLAC',      1, 176400, 'S32',  0,  32) : _lossless[(32, 176400)],
	('FLAC',      1, 192000, 'S16',  0,  16) : _lossless[(16, 192000)],
	('FLAC',      1, 192000, 'S32',  0,  24) : _lossless[(24, 192000)],
	('FLAC',      1, 192000, 'S32',  0,  32) : _lossless[(32, 192000)],
	('FLAC',      1, 44100,  'S16',  0,  16) : _lossless[(16, 44100)],
	('FLAC',      1, 44100,  'S32',  0,  24) : _lossless[(24, 44100)],
	('FLAC',      1, 44100,  'S32',  0,  32) : _lossless[(32, 44100)],
	('FLAC',      1, 48000,  'S16',  0,  16) : _lossless[(16, 48000)],
	('FLAC',      1, 48000,  'S32',  0,  24) : _lossless[(24, 48000)],
	('FLAC',      1, 48000,  'S32',  0,  32) : _lossless[(32, 48000)],
	('FLAC',      1, 96000,  'S16',  0,  16) : _lossless[(16, 96000)],
	('FLAC',      1, 96000,  'S32',  0,  24) : _lossless[(24, 96000)],
	('FLAC',      1, 96000,  'S32',  0,  32) : _lossless[(32, 96000)],
	('PCM_F32LE', 1, 176400, 'FLT',  32, 32) : _lossless[(32, 176400)],
	('PCM_F32LE', 1, 192000, 'FLT',  32, 32) : _lossless[(32, 192000)],
	('PCM_F32LE', 1, 44100,  'FLT',  32, 32) : _lossless[(32, 44100)],
	('PCM_F32LE', 1, 48000,  'FLT',  32, 32) : _lossless[(32, 48000)],
	('PCM_F32LE', 1, 96000,  'FLT',  32, 32) : _lossless[(32, 96000)],
	('PCM_S16BE', 1, 176400, 'S16',  16, 16) : _lossless[(16, 176400)],
	('PCM_S16BE', 1, 192000, 'S16',  16, 16) : _lossless[(16, 192000)],
	('PCM_S16BE', 1, 44100,  'S16',  16, 16) : _lossless[(16, 44100)],
	('PCM_S16BE', 1, 48000,  'S16',  16, 16) : _lossless[(16, 48000)],
	('PCM_S16BE', 1, 96000,  'S16',  16, 16) : _lossless[(16, 96000)],
	('PCM_S16LE', 1, 176400, 'S16',  16, 16) : _lossless[(16, 176400)],
	('PCM_S16LE', 1, 192000, 'S16',  16, 16) : _lossless[(16, 192000)],
	('PCM_S16LE', 1, 44100,  'S16',  16, 16) : _lossless[(16, 44100)],
	('PCM_S16LE', 1, 48000,  'S16',  16, 16) : _lossless[(16, 48000)],
	('PCM_S16LE', 1, 96000,  'S16',  16, 16) : _lossless[(16, 96000)],
	('PCM_S24BE', 1, 176400, 'S32',  24, 24) : _lossless[(24, 176400)],
	('PCM_S24BE', 1, 192000, 'S32',  24, 24) : _lossless[(24, 192000)],
	('PCM_S24BE', 1, 44100,  'S32',  24, 24) : _lossless[(24, 44100)],
	('PCM_S24BE', 1, 48000,  'S32',  24, 24) : _lossless[(24, 48000)],
	('PCM_S24BE', 1, 96000,  'S32',  24, 24) : _lossless[(24, 96000)],
	('PCM_S24LE', 1, 176400, 'S32',  24, 24) : _lossless[(24, 176400)],
	('PCM_S24LE', 1, 192000, 'S32',  24, 24) : _lossless[(24, 192000)],
	('PCM_S24LE', 1, 44100,  'S32',  24, 24) : _lossless[(24, 44100)],
	('PCM_S24LE', 1, 48000,  'S32',  24, 24) : _lossless[(24, 48000)],
	('PCM_S24LE', 1, 96000,  'S32',  24, 24) : _lossless[(24, 96000)],
	('PCM_S32BE', 1, 176400, 'S32',  32, 32) : _lossless[(32, 176400)],
	('PCM_S32BE', 1, 192000, 'S32',  32, 32) : _lossless[(32, 192000)],
	('PCM_S32BE', 1, 44100,  'S32',  32, 32) : _lossless[(32, 44100)],
	('PCM_S32BE', 1, 48000,  'S32',  32, 32) : _lossless[(32, 48000)],
	('PCM_S32BE', 1, 96000,  'S32',  32, 32) : _lossless[(32, 96000)],
	('PCM_S32LE', 1, 176400, 'S32',  32, 32) : _lossless[(32, 176400)],
	('PCM_S32LE', 1, 192000, 'S32',  32, 32) : _lossless[(32, 192000)],
	('PCM_S32LE', 1, 44100,  'S32',  32, 32) : _lossless[(32, 44100)],
	('PCM_S32LE', 1, 48000,  'S32',  32, 32) : _lossless[(32, 48000)],
	('PCM_S32LE', 1, 96000,  'S32',  32, 32) : _lossless[(32, 96000)],
	('WAVPACK',   1, 176400, 'S16P', 0,  16) : _lossless[(16, 176400)],
	('WAVPACK',   1, 192000, 'S16P', 0,  16) : _lossless[(16, 192000)],
	('WAVPACK',   1, 44100,  'S16P', 0,  16) : _lossless[(16, 44100)],
	('WAVPACK',   1, 48000,  'S16P', 0,  16) : _lossless[(16, 48000)],
	('WAVPACK',   1, 96000,  'S16P', 0,  16) : _lossless[(16, 96000)],

    # LOSSY 44100
	('WAVPACK',     1, 44100, 'FLTP', 0, 32) : _lossy_44k_24b,
	('WAVPACK',     1, 48000, 'FLTP', 0, 32) : _lossy_48k_24b,
	('MP3',         1, 44100, 'FLTP', 0, 0)  : _lossy_44k_24b,
	('MP3',         1, 48000, 'FLTP', 0, 0)  : _lossy_48k_24b,
	('AAC',         1, 44100, 'FLTP', 0, 0)  : _lossy_44k_24b,
	('VORBIS',      1, 44100, 'FLTP', 0, 0)  : _lossy_44k_24b,
	('VORBIS',      1, 48000, 'FLTP', 0, 0)  : _lossy_48k_24b,
	('WMAPRO',      1, 44100, 'FLTP', 0, 0)  : _lossy_44k_16b,
	('WMAV2',       1, 44100, 'FLTP', 0, 0)  : _lossy_44k_16b,
	('WMALOSSLESS', 1, 44100, 'S16P', 0, 0)  : _lossy_44k_24b,

    #('OPUS',      FLTP, 0,  None) : ('opus', 24), # CAUTION
    ('OPUS',        1, 48000, 'FLTP', 0,  None) : _lossy_48k_32b,
}

#export LC_ALL=en_US.UTF-8

# WHERE TO SAVE THE CONVERTED FILES
GOOD_DIR = '/mnt/sda2/CONVERTED'
BAD_DIR = '/mnt/sda2/BAD'

#
TMP_DIR = '/tmp'

# HOW MANY PROCESSES TO RUN SIMULTANEOUSLY
CPUS_MAX = 12

def piped (cmd, size=65536):
    with os.popen(cmd) as fd:
        ret = fd.read(size)
    return ret

def version (cmd, start):
    with os.popen(cmd) as fd:
        ret = fd.read(65536).startswith(start)
    return ret

def execute (executable, args, env=os.environ):

    pid = os.fork()

    if pid == 0:
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

ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

def mhash (length):

    f  = int.from_bytes(os.read(RANDOMFD, 8), byteorder = 'little', signed=False)
    f += int(time.time() * 1000000)
    f += int(time.monotonic() * 1000000)
    f += int(random.random() * 0xFFFFFFFFFFFFFFFF)
    f += f >> 48
    f %= len(ALPHABET) ** length

    code = ''

    while f:
        code += ALPHABET[f % len(ALPHABET)]
        f //= len(ALPHABET)

    code += ALPHABET[0] * (length - len(code))

    return code

PID = os.getpid()
assert 1 <= PID <= 0xFFFFFFFF

#
RANDOMFD = os.open('/dev/urandom', os.O_RDONLY)
assert 0 <= RANDOMFD <= 10

TNAME = mhash(13)
assert len(TNAME) == 13

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
            f'{TMP_DIR}/{TNAME}/{tid}-decoded',
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
    decoded = f'{TMP_DIR}/{TNAME}/{tid}-decoded'
    encoded = f'{TMP_DIR}/{TNAME}/{tid}-encoded'

    tmpGood = f'{GOOD_DIR}/{TNAME}-{tid}.tmp'
    tmpBad  =  f'{BAD_DIR}/{TNAME}-{tid}.tmp'

    good = GOOD_DIR, tmpGood
    bad  = BAD_DIR,  tmpBad

    while original := os.read(pipeIn, 2048):
        original = original.decode()

        i = o = imap = ibuff = fp = fpFormat = fpStream = tags = args = None

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

            try:
                fpFormat  = fp['format']
            except KeyError:
                print(f'[{tid}] {original}: ERROR: NO FFPROBE FORMAT!')
                continue

            fpStream, = (s for s in fp['streams'] if s['codec_type'] == 'audio') # NOTE: ONLY SUPPORT FILES WITH 1 AUDIO STREAM

            (
                # FORMAT
                ORIGINAL_FORMAT_NAME,
                ORIGINAL_FORMAT_NAME_LONG,
                ORIGINAL_TAGS,
                # STREAM
                ORIGINAL_CODEC_NAME,
                ORIGINAL_CODEC_LONG_NAME,
                ORIGINAL_SAMPLE_FMT,
                ORIGINAL_SAMPLE_RATE,
                ORIGINAL_CHANNELS,
                ORIGINAL_CHANNEL_LAYOUT,
                ORIGINAL_BITS,
                ORIGINAL_BITS_RAW,
                ORIGINAL_DURATION,
                ORIGINAL_BITRATE,
                ORIGINAL_TAGS2

            ) = ( (d[k] if k in d and d[k] != '' else None)
                for d, K in (
                    ( fpFormat, (
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

        if ORIGINAL_DURATION is None:
            print(f'[{tid}] {original}: ERROR: DURATION IS NONE!')
            continue

        #
        tags = { k: ' '.join(v.split()).upper()
            for k, v in ( ('_'.join(k_.replace('_', ' ').replace('-', ' ').split()).upper(), v_)
                for T in (ORIGINAL_TAGS, ORIGINAL_TAGS2)
                    if T is not None
                        for k_, v_ in T.items()
                            if k_ and v_ is not None
            )
        }

        #
        if 'CONVERSION_TIME' in tags:
            # TODAS MENOS ESTAS
            tags.pop('ORIGINAL_CODEC_TAG_STRING', None)
            tags.pop('ORIGINAL_CODEC_TAG',        None)
            tags.pop('ORIGINAL_TIME_BASE',        None)
            tags.pop('ORIGINAL_DURATION_TS',      None)
        else:
            # SOMENTE ESTAS
            tags = { k: v[:1024] for k, v in tags.items() if re.match(r'^((|ALBUM_)(ARTIST|PERFORMER|TITLE|ALBUM)(|S)(|SORT|_SORT)|TIT[1-9]|YEAR|DATE|YOUTUBE|TRACKNUMBER|TRACKTOTAL|DISCNUMBER|ENCODER|MCDI|TALB|TOAL|TOFN|TOPE|TPE[0-9]|TRCK|REMIXED.BY|REMIXE[DR]|ORIGINALTITLE|DESCRIPTION|COMMENT)$', k) }

        CONVERSION_TIME           = tags.pop('CONVERSION_TIME',         int(time.time()))
        ORIGINAL_HASH             = tags.pop('ORIGINAL_HASH',                   None)
        ORIGINAL_FILEPATH         = tags.pop('ORIGINAL_FILEPATH',        tags.pop('ORIGINAL_FILENAME', tags.pop('ORIGINAL_PATH', original)))
        ORIGINAL_BITS             = tags.pop('ORIGINAL_BITS',             ORIGINAL_BITS)
        ORIGINAL_BITS_RAW         = tags.pop('ORIGINAL_BITS_RAW',         ORIGINAL_BITS_RAW)
        ORIGINAL_BITRATE          = tags.pop('ORIGINAL_BITRATE',          ORIGINAL_BITRATE)
        ORIGINAL_CHANNELS         = tags.pop('ORIGINAL_CHANNELS',         ORIGINAL_CHANNELS)
        ORIGINAL_CHANNEL_LAYOUT   = tags.pop('ORIGINAL_CHANNEL_LAYOUT',   ORIGINAL_CHANNEL_LAYOUT)
        ORIGINAL_SAMPLE_FMT       = tags.pop('ORIGINAL_SAMPLE_FMT',       ORIGINAL_SAMPLE_FMT)
        ORIGINAL_SAMPLE_RATE      = tags.pop('ORIGINAL_SAMPLE_RATE',      ORIGINAL_SAMPLE_RATE)
        ORIGINAL_FORMAT_NAME      = tags.pop('ORIGINAL_FORMAT_NAME',      ORIGINAL_FORMAT_NAME)
        ORIGINAL_FORMAT_NAME_LONG = tags.pop('ORIGINAL_FORMAT_NAME_LONG', ORIGINAL_FORMAT_NAME_LONG)
        ORIGINAL_CODEC_NAME       = tags.pop('ORIGINAL_CODEC_NAME',       ORIGINAL_CODEC_NAME)
        ORIGINAL_CODEC_LONG_NAME  = tags.pop('ORIGINAL_CODEC_LONG_NAME',  ORIGINAL_CODEC_LONG_NAME)
        ORIGINAL_DURATION         = tags.pop('ORIGINAL_DURATION',         ORIGINAL_DURATION)

        #
        ORIGINAL_SAMPLE_FMT       = str.upper (ORIGINAL_SAMPLE_FMT)
        ORIGINAL_FORMAT_NAME      = str.upper (ORIGINAL_FORMAT_NAME)
        ORIGINAL_FORMAT_NAME_LONG = str.upper (ORIGINAL_FORMAT_NAME_LONG)
        ORIGINAL_CODEC_NAME       = str.upper (ORIGINAL_CODEC_NAME)
        ORIGINAL_CODEC_LONG_NAME  = str.upper (ORIGINAL_CODEC_LONG_NAME)
        ORIGINAL_CHANNELS         = int       (ORIGINAL_CHANNELS)
        ORIGINAL_SAMPLE_RATE      = int       (ORIGINAL_SAMPLE_RATE)
        ORIGINAL_DURATION         = float     (ORIGINAL_DURATION)

        if ORIGINAL_BITS     is not None: ORIGINAL_BITS     = int(ORIGINAL_BITS)
        if ORIGINAL_BITS_RAW is not None: ORIGINAL_BITS_RAW = int(ORIGINAL_BITS_RAW)

        if not (ORIGINAL_BITS in (None, 0, 8, 16, 24, 32)):
            print(f'[{tid}] {original}: ERROR: BAD BITS: {ORIGINAL_BITS}')
            continue

        if not (ORIGINAL_BITS_RAW in (None, 0, 8, 16, 24, 32)):
            print(f'[{tid}] {original}: ERROR: BAD BITS RAW: {ORIGINAL_BITS_RAW}')
            continue

        if not (1 <= ORIGINAL_CHANNELS <= 2):
            print(f'[{tid}] {original}: ERROR: BAD CHANNELS: {ORIGINAL_CHANNELS}')
            continue

        if not (20 <= ORIGINAL_DURATION <= 7*24*60*60):
            if ORIGINAL_DURATION < 15:
                os.unlink(original)
            print(f'[{tid}] {original}: ERROR: BAD DURATION: {ORIGINAL_DURATION}')
            continue

        #
        isBinaural = any('BINAURAL' in v.upper() for v in (original, *tags.values()))

        if isBinaural:
            print(f'[{tid}] {original}: SKIPPED: BINAURAL')
            continue

        #
        channels = 1 + isBinaural

        # TODO:
        assert channels == 1

        #
        try:
            br = mapa[(
                ORIGINAL_CODEC_NAME, channels,
                ORIGINAL_SAMPLE_RATE,
                ORIGINAL_SAMPLE_FMT,
                ORIGINAL_BITS,
                (ORIGINAL_BITS_RAW if ORIGINAL_BITS_RAW else ORIGINAL_BITS),
            )]
            assert 96 <= br <= 500
        except KeyError as e:
            print(f'[{tid}] {original}: ERROR: EITAAAAAAA!!!', repr(e))
            continue

        #
        for f in (encoded, decoded, tmpGood, tmpBad):
            try:
                os.unlink(f)
            except FileNotFoundError:
                pass

        # DECODE FIXME: error vs quiet?
        if execute('/usr/bin/ffmpeg', ('ffmpeg', '-y', '-hide_banner', '-loglevel', 'quiet', '-i', original, '-ac', str(channels), '-f', 's24le', decoded)):
            print(f'[{tid}] {original}: ERROR: DECODE FAILED.')
            continue

        #
        if ORIGINAL_HASH is None:
            with os.popen(f'b3sum --num-threads 1 --no-names --raw {decoded} | base64') as bfd:
                b3sum = bfd.read(1024)
            assert len(b3sum) == 45 and b3sum.endswith('=\n')
            ORIGINAL_HASH = b3sum.replace('/', '@').replace('+', '$').rstrip('\n').rstrip('=')

        # ENCODE
        args = [ 'opusenc', decoded, encoded,
            '--quiet',
            '--music',
            '--comp', '10',
            '--bitrate', str(br),
            '--raw',
            '--raw-endianness', '0',
            '--raw-bits', '24',
            '--raw-chan', str(channels),
            '--raw-rate', str(fpStream['sample_rate']),
        ]

        # GENERATED TAGS
        for name in (
            'CONVERSION_TIME',
            'ORIGINAL_HASH',
            'ORIGINAL_FILEPATH',
            'ORIGINAL_BITS',
            'ORIGINAL_BITS_RAW',
            'ORIGINAL_BITRATE',
            'ORIGINAL_CHANNELS',
            'ORIGINAL_CHANNEL_LAYOUT',
            'ORIGINAL_SAMPLE_FMT',
            'ORIGINAL_SAMPLE_RATE',
            'ORIGINAL_FORMAT_NAME',
            'ORIGINAL_FORMAT_NAME_LONG',
            'ORIGINAL_CODEC_NAME',
            'ORIGINAL_CODEC_LONG_NAME',
            'ORIGINAL_DURATION',
        ):
            val = eval(name)
            if val is not None:
                args.extend(('--comment', f'{name}={val}'))

        # ORIGINAL TAGS
        for name, val in tags.items():
            args.extend(('--comment', f'{name}={val}'))

        # EXECUTE THE ENCODER
        if execute('/usr/bin/opusenc', args):
            print(f'[{tid}] {original}: ERROR: ENCODE FAILED.')
            continue

        # DONT NEED IT ANYMORE
        os.unlink(decoded)

        # VERIFY
        assert channels == int(piped(f'soxi -c {encoded}'))
        assert 0        == int(piped(f'soxi -b {encoded}'))
        assert 16       == int(piped(f'soxi -p {encoded}'))
        assert 48000    == int(piped(f'soxi -r {encoded}'))

        #
        where, tmp = good

        #
        dur = float(piped(f'soxi -D {encoded}'))
        if not (-1 <= (ORIGINAL_DURATION - dur) <= 1):
            print(f'[{tid}] {original}: ERROR: DURATION MISMATCH: {ORIGINAL_DURATION} VS {dur}')
            where, tmp = bad

        # NOW COPY FROM TEMP
        new = f'{where}/{mhash(12)}'

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
