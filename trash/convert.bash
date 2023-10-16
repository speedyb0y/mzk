#!/bin/bash

set -u

function sox_get_sample_rate() {

    soxi -r ${1}
}

function sox_get_format() {

    SOX=$(soxi -t ${1})
    SOX=${SOX^^}

    echo ${SOX}
}

function sox_get_encoding() {

    SOX=$(soxi -e ${1})
    SOX=${SOX^^}

    echo ${SOX}
}

function sox_get_channels() {

    soxi -c ${1}
}

function sox_get_bits() {

    soxi -b ${ORIG}
}

function sox_get_bits_estimated() {

    soxi -p ${ORIG}
}

function convert_WAVPACK () {

    wavpack -o ${OUT}.wv \
        -hh \
        -x1 \
        --raw-pcm=${SAMPLE_RATE},${BITS}s,1,le
        ${WAVE}

    return $?
}

function convert_FLAC_GST () {

    # mid-side-stereo=true
    #streamable-subset=false
            #blocksize=8192 \

    gst-launch-1.0 --quiet filesrc name=src location=${ORIG} \
        ! rawaudioparse use-sink-caps=false format=pcm pcm-format=s${BITS}le sample-rate=${SAMPLE_RATE} num-channels=1 interleaved=true \
        ! audioconvert \
        ! flacenc padding=0 quality=9 seekpoints=-15 \
        ! filesink location=${OUT}.flac

    return $?
}

function convert_FLAC () {

    gst-launch-1.0 --quiet filesrc name=src location=${ORIG} \
        ! decodebin name=decoder \
        ! audiorate \
        ! audioconvert \
        ! audioresample \
        ! audio/x-raw,channels=1 \
        ! audioconvert \
        ! flacenc padding=0 quality=9 seekpoints=-15 \
        ! filesink location=${OUT}.flac

    return $?
}

function convert_FLAC () {

   #Apodization functions
       #To improve LPC analysis, audio data is windowed .  The window can be selected with one or  more  -A  options.   Possible  functions  are:  bartlett,
       #bartlett_hann,  blackman,  blackman_harris_4term_92db,  connes,  flattop, gauss(STDDEV), hamming, hann, kaiser_bessel, nuttall, rectangle, triangle,
       #tukey(P), partial_tukey(n[/ov[/P]]), punchout_tukey(n[/ov[/P]]), subdivide_tukey(n[/P]) welch.
    if flac -o ${OUT}.flac \
        --blocksize=16384 \
        --no-padding \
        --no-replay-gain \
        --channels=1 \
        --endian=little \
        --bps=${BITS} \
        --sign=signed \
        --sample-rate=${SAMPLE_RATE} \
        --best ${WAVE} ; then
        return 0
    fi

    return 1
}

function convert_OPUS () {

    # frame-size=20
    # max-payload-size=4000

    gst-launch-1.0 --quiet filesrc name=src location=${ORIG} \
        ! decodebin name=decoder \
        ! audiorate \
        ! audioconvert \
        ! audioresample \
        ! audio/x-raw,channels=1 \
        ! audioconvert \
        ! opusenc \
            complexity=10 \
            audio-type=generic \
            bandwidth=fullband \
            bitrate-type=vbr \
            bitrate=450000 \
        ! oggmux \
        ! filesink location=${OUT}.opus

    return $?
}

function convert_OPUS_LOW () {

    # frame-size=20
    # max-payload-size=4000

    gst-launch-1.0 --quiet filesrc name=src location=${1} \
        ! decodebin name=decoder \
        ! audiorate \
        ! audioconvert \
        ! audioresample \
        ! audio/x-raw,channels=1 \
        ! audioconvert \
        ! opusenc \
            complexity=10 \
            audio-type=generic \
            bandwidth=fullband \
            bitrate-type=vbr \
            bitrate=120000 \
        ! oggmux \
        ! filesink location=${2}.opus

    return $?
}

function convert_OPUS_HIGH () {

    gst-launch-1.0 --quiet filesrc name=src location=${1} \
        ! decodebin name=decoder \
        ! audiorate \
        ! audioconvert \
        ! audioresample \
        ! audio/x-raw,channels=1 \
        ! audioconvert \
        ! opusenc \
            complexity=10 \
            audio-type=generic \
            bandwidth=fullband \
            bitrate-type=vbr \
            bitrate=600000 \
        ! oggmux \
        ! filesink location=${2}.opus

    return $?
}

WAVE=/tmp/$$-${RANDOM}-${RANDOM}.wav

(
	mkdir -p CONVERTED
	mkdir -p METADATA

    for ORIG in "${@}" ; do

        # SEM PATH
        # NOME CERTO
        if ! grep -q -E '^[0-9A-Za-z_,]{,8}[.][0-9A-Za-z]{1,}$' <<< "${ORIG}" ; then
            continue
        fi

        if [[ ! -f ${ORIG} ]] ; then
            continue
        fi

        OUT=(${ORIG/./ })
        OUT=CONVERTED/${OUT[0]}

        FORMAT=UNKNOWN

        MIME=
        ORIG_FFMPEG=
        ORIG_FORMAT=
        ORIG_ENCODING=
        SAMPLE_RATE=
        ORIG_SAMPLE_RATE2=
        CHANNELS=
        BITS=
        ORIG_BITS1=
        ORIG_BITS2=
        ORIG_BITS3=

        MIME=$(file --brief --mime-type ${ORIG})

        SAMPLE_RATE=$(ffprobe ${ORIG} 2>&1 | grep Stream | grep Audio: | grep -E --only-matching ', [0-9]{1,} Hz,' | awk '{print $2}')
              ORIG_BITS1=$(ffprobe ${ORIG} 2>&1 | grep Stream | grep Audio: | grep -E --only-matching ' [(][0-9]{1,} bit[)]' | awk -F '(' '{print $2}' | awk '{print $1}')

        if [[ $(ffprobe ${ORIG} 2>&1 | grep Stream | grep Audio: | wc --lines) != 1 ]] ; then
            echo "INVALID NUMBER OF AUDIO STREAMS - ${ORIG}"
            continue
        fi

        case "${MIME}:$(ffprobe ${ORIG} 2>&1 | grep Stream | grep Audio:)" in

            audio/aac:*Audio:?aac??HE-AACv2?,*)           ORIG_FFMPEG=AAC-HE-AACV2 ;;
            audio/x-hx-aac-adts:*Audio:?aac??HE-AACv2?,*) ORIG_FFMPEG=AAC-ADTS     ;;
            audio/x-wav:*Audio:?pcm_s16be?*/*,*)          ORIG_FFMPEG=WAVE-S16BE   ;;
            audio/x-wav:*Audio:?pcm_s16le?*/*,*)          ORIG_FFMPEG=WAVE-S16LE   ;;
            audio/x-wav:*Audio:?pcm_s24be?*/*,*)          ORIG_FFMPEG=WAVE-S24BE   ;;
            audio/x-wav:*Audio:?pcm_s24le?*/*,*)          ORIG_FFMPEG=WAVE-S24LE   ;;
            audio/x-wav:*Audio:?pcm_s32be?*/*,*)          ORIG_FFMPEG=WAVE-S32BE   ;;
            audio/x-wav:*Audio:?pcm_s32le?*/*,*)          ORIG_FFMPEG=WAVE-S32LE   ;;
            audio/x-wav:*Audio:?pcm_f32be?*/*,*)          ORIG_FFMPEG=WAVE-F32BE   ;;
            audio/x-wav:*Audio:?pcm_f32le?*/*,*)          ORIG_FFMPEG=WAVE-F32LE   ;;
            audio/x-aiff:*Audio:?pcm_s16le,*)             ORIG_FFMPEG=AIFF-S16LE   ;;
            audio/x-aiff:*Audio:?pcm_s16be,*)             ORIG_FFMPEG=AIFF-S16BE   ;;
            audio/x-aiff:*Audio:?pcm_s24le,*)             ORIG_FFMPEG=AIFF-S24LE   ;;
            audio/x-aiff:*Audio:?pcm_s24be,*)             ORIG_FFMPEG=AIFF-S24BE   ;;
            audio/x-aiff:*Audio:?pcm_s32le,*)             ORIG_FFMPEG=AIFF-S32LE   ;;
            audio/x-aiff:*Audio:?pcm_s32be,*)             ORIG_FFMPEG=AIFF-S32BE   ;;
            audio/x-ape:*Audio:?ape??APE??/*,*)           ORIG_FFMPEG=APE          ;;
            audio/alac:*Audio:?alac??alac?/*,*)           ORIG_FFMPEG=ALAC         ;;
            audio/x-m4a:*Audio:?alac??alac?/*,*)          ORIG_FFMPEG=ALAC         ;;
            audio/flac:*Audio:?flac,*)                    ORIG_FFMPEG=FLAC         ;;
            audio/mpeg:*Audio:?mp3,*)                     ORIG_FFMPEG=MP3          ;;
            audio/ogg:*Audio:?opus,*)                     ORIG_FFMPEG=OPUS         ;;

            *)
                echo ${ORIG} "${MIME}:$(ffprobe "${ORIG}" 2>&1 | grep Stream | grep Audio:)"
                continue
                ;;

        esac

        # CARREGA A INFORMACAO DO SOX
        case ${MIME}:${ORIG_FFMPEG} in

            audio/aac:AAC-HE-AACV2)       : ;;
            audio/x-hx-aac-adts:AAC-ADTS) : ;;
            audio/x-ape:APE)              : ;;
            audio/x-m4a:ALAC)             : ;;

            *)
                ORIG_SAMPLE_RATE2=$( sox_get_sample_rate    ${ORIG})
                ORIG_FORMAT=$(       sox_get_format         ${ORIG})
                ORIG_ENCODING=$(     sox_get_encoding       ${ORIG})
                CHANNELS=$(          sox_get_channels       ${ORIG})
                ORIG_BITS2=$(        sox_get_bits           ${ORIG})
                ORIG_BITS3=$(        sox_get_bits_estimated ${ORIG})
                ;;
        esac

        # LIMPA ELES
        [[ ${ORIG_BITS1} = 0 ]] && ORIG_BITS1=
        [[ ${ORIG_BITS2} = 0 ]] && ORIG_BITS2=
        [[ ${ORIG_BITS3} = 0 ]] && ORIG_BITS3=

        # USA UM DELES
        [[ ${BITS} ]] || BITS=${ORIG_BITS1}
        [[ ${BITS} ]] || BITS=${ORIG_BITS2}
        [[ ${BITS} ]] || BITS=${ORIG_BITS3}

        # CONFIRMA A CONSISTENCIA
        if [[ -n ${ORIG_BITS1} && ${BITS} != ${ORIG_BITS1} ]] ; then
            echo "${ORIG} - MISMATCH BITS 1 ${BITS} VS ${ORIG_BITS1}"
            continue
        fi

        if [[ -n ${ORIG_BITS2} && ${BITS} != ${ORIG_BITS2} ]] ; then
            echo "${ORIG} - MISMATCH BITS 2 ${BITS} VS ${ORIG_BITS2}"
            continue
        fi

        if [[ -n ${ORIG_BITS3} && ${BITS} != ${ORIG_BITS3} ]] ; then
            echo "${ORIG} - MISMATCH BITS 3 ${BITS} VS ${ORIG_BITS3}"
            continue
        fi

        if [[ -n ${ORIG_SAMPLE_RATE2} && ${SAMPLE_RATE} != ${ORIG_SAMPLE_RATE2} ]] ; then
            echo "${ORIG} - MISMATCH SAMPLE RATE 2 ${SAMPLE_RATE} VS ${ORIG_SAMPLE_RATE2}"
            continue
        fi

        case ${MIME}:${ORIG_FFMPEG}:${ORIG_FORMAT}:${ORIG_ENCODING}:${BITS}:${SAMPLE_RATE}:${CHANNELS} in

            # FLAC
            audio/flac:FLAC:FLAC:FLAC:16:44100:?)  FORMAT=OPUS_HIGH ;;
            audio/flac:FLAC:FLAC:FLAC:24:44100:?)  FORMAT=OPUS_HIGH ;;
            audio/flac:FLAC:FLAC:FLAC:16:48000:1)  continue         ;;
            audio/flac:FLAC:FLAC:FLAC:16:48000:?)  FORMAT=FLAC      ;;
            audio/flac:FLAC:FLAC:FLAC:24:48000:1)  continue         ;;
            audio/flac:FLAC:FLAC:FLAC:24:48000:?)  FORMAT=FLAC      ;;
            audio/flac:FLAC:FLAC:FLAC:16:88200:1)  continue         ;;
            audio/flac:FLAC:FLAC:FLAC:16:88200:?)  FORMAT=FLAC      ;;
            audio/flac:FLAC:FLAC:FLAC:24:88200:1)  continue         ;;
            audio/flac:FLAC:FLAC:FLAC:24:88200:?)  FORMAT=FLAC      ;;
            audio/flac:FLAC:FLAC:FLAC:16:96000:1)  continue         ;;
            audio/flac:FLAC:FLAC:FLAC:16:96000:?)  FORMAT=FLAC      ;;
            audio/flac:FLAC:FLAC:FLAC:24:96000:1)  continue         ;;
            audio/flac:FLAC:FLAC:FLAC:24:96000:?)  FORMAT=FLAC      ;;
            audio/flac:FLAC:FLAC:FLAC:16:176400:1) continue         ;;
            audio/flac:FLAC:FLAC:FLAC:16:176400:?) FORMAT=FLAC      ;;
            audio/flac:FLAC:FLAC:FLAC:24:176400:1) continue         ;;
            audio/flac:FLAC:FLAC:FLAC:24:176400:?) FORMAT=FLAC      ;;
            audio/flac:FLAC:FLAC:FLAC:16:192000:1) continue         ;;
            audio/flac:FLAC:FLAC:FLAC:16:192000:?) FORMAT=FLAC      ;;
            audio/flac:FLAC:FLAC:FLAC:24:192000:1) continue         ;;
            audio/flac:FLAC:FLAC:FLAC:24:192000:?) FORMAT=FLAC      ;;
            audio/flac:FLAC:FLAC:FLAC:*)           :                ;;

            # OGG VORBIS
            audio/ogg:VORBIS:VORBIS:16:22050:?)  FORMAT=OPUS_LOW  ;;
            audio/ogg:VORBIS:VORBIS:24:22050:?)  FORMAT=OPUS_LOW  ;;
            audio/ogg:VORBIS:VORBIS:16:32000:?)  FORMAT=OPUS_LOW  ;;
            audio/ogg:VORBIS:VORBIS:24:32000:?)  FORMAT=OPUS_LOW  ;;
            audio/ogg:VORBIS:VORBIS:16:44100:?)  FORMAT=OPUS      ;;
            audio/ogg:VORBIS:VORBIS:24:44100:?)  FORMAT=OPUS      ;;
            audio/ogg:VORBIS:VORBIS:16:48000:?)  FORMAT=OPUS_HIGH ;;
            audio/ogg:VORBIS:VORBIS:24:48000:?)  FORMAT=OPUS_HIGH ;;
            audio/ogg:VORBIS:VORBIS:16:96000:?)  FORMAT=OPUS_HIGH ;;
            audio/ogg:VORBIS:VORBIS:24:96000:?)  FORMAT=OPUS_HIGH ;;
            audio/ogg:VORBIS:VORBIS:16:192000:?) FORMAT=OPUS_HIGH ;;
            audio/ogg:VORBIS:VORBIS:24:192000:?) FORMAT=OPUS_HIGH ;;
            audio/ogg:VORBIS:VORBIS:*)           :                ;;

            # OGG OPUS
            audio/ogg:OPUS:OPUS:OPUS:16:48000:1) continue         ;;
            audio/ogg:OPUS:OPUS:OPUS:16:48000:?) FORMAT=OPUS_HIGH ;;
            audio/ogg:OPUS:OPUS:OPUS:24:48000:1) continue         ;;
            audio/ogg:OPUS:OPUS:OPUS:24:48000:?) FORMAT=OPUS_HIGH ;;
            audio/ogg:OPUS:OPUS:OPUS:*)           :                ;;

            # MP3
            audio/mpeg:MP3:MPEG?AUDIO??LAYER?I,?II?OR?III?:0:16:44100:?) FORMAT=OPUS_LOW ;;
            audio/mpeg:MP3:MPEG?AUDIO??LAYER?I,?II?OR?III?:0:16:48000:?) FORMAT=OPUS     ;;

            # WAVE
            audio/x-wav:WAVE-*:WAV:SIGNED?INTEGER?PCM:16:44100:?)  FORMAT=OPUS_HIGH ;;
            audio/x-wav:WAVE-*:WAV:SIGNED?INTEGER?PCM:24:44100:?)  FORMAT=OPUS_HIGH ;;
            audio/x-wav:WAVE-*:WAV:SIGNED?INTEGER?PCM:32:44100:?)  FORMAT=OPUS_HIGH ;;
            audio/x-wav:WAVE-*:WAV:SIGNED?INTEGER?PCM:16:48000:?)  FORMAT=FLAC      ;;
            audio/x-wav:WAVE-*:WAV:SIGNED?INTEGER?PCM:24:48000:?)  FORMAT=FLAC      ;;
            audio/x-wav:WAVE-*:WAV:SIGNED?INTEGER?PCM:32:48000:?)  FORMAT=FLAC      ;;
            audio/x-wav:WAVE-*:WAV:SIGNED?INTEGER?PCM:16:96000:?)  FORMAT=FLAC      ;;
            audio/x-wav:WAVE-*:WAV:SIGNED?INTEGER?PCM:24:96000:?)  FORMAT=FLAC      ;;
            audio/x-wav:WAVE-*:WAV:SIGNED?INTEGER?PCM:32:96000:?)  FORMAT=FLAC      ;;
            audio/x-wav:WAVE-*:WAV:SIGNED?INTEGER?PCM:16:176400:?) FORMAT=FLAC      ;;
            audio/x-wav:WAVE-*:WAV:SIGNED?INTEGER?PCM:24:176400:?) FORMAT=FLAC      ;;
            audio/x-wav:WAVE-*:WAV:SIGNED?INTEGER?PCM:32:176400:?) FORMAT=FLAC      ;;
            audio/x-wav:WAVE-*:WAV:SIGNED?INTEGER?PCM:16:192000:?) FORMAT=FLAC      ;;
            audio/x-wav:WAVE-*:WAV:SIGNED?INTEGER?PCM:24:192000:?) FORMAT=FLAC      ;;
            audio/x-wav:WAVE-*:WAV:SIGNED?INTEGER?PCM:32:192000:?) FORMAT=FLAC      ;;
            audio/x-wav:WAVE-*:::16:44100:)                        FORMAT=OPUS_HIGH ;;
            audio/x-wav:WAVE-*:::24:44100:)                        FORMAT=OPUS_HIGH ;;
            audio/x-wav:WAVE-*:::32:44100:)                        FORMAT=OPUS_HIGH ;;

            # AIFF
            audio/x-aiff:AIFF-*:AIFF:SIGNED?INTEGER?PCM:16:44100:?)  FORMAT=OPUS_HIGH ;;
            audio/x-aiff:AIFF-*:AIFF:SIGNED?INTEGER?PCM:24:44100:?)  FORMAT=OPUS_HIGH ;;
            audio/x-aiff:AIFF-*:AIFF:SIGNED?INTEGER?PCM:16:48000:?)  FORMAT=FLAC      ;;
            audio/x-aiff:AIFF-*:AIFF:SIGNED?INTEGER?PCM:24:48000:?)  FORMAT=FLAC      ;;
            audio/x-aiff:AIFF-*:AIFF:SIGNED?INTEGER?PCM:16:96000:?)  FORMAT=FLAC      ;;
            audio/x-aiff:AIFF-*:AIFF:SIGNED?INTEGER?PCM:24:96000:?)  FORMAT=FLAC      ;;
            audio/x-aiff:AIFF-*:AIFF:SIGNED?INTEGER?PCM:16:176400:?) FORMAT=FLAC      ;;
            audio/x-aiff:AIFF-*:AIFF:SIGNED?INTEGER?PCM:24:176400:?) FORMAT=FLAC      ;;
            audio/x-aiff:AIFF-*:AIFF:SIGNED?INTEGER?PCM:16:192000:?) FORMAT=FLAC      ;;
            audio/x-aiff:AIFF-*:AIFF:SIGNED?INTEGER?PCM:24:192000:?) FORMAT=FLAC      ;;

            # AAC
            audio/aac:AAC-HE-AACV2:::44100:) FORMAT=OPUS ;;
            audio/aac:AAC-HE-AACV2:::48000:) FORMAT=OPUS_HIGH ;;

            # APE
            audio/x-ape:APE::::44100:)  FORMAT=OPUS_HIGH   ;;
            audio/x-ape:APE::::48000:)  FORMAT=FLAC_FFMPEG ;;
            audio/x-ape:APE::::96000:)  FORMAT=FLAC_FFMPEG ;;
            audio/x-ape:APE::::176400:) FORMAT=FLAC_FFMPEG ;;
            audio/x-ape:APE::::192000:) FORMAT=FLAC_FFMPEG ;;

            # M4A ALAC
            audio/x-m4a:ALAC:::16:44100:)  FORMAT=OPUS_HIGH ;;
            audio/x-m4a:ALAC:::24:44100:)  FORMAT=OPUS_HIGH ;;
            audio/x-m4a:ALAC:::16:48000:)  FORMAT=FLAC ;;
            audio/x-m4a:ALAC:::24:48000:)  FORMAT=FLAC ;;
            audio/x-m4a:ALAC:::16:96000:)  FORMAT=FLAC ;;
            audio/x-m4a:ALAC:::24:96000:)  FORMAT=FLAC ;;
            audio/x-m4a:ALAC:::16:176400:) FORMAT=FLAC ;;
            audio/x-m4a:ALAC:::24:176400:) FORMAT=FLAC ;;
            audio/x-m4a:ALAC:::16:192000:) FORMAT=FLAC ;;
            audio/x-m4a:ALAC:::24:192000:) FORMAT=FLAC ;;

        esac

        echo ${ORIG} - ${OUT} = ${FORMAT} = ${MIME}:${ORIG_FFMPEG}:${ORIG_FORMAT}:${ORIG_ENCODING}:${BITS}:${SAMPLE_RATE}:${CHANNELS}



		# TODO: AGORA UNE OS CANAIS

		# --channels=${CHANNELS}
		#--bps=${BITS} 
		#--sample-rate=${SAMPLE_RATE}
		#243000845

		# DECODE TO WAVE
		if [[ ${FORMAT} = FLAC ]] ; then
			flac --decode -o ${WAVE} ${ORIG}
		elif false ; then
			: # TODO: GSTREAMER
		else
			fmpeg -i ${ORIG} -c:a pcm_s${BITS}le ${WAVE}
		fi

		if [[ $? != 0 ]] ; then
			echo FAILED
			continue
		fi

		# TODO: NOW TO MONO
		
read
		if true ; then # SAVE THE TAGS
		
			if [[ ${FORMAT} != "UNKNOWN" ]] ; then

				rm -f -- ${WAVE}

				if ffmpeg -i ${ORIG} -f s${BITS}le -ac 1 ${WAVE} ; then

					if convert_${FORMAT} ; then
						
						rm -f -v -- ${ORIG}
					fi
				fi
read
				rm -f -- ${WAVE}
			fi
        fi		

    done

)
