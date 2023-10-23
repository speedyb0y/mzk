#!/bin/bash
#

#
( set -e

    mount /MZK /MZK -t tmpfs -o rw,noexec,nodev,nosuid

    cd /MZK

    for DEVICE in /dev/sd[a-z]{[0-9],[0-9][0-9],[0-9][0-9][0-9]} ; do
        if [ -b ${DEVICE} ] ; then
            if LABEL=$(dd status=none if=${DEVICE} skip=32808 iflag=skip_bytes bs=32 count=1 | grep --text -E '^MZK-[0-9A-Za-z]{8,32}$') ; then
                FOLDER=${LABEL/MZK-/.}
                mkdir -p ${FOLDER}
                mount ${DEVICE} ${FOLDER} -t iso9660 -o ro,noexec,nodev,norock,nojoliet,check=strict,uid=0,gid=0,dmode=0555,mode=0444,map=off,block=2048
                ln -sfn ${FOLDER}/* .
            fi
        fi
    done
)
