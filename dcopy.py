#!/usr/bin/python

import sys
import os
import mmap
import io

from cffi import FFI

ffi = FFI()
ffi.set_source("dcopy2",
'''
// #define _GNU_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <fcntl.h>
#include <linux/fs.h>

typedef unsigned long long u64;

u64 fibmap (const char* const fpath) {

    size_t block = 0;
    size_t start = 0;

    const int fd = open(fpath, O_RDONLY);

    if (fd >= 0) {

        if (ioctl(fd, FIGETBSZ, &block)
         || ioctl(fd, FIBMAP,   &start))
            start = 0;

        close(fd);
    }

    return (u64)start * block;
}

int fresize (int fd, off_t len) {

    if (fallocate(fd, 0, 0, len))
        return -1;

    if (fsync(fd))
        return -1;

    return 0;
}

''', libraries=[])
ffi.cdef('typedef long long off_t; int fresize (int fd, off_t len);')
ffi.cdef('typedef unsigned long long u64; u64 fibmap(char* fpath);')
ffi.compile(target=(sys.argv[0].rsplit('.py', 1)[0] + '2.so'))

import dcopy2

fibmap  = dcopy2.lib.fibmap
fresize = dcopy2.lib.fresize

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

def scandir (d):
    try:
        fs = os.listdir(d)
        try:
            os.mkdir(f'{ddir}/{d}')
        except FileExistsError:
            pass
        for f in fs:
            yield from scandir(f'{d}/{f}')
    except NotADirectoryError:
        yield fibmap(d.encode()), d

#
for offset, orig in sorted(scandir('.')):

    dest = f'{ddir}/{orig}'

    sizeOrig = os.stat(orig).st_size

    print(offset, sizeOrig, orig)

    if sizeOrig == 0:
        continue

    sizeAlign = ((sizeOrig + 4096 - 1) // 4096) * 4096

    assert 1 <= sizeOrig <= sizeAlign

    # WRITE DIRECT
    try:
        ofd = os.open(dest, os.O_WRONLY | os.O_DIRECT | os.O_SYNC | os.O_CREAT | os.O_EXCL, 0o444)
    except FileExistsError:
        if os.stat(dest).st_size == sizeOrig:
            # JA COPIOU
            continue
        # COPIOU INCOMPLETO
        os.unlink(dest)
        ofd = os.open(dest, os.O_WRONLY | os.O_DIRECT | os.O_SYNC | os.O_CREAT | os.O_EXCL, 0o444)

    # RESERVE ALIGNED
    # 1 MORE BLOCK SO WE ALWAYS HAVE A DIFFERENT FILE SIZE
    assert fresize(ofd, sizeAlign + 4096) == 0

    # RESIZE ALIGNED
    if sizeOrig != sizeAlign:
        os.truncate(orig, sizeAlign)

    # MAP INPUT
    fd = os.open(orig, os.O_RDONLY)
    fmap = mmap.mmap(fd, sizeAlign, mmap.MAP_SHARED | mmap.MAP_POPULATE, mmap.PROT_READ, 0, 0)
    fmap.madvise(mmap.MADV_SEQUENTIAL)
    os.close(fd)
    buffer = memoryview(fmap)

    # WRITE, FLUSH, RESIZE AS ORIGINAL AND CLOSE
    pos = 0
    while pos != sizeAlign:
        put = os.write(ofd, buffer[pos:sizeAlign])
        assert 0 <= put
        pos += put
        assert 0 <= pos <= sizeAlign

    # os.fsync(ofd)
    os.ftruncate(ofd, sizeOrig)
    # os.fsync(ofd)
    os.close(ofd)

    # UNMAP INPUT
    buffer.release()
    fmap.close()

    # RESTORE ORIGINAL SIZE
    if sizeAlign != sizeOrig:
        os.truncate(orig, sizeOrig)
