#!/bin/bash

cp /usr/sbin/tcpdump /tmp/
setcap cap_net_raw,cap_net_admin=eip /tmp/tcpdump

iwconfig wlan0 mode monitor
ip link set wlan0 up

