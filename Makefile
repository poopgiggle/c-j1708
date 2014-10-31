CC=gcc
DEPS=bb_gpio.h

all: ecm.c dpa.c
	$(CC) -o ecm -I. -pthread ecm.c
	$(CC) -o dpa -I. -pthread dpa.c 


