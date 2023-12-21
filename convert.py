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

# random.shuffle(x := list('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz@=+-'*50)) ; CHECKSUM_ALPHABET = ''.join(x)
CHECKSUM_ALPHABET = 'dAln0NK4kB7mx9ZINI@UBdb0YkCOtN-zUBTe0@dqnOhlRooren5tnRy1T7BUoKytTW5Htc9CUquWkWT0N@u5g1hQt260E3=RLdYLMn+5NtPTI2ym-i4GWa0eQAoDX32PS0vGG7aYMpk4Vdf3VLMEDCyy7558nis7bBNJ6FOPJi@v2vGDI9OYuOhyAYHI++Odhxcr8ktO3vJozxgU@G=Jmrjq+5EhjD73R1T@zDbUmX8MD6t81m1tWARFXkynruNPIP4KblMM=7BbYSHlfysH7F@V9vfES78mifyZhQq4eQicFh+YnAtJDJcADH3Jo9eHGaQ8A@h6SpcDxdKJRG69Vhz2cvq@OgtfjxZaIYzk2AMBzeN2jpy9qyzBIl9IJeJcxlWPI-ogL1wsUriybiFUUFg2MHb@wnBYKoyxgBzxl5WPcdWykta@4uCzRLL7jIK3-0PsRy-q1EaC@KUkehaHMriLkHCpgZE7lLsxbVTpXxAb+ZK-M4piIqGhuRO6KGBTDTePy-5hDPa7IWyds0HYEr2wkvae=KbCaBqfZNx3ZUB8hGcD6wmPdGecNzlO3DVht47g+LfNw1lboYfxx=JreBA@4Q2Y85dTZFgVO@51fhWb0rtfzH4Q-qNyYIlm@UXbkSHjQCHQllisxN4DkAh50fS=Xlwkwz2qU6c=uAlzKIhXEyEH@auSyM4x68NYOUgx+3Hi904+cm2X=Emf3t32lQj5dc5bU6jPsdGjTXz30pnANZMYPiDiVsFfgyCuMxr-2BnHDhkMYt5Px+lWiArT3gvvKPYQA@-a=5lKZov4@5QisgIc7xxc6pkhP7cio3CMgm35CCIcI9p1r0D0x1Ga@6-Z2n7BNvjRaCKxexoojWrgxSnSGav-lK2L=-PAQsm+nWtAGORUyuEs746@zkUXfjaQ77g+ygzhSp9+tkNQyopO30hMluLUCw03=OmwwipReTTdK71g2q-tfwi2zfdjuxV7GFM2+qQbjSoUwfNHQG0EIaROpqNwk2BgAKRVZt86VX+v2-iD7DEnonj73InxVuliWaespWU69+NSj6qhZhbKJsT@pHJTcsxwsrzV8p02noHcD6PwHsNKWo41ugzcBZxRb=9+PxOeO0jS6sF-p@6Td==8a4slgdhvZgzOvGCt5A4MrW3VFOP5dz160jwVBJ@wuREqaqupZALt4bsh2cxgfohV@rJS1VDXOTbiF44PMgPSFFNJYLXDizRMBmMpuNVfq6iHwFhYbUhAi3X3tY9cltt5qQ7s+baTSzN9953YRpSBuQaVSQt5Mv8dO6odEJ7hJCtQ6BjZmkdEAw4XBfU98c=OTOFJyd57eeRER52EpFH6qFGiIfGcr@l61jEu7lgmSCT-EH+pegEu3pUMbDAA1pTybf1waUbYebMnT+9uRlT@1P-0t=rrYPuRaFWROzsp9cLugtElTpXBKondk8wl2LhQR6ug=jSX-2WSW@diSCpW7zuSI@QwLN4FpD9XBiZn@UWDU-=tZwGovWoqHSLqCgkNc8f+HIs@URmYE-DLfO3Pm-EiZq9ZXyxDB8JYaLDxyzs03tu=1vw54Nl8EA2YfD8NYInyyp5QdtqcfqJLbmiOPKk8iRZbV655oFDeYZ8nYnw=vo7iXKdh+D4TLHiEzCrI0J9rhFbjKnjPTT+JhGMHbQHPJXe4ecRmem+-JAKP8n9VpC=2FwU=0SkgMAL1AANQ8U+3C@0O=By=f-ac1+lHowDLI73kfWSSUBjsfvAZoduG6fXN9f6f2iYJPcnNVMgUITvGpF1KZ0IVsZha1Oc65aSD4BPLgTXj=sskczT1Ld9O1MCylz-8M1eajGbzYx+84jtcDDnyWooaC-ELTwX6tZ@Wprk=hQbEpLwKI4kBP4G67Omk-GruR@0sCp2U-0UO1LnzCLL5JBsBF3OsJ2b-LqiYqunqSeWb6mWVo5lv@l2=+KPNfyMvI2qozdCbnbRmG3MkHeGOStYkXq0uK=xjT72456AykNRShMpj+d=jpe1Uej1KtdIc+HkF442NC@lWMmRg1rnwAvGz9GiTZvwGzybF998m5xsEX1fELPIIC4aw7mpCrmQOG45089uDK-WFhE09o7PPfWeZj0L2Cz7YrsRg-9Wea8iLKkH+ZjViT94cfa7hB+lcrIMA8zQnszj=qRbzPvuQx1ZZi--bGm8XfrFDKq+Cl=pm@r3r+yvN9kiEtK5VvZwZDNT1JeGlX8XwI3sJzVNi3F=GMxUSOTDPeXs1qv8poXIPVtdd@v5w4u=xAhVMr-nFm+uXBtmhaun1JEx3EVq8C1=@0+JjFZC5V0vIaSWKN62M7lO8cqJym@hyqvfoC@0MisBbr08zqisxFK5UWw2LYUizPJL8QS=WoVyjM9WuMLmNnbGB-Q6aCqSj0v5payTXwqy=1W6n-NlIEn3CtsV+KAQGlav7hw4CTCS6qvSKLT8@FHVsPSob1Eoblsn9OYNd8oov9Bf0NQM54Ymy@g1RozK4nSSdbJ-X8vk7ND-fQYCU3uVTj=o29TVLWHH4P-lMOqbxp9PS7++xvRISNeo-cCYH1PX0kq@40XKX3L04uK3IvH7cI32=+Qwv7uiG3CHpZWqg+OKrOPDsnmtUJA4gYXhduLQxV0keTmjK8Xv60WfF@BRXIIETwTMUeDmdSb3RIv+KSoHTOm6E8kZGofZgW69RpvpclxLjQrQkrZ+9Y6H3OzkrX@ujs7Zaq7P3aM0sXtjJGFe6Svr+=-Gd55jd==6pP3UYCwSHLz3@ALrwQOC+nVDyVm6KcHt7W=DrwAMBrUQ7BTEJW8d+CkW4J164oHpOOD5HEX28aQVmyZFpKwepb0kzgAh4qrt9sA9mi@LMCU2ZhPEc=C-naDtgA-YBX8V4vZU=CXJHZF8-Ag9+rjX8cQ2ykGKX57vACvf8GFs5KmicoRFcreXkYRYFGGeJV5rWE2hze9dtQDeNMaH=HJUfZl-2luinLdbVuddFn5YV14fbtEnU1ygSmh-Lu+Bf=7e-VipFeA+X6SlR82JGdok18cd5UmNjwiB=gGJe17Vrq2IEVPTVcpeRBVNm@30kcOx5wElqWrJNjXgzbQAgBJAtNex@=@UDnscFKv3VBLEZadFyWZ-7GvuRKJQqExFO9G0jyljqEry8HaIHQePZU3aMlAg6RzsjKwESwMaq4kmndF3R6TsRr=a6dA9QAiuvNBWe9ngQEtm=1IufJmh2lfS1YxfOYuw0xzRWF2FZaOBM3b9Y2T0zIYoAdZg-+DQrW1RC-roa91kIjRImxhnsRkuBBLfUoHgeJ9FuhgwcDLJt'

def checksum_xD (f):
    code = ''
    while f:
        code += CHECKSUM_ALPHABET[f % len(CHECKSUM_ALPHABET)]
        f //= len(CHECKSUM_ALPHABET)
    code += CHECKSUM_ALPHABET[0] * (44 - len(code))
    assert len(code) == 44
    return code

# any(os.system(f'mv -vn -- {f} {new}') for f in os.listdir('.') if len(f) == 128 and len(new := checksum_xD(int(f, 16))) >= 40)

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

for cmd, start in (
    ('ffmpeg    -version', 'ffmpeg'),
    ('operon   --version', 'operon'),
    ('opusenc  --version', 'opusenc'),
    ('opusdec  --version', 'opusdec'),
    ('flac     --version', 'flac'),
    ('metaflac --version', 'metaflac'),
    ('soxi',               'soxi'),
    ):
    with os.popen(cmd) as fd:
        assert fd.read(65536).startswith(start), (cmd)

# WHERE TO SAVE THE CONVERTED FILES
GOOD_DIR = '/mnt/sda2/CONVERTED'

# HOW MANY PROCESSES TO RUN SIMULTANEOUSLY
CPUS_MAX = 16

PID = os.getpid()

RANDOMFD = os.open('/dev/urandom', os.O_RDONLY)

TNAME = f'xmzk-conversor-{PID}'

CPUS = int(1.5 * open('/proc/cpuinfo').read().count('processor\t:'))

# LIMIT AS REQUESTED
if CPUS > CPUS_MAX:
    CPUS = CPUS_MAX

print('CPUS MAX:', CPUS_MAX)
print('CPUS USE:', CPUS)
print('TNAME:', TNAME)
print('DIRECTORY:', GOOD_DIR)

assert 1 <= PID <= 0xFFFFFFFF
assert 0 <= RANDOMFD <= 10
assert 5 <= len(TNAME)
assert 1 <= CPUS <= 512

if not stat.S_ISDIR(os.stat(f'{GOOD_DIR}/').st_mode):
    print('ERROR: OUTPUT DIRECTORY IS NOT A DIRECTORY')
    exit(1)

if os.getcwd().strip('/').startswith(GOOD_DIR.strip('/')):
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
                    i = os.open(f, os.O_RDONLY)
                    s = os.stat(i).st_size
                    if s < 65536:
                        os.close(i)
                        continue
                    m = mmap.mmap(i, s, mmap.MAP_SHARED | mmap.MAP_POPULATE, mmap.PROT_READ, 0, 0)
                    m = m.close()
                    os.close(i)
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

# THREAD
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

    i = o = imap = ibuff = fp = fpStream = cmd = checksum = None

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
        continue

    #
    try:
        with open(original, 'rb') as xxx:
            with os.popen(f'ffprobe -v quiet -print_format json -show_format -show_streams -- /proc/{os.getpid()}/fd/{xxx.fileno()}') as fd:
                fp = json.loads(fd.read(4*1024*1024))

        fpStream, = (s for s in fp['streams'] if s['codec_type'] == 'audio') # NOTE: ONLY SUPPORT FILES WITH 1 AUDIO STREAM

        ( # FORMAT
            format, formatName, ORIGINAL_TAGS,
            # STREAM
            codec, codecName, bitsFMT, hz, channels, channelsLayout, bits, bitsRaw, seconds, XBITRATE, ORIGINAL_TAGS2
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

    # DO ARQUIVO QUE TEMOS AGORA
    channels    = int       (channels)
    hz          = int       (hz)
    bitsFMT     = str.upper (bitsFMT)
    format      = str.upper (format)
    formatName  = str.upper (formatName)
    codec       = str.upper (codec)
    codecName   = str.upper (codecName)

    bits           = (0   if bits           is None else int       (bits))
    bitsRaw        = (0   if bitsRaw        is None else int       (bitsRaw))
    channelsLayout = ('-' if channelsLayout is None else str.upper (channelsLayout))
    seconds        = (0   if seconds        is None else float     (seconds))

    # VERIFY
    if not (bits in (0, 8, 16, 24, 32)):
        print(f'[{tid}] {original}: ERROR: BAD BITS: {bits}')
        continue

    if not (bitsRaw in (0, 8, 16, 24, 32)):
        print(f'[{tid}] {original}: ERROR: BAD BITS RAW: {bitsRaw}')
        continue

    if not (1 <= channels <= 8):
        print(f'[{tid}] {original}: ERROR: BAD CHANNELS: {channels}')
        continue

    if not (bitsFMT in ('S16', 'S16P', 'S32', 'S32P', 'FLT', 'FLTP')):
        print(f'[{tid}] {original}: ERROR: BAD SAMPLE FMT: {bitsFMT}')
        continue

    if not (20 <= seconds <= 7*24*60*60):
        print(f'[{tid}] {original}: WARNING: BAD DURATION: {seconds}')

    if not (8000 <= hz <= 4*192000):
        print(f'[{tid}] {original}: ERROR: BAD SAMPLE RATE: {hz}')
        continue

    assert codec and codecName and format and formatName

    # A PRINCIPIO, USA ELE MESMO
    XPATH, XID, XTIME, XSIZE = original, mhash(), int(time.time()), originalSize
    XFORMAT, XFORMAT_NAME, XCODEC, XCODEC_NAME, XHZ, XCHANNELS, XDURATION, XBITS_FMT = format, formatName, codec, codecName, hz, channels, seconds, bitsFMT
    XCHANNELS_LAYOUT, XBITS, XBITS_RAW = channelsLayout, bits, bitsRaw

    #
    for t in tags.values():
        t.clear()

    convert = (not (original.endswith(('.opus',)) and original.startswith('/x/')))

    for T in (ORIGINAL_TAGS, ORIGINAL_TAGS2):

        if not T:
            continue

        # POIS NAO QUEREMOS COLOCAR ISSO EM UPPER CASE
        XYOUTUBE = T.pop('YOUTUBE', XYOUTUBE)
        XYOUTUBE = T.pop('youtube', XYOUTUBE)

        #
        T = { '_'.join(k[:80].replace('_', ' ').replace('-', ' ').split()).upper().replace('XMZK_TIME', 'CONVERSION_TIME').replace('XMZK_', 'ORIGINAL_'): ' '.join(v.split())[:300].rstrip().upper()
            for k, v in T.items()
                if k and v
        }

        #
        if any(map(T.__contains__, ('CONVERSION_TIME', 'ORIGINAL_BITS', 'XID', 'XPATH', 'XTIME', 'ORIGINAL_FILEPATH', 'ORIGINAL_PATH'))): # , 'ORIGINAL_FILENAME'

            #
            convert = {
                'FLAC': True,
                'OPUS': False,
                # 'VORBIS': True,
            } [XCODEC]

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
            XHZ              = T.pop('ORIGINAL_SAMPLERATE',       XHZ)
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

            if XDURATION is None:
                assert XCODEC is XCODEC_NAME is XFORMAT is XFORMAT_NAME is None
                assert XBITS_FMT is XBITS_RAW is None
                XCODEC = XCODEC_NAME = XFORMAT = XFORMAT_NAME = '?'
                XDURATION = T.pop('ORIGINAL_SAMPLES', None)
                if XDURATION is not None:
                    XDURATION = int(float(XDURATION)/int(XHZ))
                XBITS_FMT = '?'

            if XBITS_FMT is XBITS_RAW is None:
                pass
            elif XBITS_FMT is None:
                assert XBITS_RAW is None
                XBITS_FMT, XBITS, XBITS_RAW = XBITS.split('|')

            if XFORMAT and XFORMAT_NAME is None:
                XFORMAT, XFORMAT_NAME = XFORMAT.split('|', 1)

            if XCODEC and XCODEC_NAME is None:
                XCODEC, XCODEC_NAME = XCODEC.split('|', 1)

            if XFORMAT is None:
                XFORMAT = ('FLAC',)[('RAW FLAC',).index(XFORMAT_NAME)]

            if XCODEC is None:
                XCODEC = ('FLAC',)[(('FLAC', 'FLAC (FREE LOSSLESS AUDIO CODEC)'),).index((XFORMAT, XCODEC_NAME))]

            if XCHANNELS and '|' in XCHANNELS and XCHANNELS_LAYOUT is None:
                XCHANNELS_LAYOUT, XCHANNELS = XCHANNELS.split('|', 1)

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
    XHZ              = (0   if XHZ              is None else int       (XHZ))
    XTIME            = (0   if XTIME            is None else int       (XTIME))
    XCHANNELS        = (0   if XCHANNELS        is None else int       (XCHANNELS))
    XBITS            = (0   if XBITS            is None else int       (XBITS))
    XBITS_RAW        = (0   if XBITS_RAW        is None else int       (XBITS_RAW))
    XBITS_FMT        = ('?' if XBITS_FMT        is None else str.upper (XBITS_FMT))
    XCHANNELS_LAYOUT = ('-' if XCHANNELS_LAYOUT is None else str.upper (XCHANNELS_LAYOUT))
    XPATH            = ('?' if XPATH            is None else str.upper (XPATH))
    XCODEC           = ('?' if XCODEC           is None else str.upper (XCODEC))
    XCODEC_NAME      = ('?' if XCODEC_NAME      is None else str.upper (XCODEC_NAME))
    XFORMAT          = ('?' if XFORMAT          is None else str.upper (XFORMAT))
    XFORMAT_NAME     = ('?' if XFORMAT_NAME     is None else str.upper (XFORMAT_NAME))
    XDURATION        = (0   if XDURATION        is None else float     (XDURATION))

    # VERIFY
    assert XCHANNELS == 0 or 1 <= XCHANNELS <= 8
    assert XBITS in (0, 8, 16, 24, 32)
    assert XBITS_RAW in (0, 8, 16, 24, 32)
    assert XBITS_FMT in (None, '?', 'S16', 'S16P', 'S32', 'S32P', 'FLT', 'FLTP')
    assert XFORMAT and XFORMAT_NAME and XCODEC and XCODEC_NAME
    #assert XDURATION == 0 or 1 <= XDURATION <= 7*24*60*60, (XDURATION, original, XPATH)
    assert XHZ == 0 or 8000 <= XHZ <= 4*192000

    #
    for f in (tmpRAM, tmpDISK):
        try:
            os.unlink(f)
        except FileNotFoundError:
            pass
    #XYOUTUBE=HTTPS://YOUTU.BE/SO_VUN6OUH0
    if XYOUTUBE is not None:
        if 'youtu.be' in XYOUTUBE:
            XYOUTUBE = XYOUTUBE.rsplit('/', 1)[1].split('?')[0]
        elif '/watch?v=' in XYOUTUBE:
            XYOUTUBE = XYOUTUBE.split('=')[1]
        # https://www.youtube.com/watch?v=4LHYCXaI_CI
        # https://youtu.be/4LHYCXaI_CI?
    elif re.match(r'^.*youtube.*\[[0-9a-z_-]{5,16}\][.](m4a|opus|ogg|mp4|webm)$', original.lower()):
        XYOUTUBE, = re.findall(r'^.*\[([0-9A-Za-z_-]{5,})\][.].*$', original)
    elif re.match(r'^.*youtube.*\[[0-9a-z_-]{5,16}\][.](m4a|opus|ogg|mp4|webm)$', XPATH.lower()):
        XYOUTUBE, = re.findall(r'^.*\[([0-9A-Za-z_-]{5,})\][.].*$', XPATH)

    assert XYOUTUBE is None or re.match(r'^[0-9A-Za-z_-]{5,16}$', XYOUTUBE), (XYOUTUBE, original)

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
        convert = {
            (1, 'OGG', 'OPUS'): False,
            (2, 'OGG', 'OPUS'): False,
            (1, 'MOV,MP4,M4A,3GP,3G2,MJ2', 'AAC'): True,
            (2, 'MOV,MP4,M4A,3GP,3G2,MJ2', 'AAC'): True,
        } [(channels, XFORMAT, XCODEC)]

    # CONVERSION
    if convert:
        if mono := (channels == 1 or not any( ('BINAURAL' in w) for W in ((original.upper(), XPATH.upper()), tags['XARTIST'], tags['XALBUM'], tags['XTITLE'], tags['XFILENAME']) for w in W)):
            cmd.extend(('-ac', '1'))
        # if hz != 48000:
            # aresample=48000:
            # :dither_method=none
            # :dither_method=triangular
            # :cutoff=0.990
        cmd.extend(('-af', 'aresample=48000:resampler=soxr:precision=33:out_sample_rate=48000:osr=48000:osf=flt:out_sample_fmt=flt'))
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

    #
    with os.popen(f'ffmpeg -hide_banner -loglevel error -i {tmpRAM} -sample_fmt s32 -c:a pcm_s32le -f hash -hash sha512 -') as cmd:
        checksum = cmd.read(1024)

    if len(checksum) != len('SHA512=ca48f434aa3956330d97f3d3f9681f0ec842cbd4ce4bde7be981799b238e0b1bdc9a35e0f807a88f926c4250ac52899489273301dc1ec72513cd9ab38c03ab7e\n'):
        print(f'[{tid}] {original}: ERROR: BAD CHECKSUM.')
        continue

    checksum = checksum_xD(int(checksum[len('SHA512='):-1], 16))
    assert len(checksum) == 44

    #
    new = f'{GOOD_DIR}/{checksum}'

    try:
        os.stat(new)
    except FileNotFoundError:
        pass
    else:
        print(f'[{tid}] ~~~ {original}: DUPLICATE')
        # DELETE THE ORIGINAL
        try:
                os.unlink(original)
        except :
                pass
        continue

    # NOW COPY FROM TEMP
    o = os.open(tmpDISK, os.O_WRONLY | os.O_DIRECT | os.O_SYNC | os.O_CREAT | os.O_EXCL, 0o644)
    i = os.open(tmpRAM, os.O_RDWR | os.O_DIRECT)

    # PROTECT AGAINST FILE DESCRIPTORS LEAKING
    assert 0 <= i <= 10
    assert 0 <= o <= 10

    newSize = os.fstat(i).st_size

    if not (256*1024 <= newSize <= 8*1024*1024*1024):
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
    try:
        os.unlink(original)
    except BaseException as e:
        assert e.errno == 30 # Read-only file system

print(f'[{tid}] EXITING')

exit(0)
