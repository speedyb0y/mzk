/*

    /mnt/MZK/XXXXXXXX/efhiwehfiu.flac
    /mnt/MZK/XXXXXXXX/efhiwehfiu.flac
    /mnt/MZK/XXXXXXXX/efhiwehfiu.flac
    /mnt/MZK/XXXXXXXX/efhiwehfiu.flac

    /mnt/dev/by-label/MZK-XXXXXXXX -> /mnt/MZK/XXXXXXXX
    
    sudo gcc -O2 -o /bin/mzk-map vfs_mzk/mzk-map.c
    
    sudo mzk-map /home/speedyb0y/.config/deadbeef/mzk.map /mnt/MZK/??*??
*/

#include "base.c"
#include "util.c"
#include "tree.c"
#include "core.c"

// TODO:
static int funcao_neura (const void* a, const void* b) {

    return song_start(a)
        >= song_start(b) ?
            1 : -1;
}

int main (int argsN, char* args[]) {

    //
    if (argsN < 2) {
        mzk_err("BAD USAGE");
        return 1;
    }

    const char* const dbPath = args[1];

    mzk_log("CREATING DATABASE FILE %s WITH SIZE %zu", dbPath, sizeof(*db));

    // OPEN OUTPUT FILE
    // TODO: USE A TEMPORARY FILE FIRST
    const int fd = open(dbPath, O_RDWR | O_TRUNC | O_CREAT, 0444);

    if (fd == -1) {
        mzk_err("FAILED TO OPEN/CREATE DATABASE: %s", strerror(errno));
        return 1;
    }

    if (fallocate(fd, 0, 0, sizeof(*db))) {
        mzk_err("FAILED TO FALLOCATE DATABASE: %s", strerror(errno));
        return 1;
    }

    // INITIALIZE
    mzk_log("INITIALIZING...");

    if ((db = malloc(sizeof(*db))) == NULL) {
        mzk_err("FAILED TO ALOCATE DATABASE: %s", strerror(errno));
        return 1;
    }

    db->magic    = MZK_MAGIC;
    db->version  = MZK_VERSION;
    db->revision = MZK_REVISION;
    db->checksum = 0;
    db->size     = sizeof(*db);
    db->time     = time(NULL);

    disks_new(DISKS_N, db->disksTree);
    songs_new(SONGS_N, db->songsTree);
    types_new(TYPES_N, db->typesTree);

    memcpy(&db->verify, &verify, sizeof(verify));

    for (int i = 2; i != argsN; i++) {

        const char* const fdir = args[i];

        //
        const int dfd = open(fdir, O_RDONLY);

        if (dfd == -1) {
            mzk_err("FAILED TO OPEN DIRECTORY %s: %s", fdir, strerror(errno));
            continue;
        }

        //
        off_t diskBlk = 0;

        if (ioctl(dfd, FIGETBSZ, &diskBlk) == -1 || diskBlk == 0)  {
            mzk_err("FAILED TO FIGETBSZ DIRECTORY %s: %s", fdir, strerror(errno));
            continue;
        }

        //
        struct stat st;

        if (fstat(dfd, &st)) {
            mzk_err("FAILED TO STAT DIRECTORY %s: %s", fdir, strerror(errno));
            continue;
        }

        //
        const dev_t diskDev = st.st_dev;

        ASSERT(sizeof(diskDev) <= sizeof(DISK_HASH(0)));

        const size_t new = db->disksTree->count;
        const size_t diskID = disks_lookup_add(db->disksTree, diskDev);

        if (diskID >= DISKS_N) {
            mzk_err("FAILED TO REGISTER DISK");
            continue;
        }

        if (diskID == new) {
            char dpath[128];
            snprintf(dpath, sizeof(dpath), "/dev/block/%llu:%llu",
                (uintll)major(diskDev),
                (uintll)minor(diskDev));
            const int fd = open(dpath, O_RDONLY);
            if (fd != -1) {
                if (fchmod(fd, 0444)) {
                    mzk_err("FAILED TO CHMOD DEVICE %s: %s", dpath, strerror(errno));
                } close(fd);
            } else
                mzk_err("FAILED TO OPEN DEVICE %s: %s", dpath, strerror(errno));
        }       

        DIR* const dir = fdopendir(dfd);

        if (dir == NULL) {
            mzk_err("FAILED TO OPEN DIRECTORY %s: %s", fdir, strerror(errno));
            continue;
        }

        struct dirent* dentry;

        while ((dentry = readdir(dir))) {

            char* const fname = dentry->d_name;

            // SKIP . AND ..
            if (fname[0] == '.')
                continue;

            //
            char fpath[512]; snprintf(fpath, sizeof(fpath), "%s/%s", fdir, fname);

            const int fd = openat(dfd, fname, O_RDONLY);

            if (fd == -1) {
                mzk_err("FAILED TO OPEN FILE %s: %s", fpath, strerror(errno));
                continue;
            }

            const u64 code = fname_code(fname);
            const u64 type = fpath_type(fname);

            if (!code) {
                mzk_err("BAD NAME FOR FILE %s", fpath);
                continue;
            }

            if (!type) {
                mzk_err("BAD TYPE FOR FILE %s", fpath);
                continue;
            }

            //
            struct stat st;

            if (fstat(fd, &st)) {
                mzk_err("FAILED TO STAT FILE %s: %s", fpath, strerror(errno));
                close(fd);
                continue;
            }

            //
            u64 songBlks = 0;

            if (ioctl(fd, FIBMAP, &songBlks) == -1 || songBlks == 0) {
                mzk_err("FAILED TO FIBMAP FILE %s: %s", fpath, strerror(errno));
                close(fd);
                continue;
            }

            close(fd);

            // IGNORE EMPTY FILES
            if (st.st_size == 0) {
                mzk_warn("IGNORING EMPTY FILE %s", fpath);
                continue;
            }

            //
            if (st.st_dev != diskDev) {
                mzk_err("FILE DEV IS NOT DIR DEV: %s", fpath);
                continue;
            }

            const size_t typeID = types_lookup_add(db->typesTree, type);

            if (typeID >= TYPES_N) {
                mzk_err("FAILED TO REGISTER TYPE");
                continue;
            }

            //
            const size_t had = db->songsTree->count;
            const size_t songID = songs_add_single(db->songsTree, code); // TODO: _multiple

            if (songID >= SONGS_N) {
                mzk_err("FAILED TO REGISTER FILE %s", fpath);
                continue;
            }

            if (songID != had) {
                mzk_warn("REPEATED FILE %s", fpath);
                continue;
            }

            song_set(&db->songs[songID], diskID, diskBlk * songBlks, st.st_size, typeID);
        }

        closedir(dir);
    }

    mzk_log("DISKS: %zu", (size_t)db->disksTree->count);
    mzk_log("SONGS: %zu", (size_t)db->songsTree->count);
    mzk_log("TYPES: %zu", (size_t)db->typesTree->count);

    //
    if (0) // TODO: FIXME:
        qsort(db->songs, db->songsTree->count, sizeof(db->songs[0]), funcao_neura);

    //
    if (write(fd, db, sizeof(*db)) != sizeof(*db)) {
        mzk_err("FAILED TO WRITE DATABASE: %s", strerror(errno));
        return 1;
    }

    //
    if (fsync(fd)) {
        mzk_err("FAILED TO SYNC DATABASE: %s", strerror(errno));
        return 1;
    }

    close(fd);

#if MZK_DEBUG // xD
    if (mzk_load(dbPath)) {

        return 1;
    }
#endif

    return 0;
}
