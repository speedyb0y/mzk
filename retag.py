#!/usr/bin/python

import sys
import os
import mutagen
import mutagen.ogg

for f in sys.argv[1:]:

    print(f)

    tagged = mutagen.File(f)

    modificou = None

    #
    for k, v in sorted(tagged.items()):
        assert isinstance(v, list), (k, v)
        tagged.tags[k]
        #modificou = tagged.save
        print(k, v)
        v, = v

    if modificou is not None:
        modificou()

    # print(dir(tagged))
    # tagged.close()

    tagged = modificou = None
