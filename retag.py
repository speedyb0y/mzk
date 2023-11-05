#!/usr/bin/python

import sys
import os

for f in sys.argv[1:]:

    print(f)

	cmd = [ 'ffmpeg', '-i', f, '-map_metadata', '-1' ]

	originais = {}


	for k, v in tags.items():

		k = '_'.join(k.replace('_', ' ').replace('-', ' ').split()).upper()
		v = ' '.join(v.split()).upper()

		try:
			k = {
				'TITLE': 'XTITLE',
				'ALBUM': 'XALBUM',
				'ARTIST': 'XARTIST',
			} [k]
		except KeyError:
			continue

		if k and v:
			cmd.extend(('-metadata', f'{t}={v}'))

	cmd.append('/tmp/retageado')

	print(cmd)
	if os.fork() == 0:
		os.execve("/usr/bin/ffmpeg", cmd, os.environ)
		exit(1)

	#
    fail = 0
    
    try:
        while True:
            fail |= os.wait()[1]
    except ChildProcessError:
        pass

	if fail:
		print('FAILED')
		exit(1)

	#
