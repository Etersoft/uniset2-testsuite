DOC_CFG_USER = *dox.cfg

DIRS = html
DOCFILES = ${DIRS}/*.{html,css,png,gif,js}
########################################################################

if HAVE_DOXYGEN
all: user
user: ${DOC_CFG_USER}
	${DOXYGEN} $<

depend :

clean: clean-local

clean-local:
	${RM} ${DOCFILES} *~

re: clean all


# install
ddir = $(docdir)/html
d_DATA = html/*

endif
