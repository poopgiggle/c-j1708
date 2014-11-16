CC=gcc
DEPS=bb_gpio.h
XENO_CONFIG:=/usr/bin/xeno-config
XENO_POSIX_CFLAGS:=$(shell $(XENO_CONFIG) --skin=posix --cflags)
XENO_POSIX_LIBS:=$(shell $(XENO_CONFIG) --skin=posix --ldflags)
INSTALL_PREFIX:=/opt/synercon

all: ecm.c dpa.c
	$(CC) -pthread -o ecm $(XENO_POSIX_CFLAGS) $(XENO_POSIX_LIBS) ecm.c
	$(CC) -pthread -o dpa $(XENO_POSIX_CFLAGS) $(XENO_POSIX_LIBS) dpa.c 

clean:
	rm ecm
	rm dpa

install:
	cp ecm $(DESTDIR)/$(INSTALL_PREFIX)/bin
	cp dpa $(DESTDIR)/$(INSTALL_PREFIX)/bin
	cp J1708PassthroughDriver $(DESTDIR)/$(INSTALL_PREFIX)/bin/
	cp J1708Driver.py $(DESTDIR)/usr/local/lib/python3.5/site-packages/
	cp upstart/*.conf /etc/init/
uninstall:
	rm /usr/bin/ecm
	rm /usr/bin/dpa

