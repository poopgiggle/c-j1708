CC=gcc
DEPS=bb_gpio.h
XENO_CONFIG:=/usr/bin/xeno-config
XENO_POSIX_CFLAGS:=$(shell $(XENO_CONFIG) --skin=posix --cflags)
XENO_POSIX_LIBS:=$(shell $(XENO_CONFIG) --skin=posix --ldflags)
INSTALL_PREFIX:=/opt/synercon

all: ecm.c dpa.c
	$(CC) -pthread -o ecm $(XENO_POSIX_CFLAGS) $(XENO_POSIX_LIBS) -O4 ecm.c
	$(CC) -pthread -o dpa $(XENO_POSIX_CFLAGS) $(XENO_POSIX_LIBS) -O4 dpa.c 

clean:
	rm ecm
	rm dpa

install:
	if [ ! -e $(DESTDIR)$(INSTALL_PREFIX)/bin ]; then mkdir -p $(DESTDIR)$(INSTALL_PREFIX)/bin; fi
	cp ecm $(DESTDIR)$(INSTALL_PREFIX)/bin
	cp dpa $(DESTDIR)$(INSTALL_PREFIX)/bin
	cp J1708PassthroughDriver $(DESTDIR)$(INSTALL_PREFIX)/bin/
	if [ ! -e $(DESTDIR)/usr/local/lib/python3.5/site-packages/ ]; then mkdir -p $(DESTDIR)/usr/local/lib/python3.5/site-packages/; fi
	cp J1708Driver.py $(DESTDIR)/usr/local/lib/python3.5/site-packages/
	if [ ! -e $(DESTDIR)/etc/init ]; then mkdir -p $(DESTDIR)/etc/init; fi
	cp upstart/*.conf $(DESTDIR)/etc/init/
	if [ ! -e $(DESTDIR)/var/diagnostics/toBeProcessed ]; then mkdir -p $(DESTDIR)/var/diagnostics/toBeProcessed; fi
	if [ ! -e $(DESTDIR)/var/diagnostics/archived ]; then mkdir -p $(DESTDIR)/var/diagnostics/archived; fi


