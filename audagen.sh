#!/bin/bash


#album
#album-artist
#comment
#musicbrainz-id
#publisher
#state
#track-number

echo title=Library

soxi /mnt/sda2/CONVERTED/* | tr -c '\n-~' '-' | sed -r -e "s/' \(opus\)$//g" | sed -r -e 's/[A-Z0-9]{8}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{12}([|]|$)//g' -e 's/[.][0-9]{1,}\s*$/000/g' \
    -e s/^Input\\s*File\\s*:\\s*\'/uri=/g     \
    -e s/^XID=/catalog-number=/g \
    -e s/^XALBUM=/album=/g       \
    -e s/^XARTIST=/artist=/g     \
    -e s/^XTITLE=/title=/g       \
    -e s/^XGENRE=/genre=/g       \
    -e s/^XCHANNELS=/channels=/g \
    -e s/^XDURATION=/length=/g   \
    -e s/^XCOMMENT=/comment=/g   \
    -e s/^XPATH=/description=/g  \
    -e s/^XYEAR=/year=/g         \
    -e s/^XCODEC=/codec=/g       \
    -e s/^XHZ=/quality=/g        \
    -e s/^XBITRATE=/bitrate=/g   \
    | grep -E ^[a-z]


#length=120909
#bitrate=250
