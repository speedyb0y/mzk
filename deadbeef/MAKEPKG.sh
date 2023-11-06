# Maintainer: Fabio 'Lolix' Loli <fabio.loli@disroot.org> -> https://github.com/FabioLolix
# Contributor: Lukas Fleischer <lfleischer@archlinux.org>
# Contributor: Alexey Yakovenko <waker@users.sourceforge.net>

# (cd /tmp/x && (rm -Rf /tmp/x/{src,pkg} || : ) && cat /home/speedyb0y/MUZIK/DEADBEEF.sh > PKGBUILD && makepkg -f)

pkgname=deadbeef
pkgver=1.9.6
pkgrel=1
pkgdesc="Modular GTK audio player for GNU/Linux"
arch=(x86_64 i686 pentium4 arm armv6h armv7h aarch64)
url="https://deadbeef.sourceforge.io/"
license=(GPL2 LGPL2.1 ZLIB)
depends=(gtk3 alsa-lib jansson libdispatch)

makedepends=(
    libvorbis
    #libmad
    #flac
    #curl
    #imlib2
    #wavpack
    #libsndfile
    #libcdio
    #libcddb
    #libx11
    #faad2
    zlib
    intltool
    libpipewire
    #libpulse
    #libzip
    libsamplerate
    clang
    yasm
    #ffmpeg
    opusfile
    #mpg123
)

optdepends=(
    #'alsa-oss: for OSS output plugin'
    #'cdparanoia: for cd audio plugin'
    #'curl: for last.fm, vfs_curl (shoutcast/icecast), artwork plugins'
    #'dbus: for notification daemon support (OSD current song notifications)'
    #'faad2: for AAC plugin'
    #'ffmpeg: for ffmpeg plugin'
    #'flac: for flac plugin'
    #'imlib2: for artwork plugin'
    #'libcddb: for cd audio plugin'
    #'libcdio: for cd audio plugin'
    #'libice: optional dependency for gtkui session client support'
    #'libmad: for mp3 plugin (mpeg1,2 layers1,2,3)'
    'libogg: for ogg vorbis plugin'
    'libpipewire: for pipewire plugin'
    'libsamplerate: for dsp_libsrc plugin (resampler)'
    'libsm: optional dependency for gtkui session client support'
    #'libsndfile: for sndfile plugin'
    'libvorbis: for ogg vorbis plugin'
    #'libx11: for global hotkeys plugin'
    #'libzip: for vfs_zip plugin'
    #'mpg123: for MP1/MP2/MP3 playback'
    'opusfile: for opus plugin'
    #'pulseaudio: for PulseAudio output plugin'
    #'wavpack: for wavpack plugin'
    'yasm: required to build assembly portions of ffap plugin'
    #'zlib: for Audio Overload plugin (psf, psf2, etc), GME (for vgz)'
)

conflicts=(deadbeef-pipewire-plugin-git)

SDIR=deadbeef-${pkgver}

for O in -f{,R} ; do
    rm ${O} -- \
        ${SDIR} \
        ${SDIR}.tar \
        ${SDIR}.tar.zst
done

git clone --depth 1 https://github.com/speedyb0y/deadbeef.git -b xmzk deadbeef-${pkgver}

rm -f  ${SDIR}/.git || :
rm -fR ${SDIR}/.git

tar -c -f ${SDIR}.tar ${SDIR}

rm -fR ${SDIR}

source=(${SDIR}.tar)
sha512sums=($(sha512sum ${SDIR}.tar | awk '{print $1}'))

CONFIGURE_OPTS=(
    --prefix=/usr
    --disable-{adplug,wildmidi}
    --disable-mms
    --disable-notify # NOTIFICATION-DAEMON SUPPORT
    --disable-{ffmpeg,libmad,libmpg123,sndfile} # !!!!!!!!!
    --disable-rgscanner # plugin for ReplayGain scanner support
    # sc68 -> Atari ST And Amiga player
    # SHN based on xmms-shn
    # TTA
    # libdca (DTS Audio) player plugin
    # SID based on libsidplay2
    # chiptune music player based on GME
    # vtx file player (ay8910/12 emulation)
    # FFAP -> MONKEY'S AUDIO
    # LFM -> LAST FM
    # PSF -> PSF(,QSF,SSF,DSF)
    # Libretro resampler plugin
    --disable-{dca,sid,gme,vtx,tta,psf,sc68}
    --disable-cdda{,-paranoia}
    --disable-{alac,aac,mp3,wma,wavpack,musepack,ffap,shn,flac}
     --enable-{vorbis,opus}
    --disable-gtk2 # GTK2 user interface
     --enable-gtk3 # GTK3 user interface
     --enable-vfs-mzk #zip
    --disable-vfs-curl
    --disable-lfm
    --disable-artwork{,-network}
     --enable-supereq      # equalizer based on Super EQ library by Naoki Shibata
    --disable-m3u
    --disable-nullout
    --disable-{alsa,oss,pulse,coreaudio} # oss output plugin
     --enable-pipewire
     --enable-pltbrowser # playlist browser gui plugin
    --disable-converter # plugin for converting files to any formats
     --enable-src  # High quality samplerate conversion using libsamplerate
    --disable-{libretro,soundtouch,dumb}
  #--enable-mono2stereo
  #--enable-shellexecui #build shellexec GTK UI plugin (default: auto)
  #--enable-abstract-socket #use abstract UNIX socket for IPC (default: disabled)
    #hotkeys: yes - Local and global hotkeys support
    --disable-lfm # last.fm scrobbler
    #nullout: no - NULL output
    #shellexec: yes - shell commands plugin
    #shellexecui: yes - GTK user interface for setting up shellexec plugin
    #stdio: yes - Standard IO plugin
)

build () {

    cd "${srcdir}/${SDIR}"

    export CC=clang CXX=clang++

    rm -f  plugins/vfs_zip || :
    rm -fR plugins/vfs_zip || :

    sed -r -i $(grep -REi vfs_zip . | awk -F : '{print $1}') \
		-e s/VFS_ZIP/VFS_MZK/g \
		-e s/VFS_zip/VFS_mzk/g \
		-e s/vfs_ZIP/vfs_MZK/g \
		-e s/vfs_zip/vfs_mzk/g \
		-e s/vfs-zip/vfs-mzk/g \
		-e s/vfs-ZIP/vfs-MZK/g \
		-e s/VFS-zip/VFS-mzk/g

    cp -Ra ${HOME}/MUZIK/deadbeef plugins/vfs_mzk

    ln -s -f -n ${HOME}/MUZIK/deadbeef/*.c plugins/vfs_mzk/

    for sc in autogen.sh configure ; do
        ./${sc} ${CONFIGURE_OPTS[*]}
    done

    make
}

package() {

  cd "${srcdir}/${SDIR}"

  make DESTDIR="${pkgdir}" install

  install -D COPYING -t "${pkgdir}/usr/share/licenses/${pkgname}"
}
