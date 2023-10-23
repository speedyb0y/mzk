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
    -iname '*.tif' -o \
    -iname '*.fpl' -o \
    -iname '*.doc' -o \
    -iname '*.docx' -o \
    -iname '*.rtf' -o \
    -iname '*.md5' -o \
    -iname '*.ffp' -o \
    -iname '*.exe' -o \
    -iname '*.sfv' -o \
    -iname '*.nfo' -o \
    -iname '*.nfofile' -o \
    -iname '*.url' -o \
    -iname 'Thumbs.db' -o \
    -iname 'album_info' -o \
    -iname '*.pls' \
\) -exec rm -f -v '{}' \;

find /mnt/sda2/DOWNLOAD -type d -exec rmdir '{}' \;
find /mnt/sda2/DOWNLOAD -type d -exec rmdir '{}' \;
find /mnt/sda2/DOWNLOAD -type d -exec rmdir '{}' \;
find /mnt/sda2/DOWNLOAD -type d -exec rmdir '{}' \;
find /mnt/sda2/DOWNLOAD -type d -exec rmdir '{}' \;

find /mnt/sda2/DOWNLOAD/ -type f | grep -v -E -i '[.](flac|ogg|mp3|aif|aiff|ape|wv|wav|m4a)$'

