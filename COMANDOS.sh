#!/bin/bash
exit 0

find /mnt/new/ -type f -iname '*.flac' \
    -printf '\n@ 1 %f ' -exec fpcalc -algorithm 1 -plain  '{}' \; \
    -printf '\n@ 2 %f ' -exec fpcalc -algorithm 2 -plain  '{}' \; \
    -printf '\n@ 3 %f ' -exec fpcalc -algorithm 3 -plain  '{}' \; \
    -printf '\n@ 4 %f ' -exec fpcalc -algorithm 4 -plain  '{}' \; \
    -printf '\n@ 5 %f ' -exec fpcalc -algorithm 5 -plain  '{}' \;

#
reset ; clear ; find /mnt/mzk -type f | grep -v -E '/[0-9A-Za-z_,]{27}[.](mp3|flac|opus|m4a|wav|aac|aiff|ape|wma|ogg)$' | sort

#
(
    find mzk/ -type f -iname '*.mp3'  -exec file --mime-type -- '{}' \; | grep -v -E 'audio/mpeg$'
    find mzk/ -type f -iname '*.flac' -exec file --mime-type -- '{}' \; | grep -v -E 'audio/flac$'
    find mzk/ -type f -iname '*.opus' -exec file --mime-type -- '{}' \; | grep -v -E 'audio/ogg$'
    find mzk/ -type f -iname '*.m4a'  -exec file --mime-type -- '{}' \; | grep -v -E 'audio/x-m4a$'
    find mzk/ -type f -iname '*.aac'  -exec file --mime-type -- '{}' \; | grep -v -E 'audio/x-hx-aac-adts$'
) | sort

find mzk/ -type f -iname '*.mp3' -exec file -- '{}' \; |
grep -v -E '[.]flac: FLAC audio bitstream data, [0-9]{1,} bit, (stereo|[1-9] channels), [0-9.]{2,} kHz, [0-9]{1,} samples$' |
grep -v -E '[.]mp3: Audio file with ID3 version 2.[0-9].0$' |
grep -v -E '[.]mp3: Audio file with ID3 version 2.[0-9].0, contains:[^-]*- MPEG ADTS, layer III,  v(2|2[.]5),  [0-9]{2,} kbps, [0-9.]{2,} kHz, (Stereo|Monaural|JntStereo|[1-9]x Monaural)$' |
grep -v -E '[.]mp3: Audio file with ID3 version 2.[0-9].0, contains:[^-]*- MPEG ADTS, layer III, v(2|2[.]5),  [0-9]{2,} kbps, [0-9.]{2,} kHz, (Stereo|Monaural|JntStereo|[1-9]x Monaural)$' |
grep -v -E '[.]mp3: Audio file with ID3 version 2.[0-9].0, contains: MPEG ADTS, layer III, v1, [0-9]{2,} kbps, [0-9.]{2,} kHz, (Stereo|Monaural|JntStereo|[1-9]x Monaural)$' |
grep -v -E '[.]mp3: Audio file with ID3 version 2.[0-9].0, contains:RIFF \(little-endian\) data, WAVE audio, MPEG Layer 3, stereo [0-9]{4,} Hz$' |
grep -v -E '[.]mp3: Audio file with ID3 version 2.[0-9].0, contains:[^-]*- RIFF \(little-endian\) data, WAVE audio, MPEG Layer 3, stereo [0-9]{4,} Hz$' |
grep -v -E '[.]mp3: Audio file with ID3 version 2.[0-9].0, unsynchronized frames, contains: MPEG ADTS, layer III, v1, [0-9]{2,} kbps, [0-9.]{2,} kHz, (Stereo|Monaural|JntStereo)$' |
grep -v -E '[.]mp3: MPEG ADTS, layer III, v2,  [0-9]{2,} kbps, [0-9.]{2,} kHz, (Stereo|Monaural|JntStereo)$' |
grep -v -E '[.]mp3: MPEG ADTS, layer III, v1, [0-9]{2,} kbps, [0-9.]{2,} kHz, (Stereo|Monaural|JntStereo)$' |
grep -v -E '[.]m4a: ISO Media, Apple iTunes ALAC/AAC-LC \(.M4A\) Audio$' |
grep -v -E '[.]m4a: ISO Media, MP4 Base Media v1 \[ISO 14496-12:2003\]$' |
grep -v -E '[.]aac: Audio file with ID3 version 2.[0-9].0$' |
grep -v -E '[.]aac: Audio file with ID3 version 2.[0-9].0, contains:.- MPEG ADTS, AAC, v2 LC, [0-9.]{2,} kHz, (stereo|monaural)$' |
grep -v -E '[.]aac: Audio file with ID3 version 2.[0-9].0, contains:.*- MPEG ADTS, AAC, v2 LC, [0-9.]{2,} kHz, (stereo|monaural)$' |
grep -v -E '[.]aac: MPEG ADTS, AAC, v4 LC, [0-9.]{2,} kHz, stereo$' |
grep -v -E '[.]opus: Ogg data, Opus audio, version 0.1, (stereo|mono), [0-9]{4,} Hz \(Input Sample Rate\)$' |
grep -v -E '[.]ogg: Ogg data, Vorbis audio, stereo, [0-9]{3,} Hz, ~[0-9]{2,} bps$' |
grep -v -E '[.]aiff: IFF data, AIFF audio$' |
grep -v -E "[.]ape: Monkey's Audio compressed format version [0-9]{3,} with (fast|high) compression, stereo, sample rate [0-9]{3,}$" |
grep -v -E '[.]flac: Audio file with ID3'





id3v2 --delete-all

grep -v -E '[.]mp3: Audio file with ID3 version 2.[0-9].0, contains:\012- Audio file with ID3 version 2.4.0, contains: MPEG ADTS, layer III, v1, 320 kbps, 48 kHz, Stereo$' |
grep -v -E '[.]mp3: Audio file with ID3 version 2.[0-9].0, contains:Audio file with ID3 version 2.4.0, contains: MPEG ADTS, layer III, v1, 320 kbps, 44.1 kHz, Stereo$' |

grep -v -E '[.]mp3: Audio file with ID3 version 2.3.0'

#| sort

#
find mzk/ DOWNLOAD/ -type f | grep -v -E '/[0-9A-Za-z_,]{27}[.](mp3|flac|opus|aac|m4a|ogg)$'

# CLEAR KNOWNS
find DOWNLOAD/ -type f -regextype egrep -iregex '.*[.](jpg|jpeg|log|txt|m3u|m3u8|md5|sha1|sha256|sha512|pls|ini|db|nfo|sfv|lrc|png|cue|ico|accurip|url|lnk|desktop)$' -exec rm -f -v -- '{}' \;

#
find mzk -type f -iname '*.flac' -exec metaflac --show-all-tags '{}' \;  > /tmp/TAGS

grep -E '^[a-zA-Z0-9]{1,}=' /tmp/TAGS  | awk -F = '{print $1}' |  tr [:lower:] [:upper:] | sort | uniq

find new/ -type f -iname '*.flac' -exec metaflac --dont-use-padding --remove --block-type=PICTURE,PADDING '{}' \;
find new/ -type f -iname '*.flac' -exec metaflac --dont-use-padding --remove-all-tags-except=ALBUM=ALBUMARTIST=ALBUMARTISTSORT=ALBUMSORT=ARTIST=ARTISTS=DISCSUBTITLE=PERFORMER=TITLE=TRACK=TRACKNUMBER '{}' \;


ALBUM
ALBUMARTIST
ALBUMARTISTSORT
ALBUMRATING
ALBUMSORT
ARTIST
ARTISTS
DISC
DISCID
DISCNUMBER
DISCSUBTITLE
DISCTOTAL
PERFORMER
TITLE
TOTALDISCS
TOTALTRACKS
TRACK
TRACKC
TRACKNUMBER
TRACKTOTAL

flac --totally-silent --no-keep-foreign-metadata --decode --no-delete-input-file  --decode-through-errors --stdout /mnt/DOWNLOAD/VAo5uA3aan_dKExqhW81BGEfack.flac  | xxh128sum



(
for x in *.m4a ; do
	if ffmpeg -y -hide_banner -loglevel quiet -i "${x}" -ac 1 -f wav -c:a pcm_s24le /tmp/aqui.wav ; then
		if opusenc --quiet --music --comp 10 --bitrate 128 -- /tmp/aqui.wav "${x/.m4a/.opus}" ; then
			rm -f -- "${x}"
		fi
	fi
done
)

(
for x in *.opus ; do
	if soxi ${x} | grep -q -E -i ^youtube= ; then
		if  ! (soxi ${x} | grep -q -E -i ^artist=) ; then
			operon set ARTIST '[YOUTUBE]' ${x}
		fi
	fi
done
)

(
for x in *.opus ; do
	if soxi -- "${x}" | grep -E -i ^youtube= | grep -q -E '[=/][0-9A-Za-z_-]{11}$' ; then
		mv -n -- "${x}" youtube:$(soxi -- "${x}" | grep -E -i ^youtube= | grep -E --only-matching '.{11}$').opus
	fi
done
)



(
for x in *.opus ; do
	mv -n -- ${x} $(soxi -- "${x}" | grep --only-matching -E '^youtube=...........' | tr = ':').opus
done
)

t59NU7yBSos


(
for x in *.opus ; do
	operon set -- YOUTUBE $(awk -F . '{print $1}' <<< ${x} | awk -F : '{print $2}') ${x}
done
)
