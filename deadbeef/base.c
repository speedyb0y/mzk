
//#define _FILE_OFFSET_BITS 64

#define _GNU_SOURCE 1

#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/sysmacros.h>
#include <sys/stat.h>
#include <sys/ioctl.h>
#include <sys/uio.h>
#include <sys/mman.h>
#include <linux/types.h>
#include <linux/fs.h>
#include <dirent.h>

#define PTR(p) ((void*)(p))

#define elif else if

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;

typedef unsigned int uint;

typedef long long int intll;
typedef unsigned long long int uintll;

#define foreach(t, i, n) for (t i = 0; i != (n); i++)

#define loop while(1)
#define elif else if

#define copy(b, a, as) memcpy(b, a, as)
#define clear(a, as) memset(a, 0, as)

#define ASSERT(x) ({})
