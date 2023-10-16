#!/bin/bash
exit 0

mkfs.xfs -b size=4096 -s size=4096 -L MUZIK0 -l sectsize=4096,su=256k DEVICE

mount /dev/sdb /mnt/ -t xfs -o rw,noatime,logbufs=8,logbsize=256k

xfs_repair -n DEVICE
xfs_repair DEVICE

xfs_db -c frag -r DEVICE

xfs_fsr -v DEVICE
xfs_fsr -v FILE


ffmpeg
	-vn SEM VIDEO
