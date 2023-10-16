#!/bin/bash

set -u
set -e

WIDTH=2560
HEIGHT=1440

#WIDTH=1920
#HEIGHT=1080

ORIGINAL=${1}
BITS=32
SAMPLERATE=$(soxi -r ${ORIGINAL})

NAME=${ORIGINAL}
NAME=${NAME/.opus/}
NAME=${NAME/.mp3/}
NAME=${NAME/.flac/}
NAME=${NAME/.wave/}
NAME=${NAME/.ogg/}
NAME=${NAME/.wv/}
NAME=${NAME/.aac/}
NAME=${NAME/.m4a/}
NAME=${NAME/.mp4/}

rm -f -- ${NAME}.wav
rm -f -- ${NAME}.raw
rm -f -- ${NAME}-*.raw
rm -f -- ${NAME}-*.wav
rm -f -- ${NAME}-*.flac
rm -f -- ${NAME}-*.opus
rm -f -- ${NAME}-*.wv
rm -f -- ${NAME}.*.png
rm -f -- ${NAME}-*.*.png
rm -f -- a.out

gcc -std=gnu11 \
    -Wfatal-errors \
    -Wall \
    -Wextra \
    -Wno-unused-function \
    -Wno-unused-variable \
    -Wno-unused-parameter \
    -fstrict-aliasing \
    -O2 -march=native \
    resampler.c

# UM PARA CADA CPU
for X in $(seq 4) ; do
    sleep 1 &
done

# DECODIFICA DE SEU FORMATO ORIGINAL, EM WAVE (STEREO ETC)
case ${ORIGINAL} in
    *.opus) opusdec ${ORIGINAL} ${NAME}.wav ;;
    *.flac) flac --decode ${ORIGINAL} -o ${NAME}.wav ;;
    *.wv) wvunpack ${ORIGINAL} -o ${NAME}.wav ;;
    *) ffmpeg -hide_banner -loglevel error -i ${ORIGINAL} -f wav -c:a pcm_s32le ${NAME}.wav ;;
esac

H=24

# TRANSFORMA ESTE WAVE EM MONO, E USA O RAW A PARTIR DELE
ffmpeg -hide_banner -loglevel error -i ${NAME}.wav -f wav -c:a pcm_s${BITS}le -ac 1 ${NAME}-2.wav ; mv -- ${NAME}-2.wav ${NAME}.wav
ffmpeg -hide_banner -loglevel error -i ${NAME}.wav -f s${BITS}le ${NAME}.raw

wait -n || : ; sox ${NAME}.wav -n spectrogram -x ${WIDTH} -y ${HEIGHT} -o ${NAME}.wav.png &

FS=(0 1 2 3)

ARGS_0=(1 2 3 4)
ARGS_1=(1 2)
ARGS_2=(x)
ARGS_3=(x)

BITRATES=(
    #70
    96
    #110
    128
    #192
    #200
    256
)

for F in ${FS[*]} ; do

    eval "ARGS=(\${ARGS_${F}[@]})"

    for ARG in ${ARGS[*]} ; do

        THIS=${NAME}-${F}-${ARG}

        echo ${THIS}

        SRX=$(./a.out ${F} ${ARG} ${SAMPLERATE} ${NAME}.raw ${THIS}.raw)

        ffmpeg -hide_banner -loglevel error -f s32le -ar ${SRX} -ac 1 -i ${THIS}.raw -f wav -c:a pcm_s${H}le ${THIS}.wav

        wait -n || : ; sox ${THIS}.wav -n spectrogram -x ${WIDTH} -y ${HEIGHT} -o ${THIS}.wav.png &

        #flac --best ${THIS}.wav ${THIS}.flac

        wait -n || : ; flac \
               ${THIS}.wav \
            -o ${THIS}-WAV${H}.flac \
            --silent \
            --best &

        wait -n || : ; flac \
               ${THIS}.raw \
            -o ${THIS}-RAW32.flac \
            --silent \
            --best \
            --force-raw-format \
            --sample-rate=${SRX} \
            --endian=little \
            --sign=signed \
            --bps=32 \
            --channels=1 &

        for BITRATE in ${BITRATES[*]} ; do
            wait -n || : ; opusenc ${THIS}.wav    ${THIS}-${BITRATE}.opus --quiet --music --vbr --comp 10 --bitrate ${BITRATE} &
            wait -n || : ; wavpack ${THIS}.raw -o ${THIS}-${BITRATE}H.wv --raw-pcm=${SRX},32s,1,le -q -hh -x2 &
            wait -n || : ; wavpack ${THIS}.raw -o ${THIS}-${BITRATE}L.wv --raw-pcm=${SRX},32s,1,le -q -b${BITRATE} -x2 &
        done

        sleep 3
        rm -f -v ${THIS}.raw

        #wait || :

    done

done

wait || :

file -- ${ORIGINAL} ${NAME}*.{flac,opus,wv,wav} || :

echo

(du --bytes -- ${ORIGINAL} ${NAME}*.{flac,opus,wv,wav} || :) | column --table | sort -n

exit 0

( set -x



    : opusenc ${NAME}.raw ${NAME}-${BITRATE}.opus \
        --music --vbr --comp 10 --bitrate ${BITRATE} \
        --raw --raw-bits ${BITS} --raw-rate ${SAMPLERATE} --raw-chan ${CHANNELS} --raw-endianness 0

    opusenc ${NAME}.wav ${NAME}-${BITRATE}.opus \
        --music --vbr --comp 10 --bitrate ${BITRATE}
)


ffplay -f s32le -ar   48000 -ac 1 -i MONO.raw
ffplay -f s32le -ar $[48000/2] -ac 1 -i SUPER.wav
ffplay -i SUPER-180.opus

(
sox -M \
    -c 1 flyleaf.wav \
    -c 1 flyleaf-0-1.wav \
    test.wav
)

(
gst-launch-1.0 filesrc location="electronic-12000.wav" name=src \
    ! decodebin name=decoder \
    ! audiorate \
    ! audioconvert \
    ! audioresample quality=10 \
    ! audio/x-raw,channels=1,rate=128000 \
    ! audioconvert \
    ! audio/x-raw,format=S32LE \
    ! wavenc \
    ! filesink location="teste.wav"
)

#!/bin/bash

TMPNAME=${$}${RANDOM}${RANDOM}${RANDOM}

TMP_RAW=/tmp/${TMPNAME}.raw
TMP_OGG=/tmp/${TMPNAME}.ogg

for F in ${@} ; do

    OUT=${F}
    OUT=${OUT/.mp3/}
    OUT=${OUT/.aac/}
    OUT=${OUT/.mp4/}
    OUT=${OUT/.flac/}
    OUT=${OUT}.ogg
    OUT_TMP=${OUT}.tmp

    SAMPLE_RATE=$(soxi -r "${F}")
    BITS=$(soxi -p "${F}")

    echo
    echo ${F}
    echo ${TMP_RAW}
    echo ${SAMPLE_RATE} / ${BITS}
    echo $(soxi -d "${F}") - $(du -h "${F}")
    echo

	#  -hide_banner -loglevel quiet
    if ffmpeg -i ${F} -ac 1 -f s${BITS}le ${TMP_RAW} ; then

        if oggenc --quiet ${TMP_RAW} -o ${TMP_OGG} --utf8 --raw --raw-bits=${BITS} --raw-chan=1 --raw-rate=${SAMPLE_RATE} --raw-endianness 0 --quality 7 ; then

            mv -n -- ${TMP_OGG} ${OUT_TMP}
            if mv -n -- ${OUT_TMP} ${OUT} ; then
				du -h ${F} ${OUT}
                rm -f -- "${F}"
            fi
        fi

    fi

    rm -f -- ${TMP_RAW}
    rm -f -- ${TMP_OGG}
    rm -f -- ${OUT_TMP}

done

    #! audio/x-raw,rate=128000 \
                ! audioconvert \
