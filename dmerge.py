#!/usr/bin/python
#
# MERGE A DIRECTORY STRUCTURE (ON THE SAME FILESYSTEM)
#
# SOURCE_DIR/DIR_1/FILE_1
# SOURCE_DIR/DIR_1/FILE_2
# SOURCE_DIR/DIR_1/FILE_3
# SOURCE_DIR/DIR_1/FILE_N
# SOURCE_DIR/DIR_2/FILE_1  -> DESTINATION_DIR/DIR*/FILE*
# SOURCE_DIR/DIR_2/FILE_2
# SOURCE_DIR/DIR_3/FILE_3
# SOURCE_DIR/DIR_3/FILE_N
# SOURCE_DIR/DIR_N/FILE_N
#

import sys
import os

_, sdir, ddir = sys.argv

sdir = sdir.rstrip('/')
ddir = ddir.rstrip('/')

assert sdir.startswith('/')
assert ddir.startswith('/')

assert sdir != ddir

assert not sdir.startswith(ddir)
assert not ddir.startswith(sdir)

os.chdir(sdir)

try:
    os.mkdir(ddir)
except FileExistsError:
    pass

sfd = os.open(sdir, os.O_RDONLY | os.O_DIRECTORY)
dfd = os.open(ddir, os.O_RDONLY | os.O_DIRECTORY)

assert 0 <= sfd
assert 0 <= dfd

for d in sorted(os.listdir(sfd)):

    try:
        os.mkdir(d, mode=0o0755, dir_fd=dfd)
    except FileExistsError:
        pass

    ifd = os.open(d, os.O_RDONLY | os.O_DIRECTORY, dir_fd=sfd)
    ofd = os.open(d, os.O_RDONLY | os.O_DIRECTORY, dir_fd=dfd)

    assert 0 <= ifd
    assert 0 <= ofd

    for f in sorted(os.listdir(ifd)):
        print(f'{sdir}/{d}/{f}')
        print(f'{ddir}/{d}/{f}')
        os.rename(f, f, src_dir_fd=ifd, dst_dir_fd=ofd)
        print('')

    os.close(ifd)
    os.close(ofd)

    os.rmdir(d, dir_fd=sfd)

os.close(sfd)
os.close(dfd)

os.rmdir(sdir)
