#!/usr/bin/python

'''

#for x in * ; do mv -vn "${x}" $(metaflac --show-md5sum "${x}") ; done

# CONVERT
function rehash () {
    for x in "${@}" ; do
        MD5=-
        MD5=$(metaflac --show-md5sum ${x}) || continue
        OHASH=-
        OHASH=$(spipe $[1*1024*1024] /bin/ffmpeg ffmpeg -y -hide_banner -loglevel quiet -i ${x} -f s24le - | b3sum --num-threads 1 --no-names --raw | base64 | tr / @ | tr + \$) || continue
        BR=-
        BR=$(soxi -c ${x}):$(soxi -b ${x}):$(soxi -r ${x}) || continue
        [ ${#MD5} = 32 ] || continue
        [ ${#OHASH} = 44 ] || continue
        [ ${OHASH:43:1} = = ] || continue
        OHASH=${OHASH:0:43}
        case ${BR} in
            1:16:44100) BR=180 ;;
            1:24:44100) BR=180 ;;
            1:32:44100) BR=180 ;;
            1:16:48000) BR=180 ;;
            1:24:48000) BR=190 ;;
            1:32:48000) BR=190 ;;
            1:16:88200) BR=200 ;;
            1:24:88200) BR=220 ;;
            1:32:88200) BR=220 ;;
            1:16:96000) BR=200 ;;
            1:24:96000) BR=220 ;;
            1:32:96000) BR=220 ;;
            1:16:192000) BR=256 ;;
            1:24:192000) BR=280 ;;
            1:32:192000) BR=280 ;;
            *) echo ${BR}
                continue ;;
        esac
        if opusenc --quiet --music --discard-pictures --comp 10 --bitrate ${BR} --comment ORIGINAL_HASH=${OHASH} --comment ORIGINAL_FLAC_MD5=${MD5} -- ${x} opus-flac/${OHASH} ; then
			rm -fv -- "${x}"
        fi
    done
}

rehash flac-md5/[a-c]*
rehash flac-md5/[d-f]*
rehash flac-md5/[0-4]*
rehash flac-md5/[6-9]*

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
import base64

#
_lossless_44k_16b = 180
_lossless_44k_24b = 180
_lossless_44k_32b = 180

_lossless_48k_16b = 180
_lossless_48k_24b = 190
_lossless_48k_32b = 190

_lossless_96k_16b = 200
_lossless_96k_24b = 220
_lossless_96k_32b = 220

_lossless_192k_16b = 256
_lossless_192k_24b = 280
_lossless_192k_32b = 280

_lossy_44k_16b = 150
_lossy_44k_24b = 150
_lossy_44k_32b = 150

_lossy_48k_16b = 150
_lossy_48k_24b = 150
_lossy_48k_32b = 150

mapa = {
    # LOSSLESS 44100
    ('FLAC',        1, 44100, 's16',  0,  16)   : _lossless_44k_16b,
    ('FLAC',        1, 44100, 's32',  0,  24)   : _lossless_44k_24b,
    ('FLAC',        1, 44100, 's32',  0,  32)   : _lossless_44k_32b,
    ('ALAC',        1, 44100, 's16p', 0,  16)   : _lossless_44k_16b,
    ('ALAC',        1, 44100, 's32p', 0,  24)   : _lossless_44k_24b,
    ('ALAC',        1, 44100, 's32p', 0,  32)   : _lossless_44k_32b,
    ('APE',         1, 44100, 's16p', 0,  16)   : _lossless_44k_16b,
    ('APE',         1, 44100, 's32p', 0,  24)   : _lossless_44k_24b,
    ('APE',         1, 44100, 's32p', 0,  32)   : _lossless_44k_32b,
    ('PCM_S16BE',   1, 44100, 's16',  16, None) : _lossless_44k_16b,
    ('PCM_S16LE',   1, 44100, 's16',  16, None) : _lossless_44k_16b,
    ('PCM_S24BE',   1, 44100, 's32',  24, 24)   : _lossless_44k_24b,
    ('PCM_S24LE',   1, 44100, 's32',  24, 24)   : _lossless_44k_24b,
    ('PCM_S32BE',   1, 44100, 's32',  32, 32)   : _lossless_44k_32b,
    ('PCM_S32LE',   1, 44100, 's32',  32, 32)   : _lossless_44k_32b,
    ('PCM_F32LE',   1, 44100, 'flt',  32, None) : _lossless_44k_32b,
    ('DTS',         1, 44100, 'fltp', 0,  None) : _lossless_44k_32b,
    ('WAVPACK',     1, 44100, 's16p', 0,  16)   : _lossless_44k_16b,

    # LOSSLESS 48000
    ('FLAC',        1, 48000, 's16',  0,  16)   : _lossless_48k_16b,
    ('FLAC',        1, 48000, 's32',  0,  24)   : _lossless_48k_24b,
    ('FLAC',        1, 48000, 's32',  0,  32)   : _lossless_48k_32b,
    ('ALAC',        1, 48000, 's16p', 0,  16)   : _lossless_48k_16b,
    ('ALAC',        1, 48000, 's32p', 0,  24)   : _lossless_48k_24b,
    ('ALAC',        1, 48000, 's32p', 0,  32)   : _lossless_48k_32b,
    ('APE',         1, 48000, 's16p', 0,  16)   : _lossless_48k_16b,
    ('APE',         1, 48000, 's32p', 0,  24)   : _lossless_48k_24b,
    ('APE',         1, 48000, 's32p', 0,  32)   : _lossless_48k_32b,
    ('PCM_S16BE',   1, 48000, 's16',  16, None) : _lossless_48k_16b,
    ('PCM_S16LE',   1, 48000, 's16',  16, None) : _lossless_48k_16b,
    ('PCM_S24BE',   1, 48000, 's32',  24, 24)   : _lossless_48k_24b,
    ('PCM_S24LE',   1, 48000, 's32',  24, 24)   : _lossless_48k_24b,
    ('PCM_S32BE',   1, 48000, 's32',  32, 32)   : _lossless_48k_32b,
    ('PCM_S32LE',   1, 48000, 's32',  32, 32)   : _lossless_48k_32b,
    ('PCM_F32LE',   1, 48000, 'flt',  32, None) : _lossless_48k_32b,
    ('DTS',         1, 48000, 'fltp', 0,  None) : _lossless_48k_32b,
    ('WAVPACK',     1, 48000, 's16p', 0,  16)   : _lossless_48k_16b,

    # LOSSLESS 96000
    ('FLAC',        1, 96000, 's16',  0,  16)   : _lossless_96k_16b,
    ('FLAC',        1, 96000, 's32',  0,  24)   : _lossless_96k_24b,
    ('FLAC',        1, 96000, 's32',  0,  32)   : _lossless_96k_32b,
    ('ALAC',        1, 96000, 's16p', 0,  16)   : _lossless_96k_16b,
    ('ALAC',        1, 96000, 's32p', 0,  24)   : _lossless_96k_24b,
    ('ALAC',        1, 96000, 's32p', 0,  32)   : _lossless_96k_32b,
    ('APE',         1, 96000, 's16p', 0,  16)   : _lossless_96k_16b,
    ('APE',         1, 96000, 's32p', 0,  24)   : _lossless_96k_24b,
    ('APE',         1, 96000, 's32p', 0,  32)   : _lossless_96k_32b,
    ('PCM_S16BE',   1, 96000, 's16',  16, None) : _lossless_96k_16b,
    ('PCM_S16LE',   1, 96000, 's16',  16, None) : _lossless_96k_16b,
    ('PCM_S24BE',   1, 96000, 's32',  24, 24)   : _lossless_96k_24b,
    ('PCM_S24LE',   1, 96000, 's32',  24, 24)   : _lossless_96k_24b,
    ('PCM_S32BE',   1, 96000, 's32',  32, 32)   : _lossless_96k_32b,
    ('PCM_S32LE',   1, 96000, 's32',  32, 32)   : _lossless_96k_32b,
    ('PCM_F32LE',   1, 96000, 'flt',  32, None) : _lossless_96k_32b,
    ('DTS',         1, 96000, 'fltp', 0,  None) : _lossless_96k_32b,
    ('WAVPACK',     1, 96000, 's16p', 0,  16)   : _lossless_96k_16b,

    # LOSSLESS 192000
    ('FLAC',        1, 192000, 's16',  0,  16)   : _lossless_192k_16b,
    ('FLAC',        1, 192000, 's32',  0,  24)   : _lossless_192k_24b,
    ('FLAC',        1, 192000, 's32',  0,  32)   : _lossless_192k_32b,
    ('ALAC',        1, 192000, 's16p', 0,  16)   : _lossless_192k_16b,
    ('ALAC',        1, 192000, 's32p', 0,  24)   : _lossless_192k_24b,
    ('ALAC',        1, 192000, 's32p', 0,  32)   : _lossless_192k_32b,
    ('APE',         1, 192000, 's16p', 0,  16)   : _lossless_192k_16b,
    ('APE',         1, 192000, 's32p', 0,  24)   : _lossless_192k_24b,
    ('APE',         1, 192000, 's32p', 0,  32)   : _lossless_192k_32b,
    ('PCM_S16BE',   1, 192000, 's16',  16, None) : _lossless_192k_16b,
    ('PCM_S16LE',   1, 192000, 's16',  16, None) : _lossless_192k_16b,
    ('PCM_S24BE',   1, 192000, 's32',  24, 24)   : _lossless_192k_24b,
    ('PCM_S24LE',   1, 192000, 's32',  24, 24)   : _lossless_192k_24b,
    ('PCM_S32BE',   1, 192000, 's32',  32, 32)   : _lossless_192k_32b,
    ('PCM_S32LE',   1, 192000, 's32',  32, 32)   : _lossless_192k_32b,
    ('PCM_F32LE',   1, 192000, 'flt',  32, None) : _lossless_192k_32b,
    ('DTS',         1, 192000, 'fltp', 0,  None) : _lossless_192k_32b,
    ('WAVPACK',     1, 192000, 's16p', 0,  16)   : _lossless_192k_16b,

    # LOSSY 44100
    ('WAVPACK',     1, 44100, 'fltp', 0,  32)   : _lossy_44k_24b,
    ('WAVPACK',     1, 48000, 'fltp', 0,  32)   : _lossy_48k_24b,
    ('MP3',         1, 44100, 'fltp', 0,  None) : _lossy_44k_24b,
    ('MP3',         1, 48000, 'fltp', 0,  None) : _lossy_48k_24b,
    ('AAC',         1, 44100, 'fltp', 0,  None) : _lossy_44k_24b,
    ('VORBIS',      1, 44100, 'fltp', 0,  None) : _lossy_44k_24b,
    ('VORBIS',      1, 48000, 'fltp', 0,  None) : _lossy_48k_24b,
    ('WMAPRO',      1, 44100, 'fltp', 0,  None) : _lossy_44k_16b,
    ('WMAV2',       1, 44100, 'fltp', 0,  None) : _lossy_44k_16b,
    ('WMALOSSLESS', 1, 44100, 's16p', 0,  None) : _lossy_44k_24b,

    #('OPUS',      'fltp', 0,  None) : ('opus', 24), # CAUTION
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

        CONVERSION_TIME = int(time.time())

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
                ORIGINAL_CODEC_TAG_STRING,
                ORIGINAL_CODEC_TAG,
                ORIGINAL_SAMPLE_FMT,
                ORIGINAL_SAMPLE_RATE,
                ORIGINAL_CHANNELS,
                ORIGINAL_CHANNEL_LAYOUT,
                ORIGINAL_BITS,
                ORIGINAL_BITS_RAW,
                ORIGINAL_DURATION_TS,
                ORIGINAL_DURATION,
                ORIGINAL_BITRATE,
                ORIGINAL_TIME_BASE,
                ORIGINAL_TAGS2

            ) = ( (d[k] if k in d else None)
                for d, K in (
                    ( fpFormat, (
                        'format_name',
                        'format_long_name',
                        'tags',
                    )),
                    ( fpStream, (
                        'codec_name',
                        'codec_long_name',
                        'codec_tag_string',
                        'codec_tag',
                        'sample_fmt',
                        'sample_rate',
                        'channels',
                        'channel_layout',
                        'bits_per_sample',
                        'bits_per_raw_sample',
                        'duration_ts',
                        'duration',
                        'bit_rate',
                        'time_base',
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
        ORIGINAL_FILEPATH         = original
        ORIGINAL_FORMAT_NAME      = str.upper (ORIGINAL_FORMAT_NAME)
        ORIGINAL_FORMAT_NAME_LONG = str.upper (ORIGINAL_FORMAT_NAME_LONG)
        ORIGINAL_CODEC_NAME       = str.upper (ORIGINAL_CODEC_NAME)
        ORIGINAL_CODEC_LONG_NAME  = str.upper (ORIGINAL_CODEC_LONG_NAME)
        ORIGINAL_CHANNELS         = int       (ORIGINAL_CHANNELS)
        ORIGINAL_SAMPLE_RATE      = int       (ORIGINAL_SAMPLE_RATE)
        ORIGINAL_DURATION         = float     (ORIGINAL_DURATION)
        ORIGINAL_DURATION_TS      = int       (ORIGINAL_DURATION_TS)

        if ORIGINAL_BITS     is not None: ORIGINAL_BITS     = int(ORIGINAL_BITS)
        if ORIGINAL_BITS_RAW is not None: ORIGINAL_BITS_RAW = int(ORIGINAL_BITS_RAW)

        if not (ORIGINAL_BITS in (None, 0, 8, 16, 24, 32)):
            print(f'[{tid}] {original}: ERROR: BAD BITS: {ORIGINAL_BITS}')
            continue

        if not (ORIGINAL_BITS_RAW in (None, 0, 8, 16, 24, 32)):
            print(f'[{tid}] {original}: ERROR: BAD BITS RAW: {ORIGINAL_BITS_RAW}')
            continue

        if not (1 <= ORIGINAL_CHANNELS <= 16):
            print(f'[{tid}] {original}: ERROR: BAD CHANNELS: {ORIGINAL_CHANNELS}')
            continue

        if ORIGINAL_DURATION < 15:
            print(f'[{tid}] {original}: ERROR: BAD DURATION: {ORIGINAL_DURATION}')
            os.unlink(original)
            continue

        if not (20 <= ORIGINAL_DURATION <= 7*24*60*60):
            print(f'[{tid}] {original}: ERROR: BAD DURATION: {ORIGINAL_DURATION}')
            continue

        if not (1 <= ORIGINAL_DURATION_TS):
            print(f'[{tid}] {original}: ERROR: BAD DURATION TS: {ORIGINAL_DURATION_TS}')
            continue

        #
        for f in (encoded, decoded, tmpGood, tmpBad):
            try:
                os.unlink(f)
            except FileNotFoundError:
                pass

        # TODO: verificar RELACAO ENTRE sample_fmt e ORIGINAL_BITS

        # COPY ONLY THOSE TAGS
        tags = { k: ' '.join(v.split()).upper()
            for k, v in ( ('_'.join(k_.replace('_', ' ').replace('-', ' ').split()).upper(), v_)
                for T in (ORIGINAL_TAGS, ORIGINAL_TAGS2)
                    if T is not None
                        for k_, v_ in T.items()
                            if k_ and v_ is not None
            ) if re.match(r'^((|ALBUM_)(ARTIST|PERFORMER|TITLE|ALBUM)(|S)(|SORT|_SORT)|TIT[1-9]|YEAR|DATE|YOUTUBE|TRACKNUMBER|TRACKTOTAL|DISCNUMBER|ENCODER|MCDI|TALB|TOAL|TOFN|TOPE|TPE[0-9]|TRCK|REMIXED.BY|REMIXE[DR]|ORIGINALTITLE|DESCRIPTION|COMMENT)$', k)
        }

        isBinaural = any('BINAURAL' in v.upper() for v in (original, *tags.values()))

        if isBinaural:
            print(f'[{tid}] {original}: SKIPPED: BINAURAL')
            continue

        # CHANNELS
        if not (1 <= ORIGINAL_CHANNELS <= 2):
            print(f'[{tid}] {original}: SKIPPED: BAD CHANNELS')
            continue

        #
        channels = 1 + isBinaural

        #
        try:
            br = mapa[(
                ORIGINAL_CODEC_NAME, channels,
                ORIGINAL_SAMPLE_RATE,
                ORIGINAL_SAMPLE_FMT,
                ORIGINAL_BITS,
                ORIGINAL_BITS_RAW)]
        except KeyError as e:
            print(f'[{tid}] {original}: ERROR: EITAAAAAAA!!!', repr(e))
            continue

        #
        assert 96 <= br <= 320

        #
        assert channels == 1 # TODO:

        # DECODE
        # error vs quiet?
        if execute('/usr/bin/ffmpeg', ('ffmpeg', '-y', '-hide_banner', '-loglevel', 'quiet', '-i', original, '-ac', str(channels), '-f', 's24le', decoded)):
            print(f'[{tid}] {original}: ERROR: DECODE FAILED.')
            continue

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
            '--raw-rate', str(ORIGINAL_SAMPLE_RATE),
        ]

        #
        with os.popen(f'b3sum --num-threads 1 --no-names --raw {decoded}') as bfd:
            b3sum = base64.b64encode(os.read(bfd.fileno(), 1024)).replace(b'/', b'@').replace(b'+', b'$').decode()
            assert len(b3sum) == 44 and b3sum.endswith('='), b3sum
            args.extend(('--comment', f'ORIGINAL_HASH={b3sum[:43]}')) # TODO: É O ORIGINAL, EM SEU RAW, DECODED COM OS BITS *ESCOLHIDOS*

        # GENERATED TAGS
        for name in (
            'ORIGINAL_FILEPATH',
            'ORIGINAL_FORMAT_NAME',
            'ORIGINAL_FORMAT_NAME_LONG',
            'ORIGINAL_CODEC_NAME',
            'ORIGINAL_CODEC_LONG_NAME',
            'ORIGINAL_CODEC_TAG_STRING',
            'ORIGINAL_CODEC_TAG',
            'ORIGINAL_SAMPLE_FMT',
            'ORIGINAL_SAMPLE_RATE',
            'ORIGINAL_CHANNELS',
            'ORIGINAL_CHANNEL_LAYOUT',
            'ORIGINAL_BITS',
            'ORIGINAL_BITS_RAW',
            'ORIGINAL_TIME_BASE',
            'ORIGINAL_DURATION_TS',
            'ORIGINAL_DURATION',
            'ORIGINAL_BITRATE',
            'CONVERSION_TIME',
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
        new = f'{where}/{mhash(12)}.opus'

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
