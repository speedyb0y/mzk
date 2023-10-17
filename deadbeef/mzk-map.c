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

    songs_new(SONGS_N, db->songsTree);

    memcpy(&db->verify, &verify, sizeof(verify));

    //
    part_tree_s* const partsTree = parts_new(PARTS_N, NULL);
    type_tree_s* const typesTree = types_new(TYPES_N, NULL);

    for (int i = 2; i != argsN; i++) {

        const char* const fdir = args[i];

        //
        const int dfd = open(fdir, O_RDONLY);

        if (dfd == -1) {
            mzk_err("FAILED TO OPEN DIRECTORY %s: %s", fdir, strerror(errno));
            continue;
        }

        //
        off_t partBlk = 0;

        if (ioctl(dfd, FIGETBSZ, &partBlk) == -1 || partBlk == 0)  {
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
        const dev_t partDev = st.st_dev;

        ASSERT(sizeof(partDev) <= sizeof(part_hash_t));

        const size_t partID = parts_lookup_add(partsTree, partDev);

        if (partID >= PARTS_N) {
            mzk_err("FAILED TO REGISTER PARTITION");
            continue;
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
            if (st.st_dev != partDev) {
                mzk_err("FILE DEV IS NOT DIR DEV: %s", fpath);
                continue;
            }

			const size_t typeNew = typesTree->count;
            const size_t typeID = types_lookup_add(typesTree, type);

			if (typeID >= typeNew) {
				if (typeID == typeNew) {
					*(u64*)(db->types[typeID]) = type;
				} else {
					mzk_err("FAILED TO REGISTER TYPE");
					continue;
				}
			}

            //
            const size_t songNew = db->songsTree->count;
            const size_t songID = songs_add_single(db->songsTree, code); // TODO: _multiple

            if (songID > songNew) {
                mzk_err("FAILED TO REGISTER FILE %s", fpath);
                continue;
            }

            if (songID != songNew) {
                mzk_warn("REPEATED FILE %s", fpath);
                continue;
            }

            song_s* const song = &db->songs[songID];

            song->disk  = partID;
            song->start = partBlk * songBlks;
            song->size  = st.st_size;
            song->type  = typeID;
        }

        closedir(dir);
    }

    // IDENTIFICA OS DISCOS
    disk_tree_s* const disksTree = disks_new(DISKS_N, NULL);

    foreach (size_t, partID, partsTree->count) {

        char dpath[256]; int fd;
        char  value[64]; size_t s;
        char* value2;

        uint diskMajor; off_t start;
        uint diskMinor;

#define TREE_HASH0(T, i) ((T)[1+(i)].hash[0])
        const dev_t partDev = TREE_HASH0(partsTree, partID);

        const uint partMajor = major(partDev);
        const uint partMinor = minor(partDev);

        // DESCOBRE O MAJOR/MINOR DO SEU DISCO
        snprintf(dpath, sizeof(dpath), "/sys/dev/block/%u:%u/../dev", partMajor, partMinor);

        if ((s = read((fd = open(dpath, O_RDONLY)), value, sizeof(value) - 1)) < 4 || value[s -= 1] != '\n')
            goto _part;

        close(fd);

        value[s] = '\0';
        value2 = strchr(value, ':');
       *value2++ = '\0';

        diskMajor = atoi(value);
        diskMinor = atoi(value2);

        // DESCOBRE O OFFSET DESTA PARTIÇÃO NO DISCO
        snprintf(dpath, sizeof(dpath), "/sys/dev/block/%u:%u/start", partMajor, partMinor);

        if ((s = read((fd = open(dpath, O_RDONLY)), value, sizeof(value) - 1)) <= 1 || value[s -= 1] != '\n')
            goto _part;

        close(fd);

        value[s] = '\0';

        start = strtoull(value, NULL, 10) * 512;

        goto _update;

_part: // PARTITION IS THE DISK ITSELF
        close(fd);

        diskMajor = partMajor; start = 0;
        diskMinor = partMinor;
_update:
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
    db->typesN = typesTree->count;

    mzk_log("DISKS: %zu", (size_t)db->disksN);
    mzk_log("TYPES: %zu", (size_t)db->typesN);
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
