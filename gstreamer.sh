#!/bin/bash

set -e
set -u
set -x

saida=${HOME}/teste2.opus

# audiotestsrc wave=sine num-buffers=1000

#giosrc location="file:///home/speedyb0y/%5B1997%5D%20%CE%95%CE%BD%CE%B1%CE%BB%CE%BB%CE%B1%CE%BA%CF%84%CE%B9%CE%BA%CE%BF%CE%AF%20Rock%20%CE%94%CF%81%CF%8C%CE%BC%CE%BF%CE%B9%20%5ByKzwGvz1HeQ%5D.m4a" name=src
    #! decodebin name=decoder
    #! audiorate
    #! audioconvert
    #! audioresample
    #! audio/x-raw,rate=128000
    #! audioconvert
    #! audioresample
    #! audio/x-raw,channels=1
    #! audioconvert
    #! opusenc bitrate=192000 bitrate-type=vbr bandwidth=auto
    #! oggmux
    #! giosink location="file:///home/speedyb0y/%5B1997%5D%20%CE%95%CE%BD%CE%B1%CE%BB%CE%BB%CE%B1%CE%BA%CF%84%CE%B9%CE%BA%CE%BF%CE%AF%20Rock%20%CE%94%CF%81%CF%8C%CE%BC%CE%BF%CE%B9%20%5ByKzwGvz1HeQ%5D.m4a~164104~SC~"

GST_AUDIO_DITHER_TPDF_HF=3
GST_AUDIO_NOISE_SHAPING_HIGH=4

GST_AUDIO_DITHER_TPDF_HF=GST_AUDIO_DITHER_TPDF_HF
GST_AUDIO_NOISE_SHAPING_HIGH=GST_AUDIO_NOISE_SHAPING_HIGH

DITHERING=${GST_AUDIO_DITHER_TPDF_HF}
NOISE_SHAPING=${GST_AUDIO_NOISE_SHAPING_HIGH}
DITHERING_THRESHOULD=20

    #dithering-threshold
# TODO: opusenc max-payload-size
# TODO: resample-method
gst-launch-1.0 filesrc location="${1}" \
    ! decodebin \
    ! audioconvert \
    ! audio/x-raw,format=F32LE \
    ! audioresample quality=10 \
        resample-method=kaiser \
        sinc-filter-mode=full \
        sinc-filter-interpolation=cubic \
        sinc-filter-auto-threshold=$[128*1024*1024] \
    ! audio/x-raw,format=F32LE,rate=48000 \
    ! audioconvert \
    ! audio/x-raw,format=F32LE,channels=1 \
    ! audioconvert \
        dithering=${DITHERING} \
        dithering-threshold=${DITHERING_THRESHOULD} \
        noise-shaping=${NOISE_SHAPING} \
    ! opusenc \
        packet-loss-percentage=0 \
        dtx=false \
        inband-fec=false \
        audio-type=generic \
        bandwidth=fullband \
        complexity=10 \
        frame-size=20 \
        bitrate-type=vbr \
        bitrate=$[320*1024] \
    ! vorbistag \
    ! oggmux \
    ! filesink location=${saida}

 #gst-launch-1.0 -v uridecodebin uri=file:///path/to/audio.ogg ! audioconvert ! audio/x-raw, rate=8000 ! autoaudiosink
soxi ${saida}

: ffprobe ${saida}

opusinfo ${saida}

mpv ${saida}
#scope=global
#! taginject \ tags="url=XXXXXXXXXXXXXXXXXXXXX"
