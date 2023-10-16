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

#define loop while (1)
#define elif else if

typedef   signed           int   sint;
typedef unsigned           int   uint;
typedef          long long int  intll;
typedef   signed long long int sintll;
typedef unsigned long long int uintll;

typedef int8_t  i8;
typedef int16_t i16;
typedef int32_t i32;
typedef int64_t i64;

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;

typedef i16 s16;
typedef i32 s24;
typedef i32 s32;

#define S16_MAX INT16_MAX
#define S16_MIN INT16_MIN

#define S24_MAX   8388607
#define S24_MIN (-8388608)

#define S32_MAX INT32_MAX
#define S32_MIN INT32_MIN

static inline s16 S16_CAP (i64 v) {

    return (s16) (
        v > S16_MAX ? S16_MAX :
        v < S16_MIN ? S16_MIN :
        v
    );
}

static inline s24 S24_CAP (i64 v) {

    return (s24) (
        v > S24_MAX ? S24_MAX :
        v < S24_MIN ? S24_MIN :
        v
    );
}

static inline s32 S32_CAP (i64 v) {

    return (s32) (
        v > S32_MAX ? S32_MAX :
        v < S32_MIN ? S32_MIN :
        v
    );
}

static inline i64 channels_v (const s32* const read, const uint chns) {

    i64 b = 0; // BASE
    i64 s = 0; // SALTO

    for (size_t C = 0; C != chns; C++) { b += read[C];     } b /= chns;
    for (size_t C = 0; C != chns; C++) { s += read[C] - b; } s /= chns;

    return b + s;
}

int main (int argsN, const char* args[]) {

    if (argsN != 4) {

        return 1;
    }

    const size_t samplesKnown = atoi(args[1]); // SAMPLES
    const uint chns = atoi(args[2]); // CHANNELS
    const int fd = open(args[3], O_RDONLY | O_RDWR);

    if (fd == -1) {
        fprintf(stderr, "ERROR: FAILED TO OPEN FILE: %d - %s\n", errno, strerror(errno));
        return 1;
    }

    struct stat st = { 0 };

    if (fstat(fd, &st)) {
        fprintf(stderr, "ERROR: FAILED TO STAT FILE: %d - %s\n", errno, strerror(errno));
        return 1;
    }

    const size_t size = st.st_size;
    const size_t points = size / sizeof(s32);
    const size_t samples = points / chns;

    if (size % points) {
        fprintf(stderr, "ERROR: BAD FILE SIZE\n");
        return 1;
    }

    if (samples != samplesKnown) {
        fprintf(stderr, "ERROR: EXPECTED SAMPLES %llu, HAS %llu\n", (uintll)samplesKnown, (uintll)samples);
        return 1;
    }

    // PARA QUE POSSA MAPEAR
    // PARA QUE POSSA HUGE PAGE
    if (0) {
		if (ftruncate(fd, size + 2*1024*1024)) {
			fprintf(stderr, "ERROR: FAILED TO TRUNCATE FILE: %d - %s\n", errno, strerror(errno));
			return 1;
		}
	}

    void* const buff = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);

    if (buff == NULL) {
        fprintf(stderr, "ERROR: FAILED TO MAP FILE: %d - %s\n", errno, strerror(errno));
        return 1;
    }

    if (madvise(buff, size, MADV_SEQUENTIAL | MADV_WILLNEED)) {
        fprintf(stderr, "ERROR: MADVISE FAILED: %d - %s\n", errno, strerror(errno));
        return 1;
    }

    size_t cdiverg = 0; // QUANTOS SAMPLES TIVERAM DIVERGENCIAS SIGNIFICATIVAS ENTRE OS CANAIS
    size_t c24 = 0; // QUANTOS PONTOS SAO >= 24-BIT
    size_t c32 = 0; // QUANTOS PONTOS SAO >= 32-BIT

    s32 min  = 0; // MENOR PONTO
    s32 max  = 0; // MAIOR PONTO
    i64 A  = 0; // POINTS AVERAGE
    i64 AL = 0; // POINTS AVERAGE LOW
    i64 AH = 0; // POINTS AVERAGE HIGH
    i64 WH = 0; // ACUMULADOR DE PONDERACAO, PARA DEPOIS DIVIDIR POR ESSE TOTAL
    i64 WL = 0;

    const s32* raw = buff;

    fprintf(stderr,
		"POINTS: %lld\n"
		"SAMPLES: %lld\n"
		,
		(intll)points,
		(intll)samples
	);

    // POINTS AVERAGE
    for (size_t P = 0; P != points; P++) {

        const s32 p = raw[P];

        if (min > p) min = p;
        if (max < p) max = p;

        c32 += ! (S24_MIN <= p && p <= S24_MAX);
        c24 += ! (S16_MIN <= p && p <= S16_MAX);

		A += p;
    }

    A /= points; // TODO: ISSO É O SUFICIENTE PARA DESCOBRIR  OPONTO MEDIO NO GRAFICO???

    fprintf(stderr,
		"POINTS AVERAGE: %lld\n"
		"MIN %d\n"
		"MAX %d\n"
		"C32 %llu\n"
		"C24 %llu\n"
		,
		(intll)A,
		min,
		max,
		(uintll)c32,
		(uintll)c24
	);

    // POINTS AVERAGE LOW/HIGH
    for (size_t P = 0; P != points; P++) {

        const i64 p = raw[P];

        i64 d = p - A;

        if (0 <= d) {
                  d *= d;
            WH += d;
            AH += d * p;
            printf("??????????????\n");
            return 1;
        } else {
                  d *= -1; // AQUI JA VIRA POSITIVO se dermos ^2
            WL += d;
            AL += d * p;
        }
    }

	fprintf(stderr,
		"AL %lld\n"
		"AH %lld\n"
		"WL %lld\n"
		"WH %lld\n"
		,
		(intll)AL,
		(intll)AH,
		(intll)WL,
		(intll)WH
	);
	
    AL /= WL;
    AH /= WH;

    // POINTS RANGE AVERAGE-LOW <-> AVERAGE-HIGH
    const i64 HL = AH - AL;

    if (HL < 128) {
        fprintf(stderr, "ERROR: SILENT???\n");
        return 1;
    }

    { // COUNT DIVERGENCES BETWEEN CHANNELS IN EACH SAMPLE
        const s32* pos = raw; size_t P = 0;

        while (P != points) {

            i64 avg = 0; // AVG OF CHANNELS
            i64 min = 0; // MIN CHANNEL
            i64 max = 0; // MAX CHANNEL

            // AVG, MIN, MAX
            do { const i64 P = *pos++;

                if (min > P) min = P;
                if (max < P) max = P;

                avg += P;

            } while (++P % chns);

            avg /= chns;

            const i64 diff = max - min;

            if (diff)
                cdiverg += // CONSIDERA COMO UMA DIVERGENCIA,
                    (avg && 0.005 <= (diff / avg)) || // SEJA DO PONTO DE VISTA DA MEDIA DENTRO DO SAMPLE
                    (HL  && 0.010 <= (diff / HL)) // OU DO RANGE GERAL DO ARQUIVO
                ;
        }
    }

    // DECIDE QUANTOS BITS PASSARA A USAR
    const uint bitsNew =
        c32 >= (0.008*points) ? 32 :
        c24 >= (0.002*points) ? 24 :
                                16
    ;

    // SE A DIVERGENCIA NAO FOR MUITO ALTA, TRANSFORMA EM UM CANAL SO
    const uint chnsNew = cdiverg >= (0.01*samples) ? chns : 1;

    if (chnsNew == chns) {

        if (bitsNew == 32) {

            fprintf(stderr, "NO UNIFY, 32\n");

        } elif (bitsNew == 24) {

            fprintf(stderr, "NO UNIFY, 24\n");

            s24* pos = buff;

            for (size_t P = 0; P != points; P++)
                *pos++ = S24_CAP(raw[P]);

        } else {

            fprintf(stderr, "NO UNIFY, 16\n");

            s16* pos = buff;

            for (size_t P = 0; P != points; P++)
                *pos++ = S16_CAP(raw[P]);
        }

    } elif (bitsNew == 32) {

        fprintf(stderr, "UNIFY, 32\n");

        s32* pos = buff;

        for (size_t P = 0; P != points; P += chns)
            *pos++ = S32_CAP(channels_v(&raw[P], chns));

    } elif (bitsNew == 24) {

        fprintf(stderr, "UNIFY, 24\n");

        s24* pos = buff;

        for (size_t P = 0; P != points; P += chns)
            *pos++ = S24_CAP(channels_v(&raw[P], chns));

    } else {

        fprintf(stderr, "UNIFY, 16\n");

        s16* pos = buff;

        for (size_t P = 0; P != points; P += chns)
            *pos++ = S16_CAP(channels_v(&raw[P], chns));
    }

    const size_t sizeNew = samples * chnsNew * (bitsNew == 16 ? sizeof(s16) : sizeof(s24));

    if (msync(buff, sizeNew, MS_SYNC)) {
        fprintf(stderr, "ERROR: FAILED TO MSYNC: %d - %s\n", errno, strerror(errno));
        return 1;
    }

    //
    if (munmap(buff, size)) {
        fprintf(stderr, "ERROR: FAILED TO UNMAP INPUT: %d - %s\n", errno, strerror(errno));
        return 1;
    }

    if (ftruncate(fd, sizeNew)) {
        fprintf(stderr, "ERROR: FAILED TO TRUNCATE: %d - %s\n", errno, strerror(errno));
        return 1;
    }

    //
    close(fd);

    //
    printf("%u %u %u %lld %lld %lld\n",
        (uint)sizeNew,
        (uint)bitsNew,
        (uint)chnsNew,
        (intll)A,
        (intll)min,
        (intll)max
    );

    return 0;
}
