#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

# AC_PREREQ(2.59)
AC_INIT([uniset2-testsuite], [2.4])
AM_INIT_AUTOMAKE(AC_PACKAGE_NAME,AC_PACKAGE_VERSION)

#AM_GNU_GETTEXT([external])
#AM_GNU_GETTEXT_VERSION(0.13.1)

AC_CONFIG_HEADER(config.h)

dnl Initialize maintainer mode
AM_MAINTAINER_MODE

dnl Checks for programs.
AC_PROG_INSTALL
AC_PROG_LN_S
AC_PROG_MAKE_SET
AC_PROG_LIBTOOL

# Checks for libraries.

# check Doxygen
DOXYGEN=""
doc=true
dox=
AC_MSG_CHECKING([Generate docs])
AC_ARG_ENABLE(doc,AC_HELP_STRING([--disable-doc], [disable build docs]),
[ if test $enableval = yes; then doc=true; else doc=false; fi],[ doc=true; ])

if test ${doc} = true; then
	AC_MSG_RESULT([yes])
	AC_PATH_PROG([DOXYGEN], [doxygen])
	test "x$DOXYGEN" = "x" && AC_MSG_WARN([*** Doxygen not found])
else
	DOXYGEN=
	AC_MSG_RESULT([no])
fi
AC_SUBST(DOXYGEN)
AM_CONDITIONAL(HAVE_DOXYGEN, test x$DOXYGEN != x)


dnl Python
AM_PATH_PYTHON(,,)
PKG_CHECK_MODULES(PYTHON,python-2.7,,exit)

AC_CONFIG_FILES([Makefile
				docs/Makefile
				docs/dox.cfg
				lib/Makefile
				src/Makefile
				src/Utils/Makefile
				src/guiTestPlayer/Makefile
				src/guiTestPlayer/editors/Makefile
				src/guiTestPlayer/images/Makefile])
		 
AC_OUTPUT
