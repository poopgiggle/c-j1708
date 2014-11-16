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
	if [ ! -e $(DESTDIR)$(INSTALL_PREFIX)/bin ]; then mkdir -p $(DESTDIR)$(INSTALL_PREFIX)/bin; fi
	cp ecm $(DESTDIR)$(INSTALL_PREFIX)/bin
	cp dpa $(DESTDIR)$(INSTALL_PREFIX)/bin
	cp J1708PassthroughDriver $(DESTDIR)$(INSTALL_PREFIX)/bin/
	if [ ! -e $(DESTDIR)/usr/local/lib/python3.5/site-packages/ ]; then mkdir -p $(DESTDIR)/usr/local/lib/python3.5/site-packages/; fi
	cp J1708Driver.py $(DESTDIR)/usr/local/lib/python3.5/site-packages/
	if [ ! -e $(DESTDIR)/etc/init ]; then mkdir -p $(DESTDIR)/etc/init; fi
	cp upstart/*.conf $(DESTDIR)/etc/init/

uninstall:
	rm $(DESTDIR)$(INSTALL_PREFIX)/bin/ecm
	rm $(DESTDIR)$(INSTALL_PREFIX)/bin/dpa
	rm $(DESTDIR)$(INSTALL_PREFIX)/bin/J1708PassthroughDriver
	rm $(DESTDIR)/usr/local/lib/python3.5/site-packages/J1708Driver.py
	rm $(DESTDIR)/etc/init/dpa.conf
	rm $(DESTDIR)/etc/init/ecm.conf
	rm $(DESTDIR)/etc/init/fwd-j1708.conf


