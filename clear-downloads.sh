#!/bin/dash

find /mnt/sda2/DOWNLOAD -type f \( \
    -iname '*.txt' -o \
    -iname '*.png' -o \
    -iname '*.jpg' -o \
    -iname '*.cue' -o \
    -iname '*.log' -o \
    -iname '*.m3u' -o \
    -iname '*.m3u8' -o \
    -iname '*.jpeg' -o \
    -iname '*.pdf' -o \
    -iname '*.html' -o \
    -iname '*.accurip' -o \
    -iname '*.torrent' -o \
    -iname '*.bmp' -o \
    -iname '*.gif' -o \
    -iname '*.md5' -o \
    -iname '*.ffp' -o \
    -iname '*.exe' -o \
    -iname '*.sfv' -o \
    -iname '*.pls' \
\) -exec rm -f -v '{}' \;

find /mnt/sda2/DOWNLOAD -type d -exec rmdir '{}' \;
find /mnt/sda2/DOWNLOAD -type d -exec rmdir '{}' \;
find /mnt/sda2/DOWNLOAD -type d -exec rmdir '{}' \;
find /mnt/sda2/DOWNLOAD -type d -exec rmdir '{}' \;
find /mnt/sda2/DOWNLOAD -type d -exec rmdir '{}' \;
