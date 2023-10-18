/* */

#include "base.c"
#include "util.c"
#include "tree.c"
#include "core.c"

// DEADBEEF
#include <deadbeef/deadbeef.h>
static DB_functions_t *deadbeef;
static DB_vfs_t plugin;

typedef struct mzk_file_s {
    DB_FILE file;
    u32 id;
    int fd;
    off_t pos; // of the descriptor
    off_t start;
    off_t end;
} mzk_file_s;

//
static const char* scheme_names[] = { "/mnt/MZK", NULL };

static const char** mzk_get_schemes (void) {

    mzk_dbg("GET SCHEMES");

    return scheme_names;
}

static int mzk_is_streaming (void) {

    mzk_dbg("IS STREAMING?");

    return 0;
}

// AFF, ELE RECEBE COMO mzk://path/:arquivo
static DB_FILE* mzk_open (const char* fpath) {

    mzk_dbg("OPEN FILE: PATH %s", fpath);

    // NOTE: IF THE PATH IS NOT VALID THAN ITS CODE WILL BE 0; NO 0 IS REGISTERED
    const size_t sid = songs_lookup(db->songsTree, fpath_code(fpath));   // TODO: USAR O REAL PATH :S

    if (sid >= SONGS_N) {
        mzk_err("OPEN FILE: NOT FOUND");
        errno = ENOENT;
        return NULL;
    }

	const song_s* const song = &db->songs[sid];

    const int fd = fds[song->disk];

    if (fd == -1) {
        mzk_err("OPEN FILE: DISK NOT OPEN");
        errno = ENOENT;
        return NULL;
    }

    mzk_file_s* const file = malloc(sizeof(*file));

    if (file) {

        memset(&file->file, 0, sizeof(file->file));

        file->file.vfs = &plugin;
        file->id       = sid;
        file->fd       = fd;
        file->pos      = song->start;
        file->start    = song->start;
        file->end      = song->start + song->size;
    }

    return (DB_FILE*)file;
}

static void mzk_close (DB_FILE* dfile) {

    free(dfile);
}

static size_t mzk_read (void* buff, size_t size, size_t qnt, DB_FILE* dfile) {

    mzk_file_s* const file = PTR(dfile);

    // QUANTOS OBJETOS TEM DISPONIVEIS
    const size_t tem = (file->end - file->pos) / size;

    // SE PEDIU MAIS DO QUE TEM, VAI DAR SÓ TUDO O QUE TEM
    if (qnt > tem)
        qnt = tem;

    // MARCA ONDE VAI TER QUE PARAR ENTÃO
    size *= qnt;

    off_t pos = file->pos;

    //
    while (size) {

        const ssize_t c = pread(file->fd, buff, size, pos);

		// TODO: fread() does not distinguish between end-of-file and error, and callers must use feof(3) and ferror(3) to determine which occurred.
        if (c <= 0)
            return 0;

        pos  += c;
        buff += c;
        size -= c;
    }

    //
    file->pos = pos;
    return qnt;
}

static int mzk_seek (DB_FILE* dfile, int64_t offset, int whence) {

    mzk_file_s* const file = PTR(dfile);

    off_t pos;

    switch (whence) {
        case SEEK_SET:
            pos = file->start;
            break;
        case SEEK_CUR:
            pos = file->pos;
            break;
        case SEEK_END:
            pos = file->end;
            break;
        default:
            goto _err;
    }

    // APPLY
    pos += offset;

    if (pos >= file->start
     && pos <= file->end) {
        // COMMIT
        file->pos = pos;
        return 0;
    }

_err: // NOTE: ELE PODE ESTAR QUERENDO CRIAR UM HOLE, MAS SOMOS SOMENTE LEITURA
    errno = EINVAL;
    return -1;
}

static int64_t mzk_tell (DB_FILE* dfile) {

    const mzk_file_s* const file = PTR(dfile);

    return file->pos - file->start;
}

static void mzk_rewind (DB_FILE* dfile) {

    mzk_file_s* const file = PTR(dfile);

    file->pos = file->start;
}

static int64_t mzk_getlength (DB_FILE* file) {

    const mzk_file_s* const mzf = PTR(file);

    return mzf->end - mzf->start;
}

// TODO: COLOCAR UMA FLAG NA SONG NA PRIMEIRA REPETICAO EM DIANTE
// E AI NAO RETORNAR AQUI MAIS DE UMA VEZ
static int mzk_scandir (const char *dir, struct dirent ***namelist, int (*selector) (const struct dirent *), int (*cmp) (const struct dirent **, const struct dirent **)) {

    mzk_log("mzk_scandir(%s, %p, %p, %p)",
        dir, namelist, selector, cmp);

    if (!memcmp(dir, "/mnt/MZK", strlen("/mnt/MZK"))) { // TODO: LISTAR SO OS ARQUIVOS DE TAL DIRETORIO
        errno = ENOENT;
        return -1;
    }

    struct dirent** const entries = malloc((db->songsTree->count +1)* sizeof(struct dirent*));

    size_t count = 0;

    foreach (size_t, i, db->songsTree->count) {

        struct dirent entry = { // NOTE: NO "d_namlen"
            .d_fileno = i,
            .d_type = DT_REG,
        };

        // GERA O NOME E COLOCA A EXTENSÃO
        strcpy(code_to_str(TREE_HASHES(db->songsTree, i)[0], entry.d_name),
            (char*)&db->types[db->songs[i].type]
        );

        if (!selector || selector(&entry))
            entries[count++] = memcpy(malloc(sizeof(entry)), &entry, sizeof(entry));
    }

    entries[count] = NULL;

    if (count) {
        if (cmp)
            qsort(entries, count, sizeof(*entries), (void*)cmp);
        *namelist = entries;
    } else { free(entries);
        *namelist = NULL;
    }

    mzk_dbg("mzk_scandir() -> %zu", count);
    return count;
}

#if 0
static int mzk_is_container (const char* fpath) {

    const int ret = strcmp(fpath, "/mnt/MZK") == 0 // TODO: suportar terminando em /
                 || strcmp(fpath, "/mnt/MZK/") == 0
            || strcmp(fpath, "/mnt/MZK/4404874E299B03B97F5326D2B524") == 0
            || strcmp(fpath, "/mnt/MZK/4404874E299B03B97F5326D2B524/") == 0
            || strcmp(fpath, "/mnt/MZK/01D6C4AF20D1B47014806C2620A4") == 0
            || strcmp(fpath, "/mnt/MZK/01D6C4AF20D1B47014806C2620A4/") == 0
            || strcmp(fpath, "/mnt/MZK/40346FB88F5D574206152FCF6D9A") == 0
            || strcmp(fpath, "/mnt/MZK/7A75C38FDAB39D074A16FB6BE530") == 0
            || strcmp(fpath, "/mnt/MZK/9C23EEFB22B586FC5ED6B5B8CC1F") == 0
            || strcmp(fpath, "/mnt/MZK/A724B4A19508C6590471974BA23B") == 0
            || strcmp(fpath, "/mnt/MZK/D460B739D8A696E0A10ADAA1ADE7") == 0
            || strcmp(fpath, "/mnt/MZK/T2B73OCN535NROCUW3LRCK2IKDK2") == 0
            || strcmp(fpath, "/mnt/MZK/05GK2L68OIMPP1RLYFEXO00NUYZF") == 0
    ;

    mzk_log("mzk_is_container(%s) -> %d", fpath, ret);
    return 0;
}

const char* mzk_get_scheme_for_name (const char* fname) {

    mzk_log("mzk_get_scheme_for_name(%s)", fname);

    return "@@@";
}
#endif

static DB_vfs_t plugin = {
    DDB_PLUGIN_SET_API_VERSION
    .plugin.version_major = 1,
    .plugin.version_minor = 0,
    .plugin.type = DB_PLUGIN_VFS,
    .plugin.id = "vfs_mzk",
    .plugin.name = "MZK vfs",
    .plugin.descr = "play files directly from storage devices",
    .plugin.copyright = "left",
    .plugin.website = "http://deadbeef.sf.net",
    .open                = mzk_open,
    .close               = mzk_close,
    .read                = mzk_read,
    .seek                = mzk_seek,
    .tell                = mzk_tell,
    .rewind              = mzk_rewind,
    .getlength           = mzk_getlength,
    .get_schemes         = mzk_get_schemes,
    .is_streaming        = mzk_is_streaming,
    .scandir             = mzk_scandir,
#if 0
    .is_container        = mzk_is_container,
    .get_scheme_for_name = mzk_get_scheme_for_name,
#endif
};

static int callback (DB_playItem_t *it, void *user_data) {

    mzk_dbg("calllback(%p)", user_data);
    return 0;
}

void mzk_thread (void *ctx) {

    sleep(2);

    pipe2(fds, O_DIRECT);

    // writer
    dup2(fds[1], 80);

    while (1) {
        printf("oiii\n...");
        char buff[2048];
        const int sz = read(fds[0], buff, sizeof(buff));

        printf("|..%d.|\n", sz);
        sleep(1);
    }

        sleep(10);


        printf("\n\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n");
        printf("\n\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n");
        printf("\n\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n");
        printf("\n\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n");

    ddb_playlist_t* plt = deadbeef->plt_find_by_name("CONVERTED");

    // VE TODOS OS ARQUIVOS QUE ESTAO NA PLAYLIST ALL
    //   dai os que nao estao, adiciona
    //   reordena

if (plt ){
    // request lock for adding files to playlist
    // returns 0 on success
    // this function may return -1 if it is not possible to add files right now.
    deadbeef->plt_add_files_begin (plt, 10);

    foreach (size_t, i, db->songsTree->count) {
        mzk_log("ADD FILE #%zu", i);
        deadbeef->plt_add_file2 (10, plt, "/mnt/CONVERTED/U8PBvrJFKB.flac", callback, "oiii");
        //deadbeef->plt_add_dir2 (10, plt, "/mnt/ewgewgew", callback, "huahauahua");
        //ddb_playItem_t * (*plt_insert_file2) (int visibility, ddb_playlist_t *playlist, ddb_playItem_t *after, const char *fname, int *pabort, int (*callback)(DB_playItem_t *it, void *user_data), void *user_data);
        //ddb_playItem_t *(*plt_insert_dir2) (int visibility, ddb_playlist_t *plt, ddb_playItem_t *after, const char *dirname, int *pabort, int (*callback)(DB_playItem_t *it, void *user_data), void *user_data);
    }

    deadbeef->plt_add_files_end (plt, 10);
} else {
 printf("viiiiiiiiish\n");
}

    while (1) {

        printf("\n\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n");
        printf("\n\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n");
        printf("\n\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n");
        printf("\n\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n");

        sleep(10);
    }

}

DB_plugin_t* vfs_mzk_load (DB_functions_t *api) {

    if (mzk_load("/home/speedyb0y/.config/deadbeef/mzk.map")) {
        // FAILED
        return NULL;
    }

    deadbeef = api;

    api->thread_start(mzk_thread, "contexto");

    return DB_PLUGIN(&plugin);
}
