/*

*/

#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/stat.h>
#include <sys/mman.h>

typedef unsigned long long int uintll;

typedef  int32_t i32;
typedef uint32_t u32;

typedef  int64_t i64;
typedef uint64_t u64;

typedef i32 sample_t;

typedef long double flt;

static size_t olen0 (size_t ilen, uint sr, uint n) {

    return ilen / n;
}

#define ABS_DIFF(a, b) ((a) >= (b) ? (a) - (b) : (b) - (a))

static sample_t* resample0 (const sample_t* restrict ipos, size_t ilen, sample_t* restrict opos, size_t olen, uint n) {

    for (size_t c = olen; c ; c--) {

        // MEDIA ARITMETICA
        flt A = 0;

        for (uint c = 0; c != n ; c++)
            A += ipos[c];
        A /= n;

        flt P = A; // MEDIA PONDERADA
        flt W = 1; // PESOS TOTAIS

        for (uint c = 0; c != n ; c++) {

            flt x; // ESTE
            flt w; // PESO DELE

            x = ipos[c];
            //w = 1 - ABS_DIFF(x, A) / A; // DIFERENCA DESTE COM A MEDIA ARITMETICA
            w = ABS_DIFF(ABS_DIFF(x, A), A);
            w *= w;

            W += w;
            P += w * x;
        }

        if (P >= 0.00001
         && W >= 0.00001)
            P /= W;
        else
            P = A;

        //
       *opos = P;

        ipos += n;
        opos += 1;
    }

    return opos;
}

static size_t olen1 (size_t ilen, uint sr, uint n) {

    return ilen / 3;
}

#define SACOGRANDE(a, b) ((a >= b) ? (a / b) : (b / a))

static sample_t* resample1 (const sample_t* restrict ipos, size_t ilen, sample_t* restrict opos, size_t olen, uint n) {

    int y = 1;

    flt M = *ipos;

    for (size_t c = olen; c ; c--) {

        flt A = *ipos++;
        flt B = *ipos++;
        flt C = *ipos++;

        // PREFERENCIA AO DO MEIO
        flt wA = n * 1;
        flt wB = n * 2;
        flt wC = n * 1;

        if (M) {
            wA += n * SACOGRANDE(A, M);
            wB += n * SACOGRANDE(B, M);
            wC += n * SACOGRANDE(C, M);
        }

        // ^2
        wA *= wA;
        wB *= wB;
        wC *= wC;

        M = (
            wA * A +
            wB * B +
            wC * C
        ) / (wA + wB + wC);

        A -= M;
        B -= M;
        C -= M;

        M += (
            (2 - y) * A +
             2      * B +
            (2 + y) * C
        ) / 6;

        *opos++ = M;

        y *= -1;
    }

    return opos;
}

static size_t olen2 (size_t ilen, uint sr, uint n) {

    return ilen / 2;
}

static sample_t* resample2 (const sample_t* restrict ipos, size_t ilen, sample_t* restrict opos, size_t olen, uint n) {

    do {

		flt A = *ipos++;
		flt B = *ipos++;

        *opos++ = (A + B) / 2;
        
    } while ((ilen -= 2) >= 2);

    return opos;
}

static size_t olen3 (size_t ilen, uint sr, uint n) {

    return ilen / 3;
}

static sample_t* resample3 (const sample_t* restrict ipos, size_t ilen, sample_t* restrict opos, size_t olen, uint n) {

    do {

		flt A = *ipos++;
		flt B = *ipos++;
		flt C = *ipos++;

        *opos++ = (
            A * 1 +
            B * 3 +
            C * 1
        ) / 5;
        
    } while ((ilen -= 3) >= 3);

    return opos;
}

#if 0
#define O_SIZE(isize, sr, n) ((isize) / 3)

static size_t resample (const sample_t* restrict ipos, size_t ilen, sample_t* restrict opos, size_t olen, uint n) {

    (void)n;

    int y = 1;

    for (size_t c = olen; c ; c--) {

        flt A = *ipos++;
        flt B = *ipos++;
        flt C = *ipos++;

        flt M = (
            1 * A +
            2 * B +
            1 * C
        ) / 4;

        A -= M;
        B -= M;
        C -= M;

        flt T = (
            (2 - y) * A +
             2      * B +
            (2 + y) * C
        ) / 6;

        T += M;

        *opos++ = M;

        y *= -1;
    }

    return olen;
}
#endif

typedef size_t (*olen_f) (size_t ilen, uint sr, uint n);
typedef sample_t* (*resample_f) (const sample_t* restrict ipos, size_t ilen, sample_t* restrict opos, size_t olen, uint n);

static olen_f olens [] = {
    olen0,
    olen1,
    olen2,
    olen3,
};

static resample_f resamples [] = {
    resample0,
    resample1,
    resample2,
    resample3,
};

int main (int argsN, const char* args[]) {

    if (argsN != 6) {

        return 1;
    }

    const uint f  = atoi(args[1]); // FUNCTION
    const uint n  = atoi(args[2]); // ARGUMENT
    const uint sr = atoi(args[3]); // SAMPLE RATE

    const int ifd = open(args[4], O_RDONLY);
    const int ofd = open(args[5], O_RDWR | O_CREAT | O_EXCL, 0644);

    if (ifd == -1) {
        fprintf(stderr, "FAILED TO OPEN INPUT: %d - %s\n", errno, strerror(errno));
        return 1;
    }

    if (ofd == -1) {
        fprintf(stderr, "FAILED TO OPEN OUTPUT: %d - %s\n", errno, strerror(errno));
        return 1;
    }

    struct stat istat = { 0 };

    if (fstat(ifd, &istat)) {
        fprintf(stderr, "FAILED TO STAT: %d - %s\n", errno, strerror(errno));
        return 1;
    }

    const size_t isize = istat.st_size;
    const size_t osize = olens[f](isize/sizeof(sample_t), sr, n) * sizeof(sample_t);

    if (isize % sizeof(sample_t)) {
        fprintf(stderr, "BAD INPUT SIZE\n");
        return 1;
    }

    //
    if (ftruncate(ofd, osize + (65536 - 1))) {
        fprintf(stderr, "FAILED TO TRUNCATE: %d - %s\n", errno, strerror(errno));
        return 1;
    }

    const sample_t* const ibuff = mmap(NULL, isize, PROT_READ             , MAP_SHARED | MAP_POPULATE, ifd, 0);
          sample_t* const obuff = mmap(NULL, osize, PROT_READ | PROT_WRITE, MAP_SHARED,                ofd, 0);

    if (ibuff == NULL) {
        fprintf(stderr, "FAILED TO MAP INPUT\n");
        return 1;
    }

    if (obuff == NULL) {
        fprintf(stderr, "FAILED TO MAP OUTPUT\n");
        return 1;
    }

    madvise((void*)ibuff, isize, MADV_SEQUENTIAL | MADV_WILLNEED);
    madvise((void*)obuff, osize, MADV_SEQUENTIAL);

    const size_t osizeNew = (void*)resamples[f] (
        ibuff, isize / sizeof(*ibuff),
        obuff, osize / sizeof(*obuff),
        n
    ) - (void*)obuff;

    if (osizeNew % sizeof(*obuff)) {
        fprintf(stderr, "BAD OSIZE NEW: %llu\n", (uintll)osizeNew);
        return 1;
    }
    
    if (osizeNew > osize) {
        fprintf(stderr, "BAD OSIZE NEW TOO BIG: %llu\n", (uintll)osizeNew);
        return 1;
    }

    if (msync(obuff, osizeNew, MS_SYNC)) {
        fprintf(stderr, "FAILED TO MSYNC: %d - %s\n", errno, strerror(errno));
        return 1;
    }

    //
    if (munmap((void*)obuff, osize)) {
        fprintf(stderr, "FAILED TO UNMAP OUTPUT: %d - %s\n", errno, strerror(errno));
        return 1;
    }
    if (munmap((void*)ibuff, isize)) {
        fprintf(stderr, "FAILED TO UNMAP INPUT: %d - %s\n", errno, strerror(errno));
        return 1;
    }

    if (ftruncate(ofd, osizeNew)) {
        fprintf(stderr, "FAILED TO TRUNCATE: %d - %s\n", errno, strerror(errno));
        return 1;
    }

    //
    close(ofd);
    close(ifd);

    printf("%u\n", (uint)((osizeNew * sr) / isize) );

    return 0;
}
