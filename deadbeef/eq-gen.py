#!/usr/bin/python

import sys
import random

_, directory, n = sys.argv

n = int(n)

for i in range(n):
    with open(f'{directory}/{i}.ddbeq', 'w') as fd:
        fd.write('\n'.join('%.6f' % (random.randint(-1000, 1000)/100) for x in range(18)) + '\n0.000000\n')
