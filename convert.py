#!/usr/bin/python

import sys
import os
import io
import stat
import time
import json
import re
import traceback
import mmap

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

def mhash (length, alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'):
    assert isinstance(length, int) and 1 <= length <= 512
    f = sum(int(x()*1000000) for x in (os.getpid, time.time, time.time_ns, time.monotonic, time.monotonic_ns))
    code  = ''.join(alphabet[(x + f) % len(alphabet)] for x in os.read(RANDOMFD, length))
    assert len(code) == length
    return code

PID = os.getpid()
assert 1 <= PID <= 0xFFFFFFFF

#
RANDOMFD = os.open('/dev/urandom', os.O_RDONLY)
assert 0 <= RANDOMFD <= 10

TNAME = mhash(16)
assert len(TNAME) == 16

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
            for f in os.popen(f"find '{f}' -type f -print0").read(8*1024*1024).encode().split(b'\x00'):
                os.write(pipeOut, f)
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
        if originalSize < 65536:
            print(f'[{tid}] {original}: SKIPPED (TOO SMALL)')
            continue

        CONVERSION_TIME = int(time.time())

        #
        try:
            with open(original, 'rb') as xxx:
                with os.popen(f'ffprobe -v quiet -print_format json -show_format -show_streams -- /proc/{os.getpid()}/fd/{xxx.fileno()}') as fd:
                    fp = json.loads(fd.read(1*1024*1024))
            fpFormat  = fp['format']
            fpStream, = (s for s in fp['streams'] if s['codec_type'] == 'audio') # NOTE: ONLY SUPPORT FILES WITH 1 AUDIO STREAM
        except BaseException:
            print(f'[{tid}] {original}: ERROR: FFPROBE FAILED')
            continue

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

        if not (10 <= ORIGINAL_DURATION <= 7*24*60*60):
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

        #
        try:
            fmt, bits = {
                ('FLAC',      's16',  0,  16)   : ('flac', 16),
                ('FLAC',      's32',  0,  24)   : ('flac', 24),
                ('FLAC',      's32',  0,  32)   : ('flac', 32),
                ('ALAC',      's16p', 0,  16)   : ('flac', 16),
                ('ALAC',      's32p', 0,  24)   : ('flac', 24),
                ('ALAC',      's32p', 0,  32)   : ('flac', 32),
                ('APE',       's16p', 0,  16)   : ('flac', 16),
                ('APE',       's32p', 0,  24)   : ('flac', 24),
                ('APE',       's32p', 0,  32)   : ('flac', 32),
                ('PCM_S16BE', 's16',  16, None) : ('flac', 16),
                ('PCM_S16LE', 's16',  16, None) : ('flac', 16),
                ('PCM_S24BE', 's32',  24, 24)   : ('flac', 24),
                ('PCM_S24LE', 's32',  24, 24)   : ('flac', 24),
                ('MP3',       'fltp', 0,  None) : ('opus', 24),
                ('AAC',       'fltp', 0,  None) : ('opus', 24),
                ('VORBIS',    'fltp', 0,  None) : ('opus', 24),
                ('WMAPRO',    'fltp', 0,  None) : ('opus', 24),
            } [(ORIGINAL_CODEC_NAME,
                ORIGINAL_SAMPLE_FMT,
                ORIGINAL_BITS,
                ORIGINAL_BITS_RAW)]
        except KeyError as e:
            print(f'[{tid}] {original}: ERROR: EITAAAAAAA!!!', repr(e))
            continue

        # CHANNELS
        if ORIGINAL_CHANNELS == 2:
            if False:
                # TODO: NO CASO DE BINAURAL, NAO COLOCAR EM MONO
                channels = 2
            else:
                channels = 1
        else:
            channels = ORIGINAL_CHANNELS

        # DECODE
        # error vs quiet?
        if execute('/usr/bin/ffmpeg', ('ffmpeg', '-y', '-hide_banner', '-loglevel', 'quiet', '-i', original, '-ac', str(channels), '-f', f's{bits}le', decoded)):
            print(f'[{tid}] {original}: ERROR: DECODE FAILED.')
            continue

        # ENCODE
        if fmt == 'opus': # OPUS
            cmd, args, argsTag = '/usr/bin/opusenc', [ 'opusenc', decoded, encoded,
                '--quiet',
                '--music',
                '--comp', '10',
                '--bitrate', '150',
                '--raw',
                '--raw-endianness', '0',
                '--raw-bits', str(bits),
                '--raw-chan', str(channels),
                '--raw-rate', str(ORIGINAL_SAMPLE_RATE),
            ], '--comment'
        else: # FLAC
            cmd, args, argsTag = '/usr/bin/flac', [ 'flac', decoded, '-o', encoded,
                #-A kaiser_bessel
                #-A bartlett_hann
                #-A hamming
                #-A hann
                #-A nuttall
                #-A rectangle
                #-A triangle
                #-A bartlett
                #-A blackman
                #-A blackman_harris_4term_92db
                #-A connes
                #-A flattop
                #-A gauss
                #-A subdivide_tukey
                #--exhaustive-model-search
                #--qlp-coeff-precision-search
                #--max-lpc-order=14
                #-l 16
                #--lax -b 16384 -l 32 -r 15
                '--force-raw-format',
                '--sign=signed',
                '--endian=little',
                f'--bps={bits}',
                f'--channels={channels}',
                f'--sample-rate={ORIGINAL_SAMPLE_RATE}',
                '--silent',
                '--best',
                '--no-padding',
                '--lax',
                '-b', '16384',
                '-l', '32',
                '-r', '15'
            ], '-T'

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
                args.extend((argsTag, f'{name}={val}'))

        # ORIGINAL TAGS
        for name, val in tags.items():
            args.extend((argsTag, f'{name}={val}'))

        # EXECUTE THE ENCODER
        if execute(cmd, args):
            print(f'[{tid}] {original}: ERROR: ENCODE FAILED.')
            continue

        # DONT NEED IT ANYMORE
        os.unlink(decoded)

        # VERIFY
        if fmt == 'flac':
            # FLAC
            assert channels             == int(piped(f'metaflac --show-channels    {encoded}'))
            assert bits                 == int(piped(f'metaflac --show-bps         {encoded}'))
            assert ORIGINAL_SAMPLE_RATE == int(piped(f'metaflac --show-sample-rate {encoded}'))
        else:
            # OPUS
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
        new = f'{where}/{mhash(10)}.{fmt}'

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
