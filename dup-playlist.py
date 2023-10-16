#!/usr/bin/python

import sys
import os
import json

grupos = {}, {}, {}, {}, {}, {}

for fpath in sys.argv[1:]:

	for line in open(fpath).read().split('\n'):

		if line:

			whole, fingers, duration, fpath = line.split()

			for i, cksum in enumerate((whole, *fingers.split('|'))):
				try:
					lista = grupos[i][cksum]
				except KeyError:
					lista = grupos[i][cksum] = set()
				lista.add(fpath)

open('REPEATEDS.json', 'w').write(json.dumps([[(C, tuple(L)) for C, L in sorted(G.items())] for G in grupos]))

PARES = set()

for grupo in grupos:
	for lista in grupo.values():
		if len(lista) > 1:
			PARES.add(tuple(sorted(lista)))

for i, lista in enumerate(PARES):
	open(f'{i}.m3u', 'w').write('\n'.join(sorted(lista)) + '\n')
