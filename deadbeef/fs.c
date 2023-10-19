/*

    gcc $(pkg-config --libs --cflags fuse) fs.c
*/

#include "base.c"
#include "util.c"
#include "tree.c"
#include "core.c"

//
#define FUSE_USE_VERSION 29
#include <fuse.h>

typedef struct stat stat_s;

typedef struct fuse_file_info fuse_file_info_s;

#define MZK_BLOCK_SIZE 65536

static inline size_t mzk_get_sid (const char* fpath, fuse_file_info_s* finfo) {

    if (finfo)
        return finfo->fh;

    if (*++fpath == '\0')
        return SID_ROOT;

    return mzk_fname_sid(fpath);
}

static int do_getattr (const char* fpath, stat_s* st, fuse_file_info_s* finfo) {

    //
    const size_t sid = mzk_get_sid(fpath, finfo);

    if (sid == SID_NOT_FOUND)
        //
        return -ENOENT;

    if (sid == SID_ROOT) {
        // ROOT
        st->st_mode   = S_IFDIR | 0555;
        st->st_nlink  = 2; // Why "two" hardlinks instead of "one"? The answer is here: http://unix.stackexchange.com/a/101536
        st->st_blocks = 1;

    } else {
        //
        const song_s* const song = &db->songs[sid];

        st->st_mode    = S_IFREG | 0444;
        st->st_nlink   = 1;
        st->st_size    =  song->size;
        st->st_blocks  = (song->size + MZK_BLOCK_SIZE - 1)/MZK_BLOCK_SIZE; // TODO:
    }

    st->st_ino    = sid;
    st->st_dev    = 0;
    st->st_rdev   = 0;
    st->st_uid    = 0;
    st->st_gid    = 0;
    st->st_atime  = 0; // TODO: FIXME: CREATION TIME?
    st->st_mtime  = 0;
    st->st_ctime  = 0;
    st->st_blksize = MZK_BLOCK_SIZE;

    return 0;
}

static int do_opendir (const char* fpath, fuse_file_info_s* finfo) {

    // DON'T ALLOW TO OPEN FOR WRITING
    if ((finfo->flags & O_WRONLY) == O_WRONLY
     || (finfo->flags & O_RDWR) == O_RDWR)
        return -EROFS;

    const size_t sid = mzk_get_sid(fpath, NULL);

    if (sid == SID_ROOT) {
        // IT IS THE ROOT DIRECTORY
        finfo->fh = SID_ROOT;
        return 0;
    }

    if (sid == SID_NOT_FOUND)
        // IT DOESN'T EXIST
        return -ENOENT;

    // IT EXISTS BUT IS NOT A DIRECTORY
    return -ENOTDIR;
}

static int do_readdir (const char* fpath, void* buffer, fuse_fill_dir_t filler, off_t offset, fuse_file_info_s* finfo) {

    (void)offset;

    const size_t sid = mzk_get_sid(fpath, finfo);

    if (sid == SID_NOT_FOUND)
        return -ENOENT;

    if (sid != SID_ROOT)
        return -ENOTDIR;

    filler(buffer, ".",  NULL, 0);
    filler(buffer, "..", NULL, 0);

    foreach (size_t, sid, db->songsTree->count) {

        const song_s* const song = &db->songs[sid];

        const stat_s stat = {
            .st_ino     = sid,
            .st_dev     = 0,
            .st_rdev    = 0,
            .st_uid     = 0,
            .st_gid     = 0,
            .st_atime   = 0, // TODO: FIXME: CREATION TIME?
            .st_mtime   = 0,
            .st_ctime   = 0,
            .st_mode    = S_IFREG | 0444,
            .st_size    = song->size,
            .st_nlink   = 1,
            .st_blksize = MZK_BLOCK_SIZE,
            .st_blocks  = (song->size + MZK_BLOCK_SIZE - 1)/MZK_BLOCK_SIZE, // TODO:
        };

        char fname[32];

        // GERA O NOME E COLOCA A EXTENSÃO
        code_to_str(fname,
            TREE_HASHES(db->songsTree, sid)[0],
            TREE_HASHES(db->songsTree, sid)[1]
        );

        filler(buffer, fname, &stat, 0);
    }

    return 0;
}

static int do_mkdir (const char *fpath __unused, mode_t mode __unused) {

    return -EROFS;
}

static int do_mknod (const char *fpath __unused, mode_t mode __unused, dev_t rdev __unused) {

    return -EROFS;
}

static int do_unlink (const char *fpath __unused) {

    return -EROFS;
}

static int do_rmdir (const char *fpath __unused) {

    return -EROFS;
}

static int do_rename (const char* fpath __unused, const char* fpath2 __unused) {

    return -EROFS;
}

static int do_link (const char* fpath __unused, const char* fpath2 __unused) {

    return -EROFS;
}

static int do_write (const char* fpath __unused, const char *buffer __unused, size_t size __unused, off_t offset __unused, fuse_file_info_s *info __unused) {

    return -EBADF;
}

static int do_create (const char* fpath __unused, mode_t mode __unused, fuse_file_info_s* const finfo __unused) {

    return -EROFS;
}

static int do_open (const char* fpath, fuse_file_info_s* const finfo) {

    // DON'T ALLOW TO OPEN FOR WRITING
    if ((finfo->flags & O_WRONLY) == O_WRONLY
     || (finfo->flags & O_RDWR) == O_RDWR)
        return -EROFS;

    // NOTE: IF THE PATH IS NOT VALID THAN ITS CODE WILL BE 0; NO 0 IS REGISTERED
    const size_t sid = mzk_get_sid(fpath, NULL);

    if (sid == SID_NOT_FOUND)
        return -ENOENT;

    if (sid != SID_ROOT)
        if (fds[db->songs[sid].disk] == -1)
            return -ENOENT;

    finfo->fh = sid;

    return 0;
}

static int do_read(const char *fpath, char* buff, size_t size, off_t offset, fuse_file_info_s* finfo) {

    const size_t sid = mzk_get_sid(fpath, finfo);

    if (sid == SID_NOT_FOUND)
        return -ENOENT;

    if (sid == SID_ROOT)
        return -EISDIR;

    const song_s* const song = &db->songs[sid];

    const int fd = fds[song->disk];

    if (fd == -1)
        // DISK NOT OPEN
        return -1; // TODO:

    // QUANTOS TEM DISPONIVEIS
    const size_t tem = song->size - offset;

    // SE PEDIU MAIS DO QUE TEM, VAI DAR SÓ TUDO O QUE TEM
    if (size > tem)
        size = tem;

    // ONDE ESTA
    offset += song->start;

    char* const was = buff;

    //
    while (size) {
        const ssize_t c = pread(fd, buff, size, offset);
        if (c == 0)
            break;
        if (c == -1)
            // NOTE: AQUI ESTAMOS PERDENDO QUALQUER COISA QUE TENHA SIDO LIDA, MAS NÃO ME IMPORTO
            return -errno;
        buff   += c;
        offset += c;
        size   -= c;
    }

    //
    return buff - was;
}

static struct fuse_operations operations = {
    .open    = do_open,
    .getattr = (void*)do_getattr,
    .opendir = do_opendir,
    .readdir = do_readdir,
    .read    = do_read,
    .mkdir   = do_mkdir,
    .mknod   = do_mknod,
    .write   = do_write,
    .unlink  = do_unlink,
    .rmdir   = do_rmdir,
    .link    = do_link,
    .rename  = do_rename,
    .create  = do_create,
    //int(*     truncate )(const char *, off_t, struct fuse_file_info *fi)
    //int(*     fallocate )(const char *, int, off_t, off_t, struct fuse_file_info *)
    //int(* symlink) (const char *, const char *)
};

int main(int argc, char *argv[]) {

    if (mzk_load("/home/speedyb0y/.config/deadbeef/mzk.map"))
        // FAILED
        return 1;

    return fuse_main(argc, argv, &operations, NULL);
}
