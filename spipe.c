/*

*/

#define _GNU_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>

int main (int argsN, char* args[], char* envp[]) {

    if (argsN < 3)
        return 1;

    const int x = atoi(args[1]);

    int ret = fcntl(STDOUT_FILENO, F_SETPIPE_SZ, x);
    if (ret != x)
        return 1;

    execve(args[2], &args[3], envp);

    return 1;
}
