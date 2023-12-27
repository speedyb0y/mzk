#!/bin/dash
#
# dcopy - COPY FILES IN DIRECT (AND SYNC) I/O MODE
#
# Usage:
#
#       DCOPY_DIR=/mnt/sda2/CONVERTED DCOPY_TEMP=transfer.tmp DCOPY_BLOCK=4096 DCOPY_BUFFER=1GB dcopy FILE1 FILE2 FILE3 ... FILE_N
#

set -e
set -u

TEMP=${DCOPY_TEMP}
BUFFER=${DCOPY_BUFFER}
BLOCK=${DCOPY_BLOCK}
DIR=${DCOPY_DIR}

if [ ! -d ${DIR} ] ; then
    echo ${DIR} DIR DOES NOT EXIST
    exit 1
fi

TEMP=${DIR}/${TEMP}

if [ -e ${TEMP} ] ; then
    echo ${TEMP} TEMP ALREADY EXIST
    exit 1
fi

for ORIG in "${@}" ; do

    DEST=${DIR}/$(basename -- "${ORIG}")

    if [ ! -f "${ORIG}" ] ; then
        echo ${ORIG} NOT A FILE
        continue
    fi

    if [ -e "${DEST}" ] ; then
        : ${DEST} DEST ALREADY EXIST
        continue
    fi

    if [ -e "${TEMP}" ] ; then
        echo ${TEMP} TEMP ALREADY EXIST
        exit 1
    fi

    if ! ORIGINAL_SIZE=$(du --bytes -- "${ORIG}" | awk '{print $1}') ; then
        echo ${ORIG} COULD NOT GET SIZE
        continue
    fi

    if [ ${ORIGINAL_SIZE} = 0 ] ; then
        : ${ORIG} EMPTY
        continue
    fi

    ROUNDED_SIZE=${ORIGINAL_SIZE}
    ROUNDED_SIZE=$((ROUNDED_SIZE+BLOCK-1))
    ROUNDED_SIZE=$((ROUNDED_SIZE/BLOCK))
    ROUNDED_SIZE=$((ROUNDED_SIZE*BLOCK))

    if [ ${ORIGINAL_SIZE} != ${ROUNDED_SIZE} ] ; then
        if ! fallocate -l ${ROUNDED_SIZE} -- "${ORIG}" ; then
            echo ${ORIG} COULD NOT INCREASE
            continue
        fi
    fi

    if ! fallocate -l ${ROUNDED_SIZE} -- "${TEMP}" ; then
        echo ${TEMP} COULD NOT CREATE/ALLOCATE
        continue
    fi

    if ! dd if="${ORIG}" iflag=direct bs=${BUFFER} of="${TEMP}" conv=nocreat,notrunc,fsync oflag=direct,sync,noatime,nofollow status=none ; then
        echo ${ORIG} '=>' ${TEMP} COPY FAILED
    fi

    if [ ${ORIGINAL_SIZE} != ${ROUNDED_SIZE} ] ; then
        if ! truncate -s ${ORIGINAL_SIZE} -- "${ORIG}" ; then
            echo ${ORIG} COULD NOT RESTORE SIZE
        fi
        if ! truncate -s ${ORIGINAL_SIZE} -- "${TEMP}" ; then
            echo ${TEMP} COULD NOT TRUNCATE TO ORIGINAL SIZE
            continue
        fi
    fi

    if ! mv -n -- "${TEMP}" "${DEST}" ; then
        echo ${TEMP} '=>' ${DEST} COULD NOT RENAME TEMP TO DEST
        rm -f -- "${TEMP}" || :
    fi

done

# ARQUIVOS NESTE DIRETORIO QUE NAO ESTAO IGUAIS AO TAMANHO NA LISTA du --bytes ORIGINAL
# ( while read s f in ; do [ -e ${f} ] && [ $(du --bytes ${f} | awk '{print $1}') != ${s} ] && echo ${f} ; done ) < /LISTA
# PYTHON WAY
# import os ; ls = set(os.listdir('.')) ; [f for s, f in [l.split() for l in open('/LISTA').read().split('\n') if l] if f in ls and int(s) != os.stat(f).st_size]

#
# mv -n -- $(grep -E ':\s*OK$' /tmp/OK | awk -F : '{print $1}' ) ../copiados/

#
# for x in * ; do (soxi ${x} | grep -q "^XID=${x}$") || mv -n -- ${x} bad/  ; done
