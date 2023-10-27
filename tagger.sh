#!/bin/bash

set -e

if [ ! -e /proc/$$/fd/200 ] ; then

	wl-copy --clear

    if exec 200>> ~/MINHAS-TAGS.diff ; then
        wl-paste --no-newline --watch ${0}
    fi

elif FS=$(tr '\r' '\n' | grep --text -E '^(file:|)/{1,}mnt/music/' | awk -F / '{print $NF}' | awk -F . '{print $1}' | tr '\n' ' ') ; then

    if [ ${#FS} -gt 1 ] ; then

        CBG=\#FFFFFF
        CFG=\#000000

        if TAGS=$((cat tags ; grep -E '^\+' /proc/$$/fd/200 | awk '{print $2}') | sort | uniq | bemenu -P '>>>' -p TAG: --ignorecase --fn 'Mononoki Nerd Font Regular 35' --center --margin 200 --border 8 --bdr ${CFG}  --no-cursor --no-touch --no-overlap --fixed-height --no-exec --wrap --list 12 --tb ${CBG} --fb ${CBG} --nb ${CBG} --ab ${CBG} --tf ${CFG} --ff ${CFG} --nf ${CFG} --af ${CFG} --hb ${CFG} --hf ${CBG} | tr -d '!' | tr / . | tr _ - | tr [[:upper:]] [[:lower:]] | grep -E '^\s*[0-9a-z.-]{2,}\s*$') ; then
            echo + ${TAGS} ${FS} >&200
        fi
    fi
fi
