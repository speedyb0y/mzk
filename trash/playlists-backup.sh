#!/bin/bash

QUODLIBET_PLS_DIR=${HOME}/.config/quodlibet/playlists

PLS_DIR=/mnt/pls

cd ${PLS_DIR}

for PLS in $(ls "${QUODLIBET_PLS_DIR}" | sort) ; do

    PLS_NAME=${PLS/.xspf/}

    MY_PLS="${PLS_DIR}/${PLS_NAME}.m3u"

    (
        echo "#EXTM3U"
        echo "#EXTENC: UTF-8"
        echo "#PLAYLIST:${PLS_NAME}"

        for F in $(grep -E --only-matching 'location>[^<]{1,}' "${QUODLIBET_PLS_DIR}/${PLS}" | awk -F '>' '{print $2}' | grep -E --only-matching '[^/]*$' | sort) ; do

            TRACK_DURATION=120
            TRACK_ARTIST=ARTIST_NAME
            TRACK_TITLE=MUSIC_TITLE

            echo "#EXTINF:${TRACK_DURATION},${TRACK_ARTIST} – ${TRACK_TITLE}"
            echo "${F}"

        done

    ) > ${MY_PLS}

    PLS_SIZE=$(du --total -h $(grep -v -E '^#' ${MY_PLS}) | tail -n 1  | awk '{print $1}')
    PLS_COUNT=$(grep -v -E '^#' ${MY_PLS} | wc --lines)

    echo ${PLS_NAME} ${PLS_SIZE} ${PLS_COUNT} ${MY_PLS}

done | column --table --output-separator " "
