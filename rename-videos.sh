#!/bin/bash

set -e

for X in "${@}" ; do

    CODE=$(grep -E --only-matching "\[[^[]*$" <<< "${X}" | awk -F [ '{print $2}' | awk -F ] '{print $1}')

    if [[ ! -n ${CODE} ]] ; then
        continue
    fi

    URL=https://youtu.be/${CODE}

    TITLE=$(awk -F '[' '{print $1}' <<< "${X}")

    if ! ffmpeg \
        -i "${X}" \
        -c:a copy \
        -c:v copy \
        -metadata title="${TITLE}" \
        -metadata description=${URL} \
        -metadata url=${URL} \
        $(date +%s)${RANDOM}${RANDOM}${RANDOM}$$.mkv ; then
        continue
    fi

    rm -f -v -- "${X}"

done
