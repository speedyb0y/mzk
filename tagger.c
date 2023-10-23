/*


*/

#define _GNU_SOURCE

#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>

#define BUFFER_SIZE (512*1024)

#define FD_TAGS 200

static char* fcode (char* fpath) {

    char* start = fpath;

    while (1) {

        switch (*fpath) {
            case '/':
                start = ++fpath;
                break;
            case '.':
                *fpath++ = '\0';
                break;
            case '\0':
                return start;
            default:
                fpath++;
        }
    }
}

#define ARG_CMD   0
#define ARG_OP    1
#define ARG_SONG  2

int main (int argsN, char* args[]) {

    // TEM QUE TER O COMANDO
    if (argsN < (ARG_OP + 1))
        return 1;

    // TEM QUE SER ADICIONAR OU REMOVER
    if (strcmp(args[ARG_OP], "+")
     && strcmp(args[ARG_OP], "-"))
        return 1;

    // TODO: USAR A SONG CURRENT PLAYING
    if (argsN < (ARG_SONG + 1))
        return 1;

    int fds[2];

    close(STDIN_FILENO);
    close(STDOUT_FILENO);

    if (pipe(fds)
    || fds[STDIN_FILENO ] != STDIN_FILENO
    || fds[STDOUT_FILENO] != STDOUT_FILENO)
        return 1;

    //
    if (fork() == 0) {
        close(fds[STDIN_FILENO]);
        if (open("/home/speedyb0y/tags", O_RDONLY) != STDIN_FILENO)
            return 1;
        setenv("BEMENU_SCALE", "3", 1);
        char* args[] = { "bemenu", "--no-cursor", "--no-touch", "--no-overlap", "--fixed-height", "--no-exec", "--wrap", "--list", "31", NULL };
        execve("/bin/bemenu", args, environ);
        return 1;
    }

    //
    //const int fd = open("/tmp/tags", O_WRONLY | O_CREAT | O_APPEND, 0644);

    //if (fd == -1)
        //return 1;

    char buffer[BUFFER_SIZE];

    char* end = buffer;
    char* lmt = buffer + BUFFER_SIZE;

    // THE OPERATION
    *end++ = args[ARG_OP][0];
    *end++ = ' ';

    // OBS: SE RETORNAR -1 VAI DAR OVERLOW
    end += read(STDIN_FILENO, end, lmt - end);

    // TIRA O \n
    if (--end >= lmt)
        return 1;

    for (int i = ARG_SONG; i != argsN; i++) {
        const char* const name = fcode(args[i]);
        const size_t len = strlen(name);
        if (end + len >= lmt)
            return 1;
       *end++ = ' ';
        end = memcpy(end, name, len) + len;
    }

    *end++ = '\n';

    //
    write(FD_TAGS, buffer, end - buffer);

    return 0;
}
