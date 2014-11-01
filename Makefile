CC=gcc
DEPS=bb_gpio.h
XENO_CONFIG:=/usr/xenomai/bin/xeno-config
XENO_POSIX_CFLAGS:=$(shell $(XENO_CONFIG) --skin=posix --cflags)
XENO_POSIX_LIBS:=$(shell $(XENO_CONFIG) --skin=posix --ldflags)

all: ecm.c dpa.c
	$(CC) -pthread -o ecm $(XENO_POSIX_CFLAGS) $(XENO_POSIX_LIBS) ecm.c
	$(CC) -pthread -o dpa $(XENO_POSIX_CFLAGS) $(XENO_POSIX_LIBS) dpa.c 

clean:
	rm ecm
	rm dpa

install:
	cp ecm /usr/bin/
	cp dpa /usr/bin/

uninstall:
	rm /usr/bin/ecm
	rm /usr/bin/dpa

