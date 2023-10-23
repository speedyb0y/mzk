#!/bin/bash
#
# Helper to generate /etc/fstab and corresponding mount points
#

#
( set -e

    mount /MZK /MZK -t tmpfs -o rw,noexec,nodev,nosuid

    cd /MZK
    
    for DEVICE in /dev/sd[a-z]{[0-9],[0-9][0-9],[0-9][0-9][0-9]} ; do
    	if [ -e ${DEVICE} ] ; then
    		LABEL=$(dd status=none if=${DEVICE} skip=32808 iflag=skip_bytes bs=64 count=1 | grep --only-matching --text -E '^[0-9A-Za-z-]{1,28}-[0-9A-Za-z-]{4,32}')
    		case ${LABEL} in
    			MZK-*)
    				FOLDER=${LABEL/MZK-/.}
    				echo mkdir -p ${FOLDER}
    				echo mount ${DEVICE} ${FOLDER} -t iso9660 -o ro,noexec,nodev,norock,nojoliet,check=strict,uid=0,gid=0,dmode=0555,mode=0444,map=off,block=2048
                    echo ln -sfn ${FOLDER}/XXX .
    			;;
    		esac
    	fi
    done
)
