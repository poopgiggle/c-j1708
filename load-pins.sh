#!/bin/bash

sudo sh -c 'echo 116 > /sys/class/gpio/export'
sudo sh -c 'echo 7 > /sys/class/gpio/export'
sudo sh -c 'echo in > /sys/class/gpio/gpio116/direction'
sudo sh -c 'echo in > /sys/class/gpio/gpio7/direction'
