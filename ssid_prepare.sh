#!/bin/sh

cp /usr/sbin/tcpdump /tmp/
setcap cap_net_raw,cap_net_admin=eip /tmp/tcpdump

iw phy phy0 interface add mon0 type monitor
ip link set mon0 up

