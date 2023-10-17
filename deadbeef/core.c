
#ifndef MZK_DEBUG
#define MZK_DEBUG 0
#endif

#define SONGS_N 500000
#define DISKS_N 250
#define TYPES_N 32
#define PARTS_N DISKS_N

#define SONG_SIZE_MAX (32ULL*1024*1024*1024)

// SONGS
typedef tree32x64_hash_t  song_hash_t;
typedef tree32x64_s       song_tree_s;
#define songs_new          tree32x64_new
#define songs_add_multiple tree32x64_add_multiple // TODO: ACCEPT MULTIPLE!!!
#define songs_add_single   tree32x64_add_single
#define songs_lookup       tree32x64_lookup
#define songs_lookup_add   tree32x64_lookup_add

// DISKS
typedef tree8x64_hash_t  disk_hash_t;
typedef tree8x64_s       disk_tree_s;
#define disks_new          tree8x64_new
#define disks_add_multiple tree8x64_add_multiple
#define disks_add_single   tree8x64_add_single
#define disks_lookup       tree8x64_lookup
#define disks_lookup_add   tree8x64_lookup_add

// PARTITIONS
typedef tree8x64_hash_t  part_hash_t;
typedef tree8x64_s       part_tree_s;
#define parts_new          tree8x64_new
#define parts_add_multiple tree8x64_add_multiple
#define parts_add_single   tree8x64_add_single
#define parts_lookup       tree8x64_lookup
#define parts_lookup_add   tree8x64_lookup_add

// TYPES
typedef tree8x64_hash_t  type_hash_t;
typedef tree8x64_s       type_tree_s;
#define types_new          tree8x64_new
#define types_add_multiple tree8x64_add_multiple
#define types_add_single   tree8x64_add_single
#define types_lookup       tree8x64_lookup
#define types_lookup_add   tree8x64_lookup_add

typedef struct song_s {
    u64 start;
    u64 size:48,
        disk:8,
        type:8;
} song_s;

static inline off_t song_end (const song_s* const song) {

    return song->start + song->size;
}

//
#define SONG_HASH(i) (db->songsTree[i+1].hash[0])

// DATABASE
#define MZK_MAGIC 0x57494c4552494b41ULL
#define MZK_VERSION 1
#define MZK_REVISION 0

// DEIXA UM PARA O \0
#define MZK_TYPE_LEN 7

typedef struct db_verify_s {
    song_tree_s songTree;
    song_hash_t songHash;
    song_s      song;
    u8 disksN;
    u8 typesN;
    u8 songsN;
} db_verify_s;

typedef struct db_s {
    u64 magic;
    u32 version;
    u32 revision;
    u64 checksum;
    size_t size; // OF THIS ENTIRE FILE
    time_t time;
    u16 typesN;
    u16 disksN;
    u32 disks[DISKS_N][2]; // MAJOR, MINOR
    char types[TYPES_N][MZK_TYPE_LEN];
    song_tree_s songsTree[SONGS_N + 1];
    song_s songs[SONGS_N];
    db_verify_s verify;
} db_s;

static const db_verify_s verify = {
    .songTree = { .count = 0, .size = 1, .childs = { 0, 1 }, },
    .songHash = 6,
    .song = {
        .disk = 0x13,
        .start = 0x546450465,
        .size = 0x3423432,
        .type = 0x45,
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

static int fds[DISKS_N];
static db_s* db;

// TODO: ON EXIT: unmap disks
static inline char* code_to_str (u64 code, char* str) {

    // ASSERT: code != 0
    // ASSERT; code <= 0xBA5CA5392CB03FFULL
    static char alphabet[] = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";

    while (code) {
        *str++ = alphabet[code % 62];
        code /= 62;
    }

    *str = '\0';

    return str;
}

static inline u64 fpath_type (const char* fpath) {

    const char* start = fpath;

    while (*fpath) {
        if (*fpath == '.')
            start = fpath;
        fpath++;
    }

    const size_t len = fpath - start;

    // JA POE O \0
    u64 type = 0;

    // PRECISARA DE UM \0
    // NOTE: CONSIDERAMOS ARQUIVOS COM EXTENSAO NULA INVALIDOS COMO EXTENSAO GRANDE
    if (len < sizeof(u64))
        memcpy(&type, start, len);
// TODO: FIXME: SE FOR BIG ENDIAN, PRECISA DAR UM SWAP64
    return type;
}

static inline u64 fname_code (const char* fname) {

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
            return 0;

        // 62^10
        if (code >= 0x0BA5CA5392CB0400ULL)
            return 0;

        code += mult * c;
        mult *= 10 + 26 + 26;
    }

    mzk_dbg("fname_code() -> 0x%016llX", (uintll)code);
    return code;
}

static inline u64 fpath_code (const char* fpath) {

    mzk_dbg("fpath_code(%s)", fpath);
    const char* fname = fpath;

    while (*fpath)
        if (*fpath++ == '/')
            fname = fpath;

    mzk_dbg("fpath_code() -> fname_code(%s)", fname);
    return fname_code(fname);
}

// OBS: SO SUPORTA mzk:// E NAO mzk:///////
static inline u64 fschema_code (const char* fpath) {

    if (strncasecmp("mzk://", fpath, 6))
        return 0;

    return fname_code(fpath + 6);
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
        mzk_err("LOAD: FAILED TO OPEN/CREATE DATABASE: %s", strerror(errno));
        goto _err_unmap;
    }

    if (read(fd, db, sizeof(*db)) != sizeof(*db)) {
        mzk_err("LOAD: FAILED TO READ DATABASE: %s", strerror(errno));
        goto _err_close;
    }

    mzk_log("LOAD: DISKS: %zu", (size_t)db->disksN);
    mzk_log("LOAD: TYPES: %zu", (size_t)db->typesN);
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
        mzk_warn("LOAD: RELEASE MISMATCH: %u", db->revision);

    if (memcmp(&db->verify, &verify, sizeof(verify))) {
        mzk_err("LOAD: DATABASE VERIFICATION MISMATCH");
        goto _err_close;
    }

    if (db->disksN >= DISKS_N) {
        mzk_err("LOAD: BAD DISKS COUNT");
        goto _err_close;
    }

    if (db->typesN >= TYPES_N) {
        mzk_err("LOAD: BAD TYPES COUNT");
        goto _err_close;
    }

    if (db->songsTree->size  != SONGS_N
     || db->songsTree->count >= SONGS_N) {
        mzk_err("LOAD: BAD SONGS COUNT/SIZE");
        goto _err_close;
    }

    // VERIFY SONGS
    foreach (size_t, i, db->songsTree->count) {

        song_s* const song = &db->songs[i];

        if (song->disk >= db->disksN)
            mzk_err("SONG HAS INVALID DISK");
        if (song->start == 0)
            mzk_err("SONG HAS INVALID START");
        if (song->size >= SONG_SIZE_MAX)
            mzk_err("SONG HAS INVALID SIZE");
        if (song->type >= db->typesN)
            mzk_err("SONG HAS INVALID TYPE");
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
