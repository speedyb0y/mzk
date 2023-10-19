
#ifndef MZK_DEBUG
#define MZK_DEBUG 0
#endif

#define SONGS_N 500000
#define DISKS_N 255
#define PARTS_N DISKS_N

#define SONG_SIZE_MAX (32ULL*1024*1024*1024)

// SONGS
typedef tree32x128_hash_t  song_hash_t;
typedef tree32x128_s       song_tree_s;
#define songs_new          tree32x128_new
#define songs_add_multiple tree32x128_add_multiple // TODO: ACCEPT MULTIPLE!!!
#define songs_add_single   tree32x128_add_single
#define songs_lookup       tree32x128_lookup
#define songs_lookup_add   tree32x128_lookup_add

// DISKS
typedef tree8x64_hash_t  disk_hash_t;
typedef tree8x64_s       disk_tree_s;
#define disks_new          tree8x64_new
#define disks_add_single   tree8x64_add_single
#define disks_lookup       tree8x64_lookup
#define disks_lookup_add   tree8x64_lookup_add

// PARTITIONS
typedef tree8x64_hash_t  part_hash_t;
typedef tree8x64_s       part_tree_s;
#define parts_new          tree8x64_new
#define parts_add_single   tree8x64_add_single
#define parts_lookup       tree8x64_lookup
#define parts_lookup_add   tree8x64_lookup_add

// TYPES
typedef tree8x64_hash_t  type_hash_t;
typedef tree8x64_s       type_tree_s;
#define types_new          tree8x64_new
#define types_add_single   tree8x64_add_single
#define types_lookup       tree8x64_lookup
#define types_lookup_add   tree8x64_lookup_add

typedef struct song_s {
    u64 start;
    u64 size:48,
        disk:16;
} song_s;

// DATABASE
#define MZK_MAGIC 0x57494c4552494b41ULL
#define MZK_VERSION 1
#define MZK_REVISION 0

typedef struct db_verify_s {
    song_tree_s songTree;
    song_hash_t songHash;
    song_s      song;
    u8 disksN;
    u8 songsN;
} db_verify_s;

typedef struct db_s {
    u64 magic;
    u32 version;
    u32 revision;
    u64 checksum;
    size_t size; // OF THIS ENTIRE FILE
    time_t time;
    size_t disksN;
    u32 disks[DISKS_N][2]; // MAJOR, MINOR
    song_tree_s songsTree[SONGS_N + 1];
    song_s songs[SONGS_N];
    db_verify_s verify;
} db_s;

static const db_verify_s verify = {
    .songTree = { .count = 0, .size = 1, .childs = { 0, 1 }, },
    .songHash = 6,
    .song = {
        .start = 0x5464500465ULL,
        .size = 0x3423432ULL,
        .disk = 0x13,
    }
};

#if !MZK_DEBUG
#define mzk_dbg(fmt, ...)  ({})
#else
#define mzk_dbg(fmt, ...)  fprintf(stderr, "MZK: DEBUG: "   fmt "\n", ##__VA_ARGS__)
#endif
#define mzk_log(fmt, ...)  fprintf(stderr, "MZK: "          fmt "\n", ##__VA_ARGS__)
#define mzk_warn(fmt, ...) fprintf(stderr, "MZK: WARNING: " fmt "\n", ##__VA_ARGS__)
#define mzk_err(fmt, ...)  fprintf(stderr, "MZK: ERROR: "   fmt "\n", ##__VA_ARGS__)

#define SID_NOT_FOUND    SONGS_N
#define SID_ROOT        (SONGS_N + 1)

static int fds[DISKS_N];
static db_s* db;

// TODO: ON EXIT: unmap disks
static inline void code_to_str (char* str, u64 code, u64 ext) {

    // ASSERT: code != 0
    // ASSERT; code <= 0xBA5CA5392CB03FFULL
    static char alphabet[] = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";

    while (code) {
        *str++ = alphabet[code % 62];
        code /= 62;
    }

    *str++ = '.';

#if 0
    ext = __builtin_swap64(ext);
#endif
    while ((*str++ = ext & 0xFFU))
        ext >>= 8;
}

static inline int fname_code (const char* fname, u64* const code_, u64* const ext_) {

    u64 mult = 1;
    u64 code = 0;

    int c;

    while ((c = *fname++) != '.') {

        if   (c >= '0' && c <= '9')
              c -= '0';
        elif (c >= 'a' && c <= 'z')
              c -= 'a' - 10;
        elif (c >= 'A' && c <= 'Z')
              c -= 'A' - (10 + 26);
        else // INVALID CHARACTER / MISSING EXTENSION
            return 1;

        // 62^10
        if (code >= 0x0BA5CA5392CB0400ULL)
            return 1;

        code += mult * c;
        mult *= 10 + 26 + 26;
    }

    const char* ext = fname;

    while (*fname)
            fname++;

    const size_t len = fname - ext;

    // PRECISARA DE UM \0
    if (len == 0 || len >= sizeof(u64))
        // EXTENSAO NULA / EXTENSAO GRANDE
        return 1;

    // JA POE O \0
    *code_ = code;
    *ext_ = 0;

    // TODO: FIXME: SE FOR BIG ENDIAN, PRECISA DAR UM SWAP64 AO USAR COMO HASH
    memcpy(ext_, ext, len);

    return 0;
}

static inline size_t mzk_fname_sid (const char* fpath) {

    u64 code, type;

    if (fname_code(fpath, &code, &type))
        return SID_NOT_FOUND;

    return songs_lookup(db->songsTree, code, type);
}

static int mzk_load (const char* const dbPath) {

    mzk_log("LOAD: USING DATABASE %s", dbPath);

    // MAP_HUGETLB | MAP_HUGE_2MB
    db = mmap(NULL, sizeof(*db), PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANONYMOUS, -1, 0);

    if (db == MAP_FAILED || db == NULL) {
        mzk_err("LOAD: FAILED TO MAP DATABASE: %s", strerror(errno));
        goto _err;
    }

    const int fd = open(dbPath, O_RDONLY);

    if (fd == -1) {
        mzk_err("LOAD: FAILED TO OPEN DATABASE: %s", strerror(errno));
        goto _err_unmap;
    }

    if (read(fd, db, sizeof(*db)) != sizeof(*db)) {
        mzk_err("LOAD: FAILED TO READ DATABASE: %s", strerror(errno));
        goto _err_close;
    }

    mzk_log("LOAD: DISKS: %zu", (size_t)db->disksN);
    mzk_log("LOAD: SONGS: %zu", (size_t)db->songsTree->count);

    if (db->magic != MZK_MAGIC) {
        mzk_err("LOAD: BAD MAGIC: 0x%016llX", (uintll)db->magic);
        goto _err_close;
    }

    if (db->version != MZK_VERSION) {
        mzk_err("LOAD: VERSION MISMATCH: %u", db->version);
        goto _err_close;
    }

    if (db->revision != MZK_REVISION)
        mzk_warn("LOAD: REVISION MISMATCH: %u", db->revision);

    if (memcmp(&db->verify, &verify, sizeof(verify))) {
        mzk_err("LOAD: DATABASE VERIFICATION MISMATCH");
        goto _err_close;
    }

    if (db->disksN >= DISKS_N) {
        mzk_err("LOAD: BAD DISKS COUNT");
        goto _err_close;
    }

    if (db->songsTree->size  != SONGS_N
     || db->songsTree->count >= SONGS_N) {
        mzk_err("LOAD: BAD SONGS COUNT/SIZE");
        goto _err_close;
    }

    // VERIFY SONGS
    foreach (size_t, songID, db->songsTree->count) {

        song_s* const song = &db->songs[songID];

        if (song->disk >= db->disksN
         || song->size >= SONG_SIZE_MAX
         || song->start == 0)
            mzk_err("INVALID SONG");
    }

    foreach (size_t, i, db->disksN) {

        char dpath[128];

        snprintf(dpath, sizeof(dpath), "/dev/block/%u:%u",
            db->disks[i][0],
            db->disks[i][1]);

        mzk_log("LOAD: OPENING DISK #%zu AT %s...", i, dpath);

        const int fd = open(dpath, O_RDONLY);

        if (fd == -1) {
            mzk_err("LOAD: FAILED TO OPEN DISK: %s", strerror(errno));
            goto _failed;
        }

        if (lseek(fd, 0, SEEK_END) == -1) {
            mzk_err("LOAD: FAILED TO SEEK DATABASE: %s", strerror(errno));
            goto _failed_close;
        }

        mzk_log("LOAD: DISK SIZE: %zu", (size_t)lseek(fd, 0, SEEK_CUR));
        mzk_log("LOAD: DISK FD: %d", fd);

        fds[i] = fd;

        continue;

_failed_close:
        close(fd);
_failed:
        fds[i] = -1;
    }

    close(fd);

    return 0;

_err_close:
    close(fd);
_err_unmap:
    munmap(db, sizeof(*db));
_err:
    return 1;
}
