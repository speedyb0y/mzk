/*

    gcc $(pkg-config --libs --cflags fuse) fs.c
*/

#include "base.c"
#include "util.c"
#include "tree.c"
#include "core.c"

//
#define FUSE_USE_VERSION 30
#include <fuse.h>

typedef struct stat stat_s;

typedef struct fuse_file_info fuse_file_info_s;

static inline size_t get_sid (const char* fpath, fuse_file_info_s* finfo) {

    return finfo ? finfo->fh : strcmp(fpath, "/") ? songs_lookup(db->songsTree, fname_code(fpath + 1)) : SONGS_N;
}

static int do_getattr (const char* fpath, stat_s* st, fuse_file_info_s* finfo) {

    //
    const size_t sid = get_sid(fpath, finfo);

    if (sid > SONGS_N)
        //
        return -ENOENT;
    
    if (sid == SONGS_N) {
        // ROOT
        st->st_mode  = S_IFDIR | 0555;
        st->st_nlink = 2; // Why "two" hardlinks instead of "one"? The answer is here: http://unix.stackexchange.com/a/101536
        st->st_blocks = 1;
    
    } else {
        //
        const song_s* const song = &db->songs[sid];

        st->st_mode    = S_IFREG | 0444;
        st->st_nlink   = 1;
        st->st_size    =  song->size;
        st->st_blocks  = (song->size + 65536 - 1)/65536; // TODO:
    }

    st->st_ino    = sid;
    st->st_dev    = 0;
    st->st_rdev   = 0;
    st->st_uid    = 0;
    st->st_gid    = 0;
    st->st_atime  = 0; // TODO: FIXME: CREATION TIME?
    st->st_mtime  = 0;
    st->st_ctime  = 0;
    st->st_blksize = 65536;    

    return 0;
}

static int do_opendir (const char* fpath, fuse_file_info_s* finfo) {

    if (fpath == NULL)
        return -1;

    while (*fpath == '/')
            fpath++;

    if (*fpath == '\0') {
        finfo->fh = SONGS_N;
        return 0;
    }

    return songs_lookup(db->songsTree, fname_code(fpath)) < SONGS_N ? -ENOTDIR : -ENOENT;
}

static int do_readdir (const char* fpath, void* buffer, fuse_fill_dir_t filler, off_t offset, fuse_file_info_s* finfo) {

    (void)offset;

    const size_t sid = get_sid(fpath, finfo);

    if (sid != SONGS_N)
        return -ENOTDIR;

    filler(buffer, ".",  NULL, 0);
    filler(buffer, "..", NULL, 0);

    foreach (size_t, sid, db->songsTree->count) {

        const song_s* const song = &db->songs[sid];

        const stat_s stat = {
            .st_ino     = sid,
            .st_dev     = 0,
            .st_redev   = 0,
            .st_uid     = 0,
            .st_gid     = 0,
            .st_atime   = 0, // TODO: FIXME: CREATION TIME?
            .st_mtime   = 0,
            .st_ctime   = 0,
            .st_mode    = S_IFREG | 0444,
            .st_size    = song->size,
            .st_nlink   = 1,
            .st_blksize = 65536,
            .st_blocks  = (song->size + 65536 - 1)/65536, // TODO:
        };

        filler(buffer, "NOME DO ARQUIVOOOOOOOOOO", &stat, 0);
    }

    return 0;
}

static int do_mkdir (const char *path, mode_t mode) {

    (void)path;
    (void)mode;

    return -EROFS;
}

static int do_mknod (const char *path, mode_t mode, dev_t rdev) {

    (void)path;
    (void)mode;
    (void)rdev;

    return -EROFS;
}

static int do_write (const char *path, const char *buffer, size_t size, off_t offset, fuse_file_info_s *info) {

    (void)path;
    (void)buffer;
    (void)size;
    (void)offset;
    (void)info;

    return -EROFS;
}

static int do_open (const char* const fpath, fuse_file_info_s* const finfo) {
    
    mzk_dbg("OPEN FILE: PATH %s", fpath);

    // NOTE: IF THE PATH IS NOT VALID THAN ITS CODE WILL BE 0; NO 0 IS REGISTERED
    const size_t sid = songs_lookup(db->songsTree, fpath_code(fpath));   // TODO: USAR O REAL PATH :S

    if (sid >= SONGS_N) {
        mzk_err("OPEN FILE: NOT FOUND");
        return -ENOENT;
    }

    const song_s* const song = &db->songs[sid];

    if (fds[song->disk] == -1) {
        mzk_err("OPEN FILE: DISK NOT OPEN");
        return -ENOENT;
    }

    finfo->fh = sid;

    return 0;
}

static int do_read(const char *fpath, char *buffer, size_t size, off_t offset, fuse_file_info_s *finfo) {

    const size_t sid = get_sid(fpath, finfo);

    if (sid > SONGS_N)
        return -ENOENT;

    // TODO: fh SONGS_N É O ROOT DIR
    if (sid == SONGS_N)
        return -1;
    
    const song_s* const song = &db->songs[sid];

    const int fd = fds[song->disk];
    
    if (fd == -1)
        // DISK NOT OPEN
        return -1; // TODO:

    return -1;
}

static struct fuse_operations operations = {
    .open       = do_open,
    .getattr    = do_getattr,
    .opendir    = do_opendir,
    .readdir    = do_readdir,
    .read       = do_read,
    .mkdir      = do_mkdir,
    .mknod      = do_mknod,
    .write      = do_write,
};

int main(int argc, char *argv[]) {

    if (mzk_load("/home/speedyb0y/.config/deadbeef/mzk.map"))
        // FAILED
        return 1;

    return fuse_main(argc, argv, &operations, NULL);
}
