CC=gcc
DEPS=bb_gpio.h

all: ecm.c dpa.c
	$(CC) -o ecm -I. -pthread ecm.c
	$(CC) -o dpa -I. -pthread dpa.c 

clean:
	rm ecm
	rm dpa

install:
	cp ecm /usr/bin/
	cp dpa /usr/bin/

uninstall:
	rm /usr/bin/ecm
	rm /usr/bin/dpa

