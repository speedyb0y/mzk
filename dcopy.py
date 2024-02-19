#!/usr/bin/python

import sys
import stat
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

# TODO: USE DIR FD
def scandir (d):
    st = os.stat(d, follow_symlinks=False)
    if stat.S_ISDIR(st.st_mode):
        fs = os.listdir(d)
        try:
            os.mkdir(f'{ddir}/{d}')
        except FileExistsError:
            pass
        for f in fs:
            yield from scandir(f'{d}/{f}')
    elif stat.S_ISREG(st.st_mode) and st.st_size:
        yield fibmap(d.encode()), d, st.st_size

#
for offset, orig, sizeOrig in sorted(scandir('.')):

    dest = f'{ddir}/{orig}'

    # TODO: FIXME: LINKS
    # TODO: FIXME: CACHE ALREADY FS/DEV/INODE FILES SO WE HARD LINK THEM

    #print(offset, sizeOrig, orig)

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
    _got = fresize(ofd, sizeAlign + 4096)
    assert _got == 0, (dest, sizeAlign, _got)

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
