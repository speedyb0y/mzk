/*

	/mnt/MZK/sdc1/XXXXXXXX.flac
	/mnt/MZK/sdc2/XXXXXXXX.flac
	/mnt/MZK/sdc3/XXXXXXXX.flac
	/mnt/MZK/sdcN/XXXXXXXX.flac

	sudo ./a.out /mnt/MZK
*/

#define _FILE_OFFSET_BITS 64

#define _GNU_SOURCE 1

#include <stdint.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <linux/types.h>
#include <linux/fs.h>
#include <dirent.h>

typedef uint64_t u64;

typedef unsigned int uint;
typedef unsigned long long int uintll;

typedef struct MzkEntry {
    u64 name;
    u64 ext;
    u64 offset;
    u64 size;
} MzkEntry;

static inline u64 name_to_code (const char* name) {

    u64 mult = 1;
    u64 code = 0;

    while (1) {

        u64 L = *name++;

        if (L >= (u64)'0'
         && L <= (u64)'9')
            L -= (u64)'0';
        else if (L >= (u64)'a'
              && L <= (u64)'z')
                 L -= (u64)'a' - 10;
        else if (L >= (u64)'A'
              && L <= (u64)'Z')
                 L -= (u64)'A' - (10 + 26);
        else if (L) // INVALID CHARACTER
            return 0xFFFFFFFFFFFFFFFFULL;
        else
            return code;

        code += mult * L;
        mult *= 10 + 26 + 26;
    }
}

static char* eita (char* const fname) {

    char* dot = strchr(fname, '.');

    *dot = '\0';

    return ++dot;
}

// PEGA UMA PARTICAO, E RETORNA ONDE COMECA O NUMERO DELA
static inline const char* partition_num (const char* partition) {

    if (*partition) {
        while (*partition)
                partition++;
        while (*--partition >= '0'
              && *partition <= '9');
        partition++;
    }

    return partition;
}

#define FILES_MAXIMUM 1000000

int main (int argsN, char* args[]) {

    //
    if (argsN != 2)
        return 1;

    MzkEntry* const entries = malloc(FILES_MAXIMUM * sizeof(*entries));
    MzkEntry* const lmt = entries + FILES_MAXIMUM;
    MzkEntry* entry = entries;

    //
    u64 diskName[2];
    u64 diskOffset = 0;

    // LISTA O /mnt/MZK
    DIR* const rootDir = opendir(args[1]);

    if (rootDir == NULL)
        return 1;

    const int rootFD = dirfd(rootDir);

    // HANDLE ALL IN /mnt/MZK
    struct dirent* rootEntry;

    while ((rootEntry = readdir(rootDir))) {

        const char* const partition = rootEntry->d_name;

        // SKIP . AND ..
        if (partition[0] == '.')
            continue;

        u64 diskName2[2] = { 0 , 0 };

        memcpy(diskName2, partition, partition_num(partition) - partition);

        if (diskName[0] != diskName2[0]
         || diskName[1] != diskName2[1]) {
            diskName[0]  = diskName2[0];
            diskName[1]  = diskName2[1];
            // FIM DO DISCO ATUAL

            char diskOffsetStr[16];

            char ss[512];

            snprintf(ss, sizeof(ss), "/sys/block/%s/%s/start", (char*)diskName, partition);

            const int fd = open(ss, O_RDONLY);

            if (fd == -1)
                return 1;

            const int len = read(fd, &diskOffsetStr, sizeof(diskOffsetStr));

            if (len <= 1)
                return 1;

            close(fd);

            // TRANSFORMA O \N NO \0
            diskOffsetStr[len - 1] = '\0';

            char* failed = NULL;

            // É EM BLOCOS
            diskOffset = strtoull(diskOffsetStr, &failed, 10) * 512;

            //
            if (failed
            && *failed)
                return 1;

            //
            if (entry == lmt)
                return 1;
            entry->name   = diskName[0];
            entry->ext    = diskName[1];
            entry->offset = 0;
            entry->size   = 0;
            entry++;
        }

        // LISTA /mnt/MZK/sd[a-z][0-9]*
        DIR* const fsDir = fdopendir(openat(rootFD, partition, O_RDONLY));

        if (fsDir == NULL)
            return 1;

        const int fsFD = dirfd(fsDir);

        struct dirent* fsEntry;

        while ((fsEntry = readdir(fsDir))) {

            char* const fname = fsEntry->d_name;

            // SKIP . AND ..
            if (fname[0] == '.')
                continue;

            const int fd = openat(fsFD, fname, O_RDONLY);

            if (fd == -1)
                return 1;

            struct stat st = { 0 };

            if (fstat(fd, &st))
                return 1;

            unsigned long long int blksize = 0;
            unsigned long long int blknum = 0;

            if (ioctl(fd, FIBMAP,   &blknum ) == -1
             || ioctl(fd, FIGETBSZ, &blksize) == -1)
                return 1;

            close(fd);

            char* const fext = eita(fname);

            if (entry == lmt)
                return 1;

            entry->name   = name_to_code(fname);
            entry->ext    = name_to_code(fext);
            entry->offset = diskOffset + blknum * blksize;
            entry->size   = st.st_size;
            entry++;
        }

        closedir(fsDir);
    }

    closedir(rootDir);

    // FIM DO DISCO
    if (entry == lmt)
        return 1;
    entry->name   = 0;
    entry->ext    = 0;
    entry->offset = 0;
    entry->size   = 0;
    entry++;

    if (write(STDOUT_FILENO, entries, ((void*)entry - (void*)entries))
                                   != ((void*)entry - (void*)entries))
        return 1;

    return 0;
}
