#!/bin/bash

set -e
set -u
set -x

GIT_DIR=/tmp/deadbeef-$(date +%s)${$}${RANDOM}${RANDOM}

git clone --depth 1 https://github.com/DeaDBeeF-Player/deadbeef.git ${GIT_DIR}

( set -e

    cd ${GIT_DIR}

    #
    git submodule update --init

    #
    OFFICIAL_COMMIT=$(git rev-parse HEAD)

    #
    for O in -f{,R} ; do
        rm ${O} -- $(find .      \
            -iname .git        -o \
            -iname .gitignore  -o \
            -iname .gitmodules -o \
            -iname .github        \
        ) || :
    done

    if false ; then

        #
        #echo "# deadbeef" >> README.md

        #
        git init
        git config http.postBuffer 524288000
        git config credential.helper store
        git add --all
        git commit -m "$(date +%s) - $(date) - ${OFFICIAL_COMMIT} - INIT"
        git branch -M main
        git remote add origin https://github.com/speedyb0y/deadbeef.git
        git push -u origin main

    else

        # TRANSFORMA NO MEU
        git clone --depth 1 https://github.com/speedyb0y/deadbeef.git MYGIT
        mv MYGIT/.git .
        rm -fR -- MYGIT

        #
        git config http.postBuffer 524288000
        git config credential.helper store
        git add --all
        git commit -m "$(date +%s) - $(date) - ${OFFICIAL_COMMIT}"
        git push
    fi
)

rm -f  -- ${GIT_DIR} || :
rm -fR -- ${GIT_DIR} || :

[ ! -e ${GIT_DIR} ]
