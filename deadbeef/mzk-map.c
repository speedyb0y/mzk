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

    return ((song_s*)a)->start
        >= ((song_s*)b)->start ?
            1 : -1;
}

#define MPATH_LEN 128

int main (int argsN, char* args[]) {

    //
    if (argsN != 3) {
        mzk_err("BAD USAGE");
        return 1;
    }

    const char* const dbPath = args[1];
    const char* const  mPath = args[2];

    if (strlen(mPath) >= MPATH_LEN || mPath[strlen(mPath)-1] != '/') {
        mzk_err("BAD MZK PATH: %s", mPath);
        return 1;
    }

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

    songs_new(SONGS_N, db->songsTree);

    memcpy(&db->verify, &verify, sizeof(verify));

    //
    part_tree_s* const partsTree = parts_new(PARTS_N, NULL);

    mzk_log("MZK DIRECTORY %s", mPath);

    // OPEN THE MZK DIR
    const int mfd = open(mPath, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_NOCTTY | O_NOATIME);

    if (mfd == -1) {
        mzk_err("MZK DIRECTORY %s: FAILED TO OPEN: %s", mPath, strerror(errno));
        return 1;
    }

    //
    struct stat st;

    if (fstat(mfd, &st)) {
        mzk_err("MZK DIRECTORY %s: FAILED TO STAT: %s", mPath, strerror(errno));
        return 1;
    }

    // CONFIRM IT IS A DIRECTORY
    if (!S_ISDIR(st.st_mode)) {
        mzk_err("MZK DIRECTORY %s: NOT A DIRECTORY", mPath);
        return 1;
    }

    // REMEMBER ITS DEVICE, SO WE KNOW IF A SUBDIR IS A MOUNTPOINT
    const dev_t mDev = st.st_dev;

    // SEE ALL PARTITIONS DIRECTORIES
    DIR* const mdir = fdopendir(mfd);

    if (mdir == NULL) {
        mzk_err("MZK DIRECTORY %s: FAILED TO OPEN: %s", mPath, strerror(errno));
        return 1;
    }

    struct dirent* mentry;

    while ((mentry = readdir(mdir))) {

        const char* const pName = mentry->d_name;

        // SKIP . AND ..
        if (pName[0] == '.')
            continue;

        char pPath[512]; snprintf(pPath, sizeof(pPath), "%s%s/", mPath, pName);

        mzk_log("PARTITION DIRECTORY %s", pPath);

        //
        const int pfd = openat(mfd, pPath, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_NOCTTY | O_NOATIME);

        if (pfd == -1) {
            mzk_err("PARTITION DIRECTORY %s: FAILED TO OPEN: %s", pPath, strerror(errno));
            continue;
        }

        DIR* const pdir = fdopendir(pfd);

        if (pdir == NULL) {
            mzk_err("PARTITION DIRECTORY %s: FAILED TO OPEN: %s", pPath, strerror(errno));
            close(pfd);
            continue;
        }

        //
        struct stat st;

        if (fstat(pfd, &st)) {
            mzk_err("PARTITION DIRECTORY %s: FAILED TO STAT: %s", pPath, strerror(errno));
            goto _next_partition;
        }

        // CONFIRM IT IS A DIRECTORY
        if (!S_ISDIR(st.st_mode)) {
            mzk_err("PARTITION DIRECTORY %s: NOT A DIRECTORY", mPath);
            goto _next_partition;
        }

        //
        const dev_t partDev = st.st_dev;

        if (partDev == mDev) {
            mzk_log("PARTITION DIRECTORY %s: SKIPPING (NOT MOUNTED)", pPath);
            goto _next_partition;
        }

        //
        ASSERT(sizeof(partDev) <= sizeof(part_hash_t));

        const size_t partID = parts_add_single(partsTree, partDev);

        if (partID >= PARTS_N) {
            mzk_log("PARTITION DIRECTORY %s: FAILED TO REGISTER (DUPLICATED?)", pPath);
            goto _next_partition;
        }

        //
        off_t partBlk = 0;

        if (ioctl(pfd, FIGETBSZ, &partBlk) == -1 || partBlk == 0)  {
            mzk_err("PARTITION DIRECTORY %s: FAILED TO FIGETBSZ: %s", pPath, strerror(errno));
            goto _next_partition;
        }

        // SEE ALL FILES IN THE PARTITION
        struct dirent* dentry;

        while ((dentry = readdir(pdir))) {

            char* const fname = dentry->d_name;

            // SKIP . AND ..
            if (fname[0] == '.')
                continue;

            //
            char fpath[1024]; snprintf(fpath, sizeof(fpath), "%s%s", pPath, fname);

            const int fd = openat(pfd, fname, O_RDONLY | O_NOFOLLOW | O_NOCTTY | O_NOATIME);

            if (fd == -1) {
                mzk_err("FILE %s: FAILED TO OPEN: %s", fpath, strerror(errno));
                continue;
            }

            u64 code, type;

            if (fname_code(fname, &code, &type)) {
                mzk_err("FILE %s: BAD NAME/EXTENSION", fpath);
                goto _next_file;
            }

            //
            u64 songBlks = 0;

            if (ioctl(fd, FIBMAP, &songBlks) == -1 || songBlks == 0) {
                mzk_err("FILE %s: FAILED TO FIBMAP: %s", fpath, strerror(errno));
                goto _next_file;
            }

            //
            struct stat st;

            if (fstat(fd, &st)) {
                mzk_err("FILE %s: FAILED TO STAT: %s", fpath, strerror(errno));
                goto _next_file;
            }

            // IGNORE EMPTY FILES
            if (st.st_size == 0) {
                mzk_warn("FILE %s: IGNORING (EMPTY)", fpath);
                goto _next_file;
            }

            //
            if (st.st_dev != partDev) {
                mzk_err("FILE %s: DEV IS NOT DIR DEV", fpath);
                goto _next_file;
            }

            //
            const size_t songNew = db->songsTree->count;
            const size_t sid = songs_add_single(db->songsTree, code, type); // TODO: _multiple

            if (sid > songNew) {
                mzk_err("FILE %s: FAILED TO REGISTER", fpath);
                goto _next_file;
            }

            if (sid != songNew) {
                mzk_warn("FILE %s: REPEATED", fpath);
                goto _next_file;
            }

            song_s* const song = &db->songs[sid];

            song->disk  = partID;
            song->start = partBlk * songBlks;
            song->size  = st.st_size;
_next_file:
            close(fd);
        }

_next_partition:
        closedir(pdir);
    }

    closedir(mdir);

    // IDENTIFICA OS DISCOS
    disk_tree_s* const disksTree = disks_new(DISKS_N, NULL);

    foreach (size_t, partID, partsTree->count) {

        char dpath[256]; int fd;
        char  value[64]; size_t s;
        char* value2;

        uint diskMajor; off_t start;
        uint diskMinor;

        const dev_t partDev = TREE_HASHES(partsTree, partID)[0];

        const uint partMajor = major(partDev);
        const uint partMinor = minor(partDev);

        // DESCOBRE O MAJOR/MINOR DO SEU DISCO
        snprintf(dpath, sizeof(dpath), "/sys/dev/block/%u:%u/../dev", partMajor, partMinor);

        if ((s = read((fd = open(dpath, O_RDONLY)), value, sizeof(value) - 1)) < 4 || value[s -= 1] != '\n')
            goto _use_part;

        close(fd);

        value[s] = '\0';
        value2 = strchr(value, ':');
       *value2++ = '\0';

        diskMajor = atoi(value);
        diskMinor = atoi(value2);

        // DESCOBRE O OFFSET DESTA PARTIÇÃO NO DISCO
        snprintf(dpath, sizeof(dpath), "/sys/dev/block/%u:%u/start", partMajor, partMinor);

        if ((s = read((fd = open(dpath, O_RDONLY)), value, sizeof(value) - 1)) <= 1 || value[s -= 1] != '\n')
            goto _use_part;

        close(fd);

        value[s] = '\0';

        start = strtoull(value, NULL, 10) * 512;

        mzk_dbg("%s -> %s -> %zu", dpath, value, start);

        goto _use_disk;

_use_part: // THE DISK IS THE PARTITION ITSELF
        close(fd);

        diskMajor = partMajor; start = 0;
        diskMinor = partMinor;
_use_disk: // THE DISK IS THE DISK
        // NOTE: NUNCA FALHA POIS TEM TANTOS DISCOS QUANTO PARTICOES NA ARRAY
        const size_t diskNew = disksTree->count;
        const size_t diskID = disks_lookup_add(disksTree, makedev(diskMajor, diskMinor));

        if (diskID == diskNew) {
            //
            db->disks[diskID][0] = diskMajor;
            db->disks[diskID][1] = diskMinor;

            snprintf(dpath, sizeof(dpath), "/dev/block/%u:%u", diskMajor, diskMinor);

            if ((fd = open(dpath, O_RDONLY)) != -1) {
                fchmod(fd, 0444);
                close(fd);
            }
        }

        // VE QUAIS SONGS USAM ESTA PARTICAO, E AI PASSA A USAR O DISCO DELA
        foreach (size_t, s, db->songsTree->count) {
            song_s* const song = &db->songs[s];
            if (song->disk == partID) {
                song->disk   = diskID;
                song->start += start;
            }
        }
    }

    //
    db->disksN = disksTree->count;

    mzk_log("DISKS: %zu", (size_t)db->disksN);
    mzk_log("SONGS: %zu", (size_t)db->songsTree->count);

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
