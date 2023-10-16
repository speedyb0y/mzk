#!/bin/bash
#
# Helper to generate /etc/fstab and corresponding mount points
#

#
mkdir -p /mnt/music

for DEVICE in /dev/sd?* ; do
    LABEL=$(dd status=none if=${DEVICE} skip=32808 iflag=skip_bytes bs=64 count=1 | grep --only-matching --text -E '^[0-9A-Za-z-]{1,28}-[0-9A-Za-z-]{4,32}')
    case ${LABEL} in
        *-*)
			FOLDER=/mnt/${LABEL/-//}
            mkdir -p ${FOLDER}
            echo /dev/disk/by-label/${LABEL} ${FOLDER} iso9660 noauto,ro,noexec,nodev,norock,nojoliet,check=strict,uid=0,gid=0,mode=0444,map=off,block=2048 0 0
        ;;
    esac
done
