#!/bin/bash

#
mkdir -p /mnt/MZK

for DEVICE in /dev/sd??* ; do
    LABEL=/mnt/$(dd status=none if=${DEVICE} skip=32808 iflag=skip_bytes bs=32 count=1 | tr -c -d [[:print:]] | tr - /)
    case ${LABEL} in
        /mnt/MZK/????????????????????????????)
            mkdir -p ${LABEL}
            echo ${DEVICE} ${LABEL} iso9660 noauto,ro,noexec,nodev,norock,nojoliet,check=strict,uid=0,gid=0,mode=0444,map=off,block=2048 0 0
        ;;
    esac
done

