#!/bin/dash

if X=$(ffmpeg -hide_banner -loglevel error -i "${1}"  -c:a pcm_s32le  -f hash -hash sha512 -) ; then
#if X=$(fpcalc ${1}) ; then
    echo _ ${1} ${X}
fi
