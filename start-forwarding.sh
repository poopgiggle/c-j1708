#!/bin/bash

sudo rm /var/log/upstart/ecm.log
sudo rm /var/log/upstart/dpa.log
sudo initctl start ecm
sudo initctl start dpa
sudo initctl start fwd-j1708
