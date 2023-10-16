/*

*/

#define FUSE_USE_VERSION 30

#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>
#include <time.h>
#include <errno.h>
#include <fuse.h>

typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;

typedef struct stat stat_s;

typedef struct file_entry_s file_entry_s;

struct file_entry_s {
    u64 offset;
    u64 size;
    u64 ctime; // CREATION TIME
    u64 mtime; // MODIFICATION TIME
    u16 flags;
    u16 uid;
    u16 gid;
    u16 mode;
    char name[88];
};

static uint myFilesN = 4;

static file_entry_s myFiles[] = {
    { 0 }, // ROOT
    { 1000, 65536, 160000000, 165000000, 0, 0, 0, 0644, "teste" },
    { 1000, 45435, 160000000, 165000000, 0, 0, 0, 0644, "teste2" },
    { 1000, 45545645, 160000000, 165000000, 0, 0, 0, 0644, "teste3" },
};

char dir_list[ 256 ][ 256 ];
int curr_dir_idx = -1;

char files_list[ 256 ][ 256 ];
int curr_file_idx = -1;

char files_content[ 256 ][ 256 ];
int curr_file_content_idx = -1;

static int is_dir( const char *path ) {

    path++; // Eliminating "/" in the path

    for ( int curr_idx = 0; curr_idx <= curr_dir_idx; curr_idx++ )
        if ( strcmp( path, dir_list[ curr_idx ] ) == 0 )
            return 1;

    return 0;
}

static void add_file( const char *filename ) {

    curr_file_idx++;
    strcpy( files_list[ curr_file_idx ], filename );

    curr_file_content_idx++;
    strcpy( files_content[ curr_file_content_idx ], "" );
}

static int is_file( const char *path ) {

    path++; // Eliminating "/" in the path

    for ( int curr_idx = 0; curr_idx <= curr_file_idx; curr_idx++ )
        if ( strcmp( path, files_list[ curr_idx ] ) == 0 )
            return 1;

    return 0;
}

static int get_file_index( const char *path ) {

    path++; // Eliminating "/" in the path

    for ( int curr_idx = 0; curr_idx <= curr_file_idx; curr_idx++ )
        if ( strcmp( path, files_list[ curr_idx ] ) == 0 )
            return curr_idx;

    return -1;
}

static int do_getattr (const char *path, struct stat *st) {

    printf("GETATTR |%s|\n", path);

    // ROOT
    if (strcmp(path, "/") == 0) {
        st->st_ino = 0;
        st->st_uid = 0;
        st->st_gid = 0;
        st->st_atime = 0;
        st->st_mtime = 0;
        st->st_mode = S_IFDIR | 0755;
        st->st_nlink = 2; // Why "two" hardlinks instead of "one"? The answer is here: http://unix.stackexchange.com/a/101536
        return 0;
    }

    // SKIP THE "/"
    path += 1;

    // LOOKUP
    for (int i = 1; i != myFilesN; i++) {

        file_entry_s* const mf = &myFiles[i];

        if (strcmp(mf->name, path) == 0) {
            st->st_ino    = i;
            st->st_uid    = mf->uid;
            st->st_gid    = mf->gid;
            st->st_atime  = mf->mtime; // TODO: FIXME: CREATION TIME?
            st->st_mtime  = mf->mtime;
            st->st_ctime  = mf->mtime;
            st->st_mode   = mf->mode | S_IFREG;
            st->st_size   = mf->size;
            st->st_nlink  = 1;
			st->st_blksize = 65536;
			st->st_blocks = 0; // TODO:
            return 0;
        }
    }

    return -ENOENT;
}

static int do_opendir (const char* path, struct fuse_file_info* fi) {

    if (strcmp(path, "/" ) != 0)
        return -1;

    fi->fh = 0;

    return 0;
}

static int do_readdir( const char* path, void *buffer, fuse_fill_dir_t filler, off_t offset, struct fuse_file_info* fi) {

    if (fi->fh == 0) {

        filler(buffer, ".",  NULL, 0);
        filler(buffer, "..", NULL, 0);

        for (int i = 1; i != myFilesN; i++) {

            const file_entry_s* const mf = &myFiles[i];

            const stat_s stat = {
                .st_ino    = i,
                .st_uid    = mf->uid,
                .st_gid    = mf->gid,
                .st_atime  = mf->mtime, // TODO: FIXME: CREATION TIME?
                .st_mtime  = mf->mtime,
                .st_ctime  = mf->mtime,
                .st_mode   = mf->mode | S_IFREG,
                .st_size   = mf->size,
				.st_blksize = 65536,
				.st_blocks = 0, // TODO:
                .st_nlink  = 1,
            };

            filler(buffer, mf->name, &stat, 0);
        }

        return 0;
    }

    return -1;
}

static int do_read( const char *path, char *buffer, size_t size, off_t offset, struct fuse_file_info *fi ) {

    int file_idx = get_file_index( path );

    if ( file_idx == -1 )
        return -1;

    char *content = files_content[ file_idx ];

    memcpy( buffer, content + offset, size );

    return strlen( content ) - offset;
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

static int do_write (const char *path, const char *buffer, size_t size, off_t offset, struct fuse_file_info *info) {

    (void)path;
    (void)buffer;
    (void)size;
    (void)offset;
    (void)info;

    return -EROFS;
}

static struct fuse_operations operations = {
    .getattr    = do_getattr,
    .opendir    = do_opendir,
    .readdir    = do_readdir,
    .read       = do_read,
    .mkdir      = do_mkdir,
    .mknod      = do_mknod,
    .write      = do_write,
};

int main( int argc, char *argv[] ) {

    return fuse_main( argc, argv, &operations, NULL );
}
