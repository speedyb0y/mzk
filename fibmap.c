#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <fcntl.h>
#include <linux/fs.h>
#include <linux/fs.h>

int main(int argc, char **argv) {

    if (argc != 2)
        return 1;

    const int fd = open(argv[1], O_RDONLY);

    if (fd <= 0)
        return 1;

    size_t block = 0;
    size_t start = 0;

    if (ioctl(fd, FIGETBSZ, &block)
     || ioctl(fd, FIBMAP,   &start))
         return 1;

    start *= block;

    close(fd);

    printf("%zu\n", start);

    return 0;
}

