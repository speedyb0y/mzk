#!/usr/bin/python

import sys
import cbor2 as cbor

for f in sys.argv[1:]:
    print(cbor.loads(open(f, "rb").read()))

