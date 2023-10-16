if HAVE_VFS_MZK
pkglib_LTLIBRARIES = vfs_mzk.la
vfs_mzk_la_SOURCES = vfs_mzk.c

vfs_mzk_la_LDFLAGS = -module -avoid-version

vfs_mzk_la_LIBADD = $(LDADD)
vfs_mzk_la_CFLAGS = $(CFLAGS) -std=c99 -I@top_srcdir@/include
endif
