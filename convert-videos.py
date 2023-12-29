#!/usr/bin/python

import sys
import os

for f in sys.argv[1:]:

    title = f.rsplit('/', 1)[-1].encode().replace(b'\xef\xbc\x9a', b':').decode()

    youtube = title.rsplit('[', 1)[-1].split(']', 1)[0]

    assert len(youtube) == len('JAcNXrW_J7o')

    title = ' '.join(title.rsplit('[', 1)[0].split()).upper()

    print(youtube, f)

    os.system(f"ffmpeg -y -hide_banner -loglevel error -bitexact -threads 1 -i '{f}' -map_metadata -1 -map_metadata:s -1 -f matroska -c:a copy -c:v copy -metadata TITLE='{title}' -metadata YOUTUBE={youtube} ./{youtube}.mkv")
