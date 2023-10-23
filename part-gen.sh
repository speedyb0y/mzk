#!/bin/bash
#
# XMUZIK
# Create mount points and generate the /etc/fstab entries
#

set -e

for DISK in /dev/sd[a-z]{[0-9],[0-9][0-9],[0-9][0-9][0-9]} ; do
    if [ -b ${DISK} ] ; then
        if LABEL=$(dd status=none if=${DISK} skip=32808 iflag=skip_bytes bs=32 count=1 | grep -E '^MZK-[0-9A-Z]{28}$') ; then
            FOLDER=/mnt/music/${LABEL:4:8}
            mkdir -p ${FOLDER}
            chmod 0555 ${FOLDER}
            echo ${DISK} ${FOLDER} iso9660 ro,noexec,nodev,norock,nojoliet,check=strict,uid=0,gid=0,map=off,block=2048,dmode=0555,mode=0444 0 0
        fi
    fi
done | column --table
