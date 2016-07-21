#!/usr/bin/python
# prepare wlan interface:
# iwconfig wlan0 mode monitor
# ip link set wlan0 up

import subprocess
import re
import os
import sys
import time

maxssid = 10
ssids = []

# terminal colors
class tcolors:
	N = '\033[0;39m'
	R = '\033[1;31m'
	G = '\033[1;32m'
	B = '\033[1;34m'
	W = '\033[1;37m'

# init SSID list
for cnt in range(maxssid):
	ssids.append({})
	ssids[cnt]["name"] = ""
	ssids[cnt]["lastseen"] = 0

def findfree():
	cnt = 0
	while cnt < maxssid:
		if ssids[cnt]["lastseen"] == 0:
			return cnt
		cnt += 1
	return -1

def findssid(name):
	cnt = 0
	while cnt < maxssid:
		if ssids[cnt]["name"] == name:
			return cnt
		cnt += 1
	return -1

def findoldest():
	cnt = 0
	ret = 0
	oldest = ssids[cnt]["lastseen"]
	while cnt < maxssid:
		if ssids[cnt]["lastseen"] < oldest:
			oldest = ssids[cnt]["lastseen"]
			ret = cnt
		cnt += 1
	return ret

def print_ssids():
	# move cursor to 1,1
	sys.stdout.write('\033[H')
	for cnt in range(maxssid):
		age = time.time()-ssids[cnt]["lastseen"]
		# color code age of SSIDs
		if age > 120:
			agecol = tcolors.B
		elif age > 60:
			agecol = tcolors.R
		elif age > 30:
			agecol = tcolors.G
		else:
			agecol = tcolors.W
		name = ssids[cnt]["name"]
		# limit to 32 chars
		if len(name) > 32:
			name = name[0:31]
		# pad to 32 chars, centered
		name = name.center(32)
		print agecol+'** '+name+' **'+tcolors.N

FNULL = open(os.devnull, 'w')
proc = subprocess.Popen(['/tmp/tcpdump', '-lni', 'wlan0', 'type', 'mgt', 'subtype', 'probe-req'], stdout=subprocess.PIPE, stderr=FNULL)

while True:
	ssid_re = re.compile("^.*Probe Request \((.+)\).*$")
	line = proc.stdout.readline()
	if line != '':
		# extract SSID from probe request
		res = ssid_re.match(line)
		if res:
			#print "SSID:", res.group(1), "seen:", time.time()
			ind = findssid(res.group(1))
			if ind == -1:
				# new SSID, find free slot
				ind = findfree()
				if ind == -1:
					# no free slot, replace oldest
					oind = findoldest()
					ssids[oind]["name"] = res.group(1)
					ssids[oind]["lastseen"] = time.time()
				else:
					# fill free slot
					ssids[ind]["name"] = res.group(1)
					ssids[ind]["lastseen"] = time.time()
			else:
				# old SSID, update timestamp
				ssids[ind]["lastseen"] = time.time()
			print_ssids()
	else:
		break

