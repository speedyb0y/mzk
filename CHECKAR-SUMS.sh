#!/bin/bash

set -u

sudo blockdev --setra $(((90*1024*1024)/512)) /dev/sda

sleep 1 &
sleep 1 &
sleep 1 &
sleep 1 &

for F in $(< ${1}) ; do
    if [ -e ${F} ] ; then
	    wait -n
	    /home/speedyb0y/FPCALC.sh ${F} &
    fi
done

wait
wait
wait
wait
